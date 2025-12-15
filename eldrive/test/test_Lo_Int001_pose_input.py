import rclpy
import time
from rclpy.node import Node
from nav_msgs.msg import Odometry
from mocap4r2_msgs.msg import RigidBodies, RigidBody
from geometry_msgs.msg import Quaternion


class PoseInputTestNode(Node):
    def __init__(self):
        super().__init__("pose_input_test_node")
        self.received_odom = None

        self.pose_pub = self.create_publisher(
            RigidBodies, "/pose_modelcars", 10
        )

        self.odom_sub = self.create_subscription(
            Odometry, "/odom", self.odom_callback, 10
        )

    def odom_callback(self, msg):
        self.received_odom = msg


def test_Lo_Int001_pose_input():
    rclpy.init()
    node = PoseInputTestNode()

    # create dummy pose message
    msg = RigidBodies()
    rb = RigidBody()
    rb.rigid_body_name = "5"
    rb.pose.position.x = 1.0
    rb.pose.position.y = 2.0

    q = Quaternion()
    q.w = 1.0
    rb.pose.orientation = q

    msg.rigidbodies.append(rb)

    # publish
    node.pose_pub.publish(msg)

    # wait for /odom 
    end_time = time.time() + 2.0
    while time.time() < end_time:
        rclpy.spin_once(node, timeout_sec=0.1)
        if node.received_odom is not None:
            break

    # assertions
    assert node.received_odom is not None, "No /odom message received"

    node.destroy_node()
    rclpy.shutdown()

