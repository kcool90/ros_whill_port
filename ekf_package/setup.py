from setuptools import setup

package_name = 'ekf_package'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='group1',
    maintainer_email='group1@todo.todo',
    description='EKF and helper nodes',
    license='MIT',
    entry_points={
        'console_scripts': [
            'navigation_route = ekf_package.navigation_route:main',
            'nav_goal_publisher = ekf_package.nav_goal_publisher:main',
            'temporary_imu_to_odom = ekf_package.temporary_imu_to_odom:main',
        ],
    },
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/ekf_package']),
        ('share/ekf_package', ['package.xml']),
    ],
)
