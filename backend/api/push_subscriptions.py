from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field

from backend.config import DEBUG
from backend.services.web_push_service import (
    WebPushService,
)

from backend.services.push_subscription_service import (
    PushSubscriptionService,
)


router = APIRouter(
    prefix="/api/push",
    tags=["Push"],
)

push_subscription_service = (
    PushSubscriptionService()
)
web_push_service = WebPushService()


class PushSubscriptionKeysRequest(BaseModel):
    """浏览器推送订阅的加密密钥。"""

    p256dh: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="浏览器生成的 p256dh 公钥",
    )

    auth: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="浏览器生成的 auth 密钥",
    )


class PushSubscriptionCreateRequest(BaseModel):
    """保存浏览器推送订阅的请求数据。"""

    endpoint: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="浏览器推送服务地址",
    )

    keys: PushSubscriptionKeysRequest


class PushSubscriptionDeleteRequest(BaseModel):
    """停用浏览器推送订阅的请求数据。"""

    endpoint: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="需要停用的推送服务地址",
    )


class PushSubscriptionResponse(BaseModel):
    """保存推送订阅后的响应数据。"""

    id: int
    endpoint: str
    is_active: bool
    created_at: str | None
    updated_at: str | None


class PushSubscriptionDeleteResponse(
    BaseModel
):
    """停用推送订阅后的响应数据。"""

    success: bool
    deactivated: bool
    message: str


class VapidPublicKeyResponse(BaseModel):
    """返回浏览器订阅需要的 VAPID 公钥。"""

    public_key: str

class WebPushTestRequest(BaseModel):
    """发送测试 Web Push 的请求数据。"""

    title: str = Field(
        default="随机提醒器",
        min_length=1,
        max_length=100,
        description="推送通知标题",
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="推送通知内容",
    )

    url: str = Field(
        default="/",
        min_length=1,
        max_length=500,
        description="点击通知后打开的站内地址",
    )


class WebPushTestResponse(BaseModel):
    """测试 Web Push 的发送结果。"""

    success: bool
    total: int
    sent: int
    failed: int
    deactivated: int
    message: str


@router.post(
    "/subscriptions",
    response_model=PushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_push_subscription(
    request: PushSubscriptionCreateRequest,
    user_agent: str | None = Header(
        default=None,
    ),
) -> PushSubscriptionResponse:
    """保存或更新浏览器推送订阅。"""

    try:
        subscription = (
            push_subscription_service.subscribe(
                endpoint=request.endpoint,
                p256dh=request.keys.p256dh,
                auth=request.keys.auth,
                user_agent=user_agent,
            )
        )

        if subscription.id is None:
            raise RuntimeError(
                "推送订阅缺少数据库 ID"
            )

        return PushSubscriptionResponse(
            id=subscription.id,
            endpoint=subscription.endpoint,
            is_active=subscription.is_active,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(error),
        ) from error


@router.delete(
    "/subscriptions",
    response_model=(
        PushSubscriptionDeleteResponse
    ),
)
def delete_push_subscription(
    request: PushSubscriptionDeleteRequest,
) -> PushSubscriptionDeleteResponse:
    """停用浏览器推送订阅。"""

    try:
        deactivated = (
            push_subscription_service
            .unsubscribe(
                endpoint=request.endpoint,
            )
        )

        if deactivated:
            message = "推送订阅已停用"

        else:
            message = (
                "推送订阅不存在或已经停用"
            )

        return PushSubscriptionDeleteResponse(
            success=True,
            deactivated=deactivated,
            message=message,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error
    
@router.get(
    "/vapid-public-key",
    response_model=VapidPublicKeyResponse,
)
def get_vapid_public_key(
) -> VapidPublicKeyResponse:
    """读取浏览器订阅所需的公钥。"""

    try:
        public_key = (
            push_subscription_service
            .get_public_key()
        )

        return VapidPublicKeyResponse(
            public_key=public_key,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(error),
        ) from error
    

@router.post(
    "/test-send",
    response_model=WebPushTestResponse,
)
def send_test_web_push(
    request: WebPushTestRequest,
) -> WebPushTestResponse:
    """向所有有效订阅发送测试 Web Push。"""

    if not DEBUG:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="测试推送接口未开放",
        )

    try:
        result = web_push_service.send_to_all(
            title=request.title,
            body=request.message,
            url=request.url,
        )

        success = result.sent > 0

        message = (
            f"处理 {result.total} 个订阅，"
            f"成功 {result.sent} 个，"
            f"失败 {result.failed} 个。"
        )

        return WebPushTestResponse(
            success=success,
            total=result.total,
            sent=result.sent,
            failed=result.failed,
            deactivated=result.deactivated,
            message=message,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(error),
        ) from error