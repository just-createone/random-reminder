from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.executor import router as executor_router
from backend.api.notifications import (
    router as notifications_router,
)
from backend.api.reminders import router as reminders_router
from backend.api.schedules import router as schedules_router
from backend.api.settings import router as settings_router
from backend.api.push_subscriptions import (
    router as push_subscriptions_router,
)

from backend.config import (
    PROJECT_NAME,
    VERSION,
    logger,
)

from backend.database.init_db import init_database
from backend.executor.runtime import schedule_executor


# ===============================
# 路径配置
# ===============================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"



# ===============================
# 生命周期管理
# ===============================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用启动和关闭。"""

    init_database()
    schedule_executor.start()

    logger.info("Server started")

    try:
        yield

    finally:
        schedule_executor.stop()
        logger.info("Server stopped")



# ===============================
# 创建 FastAPI
# ===============================

app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    lifespan=lifespan,
)



# ===============================
# 静态资源
# ===============================


# CSS
app.mount(
    "/css",
    StaticFiles(
        directory=FRONTEND_DIR / "css"
    ),
    name="css",
)



# JavaScript
app.mount(
    "/js",
    StaticFiles(
        directory=FRONTEND_DIR / "js"
    ),
    name="js",
)



# 图片等资源
app.mount(
    "/assets",
    StaticFiles(
        directory=FRONTEND_DIR / "assets"
    ),
    name="assets",
)



# 子页面
app.mount(
    "/pages",
    StaticFiles(
        directory=FRONTEND_DIR / "pages",
        html=True,
    ),
    name="pages",
)







# ===============================
# 健康检查
# ===============================


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    检查后端服务是否正常。
    """

    logger.info(
        "Health check requested"
    )

    return {
        "status": "ok",
        "service": PROJECT_NAME,
        "version": VERSION,
    }




# ===============================
# API 路由
# ===============================


app.include_router(
    reminders_router
)

app.include_router(
    settings_router
)

app.include_router(
    schedules_router
)

app.include_router(
    notifications_router
)

app.include_router(
    executor_router
)
app.include_router(
    push_subscriptions_router
)

# PWA 文件
app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True,
    ),
    name="frontend",
)