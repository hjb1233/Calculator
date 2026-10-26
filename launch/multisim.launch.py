"""复现官方 ROS 2 launch 教程：同时跑两个 turtlesim。

来源：docs.ros.org 的 ROS 2 教程里"启动多个节点"那个 multisim 例子。
这个例子要说明的是两件事：

* 同一个可执行文件靠两个命名空间启动两次，节点名、话题、服务才不会打架；
* remappings 把 mimic 节点那两个抽象名字 /input/pose、/output/cmd_vel
  接到具体的海龟话题上，于是一个通用的转发节点就变成了"2 号模仿 1 号"，
  全程没改 mimic 一行源码。

上游许可：CC BY 4.0（见 THIRD_PARTY_NOTICES.md）。
"""

from launch_ros.actions import Node

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="turtlesim",
                namespace="turtlesim1",
                executable="turtlesim_node",
                name="sim",
                output="screen",
            ),
            Node(
                package="turtlesim",
                namespace="turtlesim2",
                executable="turtlesim_node",
                name="sim",
                output="screen",
            ),
            Node(
                package="turtlesim",
                executable="mimic",
                name="mimic",
                output="screen",
                remappings=[
                    ("/input/pose", "/turtlesim1/turtle1/pose"),
                    ("/output/cmd_vel", "/turtlesim2/turtle1/cmd_vel"),
                ],
            ),
        ]
    )
