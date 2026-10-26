"""命令行参数校验。同样不依赖 ROS，可以单独测。

把解析单独拆出来有两个好处：单测不需要装 ROS；client 的 main() 也能写得短一点。
"""

import argparse
import math

from calculator.arithmetic import INT64_MAX, INT64_MIN


def parse_int64(text: str) -> int:
    """解析一个十进制整数，超出 int64 直接报错。"""
    try:
        value = int(text, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{text!r} 不是十进制整数") from exc
    if not INT64_MIN <= value <= INT64_MAX:
        raise argparse.ArgumentTypeError(f"{value} 超出有符号 64 位范围")
    return value


def parse_positive_seconds(text: str) -> float:
    """解析超时秒数，必须是正数，且不能是 nan / inf。"""
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{text!r} 不是数字") from exc
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("超时时间必须是有限值")
    if value <= 0:
        raise argparse.ArgumentTypeError("超时时间必须大于 0")
    return value


def build_parser() -> argparse.ArgumentParser:
    """一次性加法客户端的参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="add_two_ints_client",
        description="通过 add_two_ints 服务计算两个有符号 64 位整数的和。",
        epilog="溢出时按 int64 回绕。ROS 自己的参数放在 --ros-args 后面。",
    )
    parser.add_argument("a", type=parse_int64, help="第一个操作数")
    parser.add_argument("b", type=parse_int64, help="第二个操作数")
    parser.add_argument(
        "--discovery-timeout",
        type=parse_positive_seconds,
        default=5.0,
        metavar="SECONDS",
        help="等待服务出现的上限（默认 5 秒）",
    )
    parser.add_argument(
        "--request-timeout",
        type=parse_positive_seconds,
        default=5.0,
        metavar="SECONDS",
        help="等待响应返回的上限（默认 5 秒）",
    )
    return parser
