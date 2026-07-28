import sqlite3

from backend.database.db import get_connection
from backend.domain.notification import (
    Notification,
    NotificationTask,
)


class NotificationRepository:
    """负责 notifications 表的数据读写。"""

    def create(
        self,
        schedule_id: int,
    ) -> Notification:
        """为一条计划创建待发送通知。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT OR IGNORE INTO notifications (
                    schedule_id
                )
                VALUES (?)
                """,
                (schedule_id,),
            )

            connection.commit()

        finally:
            connection.close()

        notification = self.get_by_schedule_id(
            schedule_id
        )

        if notification is None:
            raise RuntimeError(
                "创建通知后无法读取通知记录"
            )

        return notification

    def create_many_for_schedules(
        self,
        schedule_ids: list[int],
    ) -> list[Notification]:
        """为多条计划批量创建通知记录。"""

        if not schedule_ids:
            return []

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.executemany(
                """
                INSERT OR IGNORE INTO notifications (
                    schedule_id
                )
                VALUES (?)
                """,
                [
                    (schedule_id,)
                    for schedule_id in schedule_ids
                ],
            )

            connection.commit()

            placeholders = ",".join(
                "?"
                for _ in schedule_ids
            )

            cursor.execute(
                f"""
                SELECT
                    id,
                    schedule_id,
                    status,
                    sent_at,
                    created_at
                FROM notifications
                WHERE schedule_id IN ({placeholders})
                ORDER BY id ASC
                """,
                schedule_ids,
            )

            rows = cursor.fetchall()

            return [
                self._row_to_notification(row)
                for row in rows
            ]

        finally:
            connection.close()

    def get_by_id(
        self,
        notification_id: int,
    ) -> Notification | None:
        """根据通知 ID 查询通知。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    schedule_id,
                    status,
                    sent_at,
                    created_at
                FROM notifications
                WHERE id = ?
                """,
                (notification_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_notification(row)

        finally:
            connection.close()

    def get_by_schedule_id(
        self,
        schedule_id: int,
    ) -> Notification | None:
        """根据计划 ID 查询通知。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    schedule_id,
                    status,
                    sent_at,
                    created_at
                FROM notifications
                WHERE schedule_id = ?
                """,
                (schedule_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_notification(row)

        finally:
            connection.close()

    @staticmethod
    def _row_to_notification(
        row: sqlite3.Row,
    ) -> Notification:
        """把数据库记录转换成 Notification 对象。"""

        return Notification(
            id=row["id"],
            schedule_id=row["schedule_id"],
            status=row["status"],
            sent_at=row["sent_at"],
            created_at=row["created_at"],
        )
    
    def get_due_pending(
    self,
    schedule_date: str,
    current_time: str,
    ) -> list[NotificationTask]:
        """查询指定日期中已经到达执行时间的待发送通知。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    notifications.id AS notification_id,
                    daily_schedules.id AS schedule_id,
                    daily_schedules.content_snapshot,
                    daily_schedules.scheduled_time
                FROM notifications
                INNER JOIN daily_schedules
                    ON daily_schedules.id = notifications.schedule_id
                WHERE notifications.status = 'pending'
                AND daily_schedules.status = 'pending'
                AND daily_schedules.schedule_date = ?
                AND time(daily_schedules.scheduled_time) <= time(?)
                ORDER BY
                    daily_schedules.scheduled_time ASC,
                    notifications.id ASC
                """,
                (
                    schedule_date,
                    current_time,
                ),
            )

            rows = cursor.fetchall()

            return [
                NotificationTask(
                    notification_id=row["notification_id"],
                    schedule_id=row["schedule_id"],
                    content_snapshot=row["content_snapshot"],
                    scheduled_time=row["scheduled_time"],
                )
                for row in rows
            ]

        finally:
            connection.close()


    def mark_sent(
        self,
        notification_id: int,
        schedule_id: int,
    ) -> bool:
        """把通知和每日计划同时标记为已发送。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE notifications
                SET
                    status = 'sent',
                    sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
                AND status = 'pending'
                """,
                (notification_id,),
            )

            notification_updated = (
                cursor.rowcount == 1
            )

            if not notification_updated:
                connection.rollback()
                return False

            cursor.execute(
                """
                UPDATE daily_schedules
                SET status = 'sent'
                WHERE id = ?
                AND status = 'pending'
                """,
                (schedule_id,),
            )

            schedule_updated = (
                cursor.rowcount == 1
            )

            if not schedule_updated:
                connection.rollback()
                return False

            connection.commit()

            return True

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()


    def mark_failed(
        self,
        notification_id: int,
        schedule_id: int,
    ) -> None:
        """把通知和每日计划标记为发送失败。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE notifications
                SET status = 'failed'
                WHERE id = ?
                AND status = 'pending'
                """,
                (notification_id,),
            )

            cursor.execute(
                """
                UPDATE daily_schedules
                SET status = 'failed'
                WHERE id = ?
                AND status = 'pending'
                """,
                (schedule_id,),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()