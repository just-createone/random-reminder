import sqlite3

from backend.database.db import get_connection
from backend.domain.notification import Notification


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