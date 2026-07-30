import logging

import uvicorn

from backend.config import (
    APP_HOST,
    APP_PORT,
    DEBUG,
    ENVIRONMENT,
    LOG_LEVEL,
    logger,
)


def main() -> None:
    """根据应用配置启动 Uvicorn。"""

    uvicorn_log_level = (
        logging
        .getLevelName(LOG_LEVEL)
        .lower()
    )

    logger.info(
        "Starting application: "
        "environment=%s, "
        "host=%s, "
        "port=%s, "
        "reload=%s",
        ENVIRONMENT,
        APP_HOST,
        APP_PORT,
        DEBUG,
    )

    uvicorn.run(
        "backend.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=DEBUG,
        log_level=uvicorn_log_level,
    )


if __name__ == "__main__":
    main()