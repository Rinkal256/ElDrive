import rclpy
import time
import math
from rclpy.node import Node
from nav_msgs.msg import Odometry
from mocap4r2_msgs.msg import RigidBodies, RigidBody
from geometry_msgs.msg import Quaternion


class OdomOutputTestNode(Node):
    def __init__(self):
        super().__init__("odom_output_test_node")
        self.received_odom = None

        self.pose_pub = self.create_publisher(
            RigidBodies, "/pose_modelcars", 10
        )
        self.odom_sub = self.create_subscription(
            Odometry, "/odom", self.odom_callback, 10
        )

    def odom_callback(self, msg):
        self.received_odom = msg


def test_Lo_Int003_odom_output():
    rclpy.init()
    node = OdomOutputTestNode()

    # prepare pose message
    msg = RigidBodies()
    rb = RigidBody()
    rb.rigid_body_name = "5"
    rb.pose.position.x = 3.0
    rb.pose.position.y = 4.0
    q = Quaternion()
    q.w = 1.0
    rb.pose.orientation = q
    msg.rigidbodies.append(rb)

    # publish pose multiple times
    start_time = time.time()
    while time.time() - start_time < 1.0:
        node.pose_pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.05)

    # wait for odom (allow several EKF cycles)
    end_time = time.time() + 3.0
    while time.time() < end_time:
        rclpy.spin_once(node, timeout_sec=0.1)
        if node.received_odom is not None:
            break

    assert node.received_odom is not None, "Localization did not publish /odom"

    # validate content (black-box)
    x = node.received_odom.pose.pose.position.x
    y = node.received_odom.pose.pose.position.y
    q_out = node.received_odom.pose.pose.orientation

    assert not math.isnan(x)
    assert not math.isnan(y)
    assert q_out.w != 0.0

    node.destroy_node()
    rclpy.shutdown()

