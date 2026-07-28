from datetime import datetime, timedelta
from pprint import pprint

from backend.database.db import get_connection
from backend.executor.schedule_executor import (
    ScheduleExecutor,
)


def prepare_due_notification() -> tuple[int, int]:
    """把一条 pending 计划调整为已经到期。"""

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                notifications.id
                    AS notification_id,
                notifications.schedule_id
            FROM notifications
            INNER JOIN daily_schedules
                ON daily_schedules.id =
                   notifications.schedule_id
            WHERE notifications.status = 'pending'
              AND daily_schedules.status = 'pending'
            ORDER BY notifications.id ASC
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "没有 pending 通知，"
                "请先重新生成今日计划"
            )

        now = datetime.now()

        schedule_date = (
            now.date().isoformat()
        )

        scheduled_time = (
            now - timedelta(minutes=1)
        ).strftime("%H:%M")

        connection.execute(
            """
            UPDATE daily_schedules
            SET
                schedule_date = ?,
                scheduled_time = ?,
                status = 'pending'
            WHERE id = ?
            """,
            (
                schedule_date,
                scheduled_time,
                row["schedule_id"],
            ),
        )

        connection.commit()

        return (
            row["notification_id"],
            row["schedule_id"],
        )

    finally:
        connection.close()


def print_result(
    notification_id: int,
) -> None:
    """打印通知执行结果。"""

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                notifications.id
                    AS notification_id,
                notifications.status
                    AS notification_status,
                notifications.sent_at,
                daily_schedules.id
                    AS schedule_id,
                daily_schedules.status
                    AS schedule_status,
                daily_schedules.content_snapshot
            FROM notifications
            INNER JOIN daily_schedules
                ON daily_schedules.id =
                   notifications.schedule_id
            WHERE notifications.id = ?
            """,
            (notification_id,),
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "没有找到测试通知记录"
            )

        pprint(dict(row))

    finally:
        connection.close()


def main() -> None:
    """测试执行器的 Web Push 发送链路。"""

    notification_id, schedule_id = (
        prepare_due_notification()
    )

    print(
        {
            "notification_id": notification_id,
            "schedule_id": schedule_id,
        }
    )

    executor = ScheduleExecutor()

    executor.run_once()

    print_result(
        notification_id
    )


if __name__ == "__main__":
    main()