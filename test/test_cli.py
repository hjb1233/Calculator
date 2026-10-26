"""命令行参数校验的单测。同样不需要装 ROS。"""

from argparse import ArgumentTypeError

import pytest

from calculator.arithmetic import INT64_MAX, INT64_MIN
from calculator.cli import build_parser, parse_int64, parse_positive_seconds


@pytest.fixture()
def parser():
    return build_parser()


def test_default_operands_and_timeouts(parser) -> None:
    options = parser.parse_args(["12", "30"])
    assert (options.a, options.b) == (12, 30)
    assert options.discovery_timeout == 5.0
    assert options.request_timeout == 5.0


def test_negative_operands_are_accepted(parser) -> None:
    options = parser.parse_args(["-7", "12"])
    assert (options.a, options.b) == (-7, 12)


def test_boundary_operands_are_accepted(parser) -> None:
    options = parser.parse_args([str(INT64_MIN), str(INT64_MAX)])
    assert options.a == INT64_MIN
    assert options.b == INT64_MAX


def test_non_integer_operand_is_rejected(parser, capsys) -> None:
    with pytest.raises(SystemExit):
        parser.parse_args(["abc", "30"])


def test_operand_above_int64_is_rejected(parser) -> None:
    with pytest.raises(SystemExit):
        parser.parse_args([str(INT64_MAX + 1), "0"])


def test_operand_below_int64_is_rejected(parser) -> None:
    with pytest.raises(SystemExit):
        parser.parse_args([str(INT64_MIN - 1), "0"])


def test_missing_operands_are_rejected(parser) -> None:
    with pytest.raises(SystemExit):
        parser.parse_args(["1"])


def test_timeouts_can_be_overridden(parser) -> None:
    options = parser.parse_args(["1", "2", "--discovery-timeout", "0.5", "--request-timeout", "9"])
    assert options.discovery_timeout == 0.5
    assert options.request_timeout == 9.0


def test_zero_timeout_is_rejected(parser) -> None:
    with pytest.raises(SystemExit):
        parser.parse_args(["1", "2", "--request-timeout", "0"])


def test_negative_timeout_is_rejected(parser) -> None:
    with pytest.raises(SystemExit):
        parser.parse_args(["1", "2", "--discovery-timeout", "-1"])


def test_non_numeric_timeout_is_rejected(parser) -> None:
    with pytest.raises(SystemExit):
        parser.parse_args(["1", "2", "--request-timeout", "soon"])


def test_parse_int64_accepts_base_ten_only() -> None:
    assert parse_int64("0012") == 12
    with pytest.raises(ArgumentTypeError):
        parse_int64("0x10")


def test_parse_positive_seconds_rejects_nan_and_inf() -> None:
    with pytest.raises(ArgumentTypeError):
        parse_positive_seconds("nan")
    with pytest.raises(ArgumentTypeError):
        parse_positive_seconds("inf")
