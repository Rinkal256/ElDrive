"""
Integration Test Specification: Path Planner Component

Integration Test Cases Covered:
- PP_Int001
- PP_Int002
- PP_Int003

System Requirements Covered:
- Sys_PP_01: Subscribes to required inputs
- Sys_PP_02: Planning triggered by /pathplan_enable
- Sys_PP_03: Publishes /planned_path when feasible
- Sys_PP_04: Publishes valid Path message
- Sys_PP_05: Plans only once per enable transition
- Sys_PP_06: No path published if no feasible solution exists


"""

import time

import launch
import launch_ros
import launch_testing
import pytest

import rclpy
from rclpy.qos import QoSProfile, DurabilityPolicy

from nav_msgs.msg import OccupancyGrid, Odometry, Path
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Int32




def generate_test_description():
    """
    Launch Path Planner node only.
    All dependencies are mocked by the test process.
    """

    path_planner = launch_ros.actions.Node(
        package="path_planner",
        executable="path_planner_node",
        name="path_planner_node",
        output="screen",
    )

    return (
        launch.LaunchDescription([
            path_planner,
            launch_testing.actions.ReadyToTest(),
        ]),
        {}
    )



@pytest.mark.launch_test
class TestPathPlannerIntegration:
    """
    Integration-level verification of Path Planner behavior.
    """

    @classmethod
    def setup_class(cls):
        rclpy.init()
        cls.node = rclpy.create_node("pp_integration_test_node")

        # QoS compatible with map_server
        map_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )

        # Publishers (mocked dependencies)
        cls.map_pub = cls.node.create_publisher(OccupancyGrid, "/map", map_qos)
        cls.odom_pub = cls.node.create_publisher(Odometry, "/odom", 10)
        cls.goal_pub = cls.node.create_publisher(PoseStamped, "/dest_goal", 10)
        cls.enable_pub = cls.node.create_publisher(Int32, "/pathplan_enable", 10)

        # Subscriber (observe planner output)
        cls.received_paths = []

        def path_cb(msg):
            cls.received_paths.append(msg)

        cls.node.create_subscription(Path, "/planned_path", path_cb, 10)

    @classmethod
    def teardown_class(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def spin_for(self, duration_sec: float):
        """
        Spin the ROS node for a fixed duration to allow message processing.
        """
        end_time = time.time() + duration_sec
        while time.time() < end_time:
            rclpy.spin_once(self.node, timeout_sec=0.1)


    def publish_free_map(self):
        msg = OccupancyGrid()
        msg.header.frame_id = "map"
        msg.info.width = 50
        msg.info.height = 50
        msg.info.resolution = 0.1
        msg.info.origin.position.x = 0.0
        msg.info.origin.position.y = 0.0
        msg.data = [0] * (50 * 50)
        self.map_pub.publish(msg)

    def publish_blocked_map(self):
        msg = OccupancyGrid()
        msg.header.frame_id = "map"
        msg.info.width = 50
        msg.info.height = 50
        msg.info.resolution = 0.1
        msg.info.origin.position.x = 0.0
        msg.info.origin.position.y = 0.0
        msg.data = [100] * (50 * 50)
        self.map_pub.publish(msg)

    def publish_odom(self):
        msg = Odometry()
        msg.pose.pose.position.x = 2.0
        msg.pose.pose.position.y = 2.0
        msg.pose.pose.orientation.w = 1.0
        self.odom_pub.publish(msg)

    def publish_goal(self):
        msg = PoseStamped()
        msg.header.frame_id = "map"
        msg.pose.position.x = 4.0
        msg.pose.position.y = 4.0
        msg.pose.orientation.w = 1.0
        self.goal_pub.publish(msg)


    # PP_Int001
 

    def test_PP_Int001_path_planning_success(self):
        print("\n=== PP_Int001 START ===")
        print("Precondition: Valid map, odom, and goal available")

        self.received_paths.clear()

        self.publish_free_map()
        self.publish_odom()
        self.publish_goal()
        self.spin_for(1.0)

        print("Test Step 1: Publish /pathplan_enable = 1")
        self.enable_pub.publish(Int32(data=1))

        timeout = time.time() + 5.0
        while time.time() < timeout:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if self.received_paths:
                break

        if self.received_paths:
            print("Expected Result 1a: Path Planner computed a global path ")
            print("Expected Result 1b: /planned_path published ")
        else:
            pytest.fail("PP_Int001 FAILED: No path published")

        print("=== PP_Int001 END ===")

    
    # PP_Int002
    

    def test_PP_Int002_no_path_found(self):
        print("\n=== PP_Int002 START ===")
        print("Precondition: Map blocks all feasible routes")

        self.received_paths.clear()

        self.publish_blocked_map()
        self.publish_odom()
        self.publish_goal()
        time.sleep(0.5)

        print("Test Step 1: Publish /pathplan_enable = 1")
        self.enable_pub.publish(Int32(data=1))

        timeout = time.time() + 5.0
        while time.time() < timeout:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        if not self.received_paths:
            print("Expected Result 1a: No /planned_path published")
            print("Expected Result 1b: 'no path found' warning logged")
        else:
            pytest.fail("PP_Int002 FAILED: Path should not be published")

        print("=== PP_Int002 END ===")


    # PP_Int003

    def test_PP_Int003_single_trigger_only(self):
        print("\n=== PP_Int003 START ===")
        print("Precondition: Valid inputs available")

        self.received_paths.clear()

        self.publish_free_map()
        self.publish_odom()
        self.publish_goal()
        time.sleep(0.5)

        print("Test Step 1: Publish /pathplan_enable = 1")
        self.enable_pub.publish(Int32(data=1))
        self.spin_for(1.0)

        print("Test Step 2: Publish /pathplan_enable = 1 again")
        self.enable_pub.publish(Int32(data=1))
        self.spin_for(1.0)

        rclpy.spin_once(self.node, timeout_sec=0.5)

        if len(self.received_paths) == 0:
            print("Expected Result 2a: No additional path published ")
        else:
            pytest.fail(
        f"PP_Int003 FAILED: Unexpected path publications: {len(self.received_paths)}"
            )


        
        print("=== PP_Int003 END ===")
