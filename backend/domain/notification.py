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


@dataclass(frozen=True)
class NotificationTask:
    """表示一条等待执行的通知任务。"""

    notification_id: int
    schedule_id: int
    content_snapshot: str
    scheduled_time: str