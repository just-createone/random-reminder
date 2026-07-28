import json

from pywebpush import (
    WebPushException,
    webpush,
)

from backend.config import (
    VAPID_SUBJECT,
    get_vapid_private_key_path,
    logger,
)
from backend.domain.web_push import (
    WebPushSendResult,
)
from backend.repository.push_subscription_repository import (
    PushSubscriptionRepository,
)
from uuid import uuid4


class WebPushService:
    """负责向有效浏览器订阅发送 Web Push。"""

    def __init__(
        self,
        repository: PushSubscriptionRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            or PushSubscriptionRepository()
        )

    def send_to_all(
        self,
        title: str,
        body: str,
        url: str = "/",
    ) -> WebPushSendResult:
        """向所有有效订阅发送一条 Web Push。"""

        cleaned_title = title.strip()
        cleaned_body = body.strip()
        cleaned_url = url.strip()

        if not cleaned_title:
            raise ValueError(
                "推送标题不能为空"
            )

        if not cleaned_body:
            raise ValueError(
                "推送内容不能为空"
            )

        if not cleaned_url:
            cleaned_url = "/"

        if not cleaned_url.startswith("/"):
            raise ValueError(
                "推送跳转地址必须是站内路径"
            )

        private_key_path = (
            get_vapid_private_key_path()
        )

        subscriptions = (
            self.repository.get_active()
        )

        if not subscriptions:
            raise ValueError(
                "当前没有有效的后台推送订阅"
            )

        payload = json.dumps(
    {
        "title": cleaned_title,
        "body": cleaned_body,
        "url": cleaned_url,
        "tag": (
            "random-reminder-"
            f"{uuid4().hex}"
        ),
    },
    ensure_ascii=False,
)

        sent_count = 0
        failed_count = 0
        deactivated_count = 0

        for subscription in subscriptions:
            try:
                webpush(
    subscription_info={
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth,
        },
    },
    data=payload,
    vapid_private_key=private_key_path,
    vapid_claims={
        "sub": VAPID_SUBJECT,
    },
    ttl=3600,
    headers={
        "Urgency": "high",
    },
)

                sent_count += 1

                logger.info(
                    "Web Push sent successfully: "
                    "subscription_id=%s",
                    subscription.id,
                )

            except WebPushException as error:
                failed_count += 1

                status_code = (
                    error.response.status_code
                    if error.response is not None
                    else None
                )

                logger.exception(
                    "Web Push failed: "
                    "subscription_id=%s, "
                    "status_code=%s",
                    subscription.id,
                    status_code,
                )

                if status_code in (404, 410):
                    deactivated = (
                        self.repository.deactivate(
                            endpoint=(
                                subscription.endpoint
                            ),
                        )
                    )

                    if deactivated:
                        deactivated_count += 1

                        logger.info(
                            "Expired push subscription "
                            "deactivated: "
                            "subscription_id=%s",
                            subscription.id,
                        )

            except Exception:
                failed_count += 1

                logger.exception(
                    "Unexpected Web Push failure: "
                    "subscription_id=%s",
                    subscription.id,
                )

        return WebPushSendResult(
            total=len(subscriptions),
            sent=sent_count,
            failed=failed_count,
            deactivated=deactivated_count,
        )