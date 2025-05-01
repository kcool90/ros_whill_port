from setuptools import setup

package_name = 'bno055_uart'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
        'pyserial',
        'adafruit-circuitpython-bno055',
    ],
    zip_safe=True,
    maintainer='Pascal Sikorski',
    maintainer_email='you@your.email',
    description='ROS2 node for Adafruit BNO055 via UART',
    license='MIT',
    entry_points={
        'console_scripts': [
            'imu_node = bno055_uart.imu_node:main',
        ],
    },
)
