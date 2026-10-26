# 结构、接口与设计取舍

## 1. 三层分离

```
calculator/
  arithmetic.py   纯运算：int64 回绕契约，不 import 任何 ROS
  cli.py          纯参数校验：argparse，不 import 任何 ROS
  qos.py          共享 QoS 定义
  publisher.py    ROS 适配：Talker 节点
  subscriber.py   ROS 适配：Listener 节点
  service.py      ROS 适配：AdditionServer 节点
  client.py       ROS 适配：AdditionClient 节点 + 进程退出码
```

**为什么这样分**：加法契约和参数校验是这份作业里唯一有"正确性"可言的东西，
把它们从 ROS 里剥离出来，就能在没有 ROS 的机器（比如 CI 里的纯 Python job）
上跑 25 个单测。ROS 适配层只剩调度和日志，几乎不需要单测，
而需要真实中间件的部分交给集成测试。

**迁移性**：`arithmetic.py` 只依赖 Python 标准库，不 `import` 任何 ROS，
所以可以直接被别的包、别的脚本、甚至别的项目拿去用，
不需要先装 ROS、也不需要先启动节点。

## 2. 接口约定

| 接口 | 类型 | 名称 | 载荷 |
|---|---|---|---|
| 话题 | `std_msgs/msg/String` | `chatter`（相对名） | `Hello World: <计数>` |
| 服务 | `example_interfaces/srv/AddTwoInts` | `add_two_ints`（相对名） | `a`, `b` → `sum` |
| 参数 | `publish_period` (float, 只读) | talker | 默认 0.5 |
| 参数 | `prefix` (string, 只读) | talker | 默认 `Hello World: ` |

**相对名是刻意的**：节点放到命名空间 `demo` 下，话题自动变成 `/demo/chatter`，
不需要 remapping。这让同一份代码既能裸跑，也能被 launch 复用。

## 3. 五个关键取舍

### 3.1 溢出：回绕，而不是报错

`AddTwoInts` 只有 `a`、`b`、`sum` 三个 int64 字段，**没有任何错误字段**。
所以服务端面对溢出只有两种诚实的选择：拒绝请求，或者回绕。
回绕（补码语义，和 C/C++ 一致）至少保证返回值始终是合法的 int64，
不会让下游拿到越界值。代价是调用方无法区分"正好算出来"和"溢出了"——
这一点在服务端记 WARN 日志，并在文档和单测里写死。

### 3.2 操作数越界在客户端就拦掉

`INT64_MAX + 1` 是溢出（可回绕），但传入 `INT64_MAX + 1` 作为**操作数**
是协议错误，直接拒绝、退出码 2，请求根本不发出去。
两者性质不同，处理方式也不同。

### 3.3 两个超时而不是一个

- `discovery_timeout`：服务**没出现**（服务端没起、命名空间错、`ROS_DOMAIN_ID` 不匹配）
- `request_timeout`：服务**出现了但不回**（服务端卡住、executor 被饿死、DDS 丢包）

合成一个超时，错误信息就只能说"失败了"，排查时毫无帮助。

### 3.4 QoS 显式声明并共享

发布者和订阅者的 reliability / durability 不兼容时，DDS 会让双方**互相发现但不传数据**——
节点起来了、日志正常、什么也收不到。这是 ROS 2 最经典的假故障。
所以 `calculator/qos.py` 只定义一次，两侧都用它。

### 3.5 launch 用组合而不是复制

`demo.launch.py` 只声明参数并 `IncludeLaunchDescription` 另外两个文件，
所以 `demo` / `topics` / `service` 三份配置不可能漂移。

## 4. 退出码

| 码 | 含义 |
|---|---|
| 0 | 成功 |
| 1 | 发现或响应失败、被 Ctrl+C 中断 |
| 2 | 命令行参数错误（非整数、超出 int64、超时非正） |

## 5. 已知边界

- 客户端是**一次性**的：一次调用后就退出，不做长连接。
- 响应超时只能停止本地等待，无法撤销服务端已开始的计算。
- 服务本身是单线程回调，没有并发保护需求；若改成耗时计算，
  需要把计算放到独立 executor 或工作线程，否则会阻塞 `spin`。
