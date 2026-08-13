import sqlite3
from pathlib import Path

import pytest

from backend.core.exceptions import ResourceNotFoundError
from backend.database import db
from backend.database.init_db import init_database
from backend.services.auth_service import AuthService
from backend.services.data_transfer_service import DataTransferService
from backend.services.reminder_service import ReminderService
from backend.services.settings_service import SettingsService
from backend.repository.daily_schedule_repository import DailyScheduleRepository
from backend.repository.notification_repository import NotificationRepository
from backend.repository.push_subscription_repository import PushSubscriptionRepository


@pytest.fixture
def database_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    path = tmp_path / "test_random_reminder.db"
    monkeypatch.setattr(db, "get_db_path", lambda: str(path))
    init_database()
    return path


def _create_user(email: str):
    return AuthService().register(
        email,
        "password-123",
        "America/New_York",
    )


def _settings_for_user(user_id: int):
    return SettingsService().update_settings(
        enabled=True,
        all_day=False,
        start_time="09:00",
        end_time="22:00",
        times_per_day=4,
        minimum_interval=60,
        user_id=user_id,
    )


def test_reminders_settings_and_exports_are_isolated_by_user(
    database_path: Path,
) -> None:
    user_a = _create_user("a@example.com")
    user_b = _create_user("b@example.com")
    reminders = ReminderService()
    transfer = DataTransferService()

    reminder_a = reminders.create_reminder("only user A", user_a.id)
    reminder_b = reminders.create_reminder("only user B", user_b.id)
    _settings_for_user(user_a.id)

    user_b_settings = SettingsService().get_settings(user_b.id)
    assert user_b_settings.enabled is False

    assert [item.content for item in reminders.get_all_reminders(user_a.id)] == [
        "only user A"
    ]
    assert [item.content for item in reminders.get_all_reminders(user_b.id)] == [
        "only user B"
    ]
    with pytest.raises(ResourceNotFoundError):
        reminders.get_reminder(reminder_a.id, user_b.id)

    with pytest.raises(ResourceNotFoundError):
        reminders.get_reminder(reminder_b.id, user_a.id)

    export_a = transfer.export_data(user_a.id)
    export_b = transfer.export_data(user_b.id)
    assert [item["content"] for item in export_a["reminders"]] == ["only user A"]
    assert [item["content"] for item in export_b["reminders"]] == ["only user B"]
    assert export_a["settings"]["enabled"] is True
    assert export_b["settings"]["enabled"] is False


def test_import_only_changes_the_current_users_data(
    database_path: Path,
) -> None:
    user_a = _create_user("a@example.com")
    user_b = _create_user("b@example.com")
    reminders = ReminderService()
    reminders.create_reminder("existing A", user_a.id)
    reminders.create_reminder("existing B", user_b.id)

    payload = {
        "format": "random-reminder-export",
        "format_version": 1,
        "exported_at": "2026-08-10T10:30:00Z",
        "reminders": [{"content": "imported for A", "enabled": True}],
        "settings": {
            "enabled": True,
            "all_day": True,
            "start_time": None,
            "end_time": None,
            "times_per_day": 3,
            "minimum_interval": 60,
        },
    }

    DataTransferService().import_data(payload, user_a.id)

    assert [item.content for item in reminders.get_all_reminders(user_a.id)] == [
        "imported for A",
        "existing A",
    ]
    assert [item.content for item in reminders.get_all_reminders(user_b.id)] == [
        "existing B"
    ]
    assert SettingsService().get_settings(user_a.id).enabled is True
    assert SettingsService().get_settings(user_b.id).enabled is False


def test_legacy_data_is_claimed_only_by_the_first_registered_user(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "legacy_random_reminder.db"
    monkeypatch.setattr(db, "get_db_path", lambda: str(path))

    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO reminders (content) VALUES ('legacy reminder');
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER NOT NULL DEFAULT 0,
                all_day INTEGER NOT NULL DEFAULT 1,
                start_time TEXT,
                end_time TEXT,
                times_per_day INTEGER NOT NULL DEFAULT 3,
                minimum_interval INTEGER NOT NULL DEFAULT 60,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO settings (id, enabled) VALUES (1, 1);
            """)

    init_database()
    first_user = _create_user("first@example.com")
    second_user = _create_user("second@example.com")

    reminders = ReminderService()
    assert [item.content for item in reminders.get_all_reminders(first_user.id)] == [
        "legacy reminder"
    ]
    assert reminders.get_all_reminders(second_user.id) == []
    assert SettingsService().get_settings(first_user.id).enabled is True
    assert SettingsService().get_settings(second_user.id).enabled is False


def test_schedules_history_and_push_subscriptions_are_isolated(
    database_path: Path,
) -> None:
    user_a = _create_user("a@example.com")
    user_b = _create_user("b@example.com")
    schedules = DailyScheduleRepository()
    notifications = NotificationRepository()
    push = PushSubscriptionRepository()

    schedule_a = schedules.create_many(
        "2026-01-01", [("09:00", 1, "for A")], user_a.id
    )[0]
    schedule_b = schedules.create_many(
        "2026-01-01", [("09:00", 2, "for B")], user_b.id
    )[0]
    notifications.create_many_for_schedules([schedule_a.id, schedule_b.id])
    notifications.mark_sent(1, schedule_a.id)

    assert [item.content for item in schedules.get_by_date("2026-01-01", user_a.id)] == ["for A"]
    assert [item.content for item in schedules.get_by_date("2026-01-01", user_b.id)] == ["for B"]
    assert [item.content for item in notifications.get_recent_history(user_id=user_a.id, today="2026-01-01")] == ["for A"]
    assert [item.content for item in notifications.get_recent_history(user_id=user_b.id, today="2026-01-01")] == ["for B"]

    push.save(user_a.id, "https://push.example/a", "key-a", "auth-a")
    push.save(user_b.id, "https://push.example/b", "key-b", "auth-b")
    assert [item.endpoint for item in push.get_active(user_a.id)] == ["https://push.example/a"]
    assert [item.endpoint for item in push.get_active(user_b.id)] == ["https://push.example/b"]


def test_legacy_schedule_and_push_data_are_claimed_by_one_existing_user(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "legacy_schedule.db"
    monkeypatch.setattr(db, "get_db_path", lambda: str(path))
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                time_zone TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO users (email, password_hash, time_zone)
                VALUES ('owner@example.com', 'hash', 'Asia/Shanghai');
            CREATE TABLE daily_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_date TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                reminder_id INTEGER,
                content_snapshot TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(schedule_date, scheduled_time)
            );
            INSERT INTO daily_schedules (schedule_date, scheduled_time, content_snapshot)
                VALUES ('2026-01-01', '09:00', 'legacy schedule');
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                sent_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO notifications (schedule_id) VALUES (1);
            CREATE TABLE push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL UNIQUE,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                user_agent TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO push_subscriptions (endpoint, p256dh, auth)
                VALUES ('https://push.example/legacy', 'key', 'auth');
        """)

    init_database()
    with sqlite3.connect(path) as connection:
        schedule_owner = connection.execute(
            "SELECT user_id FROM daily_schedules WHERE id = 1"
        ).fetchone()[0]
        push_owner = connection.execute(
            "SELECT user_id FROM push_subscriptions WHERE id = 1"
        ).fetchone()[0]

    assert schedule_owner == 1
    assert push_owner == 1
