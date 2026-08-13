from datetime import datetime, timezone

from backend.database.db import get_connection
from backend.domain.user import User


class SessionRepository:
    """Persist opaque, revocable application sessions."""

    def create(
        self,
        session_token_hash: str,
        user_id: int,
        expires_at: datetime,
    ) -> None:
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO user_sessions (
                    session_token_hash,
                    user_id,
                    expires_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    session_token_hash,
                    user_id,
                    expires_at.astimezone(timezone.utc).isoformat(),
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def get_user_by_token_hash(
        self,
        session_token_hash: str,
    ) -> User | None:
        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT
                    users.id,
                    users.email,
                    users.time_zone,
                    users.created_at,
                    users.updated_at
                FROM user_sessions
                JOIN users ON users.id = user_sessions.user_id
                WHERE user_sessions.session_token_hash = ?
                  AND user_sessions.expires_at > ?
                """,
                (
                    session_token_hash,
                    datetime.now(timezone.utc).isoformat(),
                ),
            ).fetchone()
        finally:
            connection.close()

        if row is None:
            return None

        return User(
            id=row["id"],
            email=row["email"],
            time_zone=row["time_zone"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def delete_by_token_hash(
        self,
        session_token_hash: str,
    ) -> None:
        connection = get_connection()

        try:
            connection.execute(
                """
                DELETE FROM user_sessions
                WHERE session_token_hash = ?
                """,
                (session_token_hash,),
            )
            connection.commit()
        finally:
            connection.close()
