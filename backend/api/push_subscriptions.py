from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field

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