import threading
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from backend.config import logger
from backend.notification.notification_service import NotificationService
from backend.repository.notification_repository import NotificationRepository
from backend.repository.user_repository import UserRepository
from backend.services.schedule_service import ScheduleService
from backend.services.web_push_service import WebPushService


class ScheduleExecutor:
    """Check each enabled user's local schedule and deliver only to that user."""

    def __init__(
        self,
        notification_repository: NotificationRepository | None = None,
        notification_service: NotificationService | None = None,
        web_push_service: WebPushService | None = None,
        schedule_service: ScheduleService | None = None,
        user_repository: UserRepository | None = None,
        check_interval_seconds: int = 30,
        schedule_refresh_seconds: int = 300,
        overdue_grace_minutes: int = 5,
    ) -> None:
        self.notification_repository = notification_repository or NotificationRepository()
        self.notification_service = notification_service or NotificationService()
        self.web_push_service = web_push_service or WebPushService()
        self.schedule_service = schedule_service or ScheduleService()
        self.user_repository = user_repository or UserRepository()
        self.check_interval_seconds = check_interval_seconds

        if overdue_grace_minutes < 0:
            raise ValueError("Overdue reminder grace period cannot be negative")
        self.overdue_grace_minutes = overdue_grace_minutes
        self.schedule_refresh_interval = timedelta(seconds=schedule_refresh_seconds)
        self._last_schedule_refresh_at: dict[int, datetime] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Schedule executor is already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="schedule-executor",
            daemon=True,
        )
        self._thread.start()
        logger.info("Schedule executor started")

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2)
        self._thread = None
        logger.info("Schedule executor stopped")

    def ensure_today_schedule(
        self,
        user_id: int,
        time_zone: str,
        now: datetime,
        force_check: bool = False,
    ) -> None:
        if not force_check and not self._should_refresh_schedule(user_id, now):
            return
        self._last_schedule_refresh_at[user_id] = now
        try:
            existing_schedules = self.schedule_service.get_today_schedule(
                user_id=user_id,
                time_zone=time_zone,
                now=now,
            )
            schedules = self.schedule_service.generate_today_schedule(
                force=False,
                now=now,
                user_id=user_id,
                time_zone=time_zone,
            )
            if not existing_schedules:
                logger.info(
                    "Daily schedule generated automatically: user_id=%s date=%s count=%s",
                    user_id,
                    now.date().isoformat(),
                    len(schedules),
                )
        except ValueError as error:
            logger.info("Daily schedule was not generated for user_id=%s: %s", user_id, error)
        except Exception:
            logger.exception("Automatic daily schedule check failed for user_id=%s", user_id)

    def _should_refresh_schedule(self, user_id: int, now: datetime) -> bool:
        last_refresh = self._last_schedule_refresh_at.get(user_id)
        return (
            last_refresh is None
            or now - last_refresh >= self.schedule_refresh_interval
        )

    def run_once(self, now: datetime | None = None) -> None:
        """Run one safe delivery cycle for every enabled user."""
        current_utc = now or datetime.now(timezone.utc)
        if current_utc.tzinfo is None:
            current_utc = current_utc.replace(tzinfo=timezone.utc)

        for user in self.user_repository.get_enabled_users():
            local_now = current_utc.astimezone(ZoneInfo(user.time_zone))
            self.ensure_today_schedule(user.id, user.time_zone, local_now)
            skipped_count = self.schedule_service.skip_overdue_pending(
                now=local_now,
                grace_minutes=self.overdue_grace_minutes,
                user_id=user.id,
                time_zone=user.time_zone,
            )
            if skipped_count:
                logger.info("Overdue schedules skipped: user_id=%s count=%s", user.id, skipped_count)

            tasks = self.notification_repository.get_due_pending(
                schedule_date=local_now.date().isoformat(),
                current_time=local_now.strftime("%H:%M:%S"),
                user_id=user.id,
            )
            for task in tasks:
                try:
                    channel = self._send_notification(user.id, task.content_snapshot)
                    updated = self.notification_repository.mark_sent(
                        notification_id=task.notification_id,
                        schedule_id=task.schedule_id,
                    )
                    if updated:
                        logger.info(
                            "Notification sent: user_id=%s channel=%s notification_id=%s",
                            user.id,
                            channel,
                            task.notification_id,
                        )
                except Exception:
                    logger.exception(
                        "Failed to send notification: user_id=%s notification_id=%s",
                        user.id,
                        task.notification_id,
                    )
                    self.notification_repository.mark_failed(
                        notification_id=task.notification_id,
                        schedule_id=task.schedule_id,
                    )

    def _send_notification(self, user_id: int, message: str) -> str:
        try:
            result = self.web_push_service.send_to_user(
                user_id=user_id,
                title="随机提醒器",
                body=message,
                url="/",
            )
            if result.sent:
                return "web_push"
        except (ValueError, RuntimeError) as error:
            logger.info("Web Push unavailable for user_id=%s: %s", user_id, error)
        except Exception:
            logger.exception("Unexpected Web Push error for user_id=%s", user_id)

        return self.notification_service.send(title="随机提醒器", message=message)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                logger.exception("Schedule executor cycle failed")
            self._stop_event.wait(self.check_interval_seconds)
