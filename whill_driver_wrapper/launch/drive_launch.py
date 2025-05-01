#!/usr/bin/env python3

import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction, RegisterEventHandler, ExecuteProcess
from launch.event_handlers import OnShutdown
from launch_ros.actions import Node

def _find_port(keyword: str) -> str:
    """Find the first /dev/serial/by-id symlink matching `keyword`."""
    by_id = Path('/dev/serial/by-id')
    for link in by_id.iterdir():
        if keyword in link.name:
            return str(link.resolve())
    raise RuntimeError(f"No serial port matching '{keyword}'")

def generate_launch_description():
    # 1) discover your ports
    gps_port   = _find_port('Silicon_Labs')               # GPS
    whill_port = _find_port('FTDI_USB_Serial_Converter')  # WHILL
    imu_port   = _find_port('0403_6014')                  # IMU

    # 2) WHILL params
    whill_params = os.path.join(
        get_package_share_directory('whill_bringup'),
        'config', 'params.yaml'
    )

    # 3) Nodes:
    whill_node = Node(
        package='whill_driver', executable='whill', name='whill',
        parameters=[whill_params, {'port_name': whill_port}],
        output='screen',
    )

    gps_node = Node(
        package='nmea_navsat_driver', executable='nmea_serial_driver',
        name='gps_serial',
        parameters=[{'port': gps_port, 'baud': 9600}],
        output='screen',
    )

    imu_node = Node(
        package='bno055_uart', executable='imu_node', name='imu_node',
        parameters=[{'port': imu_port}],
        output='screen',
    )

    # 3.b) Node:
    imu_to_odom = Node(
        package='ekf_package',
        executable='temporary_imu_to_odom',
        name='imu_to_odom',
        output='screen',
    )

    # 4) navsat_transform to fuse GPS + /odom_imu → /odom
    navsat_transform = Node(
        package='robot_localization', executable='navsat_transform_node',
        name='navsat_transform_node',
        parameters=[os.path.join(
            get_package_share_directory('whill_driver_wrapper'),
            'config','navsat.yaml'
        )],
        output='screen',
    )

    # 5) ekf_node to smooth /odom_imu → filtered /odom
    ekf_filter = Node(
        package='robot_localization', executable='ekf_node',
        name='ekf_filter_node',
        parameters=[os.path.join(
            get_package_share_directory('whill_driver_wrapper'),
            'config','ekf.yaml'
        )],
        output='screen',
    )

    # 6) After  5 s, power on the WHILL
    power_on = TimerAction(
        period=5.0,
        actions=[ExecuteProcess(
            cmd=[
                'ros2','service','call',
                '/whill/set_power_srv','whill_msgs/SetPower','{p0: 1}'
            ],
            output='screen'
        )]
    )

    # 7) After 10 s, compute & publish route
    navigation_route = TimerAction(
        period=10.0,
        actions=[ExecuteProcess(
            cmd=[
                'ros2','run','ekf_package','navigation_route',
                '--stop','38.637483,-90.241264'
            ],
            output='screen'
        )]
    )

    # 8) After 15 s, publish the first goal
    nav_goal_publisher = TimerAction(
        period=15.0,
        actions=[ExecuteProcess(
            cmd=[
                'ros2','run','nav_goal_publisher','goal_publisher'
            ],
            output='screen'
        )]
    )

    # 9) On shutdown, power off the WHILL
    power_off = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[ExecuteProcess(
                cmd=[
                    'ros2','service','call',
                    '/whill/set_power_srv','whill_msgs/SetPower','{p0: 0}'
                ],
                output='screen'
            )]
        )
    )

    return LaunchDescription([
        whill_node,
        gps_node,
        imu_node,
        imu_to_odom,
        navsat_node,
        ekf_filter,
        power_on,
        navigation_route,
        nav_goal_publisher,
        power_off,
    ])
