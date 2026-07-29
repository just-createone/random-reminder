from pathlib import Path

from backend.database import db
from backend.database.db import get_connection
from backend.database.init_db import init_database
from backend.repository.daily_schedule_repository import (
    DailyScheduleRepository,
)


TEST_DATE = "2099-01-01"


def test_delete_replaceable_preserves_history(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """重新生成时应保留 sent 和 failed 计划。"""

    database_path = (
        tmp_path
        / "test_random_reminder.db"
    )

    monkeypatch.setattr(
        db,
        "get_db_path",
        lambda: str(database_path),
    )

    init_database()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        test_rows = [
            (
                TEST_DATE,
                "08:00",
                "pending reminder",
                "pending",
            ),
            (
                TEST_DATE,
                "09:00",
                "skipped reminder",
                "skipped",
            ),
            (
                TEST_DATE,
                "10:00",
                "sent reminder",
                "sent",
            ),
            (
                TEST_DATE,
                "11:00",
                "failed reminder",
                "failed",
            ),
        ]

        cursor.executemany(
            """
            INSERT INTO daily_schedules (
                schedule_date,
                scheduled_time,
                reminder_id,
                content_snapshot,
                status
            )
            VALUES (?, ?, NULL, ?, ?)
            """,
            test_rows,
        )

        rows = cursor.execute(
            """
            SELECT id, status
            FROM daily_schedules
            WHERE schedule_date = ?
            ORDER BY scheduled_time
            """,
            (TEST_DATE,),
        ).fetchall()

        schedule_ids = {
            row["status"]: row["id"]
            for row in rows
        }

        cursor.execute(
            """
            INSERT INTO notifications (
                schedule_id,
                status
            )
            VALUES (?, 'pending')
            """,
            (
                schedule_ids["pending"],
            ),
        )

        cursor.execute(
            """
            INSERT INTO notifications (
                schedule_id,
                status,
                sent_at
            )
            VALUES (
                ?,
                'sent',
                CURRENT_TIMESTAMP
            )
            """,
            (
                schedule_ids["sent"],
            ),
        )

        cursor.execute(
            """
            INSERT INTO notifications (
                schedule_id,
                status
            )
            VALUES (?, 'failed')
            """,
            (
                schedule_ids["failed"],
            ),
        )

        connection.commit()

    finally:
        connection.close()

    repository = DailyScheduleRepository()

    deleted_count = (
        repository.delete_replaceable_by_date(
            TEST_DATE
        )
    )

    assert deleted_count == 2

    connection = get_connection()

    try:
        remaining_schedules = connection.execute(
            """
            SELECT status
            FROM daily_schedules
            WHERE schedule_date = ?
            ORDER BY scheduled_time
            """,
            (TEST_DATE,),
        ).fetchall()

        remaining_statuses = [
            row["status"]
            for row in remaining_schedules
        ]

        assert remaining_statuses == [
            "sent",
            "failed",
        ]

        remaining_notifications = (
            connection.execute(
                """
                SELECT status
                FROM notifications
                ORDER BY id
                """
            ).fetchall()
        )

        notification_statuses = [
            row["status"]
            for row in remaining_notifications
        ]

        assert notification_statuses == [
            "sent",
            "failed",
        ]

    finally:
        connection.close()