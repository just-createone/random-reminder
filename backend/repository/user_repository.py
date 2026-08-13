import sqlite3

from backend.database.db import get_connection
from backend.domain.user import User


class UserRepository:
    """Persist registered users and their password hashes."""

    def create(
        self,
        email: str,
        password_hash: str,
        time_zone: str,
    ) -> User:
        connection = get_connection()

        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, time_zone)
                VALUES (?, ?, ?)
                """,
                (email, password_hash, time_zone),
            )
            user_id = cursor.lastrowid
            connection.commit()
        finally:
            connection.close()

        if user_id is None:
            raise RuntimeError("User creation did not return an ID")

        user = self.get_by_id(user_id)

        if user is None:
            raise RuntimeError("Created user could not be read")

        return user

    def get_by_email_with_password_hash(
        self,
        email: str,
    ) -> tuple[User, str] | None:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    email,
                    time_zone,
                    password_hash,
                    created_at,
                    updated_at
                FROM users
                WHERE email = ?
                """,
                (email,),
            ).fetchone()
        finally:
            connection.close()

        if row is None:
            return None

        return self._row_to_user(row), row["password_hash"]

    def get_by_id(self, user_id: int) -> User | None:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT id, email, time_zone, created_at, updated_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        finally:
            connection.close()

        if row is None:
            return None

        return self._row_to_user(row)

    def get_enabled_users(self) -> list[User]:
        """Return users whose own reminder switch is enabled."""
        connection = get_connection()
        try:
            rows = connection.execute(
                """
                SELECT users.id, users.email, users.time_zone,
                       users.created_at, users.updated_at
                FROM users
                INNER JOIN settings ON settings.user_id = users.id
                WHERE settings.enabled = 1
                ORDER BY users.id ASC
                """
            ).fetchall()
        finally:
            connection.close()
        return [self._row_to_user(row) for row in rows]

    def provision_user_data(self, user_id: int) -> None:
        """Give a new user settings and claim legacy single-user data once."""
        connection = get_connection()

        try:
            cursor = connection.cursor()
            user_count = cursor.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            if user_count == 1:
                cursor.execute(
                    """
                    UPDATE reminders
                    SET user_id = ?
                    WHERE user_id IS NULL
                    """,
                    (user_id,),
                )
                cursor.execute(
                    """
                    UPDATE settings
                    SET user_id = ?
                    WHERE user_id IS NULL
                    """,
                    (user_id,),
                )

            cursor.execute(
                """
                INSERT OR IGNORE INTO settings (user_id)
                VALUES (?)
                """,
                (user_id,),
            )
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> User:
        return User(
            id=row["id"],
            email=row["email"],
            time_zone=row["time_zone"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
