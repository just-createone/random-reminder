from fastapi import FastAPI

from backend.config import PROJECT_NAME, VERSION, logger
from backend.database.init_db import init_db

app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
)


@app.on_event("startup")
def startup_event() -> None:
    """应用启动时执行初始化操作。"""
    init_db()
    logger.info("Server started")


@app.get("/")
def root() -> dict[str, str]:
    """项目根路径。"""
    return {
        "message": "Random Reminder API is running"
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """检查后端服务是否正常运行。"""
    logger.info("Health check requested")

    return {
        "status": "ok",
        "service": PROJECT_NAME,
        "version": VERSION,
    }