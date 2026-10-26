"""加法核心的单测。不需要装 ROS 就能跑。"""

import pytest

from calculator.arithmetic import (
    INT64_MAX,
    INT64_MIN,
    add_int64,
    validate_int64,
    wraps_int64,
)


def test_small_positive_sum() -> None:
    assert add_int64(12, 30) == 42


def test_zero_is_the_identity() -> None:
    assert add_int64(0, 0) == 0
    assert add_int64(INT64_MAX, 0) == INT64_MAX
    assert add_int64(INT64_MIN, 0) == INT64_MIN


def test_negative_operands() -> None:
    assert add_int64(-7, 12) == 5
    assert add_int64(-5, -5) == -10
    assert add_int64(INT64_MIN, 0) == INT64_MIN


def test_mixed_sign_cannot_overflow() -> None:
    assert add_int64(INT64_MIN, INT64_MAX) == -1


def test_positive_overflow_wraps_to_negative() -> None:
    assert add_int64(INT64_MAX, 1) == INT64_MIN
    assert add_int64(INT64_MAX, 2) == INT64_MIN + 1


def test_negative_overflow_wraps_to_positive() -> None:
    assert add_int64(INT64_MIN, -1) == INT64_MAX
    assert add_int64(INT64_MIN, INT64_MIN) == 0


def test_wraps_int64_reports_the_same_boundary() -> None:
    assert wraps_int64(INT64_MAX, 1) is True
    assert wraps_int64(INT64_MIN, -1) is True
    assert wraps_int64(INT64_MAX, 0) is False
    assert wraps_int64(1, 1) is False


def test_result_always_stays_inside_int64() -> None:
    for a, b in ((INT64_MAX, INT64_MAX), (INT64_MIN, INT64_MIN), (INT64_MAX, INT64_MIN)):
        assert INT64_MIN <= add_int64(a, b) <= INT64_MAX


def test_out_of_range_operands_are_rejected() -> None:
    with pytest.raises(ValueError):
        add_int64(INT64_MAX + 1, 0)
    with pytest.raises(ValueError):
        add_int64(0, INT64_MIN - 1)


def test_bool_is_rejected_because_it_is_not_a_number_here() -> None:
    with pytest.raises(TypeError):
        add_int64(True, 1)  # type: ignore[arg-type]


def test_non_integer_types_are_rejected() -> None:
    with pytest.raises(TypeError):
        add_int64(1.0, 2)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        add_int64("1", 2)  # type: ignore[arg-type]


def test_validate_int64_returns_the_value() -> None:
    assert validate_int64(7) == 7
    assert validate_int64(INT64_MIN) == INT64_MIN
