import time
import json
import pytest
import rclpy
from rclpy.node import Node

from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped


@pytest.fixture(scope="module")
def ros():
    rclpy.init()
    yield
    rclpy.shutdown()


class PipelineNode(Node):
    __test__ = False

    def __init__(self):
        super().__init__(f"ua_pipeline_test_node_{time.time_ns()}")

        # captured outputs
        self.auth_done = None
        self.goal = None

        # publishers (inputs)
        self.pub_login_id = self.create_publisher(String, "/auth/login_id", 10)
        self.pub_user_input = self.create_publisher(String, "/auth/user_input", 10)

        # for end-to-end with server
        self.pub_login_req = self.create_publisher(String, "/auth/login_request", 10)
        self.pub_quote_req = self.create_publisher(String, "/trip/quote_request", 10)
        self.pub_confirm_req = self.create_publisher(String, "/trip/confirm_request", 10)

        # subscribers (outputs)
        self.create_subscription(Bool, "/user_auth_done", lambda m: setattr(self, "auth_done", m.data), 10)
        self.create_subscription(PoseStamped, "/dest_goal", lambda m: setattr(self, "goal", m), 10)


def wait_for_discovery(node, timeout=1.0):
    start = time.time()
    while time.time() - start < timeout:
        rclpy.spin_once(node, timeout_sec=0.1)


def spin_until(node, condition, timeout=3.0):
    start = time.time()
    while time.time() - start < timeout:
        rclpy.spin_once(node, timeout_sec=0.1)
        if condition():
            return True
    return False


def test_SR_UA_int001_auth_success(ros):
    """
    Precondition:
    - UserAuthorization node running

    Test Steps:
    1. Publish mismatching IDs to reset auth state
    2. Publish matching IDs

    Expected Result:
    - /user_auth_done publishes True
    """
    n = PipelineNode()
    wait_for_discovery(n)

    # Step 0: force state reset (ensure last_state != True)
    n.pub_login_id.publish(String(data="user123"))
    time.sleep(0.1)
    n.pub_user_input.publish(String(data="wrong"))
    spin_until(n, lambda: n.auth_done is not None, timeout=2.0)

    # Reset captured value
    n.auth_done = None

    # Step 1–2: now test success
    n.pub_login_id.publish(String(data="user123"))
    time.sleep(0.1)
    n.pub_user_input.publish(String(data="user123"))

    assert spin_until(n, lambda: n.auth_done is not None, timeout=3.0)
    assert n.auth_done is True

    n.destroy_node()



def test_SR_UA_int002_auth_failure(ros):
    """
    Precondition:
    - Server node running
    - UserAuthorization node running

    Test Steps:
    1. Publish /auth/login_request "user123"
    2. Publish /auth/user_input "wrong"

    Expected Result:
    - /user_auth_done publishes False
    """
    n = PipelineNode()
    wait_for_discovery(n)

    # Step 1: let server publish /auth/login_id
    n.pub_login_req.publish(String(data="user123"))
    time.sleep(0.3)  # allow UA to receive login_id

    # Step 2: wrong user input
    n.pub_user_input.publish(String(data="wrong"))

    assert spin_until(n, lambda: n.auth_done is not None, timeout=3.0)
    assert n.auth_done is False

    n.destroy_node()


def test_SR_UA_int003_missing_input_no_publish(ros):
    """
    Precondition:
    - UserAuthorization node running

    Test Steps:
    1. Publish only /auth/login_id "user123"
    2. Wait

    Expected Result:
    - No /user_auth_done published
    """
    n = PipelineNode()
    wait_for_discovery(n)

    n.pub_login_id.publish(String(data="user123"))
    ok = spin_until(n, lambda: n.auth_done is not None, timeout=1.5)

    assert ok is False
    assert n.auth_done is None

    n.destroy_node()


def test_SR_UA_int004_end_to_end_auth_triggers_destination_goal(ros):
    """
    Precondition:
    - Server node running
    - UserAuthorization node running

    Test Steps:
    1. Publish /auth/login_request "user123"
    2. Publish /trip/quote_request with destination id "dest1"
    3. Publish /trip/confirm_request
    4. Publish /auth/user_input "user123"
    5. Observe /user_auth_done and /dest_goal

    Expected Result:
    - /user_auth_done publishes True
    - A /dest_goal is published after auth completion
    """
    n = PipelineNode()
    wait_for_discovery(n)

    # Step 1: trigger server to publish /auth/login_id
    n.pub_login_req.publish(String(data="user123"))
    time.sleep(0.4)  # allow UA to receive login_id

    # Step 2: set destination in server
    n.pub_quote_req.publish(
        String(data=json.dumps({"destination": {"id": "dest1"}}))
    )
    time.sleep(0.4)

    # Step 3: confirm trip
    # Boarding goal may be published before subscriber discovery — do not assert on it
    n.pub_confirm_req.publish(String(data="confirm"))
    time.sleep(0.4)  # allow server internal state update

    # ---------------------------------------------------------
    # Step 4: Authorization sequence (force synchronization)
    # ---------------------------------------------------------

    # Reset captured values
    n.auth_done = None
    n.goal = None

    # First: correct input to guarantee UA has server_login_id
    n.pub_user_input.publish(String(data="user123"))
    assert spin_until(n, lambda: n.auth_done is not None, timeout=3.0)
    assert n.auth_done is True

    # Reset capture
    n.auth_done = None

    # Second: wrong input → force failure
    n.pub_user_input.publish(String(data="wrong"))
    assert spin_until(n, lambda: n.auth_done is not None, timeout=3.0)
    assert n.auth_done is False

    # Reset capture
    n.auth_done = None

    # Third: correct input again → recovery
    n.pub_user_input.publish(String(data="user123"))
    assert spin_until(n, lambda: n.auth_done is not None, timeout=3.0)
    assert n.auth_done is True

    # ---------------------------------------------------------
    # Step 5: destination goal must be published AFTER auth
    # ---------------------------------------------------------
    assert spin_until(n, lambda: n.goal is not None, timeout=3.0)

    n.destroy_node()


	



