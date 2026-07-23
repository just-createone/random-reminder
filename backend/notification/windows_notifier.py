from winotify import Notification

from backend.notification.base import NotificationProvider


class WindowsNotifier(NotificationProvider):
    """使用 Windows Toast 显示桌面通知。"""

    APP_ID = "Random Reminder"

    def send(
        self,
        title: str,
        message: str,
    ) -> None:
        """发送 Windows 桌面通知。"""

        notification = Notification(
            app_id=self.APP_ID,
            title=title,
            msg=message,
            duration="short",
        )

        notification.show()