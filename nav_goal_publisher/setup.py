from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'nav_goal_publisher'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # Allow ROS2 to locate this package
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools', 'pyproj'],
    zip_safe=True,
    maintainer='group1',
    maintainer_email='kccool966@gmail.com',
    description='A package for converting a GPS goal to a ROS2 PoseStamped message',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'goal_publisher = nav_goal_publisher.goal_publisher:main'
        ],
    },
)
