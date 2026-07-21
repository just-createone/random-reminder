from dataclasses import dataclass


@dataclass
class Settings:
    """随机提醒器的全局提醒设置。"""

    id: int
    enabled: bool
    all_day: bool
    start_time: str | None
    end_time: str | None
    times_per_day: int
    minimum_interval: int
    created_at: str
    updated_at: str