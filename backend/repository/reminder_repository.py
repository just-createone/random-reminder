import sqlite3

from backend.database.db import get_connection
from backend.domain.reminder import Reminder


class ReminderRepository:
    """负责 reminders 表的数据读写。"""

    def create(self, content: str) -> Reminder:
        """向数据库新增一条提醒。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO reminders (content)
                VALUES (?)
                """,
                (content,),
            )

            reminder_id = cursor.lastrowid
            connection.commit()

        finally:
            connection.close()

        if reminder_id is None:
            raise RuntimeError("创建提醒失败，数据库未返回提醒 ID")

        reminder = self.get_by_id(reminder_id)

        if reminder is None:
            raise RuntimeError("创建提醒后无法读取该提醒")

        return reminder

    def get_by_id(self, reminder_id: int) -> Reminder | None:
        """根据 ID 查询一条提醒。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, content, enabled, created_at, updated_at
                FROM reminders
                WHERE id = ?
                """,
                (reminder_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_reminder(row)

        finally:
            connection.close()

    def get_all(self) -> list[Reminder]:
        """查询全部提醒，最新创建的排在前面。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT id, content, enabled, created_at, updated_at
                FROM reminders
                ORDER BY id DESC
                """)

            rows = cursor.fetchall()

            return [self._row_to_reminder(row) for row in rows]

        finally:
            connection.close()

    def get_enabled(self) -> list[Reminder]:
        """查询全部已启用的提醒。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT id, content, enabled, created_at, updated_at
                FROM reminders
                WHERE enabled = 1
                ORDER BY id DESC
                """)

            rows = cursor.fetchall()

            return [self._row_to_reminder(row) for row in rows]

        finally:
            connection.close()

    def update_content(
        self,
        reminder_id: int,
        content: str,
    ) -> Reminder | None:
        """修改指定提醒的内容。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE reminders
                SET content = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (content, reminder_id),
            )

            updated_count = cursor.rowcount
            connection.commit()

        finally:
            connection.close()

        if updated_count == 0:
            return None

        return self.get_by_id(reminder_id)

    def update_enabled(
        self,
        reminder_id: int,
        enabled: bool,
    ) -> Reminder | None:
        """修改指定提醒的启用状态。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE reminders
                SET enabled = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (int(enabled), reminder_id),
            )

            updated_count = cursor.rowcount
            connection.commit()

        finally:
            connection.close()

        if updated_count == 0:
            return None

        return self.get_by_id(reminder_id)

    def delete(self, reminder_id: int) -> bool:
        """删除指定提醒。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM reminders
                WHERE id = ?
                """,
                (reminder_id,),
            )

            deleted_count = cursor.rowcount
            connection.commit()

            return deleted_count > 0

        finally:
            connection.close()

    @staticmethod
    def _row_to_reminder(
        row: sqlite3.Row,
    ) -> Reminder:
        """将数据库查询结果转换为 Reminder 对象。"""

        return Reminder(
            id=row["id"],
            content=row["content"],
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
