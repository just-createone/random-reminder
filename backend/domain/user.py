from dataclasses import dataclass


@dataclass
class User:
    """A registered application user without password data."""

    id: int
    email: str
    time_zone: str
    created_at: str
    updated_at: str
