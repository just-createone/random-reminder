from backend.config import logger
from backend.notification.base import NotificationProvider


class ConsoleNotifier(NotificationProvider):
    """将通知内容输出到日志的备用通知实现。"""

    def send(
        self,
        title: str,
        message: str,
    ) -> None:
        """把通知写入日志。"""

        logger.info(
            "Notification | title=%s | message=%s",
            title,
            message,
        )