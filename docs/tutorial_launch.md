# 官方 launch 教程复现

来源：ROS 2 官方文档 *Launch* 教程里"同时启动两个 turtlesim 并用 mimic 联动"的例子。
上游许可 CC BY 4.0，见 `THIRD_PARTY_NOTICES.md` 与 `LICENSES/CC-BY-4.0.txt`。

## 运行

```bash
source /opt/ros/humble/setup.bash
source ~/calculator_ws/install/setup.bash
ros2 launch Calculator multisim.launch.py
```

图形环境下应看到两个海龟窗口。移动 1 号，2 号会跟着动。

## 这个文件说明了什么

```python
Node(package="turtlesim", namespace="turtlesim1", executable="turtlesim_node", name="sim")
Node(package="turtlesim", namespace="turtlesim2", executable="turtlesim_node", name="sim")
Node(package="turtlesim", executable="mimic", name="mimic",
     remappings=[
         ("/input/pose",      "/turtlesim1/turtle1/pose"),
         ("/output/cmd_vel",  "/turtlesim2/turtle1/cmd_vel"),
     ])
```

1. **同一个可执行文件启动两次**。如果不加 `namespace`，两个 `turtlesim_node`
   会争抢同一个节点名、同一批话题和服务，后者起不来或者互相顶掉。
   命名空间让 `/turtlesim1/turtle1/pose` 和 `/turtlesim2/turtle1/pose` 共存。
2. **`remappings` 把通用节点改造成具体行为**。`mimic` 只认识
   `/input/pose` 和 `/output/cmd_vel` 这两个抽象名字，重映射之后它就变成了
   "2 号复制 1 号的运动"——**没有改一行 mimic 的源码**。
   这是 launch 相对于"写死话题名"最大的价值。

## 自动化验证

`test/test_tutorial_launch.py` 断言三件事：

- `/turtlesim1/turtlesim` 和 `/turtlesim2/turtlesim` 都在 `ros2 node list` 里；
- `/mimic` 也在；
- `/turtlesim1/turtle1/pose` 与 `/turtlesim2/turtle1/cmd_vel` 话题存在且 `mimic` 在发数据。

**为什么默认跳过**：`turtlesim_node` 要开窗口，无图形环境的 CI 里跑必然失败。
与其让 CI 红着，不如显式跳过并在日志里写清楚原因。
需要强制跑时：

```bash
export CALCULATOR_TUTORIAL_LIVE=1     # 有 DISPLAY 时不需设
python3 -m pytest test/test_tutorial_launch.py -v
```

## 手动核对清单

```bash
ros2 node list          # 期望含 /turtlesim1/turtlesim /turtlesim2/turtlesim /mimic
ros2 topic list         # 期望含 /turtlesim1/turtle1/pose /turtlesim2/turtle1/cmd_vel
ros2 topic echo /turtlesim2/turtle1/cmd_vel
ros2 topic pub /turtlesim1/turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}' -1
```

最后一条会让 1 号转圈，2 号跟着转——这条同时验证了发布、订阅、
命名空间和重映射四件事。
