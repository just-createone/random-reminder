from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.core.exceptions import ResourceNotFoundError
from backend.services.reminder_service import ReminderService


router = APIRouter(
    prefix="/api/reminders",
    tags=["Reminders"],
)

reminder_service = ReminderService()


class ReminderCreateRequest(BaseModel):
    """创建提醒的请求数据。"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="提醒内容",
        examples=["不要刷短视频"],
    )


class ReminderUpdateRequest(BaseModel):
    """修改提醒内容的请求数据。"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="新的提醒内容",
        examples=["今天学习 Python 60 分钟"],
    )


class ReminderEnabledRequest(BaseModel):
    """修改提醒启用状态的请求数据。"""

    enabled: bool = Field(
        ...,
        description="是否启用提醒",
        examples=[True],
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_reminder(
    request: ReminderCreateRequest,
) -> dict:
    """新增一条提醒。"""

    try:
        reminder = reminder_service.create_reminder(
            request.content
        )

        return {
            "success": True,
            "data": asdict(reminder),
            "message": "提醒创建成功",
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get("")
def get_reminders() -> dict:
    """查询全部提醒。"""

    reminders = reminder_service.get_all_reminders()

    return {
        "success": True,
        "data": [
            asdict(reminder)
            for reminder in reminders
        ],
        "message": "",
    }


@router.get("/{reminder_id}")
def get_reminder(reminder_id: int) -> dict:
    """根据 ID 查询一条提醒。"""

    try:
        reminder = reminder_service.get_reminder(
            reminder_id
        )

        return {
            "success": True,
            "data": asdict(reminder),
            "message": "",
        }

    except ResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.put("/{reminder_id}")
def update_reminder(
    reminder_id: int,
    request: ReminderUpdateRequest,
) -> dict:
    """修改一条提醒的内容。"""

    try:
        reminder = reminder_service.update_reminder(
            reminder_id=reminder_id,
            content=request.content,
        )

        return {
            "success": True,
            "data": asdict(reminder),
            "message": "提醒修改成功",
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except ResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.patch("/{reminder_id}/enabled")
def update_reminder_enabled(
    reminder_id: int,
    request: ReminderEnabledRequest,
) -> dict:
    """启用或停用一条提醒。"""

    try:
        reminder = (
            reminder_service.update_reminder_enabled(
                reminder_id=reminder_id,
                enabled=request.enabled,
            )
        )

        action = "启用" if request.enabled else "停用"

        return {
            "success": True,
            "data": asdict(reminder),
            "message": f"提醒{action}成功",
        }

    except ResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int) -> dict:
    """删除一条提醒。"""

    try:
        reminder_service.delete_reminder(reminder_id)

        return {
            "success": True,
            "data": None,
            "message": "提醒删除成功",
        }

    except ResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error