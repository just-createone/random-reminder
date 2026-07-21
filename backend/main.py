from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.reminders import router as reminders_router
from backend.api.settings import router as settings_router
from backend.config import PROJECT_NAME, VERSION, logger
from backend.database.init_db import init_database




@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """管理应用启动和关闭时的操作。"""

    init_database()
    logger.info("Server started")

    yield

    logger.info("Server stopped")


app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict[str, str]:
    """项目根路径。"""

    return {
        "message": "Random Reminder API is running"
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """检查后端服务是否正常。"""

    logger.info("Health check requested")

    return {
        "status": "ok",
        "service": PROJECT_NAME,
        "version": VERSION,
    }


app.include_router(reminders_router)
app.include_router(settings_router)