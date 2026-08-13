from dataclasses import dataclass


@dataclass
class Settings:
    """A registered user's reminder settings."""

    id: int
    user_id: int | None
    enabled: bool
    all_day: bool
    start_time: str | None
    end_time: str | None
    times_per_day: int
    minimum_interval: int
    created_at: str
    updated_at: str
