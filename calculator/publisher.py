"""发布者节点：按固定周期往 chatter 话题发消息。

话题名故意写成相对名 chatter 而不是 /chatter。这样节点被放进某个命名空间时，
话题会自动变成 /demo/chatter，不需要额外做 remapping，同一份代码能在多个 launch 里复用。
"""

import math
from typing import List, Optional

import rclpy
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

from calculator.qos import chatter_qos


class Talker(Node):
    """每隔一段时间发一条 "前缀 + 计数"。"""

    def __init__(self) -> None:
        super().__init__("talker")
        try:
            self.declare_parameter(
                "publish_period",
                0.5,
                ParameterDescriptor(description="发送间隔（秒），必须是正数。", read_only=True),
            )
            self.declare_parameter(
                "prefix",
                "Hello World: ",
                ParameterDescriptor(description="计数前面的文字。", read_only=True),
            )

            period = float(self.get_parameter("publish_period").value)
            if not math.isfinite(period) or period <= 0.0:
                raise ValueError("publish_period 必须是正数")

            self._prefix = str(self.get_parameter("prefix").value)
            self._counter = 0
            self._publisher = self.create_publisher(String, "chatter", chatter_qos())
            self._timer = self.create_timer(period, self._publish_message)
        except Exception:
            # 构造失败要把节点销毁掉，否则会留下一个半初始化的节点：
            # 定时器会去访问根本没赋值的属性，进程还退不出来。
            self.destroy_node()
            raise
        self.get_logger().info(f"开始向 {self._publisher.topic_name} 发消息，间隔 {period:g} 秒")

    def _publish_message(self) -> None:
        message = String()
        message.data = f"{self._prefix}{self._counter}"
        self._publisher.publish(message)
        self.get_logger().info(f'Publishing: "{message.data}"')
        self._counter += 1


def main(args: Optional[List[str]] = None) -> None:
    """跑起来，直到被 Ctrl+C 或者 ROS 关闭。"""
    rclpy.init(args=args)
    node = None
    try:
        node = Talker()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
