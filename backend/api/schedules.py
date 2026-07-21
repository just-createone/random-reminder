from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, status

from backend.services.schedule_service import (
    ScheduleService,
)


router = APIRouter(
    prefix="/api/schedules",
    tags=["Schedules"],
)

schedule_service = ScheduleService()


@router.get("/today")
def get_today_schedule() -> dict:
    """查询今天的提醒计划。"""

    schedules = (
        schedule_service.get_today_schedule()
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
) -> dict:
    """生成今天的随机提醒计划。"""

    try:
        schedules = (
            schedule_service.generate_today_schedule(
                force=force
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