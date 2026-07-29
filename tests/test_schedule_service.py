from datetime import datetime

import pytest

from backend.services.schedule_service import (
    ScheduleService,
)


def test_future_start_uses_configured_start_before_range() -> None:
    """当前时间早于设置范围时使用设置开始时间。"""

    result = (
        ScheduleService
        ._resolve_future_start_time(
            start_time="08:00",
            end_time="22:00",
            now=datetime(
                2026,
                7,
                29,
                7,
                0,
                0,
            ),
            lead_minutes=2,
        )
    )

    assert result == "08:00"


def test_future_start_uses_current_time_during_range() -> None:
    """当前时间位于范围内时使用未来整分钟。"""

    result = (
        ScheduleService
        ._resolve_future_start_time(
            start_time="08:00",
            end_time="22:00",
            now=datetime(
                2026,
                7,
                29,
                13,
                15,
                20,
            ),
            lead_minutes=2,
        )
    )

    assert result == "13:18"


def test_future_start_rejects_finished_range() -> None:
    """提醒时间范围结束后不能继续生成。"""

    with pytest.raises(
        ValueError,
        match="提醒时间范围已经结束",
    ):
        (
            ScheduleService
            ._resolve_future_start_time(
                start_time="08:00",
                end_time="22:00",
                now=datetime(
                    2026,
                    7,
                    29,
                    22,
                    5,
                    0,
                ),
                lead_minutes=2,
            )
        )