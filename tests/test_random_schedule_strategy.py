import pytest

from backend.strategy.random_schedule_strategy import (
    RandomScheduleStrategy,
)


def to_minutes(value: str) -> int:
    """把 HH:MM 转换成当天总分钟数。"""

    hour_text, minute_text = value.split(":")

    return (
        int(hour_text) * 60
        + int(minute_text)
    )


def test_generate_times_respects_range_and_interval() -> None:
    """生成结果应满足数量、范围和最小间隔。"""

    strategy = RandomScheduleStrategy()

    result = strategy.generate_times(
        start_time="08:00",
        end_time="12:00",
        times_per_day=3,
        minimum_interval=60,
    )

    assert len(result) == 3
    assert result == sorted(result)

    minute_values = [
        to_minutes(value)
        for value in result
    ]

    assert minute_values[0] >= to_minutes("08:00")
    assert minute_values[-1] <= to_minutes("12:00")

    intervals = [
    current - previous
    for previous, current
    in zip(
        minute_values[:-1],
        minute_values[1:],
        strict=True,
    )
]

    assert all(
        interval >= 60
        for interval in intervals
    )


def test_generate_times_rejects_insufficient_range() -> None:
    """范围不足时应给出异常。"""

    strategy = RandomScheduleStrategy()

    with pytest.raises(
        ValueError,
        match="当前时间范围无法生成",
    ):
        strategy.generate_times(
            start_time="08:00",
            end_time="08:30",
            times_per_day=3,
            minimum_interval=30,
        )


def test_generate_times_avoids_excluded_times() -> None:
    """生成时间不能使用已经被占用的时间。"""

    strategy = RandomScheduleStrategy()

    result = strategy.generate_times(
        start_time="08:00",
        end_time="08:02",
        times_per_day=2,
        minimum_interval=1,
        excluded_times={
            "08:01",
        },
    )

    assert result == [
        "08:00",
        "08:02",
    ]


def test_generate_times_rejects_insufficient_range_after_exclusion(
) -> None:
    """排除占用时间后数量不足应生成失败。"""

    strategy = RandomScheduleStrategy()

    with pytest.raises(
        ValueError,
        match="当前时间范围无法生成",
    ):
        strategy.generate_times(
            start_time="08:00",
            end_time="08:02",
            times_per_day=3,
            minimum_interval=1,
            excluded_times={
                "08:01",
            },
        )