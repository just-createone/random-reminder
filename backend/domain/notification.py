from dataclasses import dataclass


@dataclass
class Notification:
    """
    表示一次提醒通知记录。
    """

    id: int | None

    schedule_id: int

    status: str

    sent_at: str | None

    created_at: str | None