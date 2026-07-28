from fastapi import APIRouter, HTTPException, Query, status
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


class NotificationHistoryResponse(BaseModel):
    """通知历史接口的响应数据。"""

    notification_id: int
    schedule_id: int
    content: str
    schedule_date: str
    scheduled_time: str
    notification_status: str
    schedule_status: str
    sent_at: str | None
    created_at: str


@router.post("/test")
def test_notification(
    request: NotificationTestRequest,
) -> dict[str, object]:
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


@router.get(
    "/history",
    response_model=list[NotificationHistoryResponse],
)
def get_notification_history(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
) -> list[NotificationHistoryResponse]:
    """查询最近的通知历史。"""

    items = notification_service.get_recent_history(
        limit=limit,
    )

    return [
        NotificationHistoryResponse(
            notification_id=item.notification_id,
            schedule_id=item.schedule_id,
            content=item.content,
            schedule_date=item.schedule_date,
            scheduled_time=item.scheduled_time,
            notification_status=item.notification_status,
            schedule_status=item.schedule_status,
            sent_at=item.sent_at,
            created_at=item.created_at,
        )
        for item in items
    ]