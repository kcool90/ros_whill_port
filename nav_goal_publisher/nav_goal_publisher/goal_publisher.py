#!/usr/bin/env python3
import math
import json
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from pyproj import Transformer
import tf2_ros
from rclpy.duration import Duration
from rclpy.time import Time

class GoalPublisher(Node):
    def __init__(self):
        super().__init__('goal_publisher')
        # Publisher for goal poses.
        self.goal_pub = self.create_publisher(PoseStamped, 'goal_pose', 10)
        # Subscriber to get the robot's current odometry (assumed in the "odom" frame).
        self.odom_sub = self.create_subscription(Odometry, 'odom_imu', self.odom_callback, 10)
        # Subscriber to receive dynamic GPS waypoints as a JSON string.
        self.waypoints_sub = self.create_subscription(String, 'gps_waypoints', self.waypoints_callback, 10)
        # Timer to periodically check if the current goal is reached and publish the next one.
        self.timer = self.create_timer(1.0, self.check_and_publish_goal)
        
        # Set up the transformer: convert GPS (WGS84, EPSG:4326) to UTM (for Missouri, use EPSG:32615).
        self.transformer = Transformer.from_crs("epsg:4326", "epsg:32615", always_xy=True)
        
        # Hardcoded list of GPS waypoints as (latitude, longitude).
        # (These are absolute GPS coordinates. You can later have these come from another node.)
        self.gps_waypoints = []
        
        # Current goal in local (odom) frame as a tuple (x, y).
        self.current_goal = None
        
        # A threshold (in meters) for considering a goal "reached."
        self.goal_threshold = 1.0
        
        # To compare with the current robot pose.
        self.current_pose = None
        
        # Set up a TF listener to retrieve the datum offset from the navsat_transform node.
        # (navsat_transform publishes a transform from "utm" to "odom")
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

    def odom_callback(self, msg: Odometry):
        # Update the current robot pose (in the "odom" frame).
        self.current_pose = msg.pose.pose

    def waypoints_callback(self, msg: String):
        # Expect the message data to be a JSON string representing a list of waypoints.
        # Example JSON: "[[38.6362228, -90.22785], [38.6363101, -90.2282702], ...]"
        try:
            waypoints = json.loads(msg.data)
            # Ensure each waypoint is a tuple of floats (lat, lon)
            self.gps_waypoints = [(float(wp[0]), float(wp[1])) for wp in waypoints]
            self.get_logger().info(f"Received dynamic waypoints: {self.gps_waypoints}")
        except Exception as e:
            self.get_logger().error(f"Error parsing waypoints: {e}")

    def check_and_publish_goal(self):
        # If no current goal and waypoints remain, compute and publish the next goal.
        if self.current_goal is None and self.gps_waypoints:
            waypoint = self.gps_waypoints.pop(0)
            lat, lon = waypoint  # Waypoints are provided as (lat, lon)
            # Convert the GPS coordinate to absolute UTM.
            # (With always_xy=True, pass parameters as (lon, lat))
            abs_easting, abs_northing = self.transformer.transform(lon, lat)
            self.get_logger().info(
                f"Absolute UTM for {waypoint}: {abs_easting:.2f}, {abs_northing:.2f}"
            )
            # Get the datum offset (the transform from "utm" to "odom").
            try:
                trans = self.tf_buffer.lookup_transform("utm", "odom", Time(), Duration(seconds=0.5))
                datum_easting = trans.transform.translation.x
                datum_northing = trans.transform.translation.y
                self.get_logger().info(
                    f"Datum offset: {datum_easting:.2f}, {datum_northing:.2f}"
                )
            except Exception as e:
                self.get_logger().error(f"Could not get datum transform: {e}")
                return
            
            # Compute the relative goal: absolute UTM minus the datum offset.
            rel_easting = abs_easting - datum_easting
            rel_northing = abs_northing - datum_northing
            self.current_goal = (rel_easting, rel_northing)
            self.publish_goal(rel_easting, rel_northing)
        # If a current goal exists and we have the current pose, check if the goal is reached.
        elif self.current_goal is not None and self.current_pose is not None:
            goal_x, goal_y = self.current_goal
            curr_x = self.current_pose.position.x
            curr_y = self.current_pose.position.y
            distance = math.sqrt((goal_x - curr_x)**2 + (goal_y - curr_y)**2)
            self.get_logger().info(f"Distance to goal: {distance:.2f} m")
            if distance < self.goal_threshold:
                if self.gps_waypoints:
                    self.get_logger().info("Goal reached. Publishing next waypoint.")
                    self.current_goal = None  # Clear current goal so next waypoint can be published.
                else:
                    self.get_logger().info("Final goal reached. No more waypoints.")
                    self.timer.cancel()

    def publish_goal(self, x, y):
        # Create a PoseStamped message with the relative goal in the "odom" frame.
        goal_msg = PoseStamped()
        goal_msg.header.frame_id = "odom"  # Robot's local frame
        goal_msg.pose.position.x = x
        goal_msg.pose.position.y = y
        goal_msg.pose.position.z = 0.0
        goal_msg.pose.orientation.w = 1.0
        self.goal_pub.publish(goal_msg)
        self.get_logger().info(f"Published goal pose: ({x:.2f}, {y:.2f})")

def main(args=None):
    rclpy.init(args=args)
    node = GoalPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
