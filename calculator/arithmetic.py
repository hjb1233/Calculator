"""加法核心。故意不 import 任何 ROS，这样可以脱离 ROS 单独跑单测。

AddTwoInts 这个服务只有 a / b / sum 三个 int64 字段，没有错误字段，
所以结果超出范围时只能按 64 位补码回绕，和 C 的行为保持一致。
要区分两种情况：
  * 操作数合法但结果溢出  -> 回绕，服务端记一条 WARN
  * 操作数本身超出 int64  -> 属于协议错误，由调用方拦掉，不在这里处理
"""

INT64_MIN = -(1 << 63)
INT64_MAX = (1 << 63) - 1
_MODULUS = 1 << 64


def validate_int64(value: int) -> int:
    """检查操作数是否是合法的 int64。

    bool 是 int 的子类，True 会被当成 1 悄悄混进来，所以用 type() 而不是 isinstance()。
    """
    if type(value) is not int:
        raise TypeError(f"操作数必须是整数，收到的是 {type(value).__name__}")
    if not INT64_MIN <= value <= INT64_MAX:
        raise ValueError(f"操作数超出 int64 范围 [{INT64_MIN}, {INT64_MAX}]，收到 {value}")
    return value


def wraps_int64(a: int, b: int) -> bool:
    """判断两数相加会不会溢出 int64。"""
    return not INT64_MIN <= a + b <= INT64_MAX


def add_int64(a: int, b: int) -> int:
    """int64 加法。溢出时回绕：INT64_MAX + 1 得到 INT64_MIN。"""
    validate_int64(a)
    validate_int64(b)
    return (a + b - INT64_MIN) % _MODULUS + INT64_MIN
