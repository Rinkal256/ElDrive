# =========================================================
# Integration Tests for ObstacleLaneFilter (NO TF)
#
# IT-OLF-01 : obstacle + path -> obstacle_on_path FALSE
# IT-OLF-02 : obstacle but NO path -> obstacle_on_path FALSE
# IT-OLF-03 : repeated obstacle -> stable FALSE
# =========================================================

import rclpy
import pytest

from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from eldrive_custom_msgs.msg import Obstacle, ObstacleArray
from std_msgs.msg import Bool


@pytest.mark.ros
def test_OF_Int001_obstacle_with_path_no_tf(ros_node):
    """Obstacle + path, TF not available -> safe FALSE"""

    path_pub = ros_node.create_publisher(Path, "/planned_path", 10)
    obs_pub = ros_node.create_publisher(ObstacleArray, "/obstacle_array", 10)

    states = []

    def cb(msg):
        states.append(msg.data)

    ros_node.create_subscription(Bool, "/obstacle_on_path", cb, 10)

    # Publish path
    path = Path()
    p = PoseStamped()
    p.pose.position.x = 1.0
    p.pose.position.y = 0.0
    path.poses.append(p)
    path_pub.publish(path)

    rclpy.spin_once(ros_node, timeout_sec=0.5)

    # Publish obstacle
    obs = Obstacle()
    obs.obstacle_id = 1
    obs.left_x = 1.0
    obs.left_y = 0.2
    obs.right_x = 1.0
    obs.right_y = -0.2

    arr = ObstacleArray()
    arr.obstacles.append(obs)
    obs_pub.publish(arr)

    rclpy.spin_once(ros_node, timeout_sec=1.0)

    # Safe behavior expected
    assert False in states


@pytest.mark.ros
def test_OF_Int002_obstacle_no_path(ros_node):
    """Obstacle without path -> FALSE"""

    obs_pub = ros_node.create_publisher(ObstacleArray, "/obstacle_array", 10)
    states = []

    def cb(msg):
        states.append(msg.data)

    ros_node.create_subscription(Bool, "/obstacle_on_path", cb, 10)

    obs = Obstacle()
    obs.obstacle_id = 2
    obs.left_x = 1.0
    obs.left_y = 0.2
    obs.right_x = 1.0
    obs.right_y = -0.2

    arr = ObstacleArray()
    arr.obstacles.append(obs)
    obs_pub.publish(arr)

    rclpy.spin_once(ros_node, timeout_sec=1.0)

    assert False in states


@pytest.mark.ros
def test_OF_Int003_repeated_obstacle_stable(ros_node):
    """Repeated obstacle messages -> stable FALSE"""

    obs_pub = ros_node.create_publisher(ObstacleArray, "/obstacle_array", 10)
    states = []

    def cb(msg):
        states.append(msg.data)

    ros_node.create_subscription(Bool, "/obstacle_on_path", cb, 10)

    obs = Obstacle()
    obs.obstacle_id = 3
    obs.left_x = 1.0
    obs.left_y = 0.2
    obs.right_x = 1.0
    obs.right_y = -0.2

    arr = ObstacleArray()
    arr.obstacles.append(obs)

    for _ in range(3):
        obs_pub.publish(arr)
        rclpy.spin_once(ros_node, timeout_sec=0.5)

    assert False in states

