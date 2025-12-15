# =========================================================
# Integration Tests for DecisionMaker
#
# IT-DM-01 : ride booked -> driving enabled
# IT-DM-02 : destination reached + door open -> access granted
# IT-DM-03 : door closed after boarding -> driving resumes
# =========================================================

import rclpy
import pytest

from std_msgs.msg import Bool, Int32


@pytest.mark.ros
def test_DM_Int001_ride_booked_to_driving(ros_node):
    """Ride booked in IDLE -> pathplan_enable = DRIVING (1)"""

    ride_pub = ros_node.create_publisher(Bool, "/decision/ride_booked", 10)
    states = []

    def cb(msg):
        states.append(msg.data)

    ros_node.create_subscription(Int32, "/pathplan_enable", cb, 10)

    # Send ride booked
    ride_pub.publish(Bool(data=True))
    rclpy.spin_once(ros_node, timeout_sec=1.0)

    # DRIVING = 1
    assert 1 in states


@pytest.mark.ros
def test_DM_Int002_destination_and_door_open(ros_node):
    """Reached destination + door open -> access_permission = True"""

    dest_pub = ros_node.create_publisher(Bool, "/dest_reached", 10)
    door_pub = ros_node.create_publisher(Bool, "/door_state", 10)

    access = []

    def cb(msg):
        access.append(msg.data)

    ros_node.create_subscription(Bool, "/access_permission", cb, 10)

    # Simulate reaching destination
    dest_pub.publish(Bool(data=True))
    rclpy.spin_once(ros_node, timeout_sec=0.5)

    # Door opens
    door_pub.publish(Bool(data=True))
    rclpy.spin_once(ros_node, timeout_sec=1.0)

    assert True in access


@pytest.mark.ros
def test_DM_Int003_door_close_after_boarding(ros_node):
    """Door closes after boarding -> driving resumes"""

    door_pub = ros_node.create_publisher(Bool, "/door_state", 10)
    states = []

    def cb(msg):
        states.append(msg.data)

    ros_node.create_subscription(Int32, "/pathplan_enable", cb, 10)

    # Door closes (boarding finished)
    door_pub.publish(Bool(data=False))
    rclpy.spin_once(ros_node, timeout_sec=1.0)

    # Expect DRIVING state again
    assert 1 in states
