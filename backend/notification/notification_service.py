import platform

from backend.config import logger
from backend.notification.base import NotificationProvider
from backend.notification.console_notifier import ConsoleNotifier
from backend.notification.windows_notifier import WindowsNotifier


class NotificationService:
    """根据当前运行平台发送通知。"""

    def __init__(
        self,
        provider: NotificationProvider | None = None,
    ) -> None:
        self.provider = provider or self._create_provider()

    def send(
        self,
        title: str,
        message: str,
    ) -> None:
        """验证内容并发送通知。"""

        cleaned_title = title.strip()
        cleaned_message = message.strip()

        if not cleaned_title:
            raise ValueError("通知标题不能为空")

        if not cleaned_message:
            raise ValueError("通知内容不能为空")

        try:
            self.provider.send(
                title=cleaned_title,
                message=cleaned_message,
            )

        except Exception:
            logger.exception(
                "System notification failed, using console fallback"
            )

            fallback = ConsoleNotifier()

            fallback.send(
                title=cleaned_title,
                message=cleaned_message,
            )

            raise RuntimeError(
                "系统通知发送失败，请检查 Windows 通知权限"
            )

    @staticmethod
    def _create_provider() -> NotificationProvider:
        """根据操作系统选择通知实现。"""

        system_name = platform.system()

        if system_name == "Windows":
            return WindowsNotifier()

        logger.warning(
            "Unsupported notification platform: %s; "
            "using console notifier",
            system_name,
        )

        return ConsoleNotifier()