#!/usr/bin/env python3
import osmnx as ox
import networkx as nx
import rclpy
from rclpy.node import Node
import argparse
import logging
import json

from sensor_msgs.msg import NavSatFix
from std_msgs.msg import String

# Optional: adjust logging level
logging.basicConfig(level=logging.INFO)

class NavigationRoute(Node):
    def __init__(self, stop_coord):
        super().__init__('navigation_route')
        self.stop_coord = stop_coord  # tuple (lat, lon)
        self.start_coord = None       # to be set from the first GPS fix

        # Publisher for the JSON waypoint list
        self.wp_pub = self.create_publisher(String, 'gps_waypoints', 10)

        # Subscribe to your GPS fix topic (e.g. /fix)
        self.gps_sub = self.create_subscription(
            NavSatFix, '/fix', self.gps_callback, 10)
        self.get_logger().info("Waiting for GPS fix...")

    def gps_callback(self, msg: NavSatFix):
        if self.start_coord is None and msg.latitude != 0.0:
            self.start_coord = (msg.latitude, msg.longitude)
            self.get_logger().info(f"Received start fix: {self.start_coord}")
            # No longer need this subscription
            self.destroy_subscription(self.gps_sub)
            # Now compute and publish the route
            self.compute_route()

    def compute_route(self):
        start = self.start_coord
        stop  = self.stop_coord
        if start is None:
            self.get_logger().error("No start coordinate!")
            return

        self.get_logger().info(f"Start coordinate: {start}")
        self.get_logger().info(f"Stop coordinate: {stop}")

        # build bounding box
        offset = 0.001
        north = max(start[0], stop[0]) + offset
        south = min(start[0], stop[0]) - offset
        east  = max(start[1], stop[1]) + offset
        west  = min(start[1], stop[1]) - offset
        bbox = (west, south, east, north)
        self.get_logger().info(f"Bounding box: {bbox}")

        # download graph
        self.get_logger().info("Downloading graph…")
        G = ox.graph_from_bbox(bbox, network_type='walk')
        self.get_logger().info(f"Graph nodes: {len(G.nodes)}, edges: {len(G.edges)}")

        # find nearest nodes
        start_node = ox.distance.nearest_nodes(G, start[1], start[0])
        stop_node  = ox.distance.nearest_nodes(G, stop[1],  stop[0])
        self.get_logger().info(f"Nearest start node: {start_node}, stop node: {stop_node}")

        # shortest path
        self.get_logger().info("Computing shortest path…")
        route = nx.shortest_path(G, start_node, stop_node, weight='length')
        self.get_logger().info(f"Route length (nodes): {len(route)}")

        # extract lat/lon waypoints
        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
        self.get_logger().info(f"Route waypoints: {route_coords}")

        # convert to JSON and publish
        waypoints_json = json.dumps(route_coords)
        msg = String()
        msg.data = waypoints_json
        self.wp_pub.publish(msg)
        self.get_logger().info("Published gps_waypoints JSON")

        # shutdown
        rclpy.shutdown()

def main(args=None):
    parser = argparse.ArgumentParser(
        description="Compute navigation route from live GPS fix to a stop coordinate")
    parser.add_argument(
        "--stop", required=True,
        help="Stop coordinate as 'lat,lon' (e.g. 38.637483,-90.241264')")
    parsed, ros_args = parser.parse_known_args(args=args)

    try:
        stop_coord = tuple(map(float, parsed.stop.split(',')))
    except ValueError:
        print("Error: --stop must be in format lat,lon")
        return

    rclpy.init(args=ros_args)
    node = NavigationRoute(stop_coord)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
