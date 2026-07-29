import platform

from backend.config import logger
from backend.domain.notification import (
    NotificationHistoryItem,
)
from backend.notification.base import (
    NotificationProvider,
)
from backend.notification.console_notifier import (
    ConsoleNotifier,
)
from backend.repository.notification_repository import (
    NotificationRepository,
)


class NotificationService:
    """负责发送系统通知和查询通知历史。"""

    def __init__(
        self,
        provider: NotificationProvider | None = None,
        notification_repository: (
            NotificationRepository | None
        ) = None,
    ) -> None:
        self.provider = (
            provider
            or self._create_provider()
        )

        self.notification_repository = (
            notification_repository
            or NotificationRepository()
        )

    def send(
        self,
        title: str,
        message: str,
    ) -> str:
        """
        验证并发送系统通知。

        返回实际使用的通知渠道：
        windows 或 console。
        """

        cleaned_title = title.strip()
        cleaned_message = message.strip()

        if not cleaned_title:
            raise ValueError(
                "通知标题不能为空"
            )

        if not cleaned_message:
            raise ValueError(
                "通知内容不能为空"
            )

        try:
            self.provider.send(
                title=cleaned_title,
                message=cleaned_message,
            )

            return self._get_provider_name(
                self.provider
            )

        except Exception:
            logger.exception(
                "System notification failed, "
                "using console fallback"
            )

            fallback = ConsoleNotifier()

            fallback.send(
                title=cleaned_title,
                message=cleaned_message,
            )

            return "console"

    def get_recent_history(
        self,
        limit: int = 20,
    ) -> list[NotificationHistoryItem]:
        """查询最近的通知历史记录。"""

        if limit < 1:
            raise ValueError(
                "查询数量不能小于 1"
            )

        if limit > 100:
            raise ValueError(
                "查询数量不能超过 100"
            )

        return (
            self.notification_repository
            .get_recent_history(
                limit=limit,
            )
        )

    @staticmethod
    def _create_provider() -> NotificationProvider:
        """根据当前操作系统创建通知实现。"""

        system_name = platform.system()

        if system_name == "Windows":
            try:
                # 只在 Windows 环境中导入，
                # 避免 Linux 启动时依赖 winotify。
                from backend.notification.windows_notifier import (
                    WindowsNotifier,
                )

                return WindowsNotifier()

            except (ImportError, OSError):
                logger.exception(
                    "Windows notification provider "
                    "is unavailable; "
                    "using console notifier"
                )

                return ConsoleNotifier()

        logger.info(
            "System notification platform=%s; "
            "using console notifier",
            system_name,
        )

        return ConsoleNotifier()

    @staticmethod
    def _get_provider_name(
        provider: NotificationProvider,
    ) -> str:
        """返回通知提供者对应的渠道名称。"""

        if isinstance(
            provider,
            ConsoleNotifier,
        ):
            return "console"

        provider_name = (
            provider.__class__.__name__
            .removesuffix("Notifier")
            .lower()
        )

        return (
            provider_name
            or "system"
        )