import threading
from datetime import datetime

from backend.config import logger
from backend.notification.windows_notifier import (
    WindowsNotifier,
)
from backend.repository.notification_repository import (
    NotificationRepository,
)
from backend.services.web_push_service import (
    WebPushService,
)


class ScheduleExecutor:
    """定时检查并发送已经到期的提醒通知。"""

    def __init__(
        self,
        notification_repository: (
            NotificationRepository | None
        ) = None,
        notifier: WindowsNotifier | None = None,
        web_push_service: WebPushService | None = None,
        check_interval_seconds: int = 30,
    ) -> None:
        self.notification_repository = (
            notification_repository
            or NotificationRepository()
        )

        self.notifier = (
            notifier
            or WindowsNotifier()
        )

        self.web_push_service = (
            web_push_service
            or WebPushService()
        )

        self.check_interval_seconds = (
            check_interval_seconds
        )

        self._stop_event = threading.Event()

        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """启动后台执行线程。"""

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            logger.warning(
                "Schedule executor is already running"
            )
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="schedule-executor",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "Schedule executor started"
        )

    def stop(self) -> None:
        """停止后台执行线程。"""

        self._stop_event.set()

        thread = self._thread

        if (
            thread is not None
            and thread.is_alive()
            and thread is not threading.current_thread()
        ):
            thread.join(
                timeout=2
            )

        self._thread = None

        logger.info(
            "Schedule executor stopped"
        )

    def run_once(self) -> None:
        """立即执行一次到期通知检查。"""

        now = datetime.now()

        schedule_date = (
            now.date().isoformat()
        )

        current_time = (
            now.strftime("%H:%M:%S")
        )

        tasks = (
            self.notification_repository
            .get_due_pending(
                schedule_date=schedule_date,
                current_time=current_time,
            )
        )

        if not tasks:
            return

        logger.info(
            "Found %s due notification tasks",
            len(tasks),
        )

        for task in tasks:
            try:
                delivery_channel = (
                    self._send_notification(
                        message=task.content_snapshot,
                    )
                )

                updated = (
                    self.notification_repository
                    .mark_sent(
                        notification_id=(
                            task.notification_id
                        ),
                        schedule_id=(
                            task.schedule_id
                        ),
                    )
                )

                if not updated:
                    logger.warning(
                        "Notification status was not updated: "
                        "notification_id=%s, "
                        "schedule_id=%s",
                        task.notification_id,
                        task.schedule_id,
                    )

                    continue

                logger.info(
                    "Notification sent: "
                    "channel=%s, "
                    "notification_id=%s, "
                    "schedule_id=%s",
                    delivery_channel,
                    task.notification_id,
                    task.schedule_id,
                )

            except Exception:
                logger.exception(
                    "Failed to send notification: "
                    "notification_id=%s, "
                    "schedule_id=%s",
                    task.notification_id,
                    task.schedule_id,
                )

                try:
                    self.notification_repository.mark_failed(
                        notification_id=(
                            task.notification_id
                        ),
                        schedule_id=(
                            task.schedule_id
                        ),
                    )

                except Exception:
                    logger.exception(
                        "Failed to update notification "
                        "failure status"
                    )

    def _send_notification(
        self,
        message: str,
    ) -> str:
        """
        优先发送 Web Push。

        没有有效订阅或全部推送失败时，
        回退到 Windows 本地通知。
        """

        try:
            result = self.web_push_service.send_to_all(
                title="随机提醒器",
                body=message,
                url="/",
            )

        except ValueError as error:
            logger.info(
                "Web Push unavailable; "
                "using local notification: %s",
                error,
            )

        except RuntimeError as error:
            logger.warning(
                "Web Push configuration failed; "
                "using local notification: %s",
                error,
            )

        except Exception:
            logger.exception(
                "Unexpected Web Push error; "
                "using local notification"
            )

        else:
            if result.sent > 0:
                logger.info(
                    "Web Push delivery completed: "
                    "total=%s, sent=%s, failed=%s, "
                    "deactivated=%s",
                    result.total,
                    result.sent,
                    result.failed,
                    result.deactivated,
                )

                return "web_push"

            logger.warning(
                "No Web Push subscription received "
                "the notification; "
                "using local notification"
            )

        send_result = self.notifier.send(
            title="随机提醒器",
            message=message,
        )

        if send_result is False:
            raise RuntimeError(
                "Windows notifier returned False"
            )

        return "local"

    def _run(self) -> None:
        """后台线程循环检查到期任务。"""

        while not self._stop_event.is_set():
            try:
                self.run_once()

            except Exception:
                logger.exception(
                    "Schedule executor cycle failed"
                )

            self._stop_event.wait(
                self.check_interval_seconds
            )