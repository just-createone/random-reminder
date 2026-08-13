from datetime import datetime, timezone

from backend.domain.notification import NotificationTask
from backend.domain.user import User
from backend.executor.schedule_executor import ScheduleExecutor


def _user(user_id: int, time_zone: str) -> User:
    return User(
        id=user_id,
        email=f"user-{user_id}@example.com",
        time_zone=time_zone,
        created_at="",
        updated_at="",
    )


class FakeUserRepository:
    def __init__(self, users: list[User]) -> None:
        self.users = users

    def get_enabled_users(self) -> list[User]:
        return self.users


class FakeScheduleService:
    def __init__(self) -> None:
        self.checked_users: list[tuple[int, str]] = []
        self.skipped_users: list[int] = []

    def get_today_schedule(self, *, user_id: int, time_zone: str, now):
        self.checked_users.append((user_id, now.date().isoformat()))
        return [object()]

    def generate_today_schedule(self, **kwargs):
        return [object()]

    def skip_overdue_pending(self, *, user_id: int, **kwargs) -> int:
        self.skipped_users.append(user_id)
        return 0


class FakeNotificationRepository:
    def __init__(self) -> None:
        self.queries: list[tuple[int, str]] = []
        self.marked_sent: list[int] = []

    def get_due_pending(self, *, user_id: int, schedule_date: str, current_time: str):
        self.queries.append((user_id, schedule_date))
        if user_id == 1:
            return [NotificationTask(1, 10, "only user one", "09:00")]
        return []

    def mark_sent(self, *, notification_id: int, schedule_id: int) -> bool:
        self.marked_sent.append(notification_id)
        return True

    def mark_failed(self, **kwargs) -> None:
        raise AssertionError("the successful fake push must not fail")


class FakeWebPushService:
    def __init__(self) -> None:
        self.deliveries: list[tuple[int, str]] = []

    def send_to_user(self, *, user_id: int, body: str, **kwargs):
        self.deliveries.append((user_id, body))
        return type("Result", (), {"sent": 1})()


def test_executor_processes_enabled_users_in_their_own_time_zones() -> None:
    schedule_service = FakeScheduleService()
    notifications = FakeNotificationRepository()
    web_push = FakeWebPushService()
    executor = ScheduleExecutor(
        user_repository=FakeUserRepository(
            [_user(1, "America/New_York"), _user(2, "Asia/Shanghai")]
        ),
        schedule_service=schedule_service,
        notification_repository=notifications,
        notification_service=object(),
        web_push_service=web_push,
    )

    executor.run_once(datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc))

    assert schedule_service.checked_users == [(1, "2025-12-31"), (2, "2026-01-01")]
    assert schedule_service.skipped_users == [1, 2]
    assert notifications.queries == [(1, "2025-12-31"), (2, "2026-01-01")]
    assert web_push.deliveries == [(1, "only user one")]
    assert notifications.marked_sent == [1]
