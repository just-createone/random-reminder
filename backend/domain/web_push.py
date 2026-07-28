from dataclasses import dataclass


@dataclass(frozen=True)
class WebPushSendResult:
    """表示一次批量 Web Push 的发送结果。"""

    total: int
    sent: int
    failed: int
    deactivated: int