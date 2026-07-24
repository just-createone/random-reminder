from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.executor import router as executor_router
from backend.api.notifications import (
    router as notifications_router,
)
from backend.api.reminders import router as reminders_router
from backend.api.schedules import router as schedules_router
from backend.api.settings import router as settings_router
from backend.config import PROJECT_NAME, VERSION, logger
from backend.database.init_db import init_database
from backend.executor.runtime import schedule_executor


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(
    _app: FastAPI,
) -> AsyncIterator[None]:
    """管理应用启动和关闭时的操作。"""

    init_database()
    schedule_executor.start()

    logger.info("Server started")

    yield

    await schedule_executor.stop()

    logger.info("Server stopped")


app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    lifespan=lifespan,
)


app.mount(
    "/css",
    StaticFiles(
        directory=FRONTEND_DIR / "css"
    ),
    name="css",
)

app.mount(
    "/js",
    StaticFiles(
        directory=FRONTEND_DIR / "js"
    ),
    name="js",
)

app.mount(
    "/assets",
    StaticFiles(
        directory=FRONTEND_DIR / "assets"
    ),
    name="assets",
)

app.mount(
    "/pages",
    StaticFiles(
        directory=FRONTEND_DIR / "pages",
        html=True,
    ),
    name="pages",
)


@app.get(
    "/",
    response_class=FileResponse,
)
def frontend_home() -> FileResponse:
    """返回随机提醒器前端首页。"""

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


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
app.include_router(schedules_router)
app.include_router(notifications_router)
app.include_router(executor_router)