# ros_whill_port
cd whill_ws/

source /opt/ros/humble/setup.bash

colcon build --packages-select whill_driver_wrapper

source install/setup.bash

ros2 launch whill_driver_wrapper drive_launch.py
