from dataclasses import dataclass


@dataclass
class Reminder:
    """随机提醒器中的一条提醒内容。"""

    id: int
    content: str
    enabled: bool
    created_at: str
    updated_at: str