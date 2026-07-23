import asyncio
from contextlib import suppress
from datetime import datetime, timedelta

from backend.config import logger
from backend.notification.notification_service import (
    NotificationService,
)
from backend.repository.daily_schedule_repository import (
    DailyScheduleRepository,
)
from backend.repository.settings_repository import (
    SettingsRepository,
)
from backend.services.schedule_service import ScheduleService


class ScheduleExecutor:
    """持续检查并执行已经到期的随机提醒计划。"""

    CHECK_INTERVAL_SECONDS = 15
    LATE_GRACE_MINUTES = 2

    def __init__(
        self,
        schedule_repository: DailyScheduleRepository | None = None,
        settings_repository: SettingsRepository | None = None,
        schedule_service: ScheduleService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.schedule_repository = (
            schedule_repository
            or DailyScheduleRepository()
        )

        self.settings_repository = (
            settings_repository
            or SettingsRepository()
        )

        self.schedule_service = (
            schedule_service
            or ScheduleService()
        )

        self.notification_service = (
            notification_service
            or NotificationService()
        )

        self._task: asyncio.Task[None] | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        """返回执行器是否正在运行。"""

        return (
            self._running
            and self._task is not None
            and not self._task.done()
        )

    def start(self) -> None:
        """启动后台执行器。"""

        if self.is_running:
            logger.warning(
                "Schedule executor is already running"
            )
            return

        self._running = True

        self._task = asyncio.create_task(
            self._run_loop(),
            name="random-reminder-schedule-executor",
        )

        logger.info(
            "Schedule executor started | interval=%s seconds",
            self.CHECK_INTERVAL_SECONDS,
        )

    async def stop(self) -> None:
        """停止后台执行器。"""

        self._running = False

        if self._task is None:
            return

        self._task.cancel()

        with suppress(asyncio.CancelledError):
            await self._task

        self._task = None

        logger.info("Schedule executor stopped")

    async def run_once(self) -> dict[str, int]:
        """立即执行一次计划检查。"""

        return await asyncio.to_thread(
            self._run_once_sync
        )

    async def _run_loop(self) -> None:
        """按照固定时间间隔持续检查计划。"""

        while self._running:
            try:
                result = await self.run_once()

                if (
                    result["sent"] > 0
                    or result["skipped"] > 0
                    or result["failed"] > 0
                ):
                    logger.info(
                        "Schedule check completed | "
                        "sent=%s | skipped=%s | failed=%s",
                        result["sent"],
                        result["skipped"],
                        result["failed"],
                    )

            except Exception:
                logger.exception(
                    "Unexpected schedule executor error"
                )

            await asyncio.sleep(
                self.CHECK_INTERVAL_SECONDS
            )

    def _run_once_sync(self) -> dict[str, int]:
        """同步完成一次数据库检查和通知发送。"""

        result = {
            "sent": 0,
            "skipped": 0,
            "failed": 0,
        }

        settings = self.settings_repository.get()

        if not settings.enabled:
            return result

        now = datetime.now()
        today = now.date().isoformat()

        schedules = (
            self.schedule_repository.get_by_date(
                today
            )
        )

        if not schedules:
            try:
                schedules = (
                    self.schedule_service
                    .generate_today_schedule()
                )

            except ValueError as error:
                logger.warning(
                    "Today schedule was not generated: %s",
                    error,
                )

                return result

        grace_deadline_delta = timedelta(
            minutes=self.LATE_GRACE_MINUTES
        )

        for schedule in schedules:
            if schedule.status != "pending":
                continue

            scheduled_datetime = datetime.fromisoformat(
                (
                    f"{schedule.schedule_date}"
                    f"T{schedule.scheduled_time}"
                )
            )

            if scheduled_datetime > now:
                continue

            delay = now - scheduled_datetime

            if delay > grace_deadline_delta:
                self.schedule_repository.update_status(
                    schedule_id=schedule.id,
                    status="skipped",
                )

                result["skipped"] += 1

                logger.info(
                    "Expired schedule skipped | "
                    "schedule_id=%s | scheduled_time=%s",
                    schedule.id,
                    schedule.scheduled_time,
                )

                continue

            try:
                self.notification_service.send(
                    title="随机提醒器",
                    message=schedule.content,
                )

                self.schedule_repository.update_status(
                    schedule_id=schedule.id,
                    status="sent",
                )

                result["sent"] += 1

                logger.info(
                    "Schedule notification sent | "
                    "schedule_id=%s | scheduled_time=%s",
                    schedule.id,
                    schedule.scheduled_time,
                )

            except RuntimeError:
                result["failed"] += 1

                logger.exception(
                    "Schedule notification failed | "
                    "schedule_id=%s",
                    schedule.id,
                )

        return result