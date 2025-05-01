#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
import tf_transformations as tf
import tf2_ros
from geometry_msgs.msg import TransformStamped
import numpy as np

class ImuOdometry(Node):
    def __init__(self):
        super().__init__('imu_odometry_node')
        self.odom_pub = self.create_publisher(Odometry, 'odom_imu', 10)
        self.sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.last_time = None
        self.position = np.zeros(3)
        self.velocity = np.zeros(3)
        self.orientation = [0, 0, 0, 1]
        self.gravity = np.array([0, 0, -9.81])

    def imu_callback(self, msg: Imu):
        now = self.get_clock().now()
        if self.last_time is None:
            self.last_time = now
            return
        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now

        # 1) orientation update (same as before)…
        wx, wy, wz = msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z
        delta = np.array([wx*dt, wy*dt, wz*dt])
        angle = np.linalg.norm(delta)
        if angle > 0:
            axis = delta / angle
            delta_q = tf.quaternion_about_axis(angle, axis)
        else:
            delta_q = [0, 0, 0, 1]
        self.orientation = tf.quaternion_multiply(self.orientation, delta_q)

        # 2) correct acceleration in world frame
        accel = np.array([msg.linear_acceleration.x,
                          msg.linear_acceleration.y,
                          msg.linear_acceleration.z])
        rot = tf.quaternion_matrix(self.orientation)[:3, :3]
        accel_world = rot.dot(accel) - self.gravity

        # 3) integrate velocity & position
        self.velocity += accel_world * dt
        self.position += self.velocity * dt

        # 4) publish Odometry
        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x, odom.pose.pose.position.y, odom.pose.pose.position.z = self.position
        odom.pose.pose.orientation.x, odom.pose.pose.orientation.y, odom.pose.pose.orientation.z, odom.pose.pose.orientation.w = self.orientation
        odom.twist.twist.linear.x, odom.twist.twist.linear.y, odom.twist.twist.linear.z = self.velocity
        odom.twist.twist.angular.x, odom.twist.twist.angular.y, odom.twist.twist.angular.z = wx, wy, wz
        self.odom_pub.publish(odom)

        # 5) broadcast TF
        t = TransformStamped()
        t.header.stamp = now.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = self.position
        t.transform.rotation.x, t.transform.rotation.y, t.transform.rotation.z, t.transform.rotation.w = self.orientation
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = ImuOdometry()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
