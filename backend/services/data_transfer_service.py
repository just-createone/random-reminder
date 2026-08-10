from datetime import datetime, timezone
from typing import Any

from backend.repository.data_transfer_repository import (
    DataTransferRepository,
)
from backend.services.reminder_service import ReminderService
from backend.services.settings_service import SettingsService


EXPORT_FORMAT = "random-reminder-export"
EXPORT_FORMAT_VERSION = 1
MAX_IMPORT_REMINDERS = 5000


class DataTransferService:
    """Build exports and validate portable user-data imports."""

    def __init__(
        self,
        repository: DataTransferRepository | None = None,
    ) -> None:
        self.repository = repository or DataTransferRepository()

    def export_data(self) -> dict[str, object]:
        """Build the versioned, portable user-data export."""

        reminders, settings = self.repository.get_export_data()

        return {
            "format": EXPORT_FORMAT,
            "format_version": EXPORT_FORMAT_VERSION,
            "exported_at": self._utc_now_iso(),
            "reminders": reminders,
            "settings": settings,
        }

    def import_data(
        self,
        payload: object,
    ) -> dict[str, object]:
        """Validate a portable export and import it atomically."""

        if not isinstance(payload, dict):
            raise ValueError("导入数据必须是 JSON 对象")

        self._validate_format(payload)
        self._validate_exported_at(payload)

        reminders = self._validate_reminders(payload)
        settings = self._validate_settings(payload)

        imported_reminders = self.repository.import_data(
            reminders=reminders,
            settings=settings,
        )

        return {
            "imported_reminders": imported_reminders,
            "settings_restored": True,
        }

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        )

    @staticmethod
    def _validate_format(payload: dict[str, Any]) -> None:
        if payload.get("format") != EXPORT_FORMAT:
            raise ValueError("不支持的导入文件格式")

        format_version = payload.get("format_version")

        if (
            type(format_version) is not int
            or format_version != EXPORT_FORMAT_VERSION
        ):
            raise ValueError("不支持的导入文件版本")

    @staticmethod
    def _validate_exported_at(payload: dict[str, Any]) -> None:
        exported_at = payload.get("exported_at")

        if not isinstance(exported_at, str):
            raise ValueError("导入文件缺少有效的导出时间")

        try:
            parsed_time = datetime.fromisoformat(
                exported_at.replace("Z", "+00:00")
            )

        except ValueError as error:
            raise ValueError("导出时间格式无效") from error

        if parsed_time.tzinfo is None:
            raise ValueError("导出时间必须包含时区")

    @staticmethod
    def _validate_reminders(
        payload: dict[str, Any],
    ) -> list[tuple[str, bool]]:
        raw_reminders = payload.get("reminders")

        if not isinstance(raw_reminders, list):
            raise ValueError("导入文件中的 reminders 必须是数组")

        if len(raw_reminders) > MAX_IMPORT_REMINDERS:
            raise ValueError(
                "导入文件中的提醒数量不能超过 5000 条"
            )

        reminders: list[tuple[str, bool]] = []

        for raw_reminder in raw_reminders:
            if not isinstance(raw_reminder, dict):
                raise ValueError("每条提醒必须是对象")

            content = raw_reminder.get("content")
            enabled = raw_reminder.get("enabled")

            if not isinstance(content, str):
                raise ValueError("提醒内容必须是字符串")

            if type(enabled) is not bool:
                raise ValueError("提醒启用状态必须是布尔值")

            cleaned_content = ReminderService._validate_content(
                content
            )

            reminders.append((cleaned_content, enabled))

        return reminders

    @staticmethod
    def _validate_settings(
        payload: dict[str, Any],
    ) -> dict[str, object]:
        raw_settings = payload.get("settings")

        if not isinstance(raw_settings, dict):
            raise ValueError("导入文件中的 settings 必须是对象")

        required_fields = (
            "enabled",
            "all_day",
            "start_time",
            "end_time",
            "times_per_day",
            "minimum_interval",
        )

        missing_fields = [
            field
            for field in required_fields
            if field not in raw_settings
        ]

        if missing_fields:
            raise ValueError("导入文件中的 settings 字段不完整")

        enabled = raw_settings["enabled"]
        all_day = raw_settings["all_day"]
        start_time = raw_settings["start_time"]
        end_time = raw_settings["end_time"]
        times_per_day = raw_settings["times_per_day"]
        minimum_interval = raw_settings["minimum_interval"]

        if type(enabled) is not bool or type(all_day) is not bool:
            raise ValueError("设置中的开关必须是布尔值")

        if (
            start_time is not None
            and not isinstance(start_time, str)
        ) or (
            end_time is not None
            and not isinstance(end_time, str)
        ):
            raise ValueError("设置中的时间必须是字符串或 null")

        if (
            type(times_per_day) is not int
            or type(minimum_interval) is not int
        ):
            raise ValueError("设置中的次数和间隔必须是整数")

        validated_start_time, validated_end_time = (
            SettingsService._validate_time_range(
                all_day=all_day,
                start_time=start_time,
                end_time=end_time,
            )
        )

        SettingsService._validate_times_per_day(times_per_day)
        SettingsService._validate_minimum_interval(
            minimum_interval
        )

        if not all_day:
            SettingsService._validate_schedule_capacity(
                start_time=validated_start_time,
                end_time=validated_end_time,
                times_per_day=times_per_day,
                minimum_interval=minimum_interval,
            )

        return {
            "enabled": enabled,
            "all_day": all_day,
            "start_time": validated_start_time,
            "end_time": validated_end_time,
            "times_per_day": times_per_day,
            "minimum_interval": minimum_interval,
        }
