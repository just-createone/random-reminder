from dataclasses import dataclass


@dataclass(frozen=True)
class PushSubscription:
    """表示一个浏览器 Web Push 订阅。"""

    id: int | None
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None
    is_active: bool
    created_at: str | None
    updated_at: str | None