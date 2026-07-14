import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'shaheen'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
        (os.path.join('share', package_name, 'models'), glob('models/*.pt')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mohammed S. Alajmi',
    maintainer_email='mohammed.alajmi@tuwaiq.local',
    description='SHAHEEN runway inspection - ROS 2 perception and mission nodes.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'yolo_detector = shaheen.yolo_detector:main',
            'tower = shaheen.tower:main',
            'mission_supervisor = shaheen.mission_supervisor:main',
        ],
    },
)
