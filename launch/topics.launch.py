"""在一个命名空间里启动发布者和订阅者。

两个节点用的都是相对话题名 chatter，所以只要给个 namespace 参数，
整对节点就迁到 /demo/chatter 去了，不需要写 remapping。
"""

from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    namespace = LaunchConfiguration("namespace")
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace",
                default_value="",
                description="Namespace shared by talker and listener.",
            ),
            DeclareLaunchArgument(
                "publish_period",
                default_value="0.5",
                description="Seconds between two published messages.",
            ),
            DeclareLaunchArgument(
                "prefix",
                default_value="Hello World: ",
                description="Text placed before the message counter.",
            ),
            Node(
                package="Calculator",
                executable="talker",
                namespace=namespace,
                output="screen",
                parameters=[
                    {
                        "publish_period": ParameterValue(
                            LaunchConfiguration("publish_period"), value_type=float
                        ),
                        "prefix": ParameterValue(LaunchConfiguration("prefix"), value_type=str),
                    }
                ],
            ),
            Node(
                package="Calculator",
                executable="listener",
                namespace=namespace,
                output="screen",
            ),
        ]
    )
