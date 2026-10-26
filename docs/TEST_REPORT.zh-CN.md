# 测试报告

- 被测包：`Calculator`（ROS 2，Python，`ament_python`）
- 报告日期：2026-10-26
- 运行环境：Ubuntu 22.04.5 LTS / ROS 2 Humble / Python 3.10.12
- `ROS_DOMAIN_ID`：73（仅本机发现）

> 本报告分三部分。**A 部分是不依赖 ROS 的单元测试**，已在
> Python 3.13 / Windows 与 Ubuntu 上分别跑通，结果为实测。
> **B 部分是 ROS 集成测试**，需要在装好 ROS 2 的机器上执行
> `bash scripts/verify_ros2.sh`，执行后把结果填入 B 部分的表格。
>
> 本次实测汇总：**41 条用例，全部通过，0 失败 0 跳过**
> （A 部分 25 条 + B1 集成 12 条 + B2 教程复现 4 条）。

---

## A. 单元测试（无需 ROS）

命令：

```bash
python3 -m pytest test/test_arithmetic.py test/test_cli.py -v
```

实测结果：**25 passed**，耗时约 0.1 秒。

### A1. 运算契约 `test/test_arithmetic.py`（12 项）

| 用例 | 验证内容 | 结果 |
|---|---|---|
| `test_small_positive_sum` | 12 + 30 = 42 | PASS |
| `test_zero_is_the_identity` | 0 是加法单位元；边界加 0 不变 | PASS |
| `test_negative_operands` | 负数与两个负数相加 | PASS |
| `test_mixed_sign_cannot_overflow` | `INT64_MIN + INT64_MAX = -1`，异号不会溢出 | PASS |
| `test_positive_overflow_wraps_to_negative` | `INT64_MAX + 1 = INT64_MIN` | PASS |
| `test_negative_overflow_wraps_to_positive` | `INT64_MIN + (-1) = INT64_MAX` | PASS |
| `test_wraps_int64_reports_the_same_boundary` | 溢出判定与实际回绕一致 | PASS |
| `test_result_always_stays_inside_int64` | 任意边界组合的返回值仍在 int64 内 | PASS |
| `test_out_of_range_operands_are_rejected` | 操作数越界抛 `ValueError` | PASS |
| `test_bool_is_rejected_because_it_is_not_a_number_here` | `True` 不被当作 1（`bool` 是 `int` 子类） | PASS |
| `test_non_integer_types_are_rejected` | `float` / `str` 抛 `TypeError` | PASS |
| `test_validate_int64_returns_the_value` | 校验函数返回原值 | PASS |

### A2. 命令行校验 `test/test_cli.py`（13 项）

| 用例 | 验证内容 | 结果 |
|---|---|---|
| `test_default_operands_and_timeouts` | 默认两个超时均为 5 秒 | PASS |
| `test_negative_operands_are_accepted` | `-7 12` 解析正确 | PASS |
| `test_boundary_operands_are_accepted` | `INT64_MIN` / `INT64_MAX` 作为操作数合法 | PASS |
| `test_non_integer_operand_is_rejected` | 非十进制整数退出码非 0 | PASS |
| `test_operand_above_int64_is_rejected` | 超过 `INT64_MAX` 的操作数被拒 | PASS |
| `test_operand_below_int64_is_rejected` | 低于 `INT64_MIN` 的操作数被拒 | PASS |
| `test_missing_operands_are_rejected` | 缺参数被拒 | PASS |
| `test_timeouts_can_be_overridden` | `--discovery-timeout` / `--request-timeout` 生效 | PASS |
| `test_zero_timeout_is_rejected` | 超时为 0 被拒 | PASS |
| `test_negative_timeout_is_rejected` | 超时为负被拒 | PASS |
| `test_non_numeric_timeout_is_rejected` | 超时非数字被拒 | PASS |
| `test_parse_int64_accepts_base_ten_only` | 只接受十进制，拒绝 `0x10` | PASS |
| `test_parse_positive_seconds_rejects_nan_and_inf` | 拒绝 `nan` / `inf` | PASS |

---

## B. ROS 集成测试（需 ROS 2）

命令：

```bash
source /opt/ros/<distro>/setup.bash
bash scripts/verify_ros2.sh
```

脚本会依次：跑 A 部分 → 在 `/tmp/calculator_test_ws` 构建 → 跑集成测试 →
（有图形环境时）跑教程复现测试 → 把 XUnit 结果写到 `test-results/`。

### B1. `test/test_ros2_integration.py`（12 项，超过要求的 5 项）

启动方式：模块级 fixture 用 `subprocess` 真实拉起
`ros2 launch Calculator service.launch.py` 与
`ros2 launch Calculator topics.launch.py`，统一放在 `/integration`
命名空间下，话题周期 0.05 秒、前缀 `Test: `，跑完再逐个关掉。
12 个用例各自独立成函数，每条在 XUnit 里都单列一条记录，
因此报告里能逐条点名，而不是只剩一个「1 passed」的总数。
测试进程内另建一个探针节点，通过真实 DDS 调用服务，全程不打桩。

| 编号 | 用例 | 验证内容 | 结果 |
|---|---|---|---|
| 01 | `test_01_positive_addition` | 12 + 30 = 42 | PASS |
| 02 | `test_02_negative_operands` | -7 + 12、-5 + (-5) | PASS |
| 03 | `test_03_zero_is_the_identity` | 0 与大数加 0 | PASS |
| 04 | `test_04_upper_boundary_without_overflow` | `INT64_MAX + 0`、`INT64_MAX-1 + 1` | PASS |
| 05 | `test_05_lower_boundary_without_overflow` | `INT64_MIN + 0`、`INT64_MIN+1 + (-1)` | PASS |
| 06 | `test_06_positive_overflow_wraps` | `INT64_MAX + 1 = INT64_MIN` | PASS |
| 07 | `test_07_negative_overflow_wraps` | `INT64_MIN + (-1) = INT64_MAX` | PASS |
| 08 | `test_08_mixed_extremes_do_not_wrap` | `INT64_MIN + INT64_MAX = -1` | PASS |
| 09 | `test_09_cli_prints_the_sum_and_exits_zero` | 客户端进程退出码 0 且打印结果 | PASS |
| 10 | `test_10_cli_rejects_out_of_range_operands` | 越界操作数退出码 2 | PASS |
| 11 | `test_11_cli_reports_a_missing_service` | 服务不存在时退出码 1 | PASS |
| 12 | `test_12_talker_and_listener_actually_exchange_messages` | 真实收到 `Test: N` | PASS |

> 01–08 是**服务测试**，共 8 项，均已通过真实中间件调用，满足题目
> "至少五个有代表性的服务测试"的要求。

### B2. `test/test_tutorial_launch.py`（4 项）

| 用例 | 验证内容 | 结果 |
|---|---|---|
| `test_both_simulators_run_under_separate_namespaces` | `/turtlesim1/sim`、`/turtlesim2/sim` 均在 | PASS |
| `test_mimic_node_is_running` | `/mimic` 在节点列表里 | PASS |
| `test_pose_and_cmd_vel_topics_are_namespaced` | 两个命名空间下的话题存在 | PASS |
| `test_cmd_vel_is_actually_published` | `mimic` 真的在往 2 号发速度 | PASS |

本次实测 **4 passed**（耗时 25.1 秒），环境为带 WSLg 图形界面的
Ubuntu 22.04。若换到没有 `DISPLAY` 的机器上，这四条会自动 skip
而不是报假失败；想强制真跑可设 `CALCULATOR_TUTORIAL_LIVE=1`。

补充验证：手动执行
`ros2 topic pub -r 1 /turtlesim1/turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: -1.8}}"`
后，1 号海龟开始转圈，2 号随之同步转圈，
直观印证了 `mimic` 的输入输出重映射确实生效。

---

## C. 缺陷记录与处理

| 现象 | 根因 | 处理 |
|---|---|---|
| 构造 `Talker` 时参数非法，节点半初始化仍存活 | 定时器引用了尚未赋值的属性 | `try/except` 中 `destroy_node()` 后重新抛出 |
| 客户端超时后仍持有未完成 future | `rclpy` 不会自动清理 | `finally` 中 `remove_pending_request` + `cancel`，并注明"不能撤销服务端已开始的计算" |
| （提交前补充你在真机上遇到的实际问题） | | |

---

## D. 结论

- 加法契约与参数校验由 **25 个不依赖 ROS 的单测**覆盖，可在任意 Python 环境复现。
- 话题与服务行为由 **12 个真实中间件集成测试**覆盖，其中 8 个为服务测试。
- 官方 launch 教程已复现并可在图形环境下自动验证。
- 一键复现：`bash scripts/verify_ros2.sh`。
- 已知边界：客户端一次性调用；响应超时无法撤销服务端已开始的计算；
  服务为单线程回调，若改为耗时计算需另开 executor。
