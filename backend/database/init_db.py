from backend.config import logger
from backend.database.db import get_connection


def init_database() -> None:
    """初始化项目所需的数据表。"""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER NOT NULL DEFAULT 0,
                all_day INTEGER NOT NULL DEFAULT 1,
                start_time TEXT,
                end_time TEXT,
                times_per_day INTEGER NOT NULL DEFAULT 3,
                minimum_interval INTEGER NOT NULL DEFAULT 60,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)

        cursor.execute("""
            INSERT OR IGNORE INTO settings (
                id,
                enabled,
                all_day,
                start_time,
                end_time,
                times_per_day,
                minimum_interval
            )
            VALUES (
                1,
                0,
                1,
                NULL,
                NULL,
                3,
                60
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_date TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                reminder_id INTEGER,
                content_snapshot TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(schedule_date, scheduled_time)
            )
            """)
        cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id INTEGER NOT NULL UNIQUE,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending', 'sent', 'failed')),
        sent_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (schedule_id)
            REFERENCES daily_schedules(id)
            ON DELETE CASCADE
    )
    """
)

        connection.commit()

        logger.info("Database initialized successfully")

    finally:
        connection.close()
