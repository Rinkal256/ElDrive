
import rclpy
import pytest
import numpy as np

from builtin_interfaces.msg import Time
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from eldrive_custom_msgs.msg import FusionObjectArray


def now_msg(node):
    t = node.get_clock().now().to_msg()
    return t


@pytest.mark.ros
def test_SF_Int001_detection_and_depth(ros_node):
    """Detection + depth image -> fusion output published"""

    det_pub = ros_node.create_publisher(
        Detection2DArray, "/detectnet/detections", 10
    )
    depth_pub = ros_node.create_publisher(
        Image, "/camera/camera/depth/image_rect_raw", 10
    )

    received = []

    def cb(msg):
        received.append(msg)

    ros_node.create_subscription(
        FusionObjectArray, "/detected_objects_pos", cb, 10
    )

    stamp = now_msg(ros_node)

    # -------- Depth Image --------
    depth = np.ones((480, 640), dtype=np.uint16) * 1000
    depth_msg = Image()
    depth_msg.header.stamp = stamp
    depth_msg.height = 480
    depth_msg.width = 640
    depth_msg.encoding = "16UC1"
    depth_msg.step = 640 * 2
    depth_msg.data = depth.tobytes()

    # -------- Detection --------
    det = Detection2D()
    det.bbox.center.position.x = 320.0
    det.bbox.center.position.y = 240.0
    det.bbox.size_x = 50.0
    det.bbox.size_y = 100.0

    hyp = ObjectHypothesisWithPose()
    hyp.hypothesis.class_id = "A"
    hyp.hypothesis.score = 0.9
    det.results.append(hyp)

    det_array = Detection2DArray()
    det_array.header.stamp = stamp
    det_array.detections.append(det)

    depth_pub.publish(depth_msg)
    det_pub.publish(det_array)

    rclpy.spin_once(ros_node, timeout_sec=2.0)

    # At least one fusion output must be published
    assert len(received) >= 1


@pytest.mark.ros
def test_SF_Int002_empty_detection_safe(ros_node):
    """Empty detection -> node stays stable (message_filters may still fire)"""

    det_pub = ros_node.create_publisher(
        Detection2DArray, "/detectnet/detections", 10
    )

    received = []

    def cb(msg):
        received.append(msg)

    ros_node.create_subscription(
        FusionObjectArray, "/detected_objects_pos", cb, 10
    )

    empty = Detection2DArray()
    empty.header.stamp = now_msg(ros_node)

    det_pub.publish(empty)
    rclpy.spin_once(ros_node, timeout_sec=1.5)

    # Integration test goal: no crash, valid message if published
    if received:
        assert isinstance(received[0], FusionObjectArray)

