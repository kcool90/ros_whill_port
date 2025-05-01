#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from whill_msgs.srv import SetPower

def main(args=None):
    rclpy.init(args=args)
    node = Node('power_on')

    cli = node.create_client(SetPower, '/whill/set_power_srv')
    node.get_logger().info('Waiting for set_power_srv...')
    cli.wait_for_service()
    req = SetPower.Request()
    req.p0 = 1
    node.get_logger().info('Calling SetPower(p0=1)…')
    res = cli.call(req)
    node.get_logger().info(f'SetPower call returned: result={res.result}')
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
