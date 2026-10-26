"""把话题那一对和服务那一对一起启动，参数共享。

用组合而不是复制：这个文件只负责声明参数，再转发给两个单用途的 launch 文件，
这样 demo / topics / service 三份配置就不会各改各的、慢慢对不上。
"""

from typing import Dict, List, Tuple

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

from launch import LaunchDescription

ARGUMENTS: List[Tuple[str, str, str]] = [
    ("namespace", "", "Namespace shared by all nodes."),
    ("publish_period", "0.5", "Seconds between two published messages."),
    ("prefix", "Hello World: ", "Text placed before the message counter."),
    ("start_client", "true", "Run one example addition request."),
    ("a", "2", "First signed 64-bit operand."),
    ("b", "3", "Second signed 64-bit operand."),
    ("discovery_timeout", "5.0", "Service discovery limit in seconds."),
    ("request_timeout", "5.0", "Service response limit in seconds."),
]


def generate_launch_description() -> LaunchDescription:
    declarations = [
        DeclareLaunchArgument(name, default_value=default, description=description)
        for name, default, description in ARGUMENTS
    ]

    def include(filename: str, names: List[str]) -> IncludeLaunchDescription:
        arguments: Dict[str, LaunchConfiguration] = {
            name: LaunchConfiguration(name) for name in names
        }
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([FindPackageShare("Calculator"), "launch", filename])
            ),
            launch_arguments=arguments.items(),
        )

    return LaunchDescription(
        declarations
        + [
            include("topics.launch.py", ["namespace", "publish_period", "prefix"]),
            include(
                "service.launch.py",
                [
                    "namespace",
                    "start_client",
                    "a",
                    "b",
                    "discovery_timeout",
                    "request_timeout",
                ],
            ),
        ]
    )
