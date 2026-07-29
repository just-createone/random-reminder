from datetime import datetime
from pathlib import Path

from backend.database import db
from backend.database.db import get_connection
from backend.database.init_db import init_database
from backend.services.schedule_service import (
    ScheduleService,
)


TEST_DATE = "2099-01-01"


class FixedScheduleStrategy:
    """返回固定时间，避免随机结果影响测试。"""

    def __init__(self) -> None:
        self.requested_count: (
            int | None
        ) = None

        self.excluded_times: (
            set[str] | None
        ) = None

    def generate_times(
        self,
        start_time: str,
        end_time: str,
        times_per_day: int,
        minimum_interval: int,
        excluded_times: (
            set[str] | None
        ) = None,
    ) -> list[str]:
        self.requested_count = (
            times_per_day
        )

        self.excluded_times = (
            excluded_times
        )

        assert times_per_day == 2

        return [
            "12:00",
            "13:00",
        ]


def test_regeneration_preserves_sent_history(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """已发送一条时，只重新生成剩余两条。"""

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

        cursor.execute(
            """
            UPDATE settings
            SET
                enabled = 1,
                all_day = 0,
                start_time = '08:00',
                end_time = '22:00',
                times_per_day = 3,
                minimum_interval = 60
            WHERE id = 1
            """
        )

        cursor.executemany(
            """
            INSERT INTO reminders (
                content,
                enabled
            )
            VALUES (?, 1)
            """,
            [
                ("提醒内容一",),
                ("提醒内容二",),
                ("提醒内容三",),
            ],
        )

        reminder_ids = [
            row["id"]
            for row in cursor.execute(
                """
                SELECT id
                FROM reminders
                ORDER BY id
                """
            ).fetchall()
        ]

        cursor.execute(
            """
            INSERT INTO daily_schedules (
                schedule_date,
                scheduled_time,
                reminder_id,
                content_snapshot,
                status
            )
            VALUES (?, '09:00', ?, ?, 'sent')
            """,
            (
                TEST_DATE,
                reminder_ids[0],
                "已经发送的提醒",
            ),
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

        cursor.execute(
            """
            INSERT INTO daily_schedules (
                schedule_date,
                scheduled_time,
                reminder_id,
                content_snapshot,
                status
            )
            VALUES (?, '10:00', ?, ?, 'pending')
            """,
            (
                TEST_DATE,
                reminder_ids[1],
                "等待替换的提醒",
            ),
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

    strategy = FixedScheduleStrategy()

    service = ScheduleService(
        strategy=strategy,
    )

    schedules = service.generate_today_schedule(
        force=True,
        now=datetime(
            2099,
            1,
            1,
            8,
            0,
            0,
        ),
    )

    assert strategy.requested_count == 2
    assert strategy.excluded_times == {
    "09:00",
}
    assert len(schedules) == 3

    statuses = [
        schedule.status
        for schedule in schedules
    ]

    assert statuses.count("sent") == 1
    assert statuses.count("pending") == 2

    schedule_ids = [
        schedule.id
        for schedule in schedules
    ]

    assert sent_schedule_id in schedule_ids
    assert pending_schedule_id not in schedule_ids

    connection = get_connection()

    try:
        notification_rows = connection.execute(
            """
            SELECT
                notifications.status,
                notifications.schedule_id
            FROM notifications
            INNER JOIN daily_schedules
                ON daily_schedules.id =
                   notifications.schedule_id
            WHERE daily_schedules.schedule_date = ?
            ORDER BY notifications.id
            """,
            (TEST_DATE,),
        ).fetchall()

        notification_statuses = [
            row["status"]
            for row in notification_rows
        ]

        assert notification_statuses.count(
            "sent"
        ) == 1

        assert notification_statuses.count(
            "pending"
        ) == 2

    finally:
        connection.close()