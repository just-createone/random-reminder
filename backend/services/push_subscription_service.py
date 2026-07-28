from backend.domain.push_subscription import (
    PushSubscription,
)
from backend.repository.push_subscription_repository import (
    PushSubscriptionRepository,
)


class PushSubscriptionService:
    """负责浏览器推送订阅的业务逻辑。"""

    def __init__(
        self,
        repository: PushSubscriptionRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            or PushSubscriptionRepository()
        )

    def subscribe(
        self,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str | None = None,
    ) -> PushSubscription:
        """保存或更新一个浏览器推送订阅。"""

        cleaned_endpoint = endpoint.strip()
        cleaned_p256dh = p256dh.strip()
        cleaned_auth = auth.strip()

        if not cleaned_endpoint:
            raise ValueError(
                "推送订阅地址不能为空"
            )

        if not cleaned_endpoint.startswith(
            "https://"
        ):
            raise ValueError(
                "推送订阅地址必须使用 HTTPS"
            )

        if not cleaned_p256dh:
            raise ValueError(
                "推送订阅缺少 p256dh 密钥"
            )

        if not cleaned_auth:
            raise ValueError(
                "推送订阅缺少 auth 密钥"
            )

        cleaned_user_agent = (
            user_agent.strip()
            if user_agent
            else None
        )

        return self.repository.save(
            endpoint=cleaned_endpoint,
            p256dh=cleaned_p256dh,
            auth=cleaned_auth,
            user_agent=cleaned_user_agent,
        )

    def unsubscribe(
        self,
        endpoint: str,
    ) -> bool:
        """停用一个浏览器推送订阅。"""

        cleaned_endpoint = endpoint.strip()

        if not cleaned_endpoint:
            raise ValueError(
                "推送订阅地址不能为空"
            )

        return self.repository.deactivate(
            endpoint=cleaned_endpoint,
        )