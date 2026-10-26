"""服务端节点：把加法通过标准 AddTwoInts 服务暴露出去。

这里只写 ROS 那部分，真正的加法在 calculator.arithmetic 里，
这样溢出行为由单测钉死，所有调用方看到的都是同一套语义。
"""

from typing import List, Optional

import rclpy
from example_interfaces.srv import AddTwoInts
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from calculator.arithmetic import add_int64


class AdditionServer(Node):
    """提供 add_two_ints 服务，溢出时按补码回绕。"""

    def __init__(self) -> None:
        super().__init__("add_two_ints_server")
        self._service = self.create_service(AddTwoInts, "add_two_ints", self._handle_add)
        self.get_logger().info(f"服务已就绪：{self.resolve_service_name('add_two_ints')}")

    def _handle_add(
        self, request: AddTwoInts.Request, response: AddTwoInts.Response
    ) -> AddTwoInts.Response:
        response.sum = add_int64(request.a, request.b)
        if request.a + request.b != response.sum:
            # AddTwoInts 没有错误字段，溢出了也只能记日志，没法告诉调用方。
            self.get_logger().warning(
                f"int64 溢出已回绕：{request.a} + {request.b} = {response.sum}"
            )
        else:
            self.get_logger().info(f"{request.a} + {request.b} = {response.sum}")
        return response


def main(args: Optional[List[str]] = None) -> None:
    """跑起来，直到被 Ctrl+C 或者 ROS 关闭。"""
    rclpy.init(args=args)
    node = None
    try:
        node = AdditionServer()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
