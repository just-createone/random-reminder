from backend.config import logger
from backend.database.db import get_connection


def init_database() -> None:
    """初始化项目所需的数据表。"""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                time_zone TEXT NOT NULL DEFAULT 'Asia/Shanghai',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)

        user_columns = {
            row["name"]
            for row in cursor.execute("PRAGMA table_info(users)")
        }

        if "time_zone" not in user_columns:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN time_zone TEXT NOT NULL
                    DEFAULT 'Asia/Shanghai'
                """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_token_hash TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id
            ON user_sessions(user_id)
            """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                user_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)

        reminder_columns = {
            row["name"]
            for row in cursor.execute("PRAGMA table_info(reminders)")
        }

        if "user_id" not in reminder_columns:
            cursor.execute("ALTER TABLE reminders ADD COLUMN user_id INTEGER")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_user_id
            ON reminders(user_id)
            """)

        _initialize_settings_table(cursor)
        connection.commit()
        _initialize_schedule_tables(connection)
        cursor = connection.cursor()
        cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS push_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        endpoint TEXT NOT NULL UNIQUE,

        p256dh TEXT NOT NULL,

        auth TEXT NOT NULL,

        user_agent TEXT,

        is_active INTEGER NOT NULL DEFAULT 1
            CHECK (is_active IN (0, 1)),

        created_at TEXT NOT NULL
            DEFAULT CURRENT_TIMESTAMP,

        updated_at TEXT NOT NULL
            DEFAULT CURRENT_TIMESTAMP
    )
    """
)

        push_columns = {
            row["name"]
            for row in cursor.execute("PRAGMA table_info(push_subscriptions)")
        }
        if "user_id" not in push_columns:
            cursor.execute(
                "ALTER TABLE push_subscriptions ADD COLUMN user_id INTEGER"
            )
            _claim_legacy_push_data(cursor)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id "
            "ON push_subscriptions(user_id)"
        )

        connection.commit()

        logger.info("Database initialized successfully")

    finally:
        connection.close()


def _initialize_schedule_tables(connection) -> None:
    """Create user-owned schedules, rebuilding the legacy global uniqueness once."""
    cursor = connection.cursor()
    schedules_exists = cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'daily_schedules'"
    ).fetchone()

    if schedules_exists is not None:
        schedule_columns = {
            row["name"] for row in cursor.execute("PRAGMA table_info(daily_schedules)")
        }
        if "user_id" not in schedule_columns:
            connection.execute("PRAGMA foreign_keys = OFF")
            try:
                cursor.execute("ALTER TABLE notifications RENAME TO notifications_legacy")
                cursor.execute("ALTER TABLE daily_schedules RENAME TO daily_schedules_legacy")
                _create_schedule_tables(cursor)
                cursor.execute(
                    """
                    INSERT INTO daily_schedules (
                        id, user_id, schedule_date, scheduled_time, reminder_id,
                        content_snapshot, status, created_at
                    )
                    SELECT id, NULL, schedule_date, scheduled_time, reminder_id,
                           content_snapshot, status, created_at
                    FROM daily_schedules_legacy
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO notifications (id, schedule_id, status, sent_at, created_at)
                    SELECT id, schedule_id, status, sent_at, created_at
                    FROM notifications_legacy
                    """
                )
                cursor.execute("DROP TABLE notifications_legacy")
                cursor.execute("DROP TABLE daily_schedules_legacy")
                _claim_legacy_schedule_data(cursor)
                connection.commit()
            finally:
                connection.execute("PRAGMA foreign_keys = ON")
        return

    _create_schedule_tables(cursor)


def _create_schedule_tables(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE daily_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            schedule_date TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            reminder_id INTEGER,
            content_snapshot TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, schedule_date, scheduled_time),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'sent', 'failed')),
            sent_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (schedule_id) REFERENCES daily_schedules(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX idx_daily_schedules_owner_time
        ON daily_schedules(
            COALESCE(user_id, -1),
            schedule_date,
            scheduled_time
        )
        """
    )


def _claim_legacy_schedule_data(cursor) -> None:
    """Keep an old single-user installation usable after the ownership migration."""
    row = cursor.execute("SELECT id FROM users ORDER BY id LIMIT 2").fetchall()
    if len(row) == 1:
        cursor.execute(
            "UPDATE daily_schedules SET user_id = ? WHERE user_id IS NULL",
            (row[0]["id"],),
        )


def _claim_legacy_push_data(cursor) -> None:
    row = cursor.execute("SELECT id FROM users ORDER BY id LIMIT 2").fetchall()
    if len(row) == 1:
        cursor.execute(
            "UPDATE push_subscriptions SET user_id = ? WHERE user_id IS NULL",
            (row[0]["id"],),
        )


def _initialize_settings_table(cursor) -> None:
    """Create per-user settings and migrate the legacy global row once."""
    settings_exists = cursor.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = 'settings'
        """
    ).fetchone()

    if settings_exists is None:
        _create_settings_table(cursor)
        cursor.execute("""
            INSERT INTO settings (user_id)
            VALUES (NULL)
            """)
        return

    settings_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(settings)")
    }

    if "user_id" in settings_columns:
        return

    cursor.execute("ALTER TABLE settings RENAME TO settings_legacy")
    _create_settings_table(cursor)
    cursor.execute("""
        INSERT INTO settings (
            user_id,
            enabled,
            all_day,
            start_time,
            end_time,
            times_per_day,
            minimum_interval,
            created_at,
            updated_at
        )
        SELECT
            NULL,
            enabled,
            all_day,
            start_time,
            end_time,
            times_per_day,
            minimum_interval,
            created_at,
            updated_at
        FROM settings_legacy
        WHERE id = 1
        """)
    cursor.execute("DROP TABLE settings_legacy")


def _create_settings_table(cursor) -> None:
    cursor.execute("""
        CREATE TABLE settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            enabled INTEGER NOT NULL DEFAULT 0,
            all_day INTEGER NOT NULL DEFAULT 1,
            start_time TEXT,
            end_time TEXT,
            times_per_day INTEGER NOT NULL DEFAULT 3,
            minimum_interval INTEGER NOT NULL DEFAULT 60,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
        """)
