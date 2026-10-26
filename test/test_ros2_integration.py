"""启动真实节点，并在真实中间件上验证话题与服务的契约。

为什么不用 launch_testing 的 unittest 集成方式：它把整个模块算作 **1 个**测试项，
XUnit 里只留下一条记录，作业要求的"至少五个有代表性的服务测试"就没法被数出来。
这里改成模块级 fixture 拉起真实 launch 进程、每个用例是独立的 pytest 项，
于是 XUnit 里有 12 条可核实的记录，测试报告也能据此自动生成。

所有断言都经过真实 DDS：服务跑在 launch 拉起的独立进程里，
本测试进程只是另一个节点，靠发现机制找到它再调用。没有任何 mock。

调用方在启动 pytest 前决定 ROS_DOMAIN_ID；本套件另外把所有端点放在
/integration 命名空间下，顺带验证 launch 的命名空间行为。
"""

# ruff: noqa: E402  (importorskip 必须先于 ROS 相关 import 执行)

import os
import subprocess
import time
from types import SimpleNamespace
from typing import List

import pytest

rclpy = pytest.importorskip("rclpy")
pytest.importorskip("example_interfaces")

from ament_index_python.packages import get_package_prefix  # noqa: E402
from example_interfaces.srv import AddTwoInts  # noqa: E402
from rclpy.executors import SingleThreadedExecutor  # noqa: E402
from std_msgs.msg import String  # noqa: E402

NAMESPACE = "/integration"
INT64_MIN = -(1 << 63)
INT64_MAX = (1 << 63) - 1
READY_TIMEOUT = 60.0
CALL_TIMEOUT = 5.0


@pytest.fixture(scope="module")
def ros_context():
    """整个模块共用一次 rclpy 初始化。"""
    rclpy.init(args=[])
    try:
        yield
    finally:
        rclpy.shutdown()


@pytest.fixture(scope="module")
def rig(ros_context):
    """用官方 launch 文件拉起真实节点，等服务就绪，用完回收。"""
    launches = [
        ["ros2", "launch", "Calculator", "service.launch.py",
         "namespace:=integration", "start_client:=false"],
        ["ros2", "launch", "Calculator", "topics.launch.py",
         "namespace:=integration", "publish_period:=0.05", "prefix:=Test: "],
    ]
    processes = [
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for command in launches
    ]
    try:
        node = rclpy.create_node("calculator_probe", namespace=NAMESPACE)
        executor = SingleThreadedExecutor()
        executor.add_node(node)
        client = node.create_client(AddTwoInts, "add_two_ints")

        deadline = time.time() + READY_TIMEOUT
        while time.time() < deadline:
            if client.wait_for_service(timeout_sec=1.0):
                break
        assert client.wait_for_service(timeout_sec=1.0), (
            f"{NAMESPACE}/add_two_ints 在 {READY_TIMEOUT:g}s 内没有就绪"
        )

        received: List[str] = []
        node.create_subscription(String, "chatter", lambda m: received.append(m.data), 10)

        client_executable = (
            f"{get_package_prefix('Calculator')}/lib/Calculator/add_two_ints_client"
        )
        assert os.path.isfile(client_executable), "找不到已安装的 add_two_ints_client"

        yield SimpleNamespace(
            node=node,
            executor=executor,
            client=client,
            received=received,
            client_executable=client_executable,
        )
        executor.remove_node(node)
        node.destroy_node()
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()


def call_service(rig, a: int, b: int) -> int:
    """发一次真实请求并返回 sum；超时或异常直接让用例失败。"""
    request = AddTwoInts.Request()
    request.a = a
    request.b = b
    future = rig.client.call_async(request)
    try:
        rig.executor.spin_until_future_complete(future, timeout_sec=CALL_TIMEOUT)
        assert future.done(), f"{CALL_TIMEOUT:g}s 内没有收到响应"
        assert future.exception() is None, f"请求出错：{future.exception()}"
        response = future.result()
        assert response is not None, "服务返回空响应"
        return response.sum
    finally:
        if not future.done():
            rig.client.remove_pending_request(future)
            future.cancel()


def run_cli(rig, a, b, *extra, namespace: str = NAMESPACE) -> subprocess.CompletedProcess:
    """把一次性客户端当独立进程跑，用于验证退出码。"""
    return subprocess.run(
        [rig.client_executable, str(a), str(b), *extra,
         "--ros-args", "-r", f"__ns:={namespace}"],
        capture_output=True, text=True, timeout=60, check=False,
    )


# --- 服务正确性：8 个用例，全部经真实 DDS ------------------------------------


def test_01_positive_addition(rig):
    assert call_service(rig, 12, 30) == 42


def test_02_negative_operands(rig):
    assert call_service(rig, -7, 12) == 5
    assert call_service(rig, -5, -5) == -10


def test_03_zero_is_the_identity(rig):
    assert call_service(rig, 0, 0) == 0
    assert call_service(rig, 1234567890123, 0) == 1234567890123


def test_04_upper_boundary_without_overflow(rig):
    assert call_service(rig, INT64_MAX, 0) == INT64_MAX
    assert call_service(rig, INT64_MAX - 1, 1) == INT64_MAX


def test_05_lower_boundary_without_overflow(rig):
    assert call_service(rig, INT64_MIN, 0) == INT64_MIN
    assert call_service(rig, INT64_MIN + 1, -1) == INT64_MIN


def test_06_positive_overflow_wraps(rig):
    assert call_service(rig, INT64_MAX, 1) == INT64_MIN


def test_07_negative_overflow_wraps(rig):
    assert call_service(rig, INT64_MIN, -1) == INT64_MAX


def test_08_mixed_extremes_do_not_wrap(rig):
    assert call_service(rig, INT64_MIN, INT64_MAX) == -1


# --- 命令行契约：3 个用例 -----------------------------------------------------


def test_09_cli_prints_the_sum_and_exits_zero(rig):
    result = run_cli(rig, 20, 22)
    assert result.returncode == 0, result.stderr
    assert "Result: 20 + 22 = 42" in (result.stdout + result.stderr)


def test_10_cli_rejects_out_of_range_operands(rig):
    assert run_cli(rig, INT64_MAX + 1, 0).returncode == 2


def test_11_cli_reports_a_missing_service(rig):
    result = run_cli(rig, 1, 2, "--discovery-timeout", "1", namespace="/no_such_namespace")
    assert result.returncode == 1


# --- 话题侧：1 个用例 ---------------------------------------------------------


def test_12_talker_and_listener_actually_exchange_messages(rig):
    deadline = time.time() + 10.0
    while time.time() < deadline and not rig.received:
        rig.executor.spin_once(timeout_sec=0.2)
    assert rig.received, "10s 内 /integration/chatter 上没有收到任何消息"
    assert any(item.startswith("Test: ") for item in rig.received), rig.received[:3]
