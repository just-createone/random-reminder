from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.notification.notification_service import (
    NotificationService,
)


router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)

notification_service = NotificationService()


class NotificationTestRequest(BaseModel):
    """测试系统通知的请求数据。"""

    title: str = Field(
        default="随机提醒器",
        min_length=1,
        max_length=100,
        description="通知标题",
        examples=["随机提醒器"],
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="通知正文",
        examples=["现在停下来，检查一下你正在做什么。"],
    )


@router.post("/test")
def test_notification(
    request: NotificationTestRequest,
) -> dict:
    """发送一条测试通知。"""

    try:
        notification_service.send(
            title=request.title,
            message=request.message,
        )

        return {
            "success": True,
            "data": None,
            "message": "测试通知发送成功",
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error