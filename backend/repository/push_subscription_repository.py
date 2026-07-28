import sqlite3

from backend.database.db import get_connection
from backend.domain.push_subscription import (
    PushSubscription,
)


class PushSubscriptionRepository:
    """负责浏览器推送订阅的数据读写。"""

    def save(
        self,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str | None = None,
    ) -> PushSubscription:
        """新增订阅，或更新已经存在的订阅。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO push_subscriptions (
                    endpoint,
                    p256dh,
                    auth,
                    user_agent
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(endpoint)
                DO UPDATE SET
                    p256dh = excluded.p256dh,
                    auth = excluded.auth,
                    user_agent = excluded.user_agent,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    endpoint,
                    p256dh,
                    auth,
                    user_agent,
                ),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

        subscription = self.get_by_endpoint(
            endpoint
        )

        if subscription is None:
            raise RuntimeError(
                "保存推送订阅后无法读取记录"
            )

        return subscription

    def get_by_endpoint(
        self,
        endpoint: str,
    ) -> PushSubscription | None:
        """根据推送地址查询订阅。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    endpoint,
                    p256dh,
                    auth,
                    user_agent,
                    is_active,
                    created_at,
                    updated_at
                FROM push_subscriptions
                WHERE endpoint = ?
                """,
                (endpoint,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_subscription(
                row
            )

        finally:
            connection.close()

    def get_active(
        self,
    ) -> list[PushSubscription]:
        """查询所有有效订阅。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    endpoint,
                    p256dh,
                    auth,
                    user_agent,
                    is_active,
                    created_at,
                    updated_at
                FROM push_subscriptions
                WHERE is_active = 1
                ORDER BY id ASC
                """
            )

            rows = cursor.fetchall()

            return [
                self._row_to_subscription(row)
                for row in rows
            ]

        finally:
            connection.close()

    def deactivate(
        self,
        endpoint: str,
    ) -> bool:
        """将一个订阅标记为已停用。"""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE push_subscriptions
                SET
                    is_active = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE endpoint = ?
                  AND is_active = 1
                """,
                (endpoint,),
            )

            changed = cursor.rowcount == 1

            connection.commit()

            return changed

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def _row_to_subscription(
        row: sqlite3.Row,
    ) -> PushSubscription:
        """把数据库记录转换为领域对象。"""

        return PushSubscription(
            id=row["id"],
            endpoint=row["endpoint"],
            p256dh=row["p256dh"],
            auth=row["auth"],
            user_agent=row["user_agent"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )