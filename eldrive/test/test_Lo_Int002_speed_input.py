import rclpy
import time
from rclpy.node import Node
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDrive
from mocap4r2_msgs.msg import RigidBodies, RigidBody
from geometry_msgs.msg import Quaternion


class SpeedInputTestNode(Node):
    def __init__(self):
        super().__init__("speed_input_test_node")
        self.received_odom = None

        self.pose_pub = self.create_publisher(
            RigidBodies, "/pose_modelcars", 10
        )
        self.speed_pub = self.create_publisher(
            AckermannDrive, "/ackermann_drive_feedback", 10
        )
        self.odom_sub = self.create_subscription(
            Odometry, "/odom", self.odom_callback, 10
        )

    def odom_callback(self, msg):
        self.received_odom = msg


def test_Lo_Int002_speed_input():
    rclpy.init()
    node = SpeedInputTestNode()

    # initialize localization with pose
    pose_msg = RigidBodies()
    rb = RigidBody()
    rb.rigid_body_name = "5"
    rb.pose.position.x = 0.0
    rb.pose.position.y = 0.0
    q = Quaternion()
    q.w = 1.0
    rb.pose.orientation = q
    pose_msg.rigidbodies.append(rb)
    node.pose_pub.publish(pose_msg)

    time.sleep(0.2)

    # publish speed
    speed_msg = AckermannDrive()
    speed_msg.speed = 1.0
    node.speed_pub.publish(speed_msg)

    # wait for odom
    end_time = time.time() + 2.0
    while time.time() < end_time:
        rclpy.spin_once(node, timeout_sec=0.1)
        if node.received_odom is not None:
            break

    assert node.received_odom is not None, "No /odom published after speed input"

    node.destroy_node()
    rclpy.shutdown()

