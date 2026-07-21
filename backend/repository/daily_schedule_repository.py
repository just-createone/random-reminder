import sqlite3

from backend.database.db import get_connection
from backend.domain.daily_schedule import DailySchedule


class DailyScheduleRepository:
    """负责 daily_schedules 表的数据读写。"""

    def get_by_date(
        self,
        schedule_date: str,
    ) -> list[DailySchedule]:
        """查询指定日期的全部提醒计划。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    schedule_date,
                    scheduled_time,
                    reminder_id,
                    content_snapshot,
                    status,
                    created_at
                FROM daily_schedules
                WHERE schedule_date = ?
                ORDER BY scheduled_time ASC
                """,
                (schedule_date,),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_schedule(row)
                for row in rows
            ]

        finally:
            connection.close()

    def delete_by_date(
        self,
        schedule_date: str,
    ) -> None:
        """删除指定日期的全部计划。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM daily_schedules
                WHERE schedule_date = ?
                """,
                (schedule_date,),
            )

            connection.commit()

        finally:
            connection.close()

    def create_many(
        self,
        schedule_date: str,
        items: list[tuple[str, int, str]],
    ) -> list[DailySchedule]:
        """批量创建某一天的提醒计划。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.executemany(
                """
                INSERT INTO daily_schedules (
                    schedule_date,
                    scheduled_time,
                    reminder_id,
                    content_snapshot
                )
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        schedule_date,
                        scheduled_time,
                        reminder_id,
                        content,
                    )
                    for scheduled_time, reminder_id, content
                    in items
                ],
            )

            connection.commit()

        finally:
            connection.close()

        return self.get_by_date(schedule_date)

    @staticmethod
    def _row_to_schedule(
        row: sqlite3.Row,
    ) -> DailySchedule:
        """将数据库记录转换为 DailySchedule 对象。"""

        return DailySchedule(
            id=row["id"],
            schedule_date=row["schedule_date"],
            scheduled_time=row["scheduled_time"],
            reminder_id=row["reminder_id"],
            content=row["content_snapshot"],
            status=row["status"],
            created_at=row["created_at"],
        )