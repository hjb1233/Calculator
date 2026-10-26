# 作业要求逐项对照

| 要求 | 交付位置 / 验证方式 |
|---|---|
| 创建 Calculator ROS 包并构建 | 根目录 `package.xml`、`setup.py`、`resource/Calculator`；`colcon build --packages-select Calculator` |
| Git 初始提交、GitHub、master、功能分支与合并 | `git log --all --graph --oneline`；每个功能一个分支，合并回 `master` |
| topic、service、launch 概念 + 教程 launch 复现 | `launch/multisim.launch.py` 复现官方双 turtlesim 示例；`test/test_tutorial_launch.py` 验证命名空间与话题；另提供 `topics` / `service` / `demo` 三个自有启动文件 |
| publisher / subscriber | `calculator/publisher.py`、`calculator/subscriber.py`；集成测试里断言真实收到消息 |
| server / client | `calculator/service.py`、`calculator/client.py`；标准 `AddTwoInts` 接口、CLI 校验、双超时 |
| test 目录与测试框架 | `test/` 下 pytest + launch_testing；不依赖 ROS 的测试与真实 ROS 测试分文件 |
| 至少五个有代表性的服务测试 | `test/test_ros2_integration.py`：**12 个**用例，全部经真实 DDS 调用或真实 CLI 进程 |
| 中文测试报告、英文加分 | `docs/TEST_REPORT.zh-CN.md`、`docs/TEST_REPORT.en.md` |
| 清晰代码结构、可调试、可迁移 | 纯运算层 / ROS 适配 / CLI 校验三层分离；显式 QoS、显式超时、日志、`scripts/verify_ros2.sh` 一键复现 |
| Python / C++ | 二选一，**本次提交选用 Python**（`ament_python`）；未实现 C++，也不声称完成 |
| 提交仓库链接 | 本仓库，主交付分支 `master` |

## 关于 ROS 版本

题目给的教程链接是 ROS 2 Humble，但 `rostest` 属于 ROS 1 术语，
ROS 2 不使用 roscore / catkin / rostest 工具链。
因此主包采用官方 ROS 2 对应方式：`ament_python + colcon + pytest + launch_testing`。

Humble 对应 Ubuntu 22.04，Jazzy 对应 Ubuntu 24.04，
代码只使用两者共有 API。CI 对两个发行版独立验证。

## 关于包名

ROS 通常要求小写包名（REP-144）。这里为了保持题目指定的拼写，
ROS 包命名为 `Calculator`，Python import 保持 `calculator`。
`catkin_pkg` 的兼容规则允许该拼写并给出命名警告。
构建、ament 索引、launch 与入口脚本中的大小写保持一致。
正常新工程建议全小写。
