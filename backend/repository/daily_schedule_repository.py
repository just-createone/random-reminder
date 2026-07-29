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

    def delete_replaceable_by_date(
    self,
    schedule_date: str,
) -> int:
        """
        删除指定日期中可以被重新生成的计划。

        pending 和 skipped 可以删除；
        sent 和 failed 需要作为执行历史保留。
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM daily_schedules
                WHERE schedule_date = ?
                AND status IN (
                    'pending',
                    'skipped'
                )
                """,
                (schedule_date,),
            )

            deleted_count = cursor.rowcount

            connection.commit()

            return deleted_count

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def skip_overdue_pending(
    self,
    cutoff_datetime: str,
) -> int:
        """
        跳过截止时间以前仍未执行的计划。

        同时删除这些计划对应的 pending 通知任务，
        但保留 daily_schedules 记录用于展示 skipped 状态。
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id
                FROM daily_schedules
                WHERE status = 'pending'
                AND datetime(
                        schedule_date
                        || ' '
                        || scheduled_time
                    ) < datetime(?)
                """,
                (cutoff_datetime,),
            )

            schedule_ids = [
                row["id"]
                for row in cursor.fetchall()
            ]

            if not schedule_ids:
                return 0

            placeholders = ",".join(
                "?"
                for _ in schedule_ids
            )

            cursor.execute(
                f"""
                UPDATE daily_schedules
                SET status = 'skipped'
                WHERE id IN ({placeholders})
                AND status = 'pending'
                """,
                schedule_ids,
            )

            skipped_count = cursor.rowcount

            cursor.execute(
                f"""
                DELETE FROM notifications
                WHERE schedule_id IN ({placeholders})
                AND status = 'pending'
                """,
                schedule_ids,
            )

            connection.commit()

            return skipped_count

        except Exception:
            connection.rollback()
            raise

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


    def update_status(
            
            self,
            schedule_id: int,
            status: str,
        ) -> bool:
            """修改一条提醒计划的执行状态。"""

            connection = get_connection()

            try:
                cursor = connection.cursor()

                cursor.execute(
                    """
                    UPDATE daily_schedules
                    SET status = ?
                    WHERE id = ?
                    """,
                    (  
                        status,
                        schedule_id,
                    ),
                )

                updated_count = cursor.rowcount

                connection.commit()

                return updated_count > 0

            finally:
                connection.close()

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