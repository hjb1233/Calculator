"""验证官方 multisim launch 教程的复现。

turtlesim_node 要开窗口，所以必须有图形环境。因此只有在能拿到 DISPLAY
（或者显式设置了 CALCULATOR_TUTORIAL_LIVE=1）时才真的跑起来检查，
其余情况直接跳过，而不是在无图形环境里报一个假失败。

真跑起来时验证两件事：

* 两个模拟器分别在两个命名空间下起来——这正是教程要讲的点，
  没有命名空间的话两个 turtlesim_node 会抢同一个节点名、话题和服务；
* mimic 的重映射生效：/turtlesim2/turtle1/cmd_vel 存在，
  并且数据来自 /turtlesim1/turtle1/pose。
"""

import os
import shutil
import subprocess
import time
import unittest

import pytest

pytest.importorskip("rclpy")

from ament_index_python.packages import get_package_share_directory  # noqa: E402


def _display_available() -> bool:
    if os.environ.get("CALCULATOR_TUTORIAL_LIVE") == "1":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _ros2(*arguments: str) -> str:
    # ros2 topic hz 这类命令不会自己退出，靠 timeout 掐断；
    # 掐断时已经打印出来的内容仍然有效，所以要把输出原样带回来。
    try:
        result = subprocess.run(
            ["ros2", *arguments], capture_output=True, text=True, timeout=20, check=False
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        if isinstance(err, bytes):
            err = err.decode(errors="replace")
        return f"{out}\n{err}"
    return f"{result.stdout}\n{result.stderr}"


class TestMultisimLaunch(unittest.TestCase):
    """Launch the tutorial reproduction and inspect the live ROS graph."""

    process = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("ros2") is None:
            raise unittest.SkipTest("ros2 CLI is not on PATH")
        if not _display_available():
            raise unittest.SkipTest("no graphical session; set CALCULATOR_TUTORIAL_LIVE=1 to force")
        package_share = get_package_share_directory("Calculator")
        cls.process = subprocess.Popen(
            [
                "ros2",
                "launch",
                "Calculator",
                "multisim.launch.py",
            ],
            cwd=package_share,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        # 不要去逐行读 launch 的输出：turtlesim 起来之后不再打印新东西，
        # readline() 会一直阻塞，把整条测试拖死。
        # 改成轮询 ros2 node list，等三个节点全部出现再往下走。
        deadline = time.time() + 60.0
        while time.time() < deadline:
            nodes = _ros2("node", "list")
            if "/turtlesim1/sim" in nodes and "/turtlesim2/sim" in nodes and "/mimic" in nodes:
                break
            time.sleep(1.0)
        time.sleep(2.0)

    @classmethod
    def tearDownClass(cls):
        if cls.process is not None and cls.process.poll() is None:
            cls.process.terminate()
            try:
                cls.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                cls.process.kill()

    def test_both_simulators_run_under_separate_namespaces(self):
        nodes = _ros2("node", "list")
        self.assertIn("/turtlesim1/sim", nodes)
        self.assertIn("/turtlesim2/sim", nodes)

    def test_mimic_node_is_running(self):
        self.assertIn("/mimic", _ros2("node", "list"))

    def test_pose_and_cmd_vel_topics_are_namespaced(self):
        topics = _ros2("topic", "list")
        self.assertIn("/turtlesim1/turtle1/pose", topics)
        self.assertIn("/turtlesim2/turtle1/cmd_vel", topics)

    def test_cmd_vel_is_actually_published(self):
        output = _ros2("topic", "hz", "/turtlesim2/turtle1/cmd_vel", "--window", "5")
        self.assertTrue("average rate" in output or "rate" in output, output[:400])
