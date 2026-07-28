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


@dataclass(frozen=True)
class NotificationHistoryItem:
    """表示一条可展示的通知历史记录。"""

    notification_id: int
    schedule_id: int
    content: str
    schedule_date: str
    scheduled_time: str
    notification_status: str
    schedule_status: str
    sent_at: str | None
    created_at: str