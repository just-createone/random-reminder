import sqlite3

from backend.database.db import get_connection
from backend.domain.notification import Notification


class NotificationRepository:
    """
    负责 notifications 表的数据读写。
    """


    def create(
        self,
        schedule_id: int,
    ) -> Notification:
        """
        创建一条待发送通知。
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO notifications
                (
                    schedule_id
                )
                VALUES
                (?)
                """,
                (
                    schedule_id,
                ),
            )

            notification_id = cursor.lastrowid

            connection.commit()

        finally:
            connection.close()


        if notification_id is None:
            raise RuntimeError(
                "创建通知失败"
            )


        notification = self.get_by_id(
            notification_id
        )


        if notification is None:
            raise RuntimeError(
                "创建通知后无法读取"
            )


        return notification



    def get_by_id(
        self,
        notification_id: int,
    ) -> Notification | None:
        """
        根据 ID 查询通知。
        """

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
                (
                    notification_id,
                ),
            )

            row = cursor.fetchone()


            if row is None:
                return None


            return Notification(
                id=row["id"],
                schedule_id=row["schedule_id"],
                status=row["status"],
                sent_at=row["sent_at"],
                created_at=row["created_at"],
            )

        finally:
            connection.close()