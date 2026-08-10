from typing import Any

from fastapi import APIRouter, Body, HTTPException, status

from backend.config import logger
from backend.services.data_transfer_service import (
    DataTransferService,
)


router = APIRouter(
    prefix="/api/data",
    tags=["Data"],
)

data_transfer_service = DataTransferService()


@router.get("/export")
def export_user_data() -> dict[str, object]:
    """Export portable reminders and settings without runtime data."""

    try:
        data = data_transfer_service.export_data()

        return {
            "success": True,
            "data": data,
            "message": "用户数据导出成功",
        }

    except Exception as error:
        logger.exception("User-data export failed")

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="导出数据失败，请稍后重试",
        ) from error


@router.post("/import")
def import_user_data(
    payload: Any = Body(...),
) -> dict[str, object]:
    """Validate and atomically import a portable user-data export."""

    try:
        result = data_transfer_service.import_data(payload)

        return {
            "success": True,
            "data": result,
            "message": "用户数据导入成功",
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("User-data import failed")

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="导入数据失败，请稍后重试",
        ) from error
