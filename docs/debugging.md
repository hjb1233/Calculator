# 命令行、pdb 与 VS Code 调试

## 1. 先看现象在哪一层

```
界面/调用方  →  节点进程  →  DDS 发现  →  话题/服务契约  →  运算逻辑
```

按层排查，每层都有对应的命令，一次只验证一件事。

## 2. 命令行工具（最常用）

```bash
# 节点和服务在不在
ros2 node list
ros2 service list -t | grep add_two_ints

# 手动发一次请求，绕开自己的客户端
ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts '{a: 12, b: 30}'

# 话题有没有数据、速率多少、内容是什么
ros2 topic list
ros2 topic echo /chatter
ros2 topic hz /chatter
ros2 topic info /chatter -v          # 看发布者/订阅者数量与 QoS

# 参数是否生效
ros2 param get /talker publish_period
ros2 param list /talker

# 图结构
rqt_graph
```

**最常见的三个故障和它们的定位命令**

| 现象 | 先跑这条 | 典型原因 |
|---|---|---|
| 客户端报"服务不可用" | `ros2 service list` | 命名空间不匹配 / `ROS_DOMAIN_ID` 不一致 |
| 节点起来了但没消息 | `ros2 topic info /chatter -v` | 发布订阅 QoS 不兼容（reliable vs best_effort） |
| 有消息但内容不对 | `ros2 topic echo` | 参数没传进去 / 两个同名节点在抢 |

```bash
# 域隔离：一组终端用 73，另一组用 74，互不干扰
export ROS_DOMAIN_ID=73
```

## 3. 用 pdb 断点

```bash
# 在服务端回调里插断点
python3 -c "
import pdb, sys
from calculator.service import main
sys.argv = ['add_two_ints_server']
pdb.runcall(main, sys.argv)
"
```

或者直接在源码里加一行 `breakpoint()`，然后用
`ros2 run Calculator add_two_ints_server` 启动，命中断点后进入 pdb：

```
> calculator/service.py(31)_handle_add()
-> response.sum = add_int64(request.a, request.b)
(Pdb) p request.a, request.b
(Pdb) n
(Pdb) p response.sum
```

注意：**服务端回调在 executor 线程里执行**，断点会卡住整个 `spin`，
客户端那边会观察到 `request_timeout` 超时——这不是 bug，是预期行为。

## 4. VS Code

`.vscode/launch.json` 提供了三个配置：
`ROS: talker`、`ROS: listener`、`ROS: pytest (no ROS)`。

前置：

```bash
source /opt/ros/humble/setup.bash      # 让 python 能 import rclpy
code ~/calculator_ws/src/Calculator
```

调试 launch 文件时，在 `generate_launch_description()` 里打断点无效的居多
（launch 在子进程里执行），这种情况用命令行 + `ros2` 工具更快。

## 5. 一键复现

```bash
bash scripts/verify_ros2.sh
```

脚本会在 `/tmp/calculator_test_ws` 里重新构建，跑完所有测试并输出 XUnit。
**任何失败都能用这一条命令在别人机器上看見**，这是调试的第一步也是最后一步。
