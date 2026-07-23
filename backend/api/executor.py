from fastapi import APIRouter

from backend.executor.runtime import schedule_executor


router = APIRouter(
    prefix="/api/executor",
    tags=["Executor"],
)


@router.get("/status")
def get_executor_status() -> dict:
    """查询后台执行器当前状态。"""

    return {
        "success": True,
        "data": {
            "running": schedule_executor.is_running,
            "check_interval_seconds": (
                schedule_executor
                .CHECK_INTERVAL_SECONDS
            ),
            "late_grace_minutes": (
                schedule_executor
                .LATE_GRACE_MINUTES
            ),
        },
        "message": "",
    }


@router.post("/run-once")
async def run_executor_once() -> dict:
    """立即执行一次计划检查。"""

    result = await schedule_executor.run_once()

    return {
        "success": True,
        "data": result,
        "message": "计划检查执行完成",
    }