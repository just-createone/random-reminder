import random
from datetime import date, datetime, timedelta

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

    MINIMUM_LEAD_MINUTES = 2

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
    
    def is_enabled(self) -> bool:
        """返回随机提醒总开关是否开启。"""

        settings = self.settings_repository.get()

        return settings.enabled
    
    def skip_overdue_pending(
    self,
    now: datetime | None = None,
    grace_minutes: int = 5,
) -> int:
        """跳过超过允许延迟时间的 pending 计划。"""

        if grace_minutes < 0:
            raise ValueError(
                "允许延迟分钟数不能小于 0"
            )

        current_datetime = now or datetime.now()

        cutoff_datetime = (
            current_datetime
            - timedelta(minutes=grace_minutes)
        )

        return (
            self.schedule_repository
            .skip_overdue_pending(
                cutoff_datetime.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

    def generate_today_schedule(
        self,
        force: bool = False,
        now: datetime | None = None,
    ) -> list[DailySchedule]:
        """生成今天的未来随机提醒计划。"""

        current_datetime = now or datetime.now()
        today = current_datetime.date().isoformat()

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

        configured_start_time, end_time = (
            self._resolve_time_range(
                all_day=settings.all_day,
                start_time=settings.start_time,
                end_time=settings.end_time,
            )
        )

        start_time = (
            self._resolve_future_start_time(
                start_time=configured_start_time,
                end_time=end_time,
                now=current_datetime,
                lead_minutes=(
                    self.MINIMUM_LEAD_MINUTES
                ),
            )
        )

        try:
            generated_times = (
                self.strategy.generate_times(
                    start_time=start_time,
                    end_time=end_time,
                    times_per_day=(
                        settings.times_per_day
                    ),
                    minimum_interval=(
                        settings.minimum_interval
                    ),
                )
            )

        except ValueError as error:
            raise ValueError(
                "今天剩余时间不足，"
                f"无法生成 {settings.times_per_day} "
                "条符合间隔要求的提醒"
            ) from error

        selected_reminders = self._select_reminders(
            reminders=reminders,
            count=len(generated_times),
        )

        # 先成功生成新时间，再删除旧计划。
        # 如果生成失败，原有计划会继续保留。
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

    @classmethod
    def _resolve_future_start_time(
        cls,
        start_time: str,
        end_time: str,
        now: datetime,
        lead_minutes: int,
    ) -> str:
        """计算今天实际可用于生成计划的开始时间。"""

        start_clock = datetime.strptime(
            start_time,
            "%H:%M",
        ).time()

        end_clock = datetime.strptime(
            end_time,
            "%H:%M",
        ).time()

        configured_start = datetime.combine(
            now.date(),
            start_clock,
        )

        configured_end = datetime.combine(
            now.date(),
            end_clock,
        )

        if configured_end < configured_start:
            raise ValueError(
                "提醒结束时间必须晚于开始时间"
            )

        earliest_future_time = (
            now
            + timedelta(
                minutes=lead_minutes,
            )
        )

        earliest_future_time = (
            cls._ceil_to_minute(
                earliest_future_time
            )
        )

        effective_start = max(
            configured_start,
            earliest_future_time,
        )

        if effective_start > configured_end:
            raise ValueError(
                "今天的提醒时间范围已经结束，"
                "无法生成新的提醒计划"
            )

        return effective_start.strftime(
            "%H:%M"
        )

    @staticmethod
    def _ceil_to_minute(
        value: datetime,
    ) -> datetime:
        """将时间向上取整到下一整分钟。"""

        rounded = value.replace(
            second=0,
            microsecond=0,
        )

        if value.second or value.microsecond:
            rounded += timedelta(minutes=1)

        return rounded

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