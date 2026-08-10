from collections.abc import Sequence

from backend.database.db import get_connection


class DataTransferRepository:
    """Read and write portable user data."""

    def get_export_data(
        self,
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        """Return only the reminder and settings fields safe to export."""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            reminder_rows = cursor.execute(
                """
                SELECT content, enabled
                FROM reminders
                ORDER BY id DESC
                """
            ).fetchall()

            settings_row = cursor.execute(
                """
                SELECT
                    enabled,
                    all_day,
                    start_time,
                    end_time,
                    times_per_day,
                    minimum_interval
                FROM settings
                WHERE id = 1
                """
            ).fetchone()

            if settings_row is None:
                raise RuntimeError("系统设置不存在")

            reminders = [
                {
                    "content": row["content"],
                    "enabled": bool(row["enabled"]),
                }
                for row in reminder_rows
            ]

            settings = {
                "enabled": bool(settings_row["enabled"]),
                "all_day": bool(settings_row["all_day"]),
                "start_time": settings_row["start_time"],
                "end_time": settings_row["end_time"],
                "times_per_day": settings_row["times_per_day"],
                "minimum_interval": settings_row[
                    "minimum_interval"
                ],
            }

            return reminders, settings

        finally:
            connection.close()

    def import_data(
        self,
        reminders: Sequence[tuple[str, bool]],
        settings: dict[str, object],
    ) -> int:
        """Append reminders and restore settings in one transaction."""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.executemany(
                """
                INSERT INTO reminders (content, enabled)
                VALUES (?, ?)
                """,
                [
                    (content, int(enabled))
                    for content, enabled in reminders
                ],
            )

            cursor.execute(
                """
                UPDATE settings
                SET
                    enabled = ?,
                    all_day = ?,
                    start_time = ?,
                    end_time = ?,
                    times_per_day = ?,
                    minimum_interval = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                """,
                (
                    int(settings["enabled"]),
                    int(settings["all_day"]),
                    settings["start_time"],
                    settings["end_time"],
                    settings["times_per_day"],
                    settings["minimum_interval"],
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError("系统设置不存在")

            connection.commit()

            return len(reminders)

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()
