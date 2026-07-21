from datetime import time

from backend.domain.settings import Settings
from backend.repository.settings_repository import (
    SettingsRepository,
)


class SettingsService:
    """处理提醒设置相关的业务规则。"""

    def __init__(
        self,
        repository: SettingsRepository | None = None,
    ) -> None:
        self.repository = repository or SettingsRepository()

    def get_settings(self) -> Settings:
        """读取当前设置。"""

        return self.repository.get()

    def update_settings(
        self,
        enabled: bool,
        all_day: bool,
        start_time: str | None,
        end_time: str | None,
        times_per_day: int,
        minimum_interval: int,
    ) -> Settings:
        """验证并保存设置。"""

        validated_start_time, validated_end_time = (
            self._validate_time_range(
                all_day=all_day,
                start_time=start_time,
                end_time=end_time,
            )
        )

        self._validate_times_per_day(times_per_day)

        self._validate_minimum_interval(
            minimum_interval
        )

        if not all_day:
            self._validate_schedule_capacity(
                start_time=validated_start_time,
                end_time=validated_end_time,
                times_per_day=times_per_day,
                minimum_interval=minimum_interval,
            )

        return self.repository.update(
            enabled=enabled,
            all_day=all_day,
            start_time=validated_start_time,
            end_time=validated_end_time,
            times_per_day=times_per_day,
            minimum_interval=minimum_interval,
        )

    @staticmethod
    def _validate_time_range(
        all_day: bool,
        start_time: str | None,
        end_time: str | None,
    ) -> tuple[str | None, str | None]:
        """检查全天模式和时间范围设置。"""

        if all_day:
            return None, None

        if start_time is None or end_time is None:
            raise ValueError(
                "关闭全天模式时，必须填写开始时间和结束时间"
            )

        parsed_start_time = (
            SettingsService._parse_time(start_time)
        )
        parsed_end_time = (
            SettingsService._parse_time(end_time)
        )

        if parsed_start_time >= parsed_end_time:
            raise ValueError(
                "开始时间必须早于结束时间"
            )

        return (
            parsed_start_time.strftime("%H:%M"),
            parsed_end_time.strftime("%H:%M"),
        )

    @staticmethod
    def _parse_time(value: str) -> time:
        """将 HH:MM 格式的字符串转换为 time 对象。"""

        try:
            hour_text, minute_text = value.split(":")

            parsed_time = time(
                hour=int(hour_text),
                minute=int(minute_text),
            )

        except (ValueError, TypeError) as error:
            raise ValueError(
                "时间格式必须为 HH:MM，例如 09:00"
            ) from error

        return parsed_time

    @staticmethod
    def _validate_times_per_day(
        times_per_day: int,
    ) -> None:
        """检查每天提醒次数。"""

        if times_per_day < 1:
            raise ValueError(
                "每天提醒次数不能少于 1 次"
            )

        if times_per_day > 20:
            raise ValueError(
                "每天提醒次数不能超过 20 次"
            )

    @staticmethod
    def _validate_minimum_interval(
        minimum_interval: int,
    ) -> None:
        """检查最小提醒间隔。"""

        if minimum_interval < 5:
            raise ValueError(
                "最小提醒间隔不能少于 5 分钟"
            )

        if minimum_interval > 720:
            raise ValueError(
                "最小提醒间隔不能超过 720 分钟"
            )

    @staticmethod
    def _validate_schedule_capacity(
        start_time: str | None,
        end_time: str | None,
        times_per_day: int,
        minimum_interval: int,
    ) -> None:
        """检查时间范围是否能容纳指定次数的提醒。"""

        if start_time is None or end_time is None:
            raise ValueError("提醒时间范围不完整")

        start = SettingsService._parse_time(start_time)
        end = SettingsService._parse_time(end_time)

        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute

        available_minutes = end_minutes - start_minutes

        required_minutes = (
            times_per_day - 1
        ) * minimum_interval

        if required_minutes > available_minutes:
            raise ValueError(
                "当前时间范围无法容纳指定的提醒次数和最小间隔"
            )