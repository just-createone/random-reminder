from pathlib import Path

import sqlite3
import pytest

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

def test_atomic_replacement_rolls_back_on_insert_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """新计划插入失败时，旧计划必须恢复。"""

    database_path = (
        tmp_path
        / "test_atomic_replacement.db"
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

        # 保留的历史计划。
        cursor.execute(
            """
            INSERT INTO daily_schedules (
                schedule_date,
                scheduled_time,
                reminder_id,
                content_snapshot,
                status
            )
            VALUES (
                '2099-01-02',
                '09:00',
                NULL,
                '已发送提醒',
                'sent'
            )
            """
        )

        sent_schedule_id = cursor.lastrowid

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
            (sent_schedule_id,),
        )

        # 本应被替换的等待计划。
        cursor.execute(
            """
            INSERT INTO daily_schedules (
                schedule_date,
                scheduled_time,
                reminder_id,
                content_snapshot,
                status
            )
            VALUES (
                '2099-01-02',
                '10:00',
                NULL,
                '原等待提醒',
                'pending'
            )
            """
        )

        pending_schedule_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO notifications (
                schedule_id,
                status
            )
            VALUES (?, 'pending')
            """,
            (pending_schedule_id,),
        )

        connection.commit()

    finally:
        connection.close()

    repository = DailyScheduleRepository()

    # 新计划使用 09:00，与保留的 sent 计划冲突。
    # 插入必须失败，并且之前删除的 pending 要被恢复。
    with pytest.raises(
        sqlite3.IntegrityError
    ):
        repository.replace_replaceable_by_date(
            schedule_date="2099-01-02",
            items=[
                (
                    "09:00",
                    1,
                    "发生时间冲突的新提醒",
                ),
            ],
        )

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                scheduled_time,
                status
            FROM daily_schedules
            WHERE schedule_date = '2099-01-02'
            ORDER BY scheduled_time
            """
        ).fetchall()

        result = [
            (
                row["scheduled_time"],
                row["status"],
            )
            for row in rows
        ]

        assert result == [
            ("09:00", "sent"),
            ("10:00", "pending"),
        ]

        notification_count = (
            connection.execute(
                """
                SELECT COUNT(*)
                FROM notifications
                """
            ).fetchone()[0]
        )

        assert notification_count == 2

    finally:
        connection.close()