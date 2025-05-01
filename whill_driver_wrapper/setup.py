from setuptools import setup

package_name = 'whill_driver_wrapper'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Pascal',
    license='MIT',
    entry_points={
        'console_scripts': [
            'power_on = whill_driver_wrapper.power_on:main',
            'whill_control = whill_driver_wrapper.whill_control:main',
        ],
    },
    data_files=[
    ('share/ament_index/resource_index/packages',
      ['resource/whill_driver_wrapper']),
    ('share/whill_driver_wrapper/config', [
       'config/navsat.yaml',
       'config/ekf.yaml',
    ]),
    ('share/whill_driver_wrapper', ['package.xml']),
],

)
