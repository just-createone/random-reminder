import hashlib
import time

from backend.database.db import get_connection


class AuthRateLimitService:
    window_seconds = 900

    def allow(self, scope: str, value: str, limit: int) -> bool:
        key = hashlib.sha256(value.encode()).hexdigest()
        now = int(time.time())
        connection = get_connection()
        try:
            row = connection.execute(
                "SELECT window_started_at, attempt_count FROM auth_rate_limits WHERE scope = ? AND rate_key = ?",
                (scope, key),
            ).fetchone()
            if row is None or now - row["window_started_at"] >= self.window_seconds:
                connection.execute(
                    "INSERT INTO auth_rate_limits VALUES (?, ?, ?, 1) ON CONFLICT(scope, rate_key) DO UPDATE SET window_started_at = excluded.window_started_at, attempt_count = 1",
                    (scope, key, now),
                )
                connection.commit()
                return True
            if row["attempt_count"] >= limit:
                return False
            connection.execute(
                "UPDATE auth_rate_limits SET attempt_count = attempt_count + 1 WHERE scope = ? AND rate_key = ?",
                (scope, key),
            )
            connection.commit()
            return True
        finally:
            connection.close()
