import sqlite3

from backend.database.db import get_connection
from backend.domain.settings import Settings


class SettingsRepository:
    """负责 settings 表的数据读写。"""

    SETTINGS_ID = 1

    def get(self) -> Settings:
        """读取全局设置。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    enabled,
                    all_day,
                    start_time,
                    end_time,
                    times_per_day,
                    minimum_interval,
                    created_at,
                    updated_at
                FROM settings
                WHERE id = ?
                """,
                (self.SETTINGS_ID,),
            )

            row = cursor.fetchone()

            if row is None:
                raise RuntimeError("系统设置不存在")

            return self._row_to_settings(row)

        finally:
            connection.close()

    def update(
        self,
        enabled: bool,
        all_day: bool,
        start_time: str | None,
        end_time: str | None,
        times_per_day: int,
        minimum_interval: int,
    ) -> Settings:
        """更新全局设置。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE settings
                SET enabled = ?,
                    all_day = ?,
                    start_time = ?,
                    end_time = ?,
                    times_per_day = ?,
                    minimum_interval = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    int(enabled),
                    int(all_day),
                    start_time,
                    end_time,
                    times_per_day,
                    minimum_interval,
                    self.SETTINGS_ID,
                ),
            )

            connection.commit()

        finally:
            connection.close()

        return self.get()

    @staticmethod
    def _row_to_settings(
        row: sqlite3.Row,
    ) -> Settings:
        """将数据库记录转换为 Settings 对象。"""

        return Settings(
            id=row["id"],
            enabled=bool(row["enabled"]),
            all_day=bool(row["all_day"]),
            start_time=row["start_time"],
            end_time=row["end_time"],
            times_per_day=row["times_per_day"],
            minimum_interval=row["minimum_interval"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )