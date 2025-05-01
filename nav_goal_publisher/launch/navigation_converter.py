#!/usr/bin/env python3


from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
   return LaunchDescription([
       #Node(
       #    package='nav2_bringup',
       #    executable='navigation_launch.py',
       #    output='screen'
       #),
       Node(
           package='nav_goal_publisher',
           executable='goal_publisher',
           output='screen'
       )
   ])
