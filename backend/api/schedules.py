from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.auth import require_current_user
from backend.domain.user import User

from backend.services.schedule_service import (
    ScheduleService,
)


router = APIRouter(
    prefix="/api/schedules",
    tags=["Schedules"],
)

schedule_service = ScheduleService()


@router.get("/today")
def get_today_schedule(
    current_user: User = Depends(require_current_user),
) -> dict:
    """查询今天的提醒计划。"""

    schedules = (
        schedule_service.get_today_schedule(
            user_id=current_user.id,
            time_zone=current_user.time_zone,
        )
    )

    return {
        "success": True,
        "data": [
            asdict(schedule)
            for schedule in schedules
        ],
        "message": "",
    }




@router.post("/today/generate")
def generate_today_schedule(
    force: bool = Query(
        default=False,
        description="是否强制重新生成今天的计划",
    ),
    current_user: User = Depends(require_current_user),
) -> dict:
    """生成今天的随机提醒计划。"""

    try:
        schedules = (
            schedule_service.generate_today_schedule(
                force=force,
                user_id=current_user.id,
                time_zone=current_user.time_zone,
            )
        )

        return {
            "success": True,
            "data": [
                asdict(schedule)
                for schedule in schedules
            ],
            "message": "今日提醒计划生成成功",
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.delete("/today")
def clear_today_schedule(
    current_user: User = Depends(require_current_user),
) -> dict:
    """Clear only the current user's unfinished schedules for today."""

    deleted_count = schedule_service.clear_today_replaceable_schedules(
        user_id=current_user.id,
        time_zone=current_user.time_zone,
    )

    return {
        "success": True,
        "data": {"deleted_count": deleted_count},
        "message": "已清理今日未执行计划",
    }
