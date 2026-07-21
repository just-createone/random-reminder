from dataclasses import dataclass


@dataclass
class DailySchedule:
    """某一天生成的一条随机提醒计划。"""

    id: int
    schedule_date: str
    scheduled_time: str
    reminder_id: int | None
    content: str
    status: str
    created_at: str