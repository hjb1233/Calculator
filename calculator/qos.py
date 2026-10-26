"""chatter 话题的 QoS 配置，发布和订阅共用一份。

两边必须一致：如果一边 reliable 一边 best_effort，DDS 照样能让它们互相发现，
但一条消息都不会传过去。表现出来就是"节点起来了、日志也正常、就是收不到东西"，
排查起来很费时间，所以干脆只定义一次，两个节点都用它。
"""

from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)


def chatter_qos() -> QoSProfile:
    """reliable / volatile / keep-last(10)，也就是官方教程的默认值。"""
    return QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=10,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.VOLATILE,
    )
