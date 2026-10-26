"""一次性客户端：发一次请求、拿到结果就退出。

用了两个独立的超时，因为它们失败的原因完全不同：
  * discovery_timeout —— 服务根本没出现（服务端没起 / 命名空间不对 / ROS_DOMAIN_ID 不一致）
  * request_timeout   —— 服务出现了但不回（服务端卡住 / executor 被饿死 / DDS 丢包）

合成一个超时的话，报错就只能说"失败了"，排查时没有方向。
"""

import sys
from typing import List, Optional

import rclpy
from example_interfaces.srv import AddTwoInts
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.utilities import remove_ros_args

from calculator.cli import build_parser

EXIT_OK = 0
EXIT_COMMUNICATION = 1
EXIT_USAGE = 2


class AdditionClient(Node):
    """用异步方式发请求，但对外只暴露一个"问一次"的接口。"""

    def __init__(self) -> None:
        super().__init__("add_two_ints_client")
        self._client = self.create_client(AddTwoInts, "add_two_ints")
        self._service_name = self.resolve_service_name("add_two_ints")

    def add(self, a: int, b: int, *, discovery_timeout: float, request_timeout: float) -> int:
        """返回求和结果，失败时抛出能说明卡在哪一步的异常。"""
        self.get_logger().info(f"最多等 {discovery_timeout:g} 秒，等待 {self._service_name}")
        if not self._client.wait_for_service(timeout_sec=discovery_timeout):
            raise TimeoutError(
                f"{discovery_timeout:g} 秒内没有等到服务 {self._service_name}"
            )

        request = AddTwoInts.Request()
        request.a = a
        request.b = b
        future = self._client.call_async(request)
        try:
            rclpy.spin_until_future_complete(self, future, timeout_sec=request_timeout)
            if not future.done():
                raise TimeoutError(
                    f"{self._service_name} 在 {request_timeout:g} 秒内没有响应"
                )
            if future.cancelled():
                raise RuntimeError("请求被取消")
            if future.exception() is not None:
                raise RuntimeError(
                    f"请求失败：{future.exception()}"
                ) from future.exception()
            response = future.result()
            if response is None:
                raise RuntimeError("服务返回了空响应")
            return response.sum
        finally:
            if not future.done():
                # 取消只是让本进程不再等，服务端已经开始的计算撤不掉。
                self._client.remove_pending_request(future)
                future.cancel()


def main(args: Optional[List[str]] = None) -> int:
    """成功返回 0，通信失败返回 1，参数错返回 2。"""
    command_line = sys.argv if args is None else [sys.argv[0], *args]
    try:
        options = build_parser().parse_args(remove_ros_args(args=command_line)[1:])
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK

    rclpy.init(args=command_line)
    node = None
    try:
        node = AdditionClient()
        result = node.add(
            options.a,
            options.b,
            discovery_timeout=options.discovery_timeout,
            request_timeout=options.request_timeout,
        )
        node.get_logger().info(f"Result: {options.a} + {options.b} = {result}")
        return EXIT_OK
    except (KeyboardInterrupt, ExternalShutdownException):
        return EXIT_COMMUNICATION
    except (TimeoutError, RuntimeError) as exc:
        if node is not None:
            node.get_logger().error(str(exc))
        else:
            print(f"创建客户端失败：{exc}", file=sys.stderr)
        return EXIT_COMMUNICATION
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
