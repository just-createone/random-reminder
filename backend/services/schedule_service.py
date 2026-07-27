import random
from datetime import date

from backend.domain.daily_schedule import DailySchedule
from backend.domain.reminder import Reminder
from backend.repository.daily_schedule_repository import (
    DailyScheduleRepository,
)
from backend.repository.notification_repository import (
    NotificationRepository,
)
from backend.repository.reminder_repository import (
    ReminderRepository,
)
from backend.repository.settings_repository import (
    SettingsRepository,
)
from backend.strategy.random_schedule_strategy import (
    RandomScheduleStrategy,
)


class ScheduleService:
    """生成并查询每日随机提醒计划。"""

    def __init__(
        self,
        schedule_repository: DailyScheduleRepository | None = None,
        reminder_repository: ReminderRepository | None = None,
        settings_repository: SettingsRepository | None = None,
        notification_repository: NotificationRepository | None = None,
        strategy: RandomScheduleStrategy | None = None,
    ) -> None:
        self.schedule_repository = (
            schedule_repository
            or DailyScheduleRepository()
        )

        self.reminder_repository = (
            reminder_repository
            or ReminderRepository()
        )

        self.settings_repository = (
            settings_repository
            or SettingsRepository()
        )

        self.notification_repository = (
            notification_repository
            or NotificationRepository()
        )

        self.strategy = (
            strategy
            or RandomScheduleStrategy()
        )

    def get_today_schedule(
        self,
    ) -> list[DailySchedule]:
        """读取今天已经生成的提醒计划。"""

        today = date.today().isoformat()

        return self.schedule_repository.get_by_date(
            today
        )

    def generate_today_schedule(
        self,
        force: bool = False,
    ) -> list[DailySchedule]:
        """生成今天的随机提醒计划。"""

        today = date.today().isoformat()

        existing_schedule = (
            self.schedule_repository.get_by_date(
                today
            )
        )

        if existing_schedule and not force:
            self._ensure_notification_records(
                existing_schedule
            )

            return existing_schedule

        settings = self.settings_repository.get()

        if not settings.enabled:
            raise ValueError(
                "随机提醒总开关尚未开启"
            )

        reminders = (
            self.reminder_repository.get_enabled()
        )

        if not reminders:
            raise ValueError(
                "没有可用于生成计划的启用提醒"
            )

        start_time, end_time = (
            self._resolve_time_range(
                all_day=settings.all_day,
                start_time=settings.start_time,
                end_time=settings.end_time,
            )
        )

        generated_times = self.strategy.generate_times(
            start_time=start_time,
            end_time=end_time,
            times_per_day=settings.times_per_day,
            minimum_interval=settings.minimum_interval,
        )

        selected_reminders = self._select_reminders(
            reminders=reminders,
            count=settings.times_per_day,
        )

        if force:
            self.schedule_repository.delete_by_date(
                today
            )

        items = [
            (
                scheduled_time,
                reminder.id,
                reminder.content,
            )
            for scheduled_time, reminder
            in zip(
                generated_times,
                selected_reminders,
                strict=True,
            )
        ]

        schedules = (
            self.schedule_repository.create_many(
                schedule_date=today,
                items=items,
            )
        )

        self._ensure_notification_records(
            schedules
        )

        return schedules

    def _ensure_notification_records(
        self,
        schedules: list[DailySchedule],
    ) -> None:
        """确保每条计划都有对应的通知记录。"""

        schedule_ids = [
            schedule.id
            for schedule in schedules
        ]

        self.notification_repository.create_many_for_schedules(
            schedule_ids
        )

    @staticmethod
    def _resolve_time_range(
        all_day: bool,
        start_time: str | None,
        end_time: str | None,
    ) -> tuple[str, str]:
        """根据设置确定实际时间范围。"""

        if all_day:
            return "00:00", "23:59"

        if start_time is None or end_time is None:
            raise ValueError(
                "提醒时间范围不完整"
            )

        return start_time, end_time

    @staticmethod
    def _select_reminders(
        reminders: list[Reminder],
        count: int,
    ) -> list[Reminder]:
        """选择当天要使用的提醒内容。"""

        if len(reminders) >= count:
            return random.sample(
                reminders,
                count,
            )

        return [
            random.choice(reminders)
            for _ in range(count)
        ]