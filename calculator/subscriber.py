"""订阅者节点：把 chatter 上收到的内容打出来。

QoS 和发布方保持一致，用的是同一个 chatter_qos()，理由见 qos.py。
"""

from typing import List, Optional

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

from calculator.qos import chatter_qos


class Listener(Node):
    """收到一条就打一条。"""

    def __init__(self) -> None:
        super().__init__("listener")
        self._subscription = self.create_subscription(
            String, "chatter", self._on_message, chatter_qos()
        )
        self.get_logger().info(f"开始监听 {self._subscription.topic_name}")

    def _on_message(self, message: String) -> None:
        self.get_logger().info(f'I heard: "{message.data}"')


def main(args: Optional[List[str]] = None) -> None:
    """跑起来，直到被 Ctrl+C 或者 ROS 关闭。"""
    rclpy.init(args=args)
    node = None
    try:
        node = Listener()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
