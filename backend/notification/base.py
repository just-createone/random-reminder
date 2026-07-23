from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    """通知提供者的抽象接口。"""

    @abstractmethod
    def send(
        self,
        title: str,
        message: str,
    ) -> None:
        """发送一条系统通知。"""

        raise NotImplementedError