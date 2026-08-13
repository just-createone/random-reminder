import json
import sqlite3
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import HTTPException

from backend.api.data import (
    export_user_data,
    import_user_data,
)
from backend.database import db
from backend.database.db import get_connection
from backend.database.init_db import init_database
from backend.main import app
from backend.services.data_transfer_service import (
    DataTransferService,
)
from backend.services.auth_service import AuthService


def valid_payload() -> dict[str, object]:
    return {
        "format": "random-reminder-export",
        "format_version": 1,
        "exported_at": "2026-08-10T10:30:00Z",
        "reminders": [
            {
                "content": "导入提醒",
                "enabled": True,
            }
        ],
        "settings": {
            "enabled": True,
            "all_day": False,
            "start_time": "09:00",
            "end_time": "22:00",
            "times_per_day": 3,
            "minimum_interval": 60,
        },
    }


@pytest.fixture
def database_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    path = tmp_path / "test_random_reminder.db"

    monkeypatch.setattr(
        db,
        "get_db_path",
        lambda: str(path),
    )

    init_database()

    return path


def read_reminders(
    database_path: Path,
) -> list[tuple[int, str, int]]:
    with sqlite3.connect(database_path) as connection:
        return connection.execute(
            """
            SELECT id, content, enabled
            FROM reminders
            ORDER BY id ASC
            """
        ).fetchall()


def read_settings(
    database_path: Path,
) -> tuple[int, int, str | None, str | None, int, int]:
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                enabled,
                all_day,
                start_time,
                end_time,
                times_per_day,
                minimum_interval
            FROM settings
            WHERE id = 1
            """
        ).fetchone()

    assert row is not None
    return row


def read_table_counts(
    database_path: Path,
) -> dict[str, int]:
    with sqlite3.connect(database_path) as connection:
        return {
            table_name: connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]
            for table_name in (
                "reminders",
                "settings",
                "daily_schedules",
                "notifications",
                "push_subscriptions",
            )
        }


def test_export_empty_reminders_contains_only_portable_fields(
    database_path: Path,
) -> None:
    data = DataTransferService().export_data()

    assert set(data) == {
        "format",
        "format_version",
        "exported_at",
        "reminders",
        "settings",
    }
    assert data["format"] == "random-reminder-export"
    assert data["format_version"] == 1
    assert data["reminders"] == []
    assert data["settings"] == {
        "enabled": False,
        "all_day": True,
        "start_time": None,
        "end_time": None,
        "times_per_day": 3,
        "minimum_interval": 60,
    }

    exported_at = str(data["exported_at"])
    assert exported_at.endswith("Z")
    assert datetime.fromisoformat(
        exported_at.replace("Z", "+00:00")
    ).tzinfo is not None


def test_export_excludes_runtime_data_and_sensitive_push_fields(
    database_path: Path,
) -> None:
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO reminders (content, enabled)
            VALUES (?, ?)
            """,
            ("启用提醒", 1),
        )
        enabled_reminder_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO reminders (content, enabled)
            VALUES (?, ?)
            """,
            ("停用提醒", 0),
        )
        cursor.execute(
            """
            UPDATE settings
            SET
                enabled = 1,
                all_day = 0,
                start_time = '09:00',
                end_time = '22:00',
                times_per_day = 4,
                minimum_interval = 90
            WHERE id = 1
            """
        )
        cursor.execute(
            """
            INSERT INTO daily_schedules (
                schedule_date,
                scheduled_time,
                reminder_id,
                content_snapshot
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "2099-01-01",
                "09:00",
                enabled_reminder_id,
                "运行时计划内容",
            ),
        )
        schedule_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO notifications (schedule_id)
            VALUES (?)
            """,
            (schedule_id,),
        )
        cursor.execute(
            """
            INSERT INTO push_subscriptions (
                endpoint,
                p256dh,
                auth,
                user_agent
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "https://push.example.test/subscription",
                "sensitive-p256dh",
                "sensitive-auth",
                "sensitive-user-agent",
            ),
        )
        connection.commit()

    finally:
        connection.close()

    counts_before_export = read_table_counts(database_path)
    data = DataTransferService().export_data()
    serialized_data = json.dumps(data, ensure_ascii=False)

    assert data["reminders"] == [
        {"content": "停用提醒", "enabled": False},
        {"content": "启用提醒", "enabled": True},
    ]
    assert data["settings"] == {
        "enabled": True,
        "all_day": False,
        "start_time": "09:00",
        "end_time": "22:00",
        "times_per_day": 4,
        "minimum_interval": 90,
    }

    for forbidden_text in (
        "daily_schedules",
        "notifications",
        "push_subscriptions",
        "https://push.example.test/subscription",
        "sensitive-p256dh",
        "sensitive-auth",
        "sensitive-user-agent",
        "运行时计划内容",
    ):
        assert forbidden_text not in serialized_data

    assert "id" not in data["reminders"][0]
    assert "created_at" not in data["reminders"][0]
    assert "updated_at" not in data["reminders"][0]
    assert read_table_counts(database_path) == counts_before_export


def test_import_empty_reminders_restores_settings(
    database_path: Path,
) -> None:
    payload = valid_payload()
    payload["reminders"] = []

    result = DataTransferService().import_data(payload)

    assert result == {
        "imported_reminders": 0,
        "settings_restored": True,
    }
    assert read_reminders(database_path) == []
    assert read_settings(database_path) == (
        1,
        0,
        "09:00",
        "22:00",
        3,
        60,
    )


def test_import_appends_reminders_and_uses_target_database_ids(
    database_path: Path,
) -> None:
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO reminders (content, enabled)
            VALUES (?, ?)
            """,
            ("本地提醒", 1),
        )
        connection.commit()

    finally:
        connection.close()

    payload = valid_payload()
    payload["reminders"] = [
        {
            "id": 999,
            "created_at": "2000-01-01T00:00:00Z",
            "updated_at": "2000-01-01T00:00:00Z",
            "content": "  导入启用提醒  ",
            "enabled": True,
        },
        {
            "content": "导入停用提醒",
            "enabled": False,
        },
    ]

    result = DataTransferService().import_data(payload)

    assert result == {
        "imported_reminders": 2,
        "settings_restored": True,
    }
    assert read_reminders(database_path) == [
        (1, "本地提醒", 1),
        (2, "导入启用提醒", 1),
        (3, "导入停用提醒", 0),
    ]
    assert read_settings(database_path) == (
        1,
        0,
        "09:00",
        "22:00",
        3,
        60,
    )


def test_import_preserves_duplicate_reminders_on_every_import(
    database_path: Path,
) -> None:
    payload = valid_payload()
    payload["reminders"] = [
        {"content": "重复提醒", "enabled": True},
        {"content": "重复提醒", "enabled": True},
    ]

    service = DataTransferService()

    assert service.import_data(payload)["imported_reminders"] == 2
    assert service.import_data(payload)["imported_reminders"] == 2
    assert read_reminders(database_path) == [
        (1, "重复提醒", 1),
        (2, "重复提醒", 1),
        (3, "重复提醒", 1),
        (4, "重复提醒", 1),
    ]


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"format": "wrong"},
        {
            key: value
            for key, value in valid_payload().items()
            if key != "format_version"
        },
        {
            **valid_payload(),
            "format_version": True,
        },
        {
            **valid_payload(),
            "format_version": 2,
        },
        {
            key: value
            for key, value in valid_payload().items()
            if key != "reminders"
        },
        {
            **valid_payload(),
            "reminders": {},
        },
        {
            **valid_payload(),
            "reminders": [
                {"content": "提醒", "enabled": True}
                for _ in range(5001)
            ],
        },
        {
            **valid_payload(),
            "reminders": [
                {"content": 1, "enabled": True}
            ],
        },
        {
            **valid_payload(),
            "reminders": [
                {"content": "   ", "enabled": True}
            ],
        },
        {
            **valid_payload(),
            "reminders": [
                {"content": "a" * 501, "enabled": True}
            ],
        },
        {
            **valid_payload(),
            "reminders": [
                {"content": "提醒", "enabled": 1}
            ],
        },
        {
            key: value
            for key, value in valid_payload().items()
            if key != "settings"
        },
        {
            **valid_payload(),
            "settings": [],
        },
        {
            **valid_payload(),
            "exported_at": "not-an-iso-time",
        },
    ],
)
def test_import_rejects_invalid_payload_shapes(
    database_path: Path,
    payload: object,
) -> None:
    with pytest.raises(ValueError):
        DataTransferService().import_data(payload)

    assert read_reminders(database_path) == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("enabled", 1),
        ("all_day", "true"),
        ("start_time", 900),
        ("end_time", 2200),
        ("times_per_day", True),
        ("minimum_interval", False),
    ],
)
def test_import_rejects_invalid_settings_field_types(
    database_path: Path,
    field: str,
    value: object,
) -> None:
    payload = valid_payload()
    settings = payload["settings"]

    assert isinstance(settings, dict)
    settings[field] = value

    with pytest.raises(ValueError):
        DataTransferService().import_data(payload)

    assert read_reminders(database_path) == []


def test_import_rejects_missing_settings_fields(
    database_path: Path,
) -> None:
    payload = valid_payload()
    settings = payload["settings"]

    assert isinstance(settings, dict)
    del settings["minimum_interval"]

    with pytest.raises(ValueError):
        DataTransferService().import_data(payload)

    assert read_reminders(database_path) == []


@pytest.mark.parametrize(
    "settings",
    [
        {
            "enabled": True,
            "all_day": False,
            "start_time": "25:00",
            "end_time": "22:00",
            "times_per_day": 3,
            "minimum_interval": 60,
        },
        {
            "enabled": True,
            "all_day": False,
            "start_time": "09:00",
            "end_time": "22:00",
            "times_per_day": 21,
            "minimum_interval": 60,
        },
        {
            "enabled": True,
            "all_day": False,
            "start_time": "09:00",
            "end_time": "22:00",
            "times_per_day": 3,
            "minimum_interval": 4,
        },
        {
            "enabled": True,
            "all_day": False,
            "start_time": "09:00",
            "end_time": "10:00",
            "times_per_day": 3,
            "minimum_interval": 60,
        },
    ],
)
def test_import_reuses_settings_business_validation(
    database_path: Path,
    settings: dict[str, object],
) -> None:
    payload = valid_payload()
    payload["settings"] = settings

    with pytest.raises(ValueError):
        DataTransferService().import_data(payload)

    assert read_reminders(database_path) == []


def test_import_ignores_unknown_fields(
    database_path: Path,
) -> None:
    payload = valid_payload()
    payload["future_top_level_field"] = "ignored"
    settings = payload["settings"]

    assert isinstance(settings, dict)
    settings["future_setting_field"] = "ignored"

    result = DataTransferService().import_data(payload)

    assert result["imported_reminders"] == 1
    assert read_reminders(database_path) == [
        (1, "导入提醒", 1),
    ]


def test_import_rolls_back_reminders_and_settings_on_write_failure(
    database_path: Path,
) -> None:
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO reminders (content, enabled)
            VALUES (?, ?)
            """,
            ("原有提醒", 1),
        )
        connection.execute(
            """
            CREATE TRIGGER fail_data_import
            BEFORE INSERT ON reminders
            WHEN NEW.content = 'trigger-failure'
            BEGIN
                SELECT RAISE(ABORT, 'forced import failure');
            END
            """
        )
        connection.commit()

    finally:
        connection.close()

    payload = valid_payload()
    payload["reminders"] = [
        {"content": "第一条导入提醒", "enabled": True},
        {"content": "trigger-failure", "enabled": False},
    ]

    with pytest.raises(sqlite3.IntegrityError):
        DataTransferService().import_data(payload)

    assert read_reminders(database_path) == [
        (1, "原有提醒", 1),
    ]
    assert read_settings(database_path) == (
        0,
        1,
        None,
        None,
        3,
        60,
    )


def test_data_routes_are_registered_and_follow_api_response_style(
    database_path: Path,
) -> None:
    registered_paths = set(app.openapi()["paths"])

    assert "/health" in registered_paths
    assert "/api/reminders" in registered_paths
    assert "/api/settings" in registered_paths
    assert "/api/data/export" in registered_paths
    assert "/api/data/import" in registered_paths

    user = AuthService().register(
        "api-test@example.com",
        "password-123",
    )
    export_response = export_user_data(user)
    import_response = import_user_data(valid_payload(), user)

    assert export_response["success"] is True
    assert set(export_response) == {"success", "data", "message"}
    assert import_response == {
        "success": True,
        "data": {
            "imported_reminders": 1,
            "settings_restored": True,
        },
        "message": "用户数据导入成功",
    }


def test_import_api_returns_400_for_validation_errors(
    database_path: Path,
) -> None:
    invalid_payload = deepcopy(valid_payload())
    invalid_payload["format"] = "wrong"
    user = AuthService().register(
        "validation-test@example.com",
        "password-123",
    )

    with pytest.raises(HTTPException) as error_info:
        import_user_data(invalid_payload, user)

    assert error_info.value.status_code == 400
    assert "不支持" in str(error_info.value.detail)
