"""启动加法服务端，可选再跟一次示例请求。

集成测试用的是 start_client:=false：它只要一个活着的服务端，
不希望旁边还有个一次性客户端抢着打印输出。
"""

from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    namespace = LaunchConfiguration("namespace")
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace",
                default_value="",
                description="Namespace shared by server and client.",
            ),
            DeclareLaunchArgument(
                "start_client",
                default_value="true",
                description="Run one example addition request.",
            ),
            DeclareLaunchArgument("a", default_value="2", description="First operand."),
            DeclareLaunchArgument("b", default_value="3", description="Second operand."),
            DeclareLaunchArgument(
                "discovery_timeout", default_value="5.0", description="Discovery limit in seconds."
            ),
            DeclareLaunchArgument(
                "request_timeout", default_value="5.0", description="Response limit in seconds."
            ),
            Node(
                package="Calculator",
                executable="add_two_ints_server",
                namespace=namespace,
                output="screen",
            ),
            Node(
                package="Calculator",
                executable="add_two_ints_client",
                namespace=namespace,
                output="screen",
                arguments=[
                    LaunchConfiguration("a"),
                    LaunchConfiguration("b"),
                    "--discovery-timeout",
                    LaunchConfiguration("discovery_timeout"),
                    "--request-timeout",
                    LaunchConfiguration("request_timeout"),
                ],
                condition=IfCondition(LaunchConfiguration("start_client")),
            ),
        ]
    )
