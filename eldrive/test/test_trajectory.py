import os
import signal
import subprocess
import time

import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

from std_msgs.msg import Bool
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped
from ackermann_msgs.msg import AckermannDrive


# ----------------------------
# Helpers
# ----------------------------
def make_path(points):
    """Create nav_msgs/Path from list[(x,y)]."""
    path = Path()
    for x, y in points:
        ps = PoseStamped()
        ps.pose.position.x = float(x)
        ps.pose.position.y = float(y)
        path.poses.append(ps)
    return path


def make_odom(node: Node, x, y, vx=0.3):
    """Create Odometry with fresh header stamp and basic orientation."""
    odom = Odometry()
    odom.header.stamp = node.get_clock().now().to_msg()  # critical for your stale-odom check
    odom.pose.pose.position.x = float(x)
    odom.pose.pose.position.y = float(y)
    odom.pose.pose.orientation.w = 1.0
    odom.twist.twist.linear.x = float(vx)
    return odom


def wait_for(predicate, timeout_s=5.0, sleep_s=0.05):
    start = time.time()
    while time.time() - start < timeout_s:
        if predicate():
            return True
        time.sleep(sleep_s)
    return False


# ----------------------------
# Controller process fixture
# ----------------------------
@pytest.fixture
def controller_process():
    """
    Start a fresh trajectory_controller node for each test.
    This avoids state leakage (have_path/current_index) between TC_Int00X tests.
    """
    # Ensure ros2 CLI is available
    cmd = ["ros2", "run", "trajectory_controller", "trajectory_controller"]

    env = os.environ.copy()

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        preexec_fn=os.setsid,  # allow killing the whole process group
    )

    # Give DDS + node time to come up
    time.sleep(2.0)

    yield proc

    # Cleanup
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        proc.wait(timeout=5.0)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass


# ----------------------------
# Test node fixture (publish/subscribe)
# ----------------------------
@pytest.fixture
def test_node(controller_process):
    rclpy.init()
    node = Node("trajectory_integration_test_node")
    executor = SingleThreadedExecutor()
    executor.add_node(node)

    # Captured outputs
    received_cmds = []
    dest_reached_msgs = []

    def cmd_cb(msg: AckermannDrive):
        received_cmds.append(msg)

    def dest_cb(msg: Bool):
        dest_reached_msgs.append(msg)

    node.create_subscription(AckermannDrive, "/ackermann_drive", cmd_cb, 10)
    node.create_subscription(Bool, "/dest_reached", dest_cb, 10)

    odom_pub = node.create_publisher(Odometry, "/odom", 10)
    path_pub = node.create_publisher(Path, "/planned_path", 10)
    signal_pub = node.create_publisher(Bool, "/traffic_light_go", 10)
    obstacle_pub = node.create_publisher(Bool, "/obstacle_on_path", 10)

    # Allow discovery between pubs/subs and controller
    time.sleep(1.0)

    # Convenience API on the node object
    node._executor = executor
    node._received_cmds = received_cmds
    node._dest_msgs = dest_reached_msgs
    node._odom_pub = odom_pub
    node._path_pub = path_pub
    node._signal_pub = signal_pub
    node._obstacle_pub = obstacle_pub

    def spin_for(seconds: float):
        end = time.time() + seconds
        while time.time() < end:
            executor.spin_once(timeout_sec=0.1)

    node.spin_for = spin_for

    def publish_signal(go: bool):
        signal_pub.publish(Bool(data=bool(go)))

    def publish_obstacle(ob: bool):
        obstacle_pub.publish(Bool(data=bool(ob)))

    def publish_path(points):
        path_pub.publish(make_path(points))

    def publish_odom(x, y, vx=0.3):
        odom_pub.publish(make_odom(node, x, y, vx=vx))

    node.publish_signal = publish_signal
    node.publish_obstacle = publish_obstacle
    node.publish_path = publish_path
    node.publish_odom = publish_odom

    yield node

    executor.remove_node(node)
    node.destroy_node()
    rclpy.shutdown()


# ----------------------------
# Integration Test Cases TC_Int001 ... TC_Int007
# ----------------------------

def test_TC_Int001_motion_on_valid_inputs(test_node):
    test_node._received_cmds.clear()

    test_node.publish_signal(True)
    test_node.publish_obstacle(False)
    test_node.publish_path([(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)])
    test_node.publish_odom(0.0, 0.0, vx=0.3)

    test_node.spin_for(3.0)

    assert len(test_node._received_cmds) > 0, "No AckermannDrive published"
    assert test_node._received_cmds[-1].speed > 0.0, "Speed is not > 0.0"


def test_TC_Int002_stop_on_red_signal(test_node):
    test_node._received_cmds.clear()

    # Start moving first
    test_node.publish_signal(True)
    test_node.publish_obstacle(False)
    test_node.publish_path([(0.0, 0.0), (2.0, 0.0)])
    test_node.publish_odom(0.0, 0.0, vx=0.3)
    test_node.spin_for(2.0)
    assert any(cmd.speed > 0.0 for cmd in test_node._received_cmds), "Did not start moving"

    # Red light
    test_node._received_cmds.clear()
    test_node.publish_signal(False)
    test_node.publish_odom(0.2, 0.0, vx=0.3)
    test_node.spin_for(2.0)

    assert len(test_node._received_cmds) > 0, "No AckermannDrive stop command published"
    last = test_node._received_cmds[-1]
    assert last.speed == 0.0 and last.steering_angle == 0.0, "Did not stop on red signal"


def test_TC_Int003_resume_on_green_signal(test_node):
    test_node._received_cmds.clear()

    # Move then stop on red
    test_node.publish_signal(True)
    test_node.publish_obstacle(False)
    test_node.publish_path([(0.0, 0.0), (2.0, 0.0)])
    test_node.publish_odom(0.0, 0.0, vx=0.3)
    test_node.spin_for(2.0)

    test_node.publish_signal(False)
    test_node.publish_odom(0.3, 0.0, vx=0.3)
    test_node.spin_for(1.5)

    # Resume on green
    test_node._received_cmds.clear()
    test_node.publish_signal(True)
    test_node.publish_odom(0.35, 0.0, vx=0.3)
    test_node.spin_for(3.0)

    assert any(cmd.speed > 0.0 for cmd in test_node._received_cmds), "Did not resume after green signal"


def test_TC_Int004_stop_on_obstacle(test_node):
    test_node._received_cmds.clear()

    # Start moving
    test_node.publish_signal(True)
    test_node.publish_obstacle(False)
    test_node.publish_path([(0.0, 0.0), (2.0, 0.0)])
    test_node.publish_odom(0.0, 0.0, vx=0.3)
    test_node.spin_for(2.0)
    assert any(cmd.speed > 0.0 for cmd in test_node._received_cmds), "Did not start moving"

    # Obstacle appears
    test_node._received_cmds.clear()
    test_node.publish_obstacle(True)
    test_node.publish_odom(0.2, 0.0, vx=0.3)
    test_node.spin_for(2.0)

    assert len(test_node._received_cmds) > 0, "No AckermannDrive stop command published"
    last = test_node._received_cmds[-1]
    assert last.speed == 0.0 and last.steering_angle == 0.0, "Did not stop on obstacle"


def test_TC_Int005_resume_after_obstacle_cleared(test_node):
    test_node._received_cmds.clear()

    # Move then stop due to obstacle
    test_node.publish_signal(True)
    test_node.publish_obstacle(False)
    test_node.publish_path([(0.0, 0.0), (2.0, 0.0)])
    test_node.publish_odom(0.0, 0.0, vx=0.3)
    test_node.spin_for(2.0)

    test_node.publish_obstacle(True)
    test_node.publish_odom(0.2, 0.0, vx=0.3)
    test_node.spin_for(1.5)

    # Clear obstacle
    test_node._received_cmds.clear()
    test_node.publish_obstacle(False)
    test_node.publish_odom(0.25, 0.0, vx=0.3)
    test_node.spin_for(3.0)

    assert any(cmd.speed > 0.0 for cmd in test_node._received_cmds), "Did not resume after obstacle cleared"


def test_TC_Int006_destination_reached(test_node):
    """
    Destination reached in YOUR controller:
    - dist_to_goal < final_stop_tolerance triggers stop_robot(True)
    - stop_motion publishes AckermannDrive(speed=0)
    - /dest_reached publishes Bool(True) once
    """
    test_node._received_cmds.clear()
    test_node._dest_msgs.clear()

    test_node.publish_signal(True)
    test_node.publish_obstacle(False)

    # Use a path long enough to generate normal motion first
    # and then enter goal tolerance near the end.
    test_node.publish_path([(0.0, 0.0), (2.0, 0.0)])

    # Step 1: start moving
    test_node.publish_odom(0.0, 0.0, vx=0.3)
    test_node.spin_for(1.5)
    assert any(cmd.speed > 0.0 for cmd in test_node._received_cmds), "Did not start moving"

    # Step 2: move near the final waypoint (goal at 2.0,0.0)
    # final_stop_tolerance in your controller is 0.45 (or similar),
    # so 1.7 is within 0.3m -> should trigger destination.
    test_node._received_cmds.clear()
    test_node.publish_odom(1.75, 0.0, vx=0.3)
    test_node.spin_for(3.0)

    # Expected:
    # 1) Bool(True) on /dest_reached
    # 2) At least one stop command on /ackermann_drive (speed == 0)
    reached = any(m.data is True for m in test_node._dest_msgs)
    stopped = any(cmd.speed == 0.0 for cmd in test_node._received_cmds)

    assert reached, "Destination reached signal (/dest_reached True) not published"
    assert stopped, "Stop command (AckermannDrive speed=0) not published at destination"


def test_TC_Int007_no_motion_without_inputs(test_node):
    test_node._received_cmds.clear()

    # No odom, no path: controller should publish nothing
    test_node.publish_signal(True)
    test_node.publish_obstacle(False)

    test_node.spin_for(2.0)

    assert len(test_node._received_cmds) == 0, "AckermannDrive published without required inputs"
