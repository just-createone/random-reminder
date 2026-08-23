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
        self.cleared_users: set[int] = set()

    def get_today_schedule(self, *, user_id: int, time_zone: str, now):
        self.checked_users.append((user_id, now.date().isoformat()))
        return [object()]

    def is_today_schedule_cleared(self, *, user_id: int, **kwargs) -> bool:
        return user_id in self.cleared_users

    def generate_today_schedule(self, **kwargs):
        return [object()]

    def skip_overdue_pending(self, *, user_id: int, **kwargs) -> int:
        self.skipped_users.append(user_id)
        return 0


class FakeNotificationRepository:
    def __init__(self) -> None:
        self.queries: list[tuple[int, str]] = []
        self.marked_sent: list[int] = []
        self.released_claim_cutoffs: list[str] = []

    def get_due_pending(self, *, user_id: int, schedule_date: str, current_time: str):
        self.queries.append((user_id, schedule_date))
        if user_id == 1:
            return [NotificationTask(1, 10, "only user one", "09:00")]
        return []

    def mark_sent(self, *, notification_id: int, schedule_id: int) -> bool:
        self.marked_sent.append(notification_id)
        return True

    def claim_pending(self, notification_id: int) -> bool:
        return True

    def release_expired_claims(self, **kwargs) -> int:
        self.released_claim_cutoffs.append(kwargs["cutoff"])
        return 0

    def mark_failed(self, **kwargs) -> None:
        raise AssertionError("the successful fake push must not fail")


class FakeWebPushService:
    def __init__(self) -> None:
        self.deliveries: list[tuple[int, str]] = []

    def send_to_user(self, *, user_id: int, body: str, **kwargs):
        self.deliveries.append((user_id, body))
        return type("Result", (), {"sent": 1})()


class NoDeliveryWebPushService:
    def send_to_user(self, **kwargs):
        return type("Result", (), {"sent": 0})()


class FailedNotificationRepository(FakeNotificationRepository):
    def __init__(self) -> None:
        super().__init__()
        self.marked_failed: list[int] = []

    def mark_failed(self, *, notification_id: int, schedule_id: int) -> None:
        self.marked_failed.append(notification_id)


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
        web_push_service=web_push,
    )

    executor.run_once(datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc))

    assert schedule_service.checked_users == [(1, "2025-12-31"), (2, "2026-01-01")]
    assert schedule_service.skipped_users == [1, 2]
    assert notifications.queries == [(1, "2025-12-31"), (2, "2026-01-01")]
    assert web_push.deliveries == [(1, "only user one")]
    assert notifications.marked_sent == [1]


def test_executor_respects_a_users_manual_schedule_clearance() -> None:
    schedule_service = FakeScheduleService()
    schedule_service.cleared_users.add(1)
    executor = ScheduleExecutor(
        user_repository=FakeUserRepository([_user(1, "Asia/Shanghai")]),
        schedule_service=schedule_service,
        notification_repository=FakeNotificationRepository(),
        web_push_service=FakeWebPushService(),
    )

    executor.ensure_today_schedule(
        user_id=1,
        time_zone="Asia/Shanghai",
        now=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        force_check=True,
    )

    assert schedule_service.checked_users == []


def test_executor_marks_undeliverable_web_push_as_failed() -> None:
    notifications = FailedNotificationRepository()
    executor = ScheduleExecutor(
        user_repository=FakeUserRepository([_user(1, "Asia/Shanghai")]),
        schedule_service=FakeScheduleService(),
        notification_repository=notifications,
        web_push_service=NoDeliveryWebPushService(),
    )

    executor.run_once(datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc))

    assert notifications.marked_sent == []
    assert notifications.marked_failed == [1]


def test_executor_uses_utc_for_notification_claim_expiry() -> None:
    notifications = FakeNotificationRepository()
    executor = ScheduleExecutor(
        user_repository=FakeUserRepository([_user(1, "Asia/Shanghai")]),
        schedule_service=FakeScheduleService(),
        notification_repository=notifications,
        web_push_service=FakeWebPushService(),
    )

    executor.run_once(datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc))

    assert notifications.released_claim_cutoffs == ["2026-01-01 00:45:00"]
