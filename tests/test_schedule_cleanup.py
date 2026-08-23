from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
import pytest

from backend.database import db
from backend.database.init_db import init_database
from backend.executor.schedule_executor import ScheduleExecutor
from backend.main import app
from backend.repository.daily_schedule_repository import DailyScheduleRepository
from backend.services.auth_service import AuthService
from backend.services.reminder_service import ReminderService
from backend.services.schedule_service import ScheduleService
from backend.services.settings_service import SettingsService


@pytest.fixture
def database_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    path = tmp_path / "test_random_reminder.db"
    monkeypatch.setattr(db, "get_db_path", lambda: str(path))
    init_database()
    return path


def test_clear_today_keeps_history_and_other_users_data(
    database_path: Path,
) -> None:
    user_a = AuthService().register("a@example.com", "password-123")
    user_b = AuthService().register("b@example.com", "password-123")
    schedules = DailyScheduleRepository()
    schedule_date = "2099-01-01"

    user_a_schedules = schedules.create_many(
        schedule_date,
        [
            ("09:00", 1, "pending"),
            ("10:00", 1, "skipped"),
            ("11:00", 1, "sent"),
        ],
        user_a.id,
    )
    schedules.create_many(
        schedule_date,
        [("09:00", 2, "other user")],
        user_b.id,
    )
    schedules.update_status(user_a_schedules[1].id, "skipped")
    schedules.update_status(user_a_schedules[2].id, "sent")

    deleted_count = ScheduleService().clear_today_replaceable_schedules(
        user_id=user_a.id,
        time_zone="Asia/Shanghai",
        now=datetime(2099, 1, 1, 12, tzinfo=ZoneInfo("Asia/Shanghai")),
    )

    assert deleted_count == 2
    assert [item.content for item in schedules.get_by_date(schedule_date, user_a.id)] == [
        "sent"
    ]
    assert [item.content for item in schedules.get_by_date(schedule_date, user_b.id)] == [
        "other user"
    ]
    assert ScheduleService().is_today_schedule_cleared(
        user_id=user_a.id,
        time_zone="Asia/Shanghai",
        now=datetime(2099, 1, 1, 12, tzinfo=ZoneInfo("Asia/Shanghai")),
    )


def test_clear_today_api_is_scoped_to_the_authenticated_user(
    database_path: Path,
) -> None:
    schedule_date = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    schedules = DailyScheduleRepository()

    with TestClient(app) as client_a, TestClient(app) as client_b:
        assert client_a.post(
            "/api/auth/register",
            json={
                "email": "a@example.com",
                "password": "password-123",
                "time_zone": "Asia/Shanghai",
            },
        ).status_code == 201
        assert client_b.post(
            "/api/auth/register",
            json={
                "email": "b@example.com",
                "password": "password-123",
                "time_zone": "Asia/Shanghai",
            },
        ).status_code == 201

        user_a_id = client_a.get("/api/auth/me").json()["data"]["id"]
        user_b_id = client_b.get("/api/auth/me").json()["data"]["id"]
        schedules.create_many(schedule_date, [("23:00", 1, "for A")], user_a_id)
        schedules.create_many(schedule_date, [("23:00", 2, "for B")], user_b_id)

        response = client_a.delete("/api/schedules/today")

    assert response.status_code == 200
    assert response.json()["data"] == {"deleted_count": 1}
    assert schedules.get_by_date(schedule_date, user_a_id) == []
    assert [item.content for item in schedules.get_by_date(schedule_date, user_b_id)] == [
        "for B"
    ]


def test_executor_does_not_regenerate_a_manually_cleared_schedule(
    database_path: Path,
) -> None:
    user = AuthService().register("user@example.com", "password-123")
    settings = SettingsService()
    settings.update_settings(
        enabled=True,
        all_day=True,
        start_time=None,
        end_time=None,
        times_per_day=1,
        minimum_interval=5,
        user_id=user.id,
    )
    ReminderService().create_reminder("temporary", user.id)
    now = datetime(2099, 1, 1, 12, tzinfo=ZoneInfo("Asia/Shanghai"))
    service = ScheduleService()
    service.generate_today_schedule(
        now=now,
        user_id=user.id,
        time_zone=user.time_zone,
    )
    service.clear_today_replaceable_schedules(
        user_id=user.id,
        time_zone=user.time_zone,
        now=now,
    )

    ScheduleExecutor(schedule_service=service).ensure_today_schedule(
        user_id=user.id,
        time_zone=user.time_zone,
        now=now,
        force_check=True,
    )

    assert service.get_today_schedule(
        user_id=user.id,
        time_zone=user.time_zone,
        now=now,
    ) == []
