from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.services.settings_service import SettingsService


router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"],
)

settings_service = SettingsService()


class SettingsUpdateRequest(BaseModel):
    """修改随机提醒设置的请求数据。"""

    enabled: bool = Field(
        ...,
        description="随机提醒总开关",
        examples=[True],
    )

    all_day: bool = Field(
        ...,
        description="是否全天允许提醒",
        examples=[False],
    )

    start_time: str | None = Field(
        default=None,
        description="提醒开始时间，格式为 HH:MM",
        examples=["09:00"],
    )

    end_time: str | None = Field(
        default=None,
        description="提醒结束时间，格式为 HH:MM",
        examples=["22:00"],
    )

    times_per_day: int = Field(
        ...,
        ge=1,
        le=20,
        description="每天提醒次数",
        examples=[5],
    )

    minimum_interval: int = Field(
        ...,
        ge=5,
        le=720,
        description="最小提醒间隔，单位为分钟",
        examples=[60],
    )


@router.get("")
def get_settings() -> dict:
    """读取当前提醒设置。"""

    settings = settings_service.get_settings()

    return {
        "success": True,
        "data": asdict(settings),
        "message": "",
    }


@router.put("")
def update_settings(
    request: SettingsUpdateRequest,
) -> dict:
    """更新提醒设置。"""

    try:
        settings = settings_service.update_settings(
            enabled=request.enabled,
            all_day=request.all_day,
            start_time=request.start_time,
            end_time=request.end_time,
            times_per_day=request.times_per_day,
            minimum_interval=request.minimum_interval,
        )

        return {
            "success": True,
            "data": asdict(settings),
            "message": "提醒设置保存成功",
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error