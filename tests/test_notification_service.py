from backend.notification.console_notifier import (
    ConsoleNotifier,
)
from backend.notification.notification_service import (
    NotificationService,
)


class RecordingProvider:
    """记录通知发送参数的测试 Provider。"""

    def __init__(self) -> None:
        self.calls: list[
            tuple[str, str]
        ] = []

    def send(
        self,
        title: str,
        message: str,
    ) -> None:
        self.calls.append(
            (
                title,
                message,
            )
        )


class FailingProvider:
    """模拟系统通知发送失败。"""

    def send(
        self,
        title: str,
        message: str,
    ) -> None:
        raise RuntimeError(
            "模拟通知失败"
        )


def test_notification_service_uses_provider() -> None:
    """正常情况下应调用指定 Provider。"""

    provider = RecordingProvider()

    service = NotificationService(
        provider=provider,
    )

    channel = service.send(
        title=" 测试标题 ",
        message=" 测试内容 ",
    )

    assert provider.calls == [
        (
            "测试标题",
            "测试内容",
        )
    ]

    assert channel == "recordingprovider"


def test_notification_service_falls_back_to_console(
    monkeypatch,
) -> None:
    """系统通知失败后应回退到控制台。"""

    calls: list[
        tuple[str, str]
    ] = []

    def fake_console_send(
        self,
        title: str,
        message: str,
    ) -> None:
        calls.append(
            (
                title,
                message,
            )
        )

    monkeypatch.setattr(
        ConsoleNotifier,
        "send",
        fake_console_send,
    )

    service = NotificationService(
        provider=FailingProvider(),
    )

    channel = service.send(
        title="随机提醒器",
        message="回退通知测试",
    )

    assert channel == "console"

    assert calls == [
        (
            "随机提醒器",
            "回退通知测试",
        )
    ]


def test_non_windows_uses_console_provider(
    monkeypatch,
) -> None:
    """非 Windows 环境应选择 ConsoleNotifier。"""

    monkeypatch.setattr(
        "platform.system",
        lambda: "Linux",
    )

    service = NotificationService()

    assert isinstance(
        service.provider,
        ConsoleNotifier,
    )