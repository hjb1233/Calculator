# Calculator

用 Python 实现的 ROS 2 计算器练习：包含 **话题发布/订阅**、`add_two_ints`
**服务与客户端**、**可组合的 launch 文件**、**官方 launch 教程复现**、
**真实中间件上的集成测试**，以及中英文测试报告。

运算逻辑与 ROS 适配层完全分离，因此加法契约（含 int64 溢出回绕）
可以在**不装 ROS 的环境里**被单测覆盖——评审在没有 ROS 的机器上也能一键验证。

主实现支持 **ROS 2 Humble / Ubuntu 22.04** 与 **ROS 2 Jazzy / Ubuntu 24.04**。
ROS 包名保持题目要求的拼写 `Calculator`，Python 模块名为 `calculator`。
大写包名会触发 REP-144 命名警告，这是保留题目拼写的有意选择，不影响构建。

---

## 1. 快速开始

以下命令在 Ubuntu Bash 中执行。22.04 用 `humble`，24.04 用 `jazzy`。
需要先按[官方说明](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)装好 ROS 2。

```bash
source /opt/ros/jazzy/setup.bash          # 22.04 改成 humble
sudo apt update
sudo apt install python3-colcon-common-extensions python3-rosdep python3-pytest \
  ros-${ROS_DISTRO}-example-interfaces ros-${ROS_DISTRO}-turtlesim \
  ros-${ROS_DISTRO}-launch-testing ros-${ROS_DISTRO}-launch-testing-ros

mkdir -p ~/calculator_ws/src
cd ~/calculator_ws
git clone <你的仓库地址> src/Calculator
rosdep install --from-paths src/Calculator --ignore-src -r -y      # 首次需先 sudo rosdep init && rosdep update
colcon build --packages-select Calculator --symlink-install
source install/setup.bash
ros2 launch Calculator demo.launch.py a:=12 b:=30
```

预期看到发布者打印 `Publishing`、订阅者打印 `I heard`，客户端打印
`Result: 12 + 30 = 42`。按 Ctrl+C 退出。**每个新终端都要重新 source。**

## 2. 单独运行

```bash
# 终端 A
ros2 run Calculator add_two_ints_server
# 终端 B
ros2 run Calculator add_two_ints_client 12 30
ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts '{a: 12, b: 30}'

# 只跑话题，带命名空间和启动参数
ros2 launch Calculator topics.launch.py namespace:=demo publish_period:=0.2 'prefix:=Demo: '
ros2 topic echo /demo/chatter

# 只起服务，稍后手动调用；所有节点都支持标准 remapping
ros2 launch Calculator service.launch.py namespace:=demo start_client:=false
ros2 run Calculator add_two_ints_client -7 12 --ros-args -r __ns:=/demo
ros2 run Calculator add_two_ints_client 1 2 --discovery-timeout 1 --request-timeout 2
```

## 3. 接口约定

- **话题** `chatter`：`std_msgs/msg/String`，默认每 0.5 秒发布
  `Hello World: <递增计数>`，QoS 为 reliable / volatile / depth 10。
  `publish_period` 和 `prefix` 是启动时只读参数。
- **服务** `add_two_ints`：标准 `example_interfaces/srv/AddTwoInts`，
  `a`、`b`、`sum` 均为有符号 int64。
- **溢出**：`AddTwoInts` 没有错误字段，所以超出范围的和**明确采用 64 位补码回绕**
  （`INT64_MAX + 1` 得到 `INT64_MIN`），并记 WARN 日志；未溢出时就是普通加法。
  超出 int64 的**操作数**在客户端就被拒绝，不会发出请求。
- **退出码**：成功 `0`；发现/响应失败或被中断 `1`；参数错误 `2`。
  响应超时只停止本地等待，**不能撤销服务端已经开始的计算**。

## 4. 官方 launch 教程复现

```bash
ros2 launch Calculator multisim.launch.py
```

启动 `/turtlesim1/turtlesim` 与 `/turtlesim2/turtlesim` 两个独立实例，
并由 `mimic` 节点把 1 号的位姿转发成 2 号的速度指令。
来源与逐项说明见 [`docs/tutorial_launch.md`](docs/tutorial_launch.md)。

## 5. 验证

```bash
cd ~/calculator_ws/src/Calculator

# 不需要 ROS 的核心与参数校验测试（25 个）
python3 -m pytest test/test_arithmetic.py test/test_cli.py -v

# 已 source ROS：构建 + 真实节点/服务/话题测试 + XUnit 结果
bash scripts/verify_ros2.sh
```

验证脚本使用临时构建目录，可用 `CALCULATOR_TEST_WORKSPACE`、
`CALCULATOR_TEST_RESULTS`、`ROS_DOMAIN_ID`（默认 73，只做本机发现）配置。
**跑之前先停掉同域里自己起的同名演示节点**，否则测试会被干扰。

纯 Python 环境直接跑 `pytest` 时，ROS 集成模块会自动 skip；
完整验证脚本会预检 ROS 依赖，缺失直接失败而不是静默通过。

## 6. 阅读入口

| 文档 | 内容 |
|---|---|
| [`docs/requirements.md`](docs/requirements.md) | 作业要求逐项对照 |
| [`docs/architecture.md`](docs/architecture.md) | 结构、接口与设计取舍 |
| [`docs/debugging.md`](docs/debugging.md) | 命令行、pdb 与 VS Code 调试 |
| [`docs/tutorial_launch.md`](docs/tutorial_launch.md) | 官方 launch 复现与验证 |
| [`docs/TEST_REPORT.zh-CN.md`](docs/TEST_REPORT.zh-CN.md) | 中文测试报告 |
| [`docs/TEST_REPORT.en.md`](docs/TEST_REPORT.en.md) | English test report |
| [`docs/requirements.md`](docs/requirements.md) | 作业要求逐项对照（含"本次选用 Python"的说明） |

## 7. 许可

原创代码 MIT。官方教程复现文件沿用上游 CC BY 4.0，见
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
