
import rclpy
import pytest
from sensor_msgs.msg import LaserScan
from eldrive_custom_msgs.msg import ObstacleArray

@pytest.mark.ros
def test_OD_Int001_scan_to_output(ros_node):

    scan_pub = ros_node.create_publisher(LaserScan, "/scan", 10)
    received = []

    def cb(msg):
        received.append(msg)

    ros_node.create_subscription(
        ObstacleArray,
        "/obstacle_array",
        cb,
        10
    )

    scan = LaserScan()
    scan.header.frame_id = "laser_frame"
    scan.angle_min = -1.57
    scan.angle_increment = 0.01
    scan.ranges = [float("inf")] * 314
    scan.ranges[157] = 1.0 

    scan_pub.publish(scan)
    rclpy.spin_once(ros_node, timeout_sec=1.5)

    assert len(received) > 0
    
def test_OD_Int002_tf_missing(ros_node):

    scan_pub = ros_node.create_publisher(LaserScan, "/scan", 10)
    received = []

    def cb(msg):
        received.append(msg)

    ros_node.create_subscription(
        ObstacleArray,
        "/obstacle_array",
        cb,
        10
    )

    scan = LaserScan()
    scan.header.frame_id = "laser_frame"
    scan.angle_min = -1.57
    scan.angle_increment = 0.01
    scan.ranges = [float("inf")] * 314
    scan.ranges[157] = 1.0

    scan_pub.publish(scan)
    rclpy.spin_once(ros_node, timeout_sec=1.5)

    if len(received) > 0:
        assert len(received[0].obstacles) == 0
