"""Integration tests for the ROS2 Server node (ADM5)."""

# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring

import time
import json
import pytest
import rclpy
from rclpy.node import Node

from std_msgs.msg import String, Bool, Int32
from geometry_msgs.msg import PoseStamped, Point
from nav_msgs.msg import Path, Odometry
from mocap4r2_msgs.msg import RigidBodies, RigidBody


@pytest.fixture(scope="module")
def ros():
    """Initialize and shutdown rclpy once per test module."""
    rclpy.init()
    yield
    rclpy.shutdown()


class IntegrationNode(Node):  # pylint: disable=too-many-instance-attributes
    """ROS2 helper node used for integration testing of the Server."""

    __test__ = False

    def __init__(self):
        super().__init__(f"integration_test_node_{time.time_ns()}")

        self.login_result = None
        self.login_id = None
        self.auth_id = None
        self.profile = None
        self.quote = None
        self.payment_ok = None
        self.trip_id = None
        self.decision = None
        self.goal = None

        self.position = None
        self.eta = None
        self.stop_index = None
        self.ride_time = None

        # publishers
        self.pub_login = self.create_publisher(
            String, "/auth/login_request", 10
        )
        self.pub_profile = self.create_publisher(
            String, "/profile/request", 10
        )
        self.pub_quote = self.create_publisher(
            String, "/trip/quote_request", 10
        )
        self.pub_payment = self.create_publisher(
            String, "/payment/confirm_request", 10
        )
        self.pub_confirm = self.create_publisher(
            String, "/trip/confirm_request", 10
        )
        self.pub_auth_done = self.create_publisher(
            Bool, "/user_auth_done", 10
        )

        self.pub_pose = self.create_publisher(
            RigidBodies, "/pose_modelcars", 10
        )
        self.pub_odom = self.create_publisher(
            Odometry, "/odom", 10
        )
        self.pub_path = self.create_publisher(
            Path, "/planned_path", 10
        )

        # subscribers
        self.create_subscription(
            Bool,
            "/auth/login_result",
            lambda m: setattr(self, "login_result", m.data),
            10,
        )
        self.create_subscription(
            String,
            "/auth/login_id",
            lambda m: setattr(self, "login_id", m.data),
            10,
        )
        self.create_subscription(
            Int32,
            "/auth_id",
            lambda m: setattr(self, "auth_id", m.data),
            10,
        )
        self.create_subscription(
            String,
            "/profile/response",
            lambda m: setattr(self, "profile", m.data),
            10,
        )
        self.create_subscription(
            String,
            "/trip/quote_response",
            lambda m: setattr(self, "quote", m.data),
            10,
        )
        self.create_subscription(
            Bool,
            "/payment/confirm_result",
            lambda m: setattr(self, "payment_ok", m.data),
            10,
        )
        self.create_subscription(
            String,
            "/trip/confirm_result",
            lambda m: setattr(self, "trip_id", m.data),
            10,
        )
        self.create_subscription(
            Bool,
            "/decision/ride_booked",
            lambda m: setattr(self, "decision", m.data),
            10,
        )
        self.create_subscription(
            PoseStamped,
            "/dest_goal",
            lambda m: setattr(self, "goal", m),
            10,
        )
        self.create_subscription(
            Point,
            "/shuttle/position",
            lambda m: setattr(self, "position", m),
            10,
        )
        self.create_subscription(
            String,
            "/shuttle/eta",
            lambda m: setattr(self, "eta", m.data),
            10,
        )
        self.create_subscription(
            Int32,
            "/shuttle/stop_index",
            lambda m: setattr(self, "stop_index", m.data),
            10,
        )
        self.create_subscription(
            String,
            "/shuttle/ride_time",
            lambda m: setattr(self, "ride_time", m.data),
            10,
        )


def wait_for_discovery(node, timeout=1.0):
    """Allow ROS graph discovery before publishing messages."""
    start = time.time()
    while time.time() - start < timeout:
        rclpy.spin_once(node, timeout_sec=0.1)


def spin_until(node, condition, timeout=3.0):
    """Spin node until condition is true or timeout expires."""
    start = time.time()
    while time.time() - start < timeout:
        rclpy.spin_once(node, timeout_sec=0.1)
        if condition():
            return True
    return False


def publish_pose(node, x, y):
    """Publish a pose for rigid body '5' on /pose_modelcars."""
    rb = RigidBody()
    rb.rigid_body_name = "5"
    rb.pose.position.x = float(x)
    rb.pose.position.y = float(y)

    msg = RigidBodies()
    msg.rigidbodies.append(rb)
    node.pub_pose.publish(msg)


def test_SR_int001_valid_login(ros):
    """
    Precondition:
    - Server node running

    Test Steps:
    1. Publish /auth/login_request "user123" (warm-up for discovery)
    2. Publish /auth/login_request "user123" again
    3. Observe /auth/login_result, /auth/login_id, /auth_id

    Expected Result:
    - /auth/login_result publishes True
    - /auth/login_id publishes "user123"
    - /auth_id publishes 123
    """
    n = IntegrationNode()
    wait_for_discovery(n, timeout=2.0)

    # Reset captured values
    n.login_result = None
    n.login_id = None
    n.auth_id = None

    # Warm-up publish (handles DDS discovery race)
    n.pub_login.publish(String(data="user123"))
    time.sleep(0.2)

    # Clear again to ensure we validate the second publish only
    n.login_result = None
    n.login_id = None
    n.auth_id = None

    # Real publish
    n.pub_login.publish(String(data="user123"))

    assert spin_until(
        n,
        lambda: (
            n.login_result is not None
            and n.login_id is not None
            and n.auth_id is not None
        ),
        timeout=3.0,
    )

    assert n.login_result is True
    assert n.login_id == "user123"
    assert n.auth_id == 123

    n.destroy_node()


def test_SR_int002_invalid_login_empty(ros):
    """
    Precondition:
    - Server node running

    Test Steps:
    1. Publish /auth/login_request with valid data (warm-up)
    2. Publish /auth/login_request with valid data again and wait for outputs
    3. Publish /auth/login_request with empty string
    4. Observe server outputs

    Expected Result:
    - No /auth/login_id is published for the empty request
    - No /auth_id is published for the empty request
    """
    n = IntegrationNode()
    wait_for_discovery(n, timeout=2.0)

    # ----------------------------
    # Step 1–2: warm up DDS path
    # ----------------------------
    n.login_result = None
    n.login_id = None
    n.auth_id = None

    n.pub_login.publish(String(data="tempuser"))
    time.sleep(0.2)

    # Clear to validate second publish
    n.login_result = None
    n.login_id = None
    n.auth_id = None

    n.pub_login.publish(String(data="tempuser"))

    assert spin_until(
        n,
        lambda: (
            n.login_result is not None
            and n.login_id is not None
            and n.auth_id is not None
        ),
        timeout=3.0,
    )

    # ----------------------------
    # Step 3–4: invalid empty login
    # ----------------------------
    n.login_result = None
    n.login_id = None
    n.auth_id = None

    n.pub_login.publish(String(data=""))

    # We only wait for login_result to confirm request was processed
    assert spin_until(n, lambda: n.login_result is not None, timeout=3.0)

    # Critical requirement: NO side-effects
    assert n.login_id is None
    assert n.auth_id is None

    n.destroy_node()


def test_SR_int003_profile_request(ros):
    n = IntegrationNode()
    wait_for_discovery(n)

    n.pub_profile.publish(String(data="user123"))

    assert spin_until(n, lambda: n.profile is not None)
    profile = json.loads(n.profile)
    assert profile["user_id"] == "user123"

    n.destroy_node()


def test_SR_int004_quote_request(ros):
    n = IntegrationNode()
    wait_for_discovery(n)

    n.pub_quote.publish(
        String(data=json.dumps({"destination": {"id": "dest1"}}))
    )

    assert spin_until(n, lambda: n.quote is not None)
    quote = json.loads(n.quote)
    assert quote["ok"] is True

    n.destroy_node()


def test_SR_int005_payment_confirm(ros):
    """
    Precondition:
    - Server node running

    Test Steps:
    1. Publish /payment/confirm_request "ok" (warm-up)
    2. Publish /payment/confirm_request "ok" again
    3. Observe /payment/confirm_result

    Expected Result:
    - /payment/confirm_result publishes True
    """
    n = IntegrationNode()
    wait_for_discovery(n, timeout=2.0)

    n.payment_ok = None

    # Warm-up publish (avoid DDS discovery race)
    n.pub_payment.publish(String(data="ok"))
    time.sleep(0.2)

    # Clear and publish again for the actual assertion
    n.payment_ok = None
    n.pub_payment.publish(String(data="ok"))

    assert spin_until(n, lambda: n.payment_ok is not None, timeout=3.0)
    assert n.payment_ok is True

    n.destroy_node()


def test_SR_int006_trip_confirm_and_boarding_goal(ros):
    n = IntegrationNode()
    wait_for_discovery(n)

    n.pub_login.publish(String(data="user123"))
    assert spin_until(n, lambda: n.login_result is not None, timeout=3.0)
    assert spin_until(n,lambda: (n.login_id is not None and n.auth_id is not None),timeout=3.0,)

    n.pub_quote.publish(
        String(data=json.dumps({"destination": {"id": "dest1"}}))
    )
    assert spin_until(n, lambda: n.quote is not None, timeout=3.0)

    n.pub_confirm.publish(String(data="confirm"))

    assert spin_until(n, lambda: n.trip_id is not None, timeout=3.0)
    assert spin_until(n, lambda: n.decision is not None, timeout=3.0)
    assert spin_until(n, lambda: n.goal is not None, timeout=3.0)

    assert n.decision is True
    assert isinstance(n.goal, PoseStamped)

    n.destroy_node()

def test_SR_int007_valid_pose_position_forwarding(ros):
    """
    Precondition:
    - Server node running
    - Localization data available

    Test Steps:
    1. Publish /pose_modelcars with valid rigid body (warm-up)
    2. Publish /pose_modelcars again
    3. Observe /shuttle/position

    Expected Result:
    - /shuttle/position publishes a Point matching the pose
    """
    n = IntegrationNode()
    wait_for_discovery(n, timeout=2.0)

    # Reset captured value
    n.position = None

    # Warm-up publish (handles DDS discovery)
    publish_pose(n, 1.0, 1.0)
    time.sleep(0.2)

    # Clear and publish again for real validation
    n.position = None
    publish_pose(n, 1.0, 1.0)

    assert spin_until(n, lambda: n.position is not None, timeout=3.0)
    assert n.position.x == pytest.approx(1.0)
    assert n.position.y == pytest.approx(1.0)

    n.destroy_node()


def test_SR_int008_eta_positive_velocity(ros):
    n = IntegrationNode()
    wait_for_discovery(n)

    path = Path()
    for i in range(5):
        pose = PoseStamped()
        pose.pose.position.x = float(i)
        pose.pose.position.y = 0.0
        path.poses.append(pose)
    n.pub_path.publish(path)

    publish_pose(n, 1.0, 1.0)
    time.sleep(0.1)

    odom = Odometry()
    odom.twist.twist.linear.x = 1.0
    n.pub_odom.publish(odom)

    assert spin_until(n, lambda: n.eta is not None, timeout=3.0)
    assert float(n.eta) >= 0.0

    n.destroy_node()


def test_SR_int009_stop_index_increment(ros):
    """
    Precondition:
    - Server node running
    - Trip has been confirmed

    Test Steps:
    1. Publish /auth/login_request
    2. Publish /trip/quote_request
    3. Publish /trip/confirm_request
    4. Publish localization poses entering stop regions

    Expected Result:
    - /shuttle/stop_index increments correctly
    """
    n = IntegrationNode()
    wait_for_discovery(n)

    # Step 1: login
    n.pub_login.publish(String(data="user123"))
    assert spin_until(n, lambda: n.login_result is not None, timeout=3.0)

    # Step 2: quote request (sets destination internally)
    n.pub_quote.publish(
        String(data=json.dumps({"destination": {"id": "dest1"}}))
    )
    assert spin_until(n, lambda: n.quote is not None, timeout=3.0)

    # Step 3: confirm trip
    n.pub_confirm.publish(String(data="confirm"))
    assert spin_until(n, lambda: n.trip_id is not None, timeout=3.0)

    # Step 4: move into first stop ROI
    publish_pose(n, 0.5, 0.5)   # outside
    time.sleep(0.1)
    publish_pose(n, 1.5, 0.5)   # inside Kronach

    assert spin_until(n, lambda: n.stop_index is not None, timeout=3.0)
    assert n.stop_index >= 1

    n.destroy_node()


def test_SR_int010_ride_time_published(ros):
    n = IntegrationNode()
    wait_for_discovery(n)

    stops = [
        (1.5, 0.5),
        (0.5, 1.5),
        (0.5, 3.5),
        (1.5, 4.5),
        (3.5, 5.5),
    ]
    for x, y in stops:
        publish_pose(n, x, y)
        time.sleep(0.1)

    assert spin_until(n, lambda: n.ride_time is not None)
    assert float(n.ride_time) > 0.0

    n.destroy_node()

