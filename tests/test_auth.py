from http.cookies import SimpleCookie
import hashlib
from pathlib import Path
import sqlite3

import pytest
from fastapi import HTTPException, Response
from fastapi.testclient import TestClient

from backend.api.auth import (
    CredentialsRequest,
    get_current_user,
    logout,
    register,
    require_current_user,
)
from backend.database import db
from backend.database.init_db import init_database
from backend.main import app
from backend.services.auth_service import (
    AuthenticationError,
    AuthService,
    EmailAlreadyRegisteredError,
)


@pytest.fixture
def database_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    path = tmp_path / "test_random_reminder.db"
    monkeypatch.setattr(db, "get_db_path", lambda: str(path))
    init_database()
    return path


def test_registration_hashes_password_and_normalizes_email(
    database_path: Path,
) -> None:
    user = AuthService().register("  Test@Example.com ", "password-123")

    assert user.email == "test@example.com"

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT email, password_hash FROM users"
        ).fetchone()

    assert row is not None
    assert row[0] == "test@example.com"
    assert row[1] != "password-123"
    assert row[1].startswith("$argon2")


def test_registration_rejects_duplicate_email_and_short_password(
    database_path: Path,
) -> None:
    service = AuthService()
    service.register("test@example.com", "password-123")

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register("TEST@example.com", "password-456")

    with pytest.raises(ValueError, match="至少"):
        service.register("other@example.com", "short")


def test_login_accepts_correct_password_and_rejects_wrong_password(
    database_path: Path,
) -> None:
    service = AuthService()
    user = service.register("test@example.com", "password-123")

    assert service.login("TEST@example.com", "password-123") == user

    with pytest.raises(AuthenticationError):
        service.login("test@example.com", "wrong-password")


def test_session_is_opaque_and_can_be_revoked(
    database_path: Path,
) -> None:
    service = AuthService()
    user = service.register("test@example.com", "password-123")
    session_token = service.create_session(user.id, duration_days=14)

    assert service.get_user_for_session_token(session_token) == user

    with sqlite3.connect(database_path) as connection:
        stored_token = connection.execute(
            "SELECT session_token_hash FROM user_sessions"
        ).fetchone()[0]

    assert stored_token != session_token

    service.revoke_session(session_token)

    with pytest.raises(AuthenticationError):
        service.get_user_for_session_token(session_token)


def test_registration_api_sets_secure_session_cookie(
    database_path: Path,
) -> None:
    response = Response()
    result = register(
        CredentialsRequest(
            email="test@example.com",
            password="password-123",
        ),
        response,
    )
    cookie = SimpleCookie()
    cookie.load(response.headers["set-cookie"])
    session_token = cookie["random_reminder_session"].value

    assert result["success"] is True
    assert result["data"]["email"] == "test@example.com"
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=lax" in response.headers["set-cookie"].lower()
    assert get_current_user(session_token)["data"]["email"] == "test@example.com"

    logout_response = Response()
    logout(logout_response, session_token)

    with pytest.raises(HTTPException) as error_info:
        get_current_user(session_token)

    assert error_info.value.status_code == 401


def test_authentication_routes_are_in_openapi_schema() -> None:
    paths = set(app.openapi()["paths"])

    assert "/api/auth/register" in paths
    assert "/api/auth/login" in paths
    assert "/api/auth/logout" in paths
    assert "/api/auth/account" in paths
    assert "/api/auth/me" in paths


def test_protected_routes_require_the_current_user_dependency() -> None:
    paths = app.openapi()["paths"]

    for route_path in (
        "/api/reminders",
        "/api/settings",
        "/api/schedules/today",
        "/api/data/export",
    ):
        assert paths[route_path]

    with pytest.raises(HTTPException) as error_info:
        require_current_user(None)

    assert error_info.value.status_code == 401


def test_http_sessions_enforce_user_data_isolation(
    database_path: Path,
) -> None:
    """The running API must apply the same user boundary as the services."""
    with TestClient(app) as client_a, TestClient(app) as client_b:
        assert client_a.get("/api/reminders").status_code == 401

        assert client_a.post(
            "/api/auth/register",
            json={
                "email": "a@example.com",
                "password": "password-123",
                "time_zone": "America/New_York",
            },
        ).status_code == 201
        reminder_a = client_a.post(
            "/api/reminders",
            json={"content": "only account A"},
        ).json()["data"]
        client_a.put(
            "/api/settings",
            json={
                "enabled": True,
                "all_day": True,
                "start_time": None,
                "end_time": None,
                "times_per_day": 3,
                "minimum_interval": 60,
            },
        )

        assert client_b.post(
            "/api/auth/register",
            json={
                "email": "b@example.com",
                "password": "password-123",
                "time_zone": "Asia/Shanghai",
            },
        ).status_code == 201
        reminder_b = client_b.post(
            "/api/reminders",
            json={"content": "only account B"},
        ).json()["data"]

        assert client_a.get(f"/api/reminders/{reminder_b['id']}").status_code == 404
        assert client_b.get(f"/api/reminders/{reminder_a['id']}").status_code == 404
        assert [item["content"] for item in client_a.get("/api/reminders").json()["data"]] == ["only account A"]
        assert [item["content"] for item in client_b.get("/api/reminders").json()["data"]] == ["only account B"]
        assert client_a.get("/api/data/export").json()["data"]["settings"]["enabled"] is True
        assert client_b.get("/api/data/export").json()["data"]["settings"]["enabled"] is False


def test_login_rate_limit_returns_429(database_path: Path) -> None:
    with TestClient(app) as client:
        for _ in range(10):
            response = client.post(
                "/api/auth/login",
                json={"email": "missing@example.com", "password": "password-123"},
            )
            assert response.status_code == 401
        response = client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "password-123"},
        )
    assert response.status_code == 429


def test_registration_rate_limit_applies_to_the_client_address(database_path: Path) -> None:
    with TestClient(app) as client:
        for index in range(5):
            response = client.post(
                "/api/auth/register",
                json={"email": f"user-{index}@example.com", "password": "password-123"},
            )
            assert response.status_code == 201
        response = client.post(
            "/api/auth/register",
            json={"email": "blocked@example.com", "password": "password-123"},
        )
    assert response.status_code == 429


def test_account_deletion_removes_only_the_current_users_data(
    database_path: Path,
) -> None:
    with TestClient(app) as client_a, TestClient(app) as client_b:
        registered_a = client_a.post(
            "/api/auth/register",
            json={"email": "a@example.com", "password": "password-123"},
        )
        assert registered_a.status_code == 201
        user_id = registered_a.json()["data"]["id"]
        reminder = client_a.post(
            "/api/reminders",
            json={"content": "delete me"},
        )
        assert reminder.status_code == 201
        reminder_id = reminder.json()["data"]["id"]

        with sqlite3.connect(database_path) as connection:
            schedule_id = connection.execute(
                "INSERT INTO daily_schedules "
                "(user_id, schedule_date, scheduled_time, reminder_id, content_snapshot) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, "2026-08-22", "12:00", reminder_id, "delete me"),
            ).lastrowid
            connection.execute(
                "INSERT INTO notifications (schedule_id) VALUES (?)",
                (schedule_id,),
            )
            connection.execute(
                "INSERT INTO daily_schedule_clearances (user_id, schedule_date) "
                "VALUES (?, ?)",
                (user_id, "2026-08-22"),
            )
            connection.execute(
                "INSERT INTO push_subscriptions "
                "(user_id, endpoint, p256dh, auth) VALUES (?, ?, ?, ?)",
                (user_id, "https://example.invalid/a", "key", "auth"),
            )
            connection.commit()

        registered_b = client_b.post(
            "/api/auth/register",
            json={"email": "b@example.com", "password": "password-123"},
        )
        assert registered_b.status_code == 201

        deleted = client_a.delete("/api/auth/account")

        assert deleted.status_code == 200
        assert client_a.get("/api/auth/me").status_code == 401
        assert client_b.get("/api/auth/me").status_code == 200

    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM users WHERE id = ?", (user_id,)
        ).fetchone()[0] == 0
        for table in (
            "reminders",
            "settings",
            "user_sessions",
            "push_subscriptions",
            "daily_schedules",
            "daily_schedule_clearances",
        ):
            assert connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", (user_id,)
            ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM notifications WHERE schedule_id = ?",
            (schedule_id,),
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM auth_rate_limits WHERE rate_key = ?",
            (hashlib.sha256(b"a@example.com").hexdigest(),),
        ).fetchone()[0] == 0
