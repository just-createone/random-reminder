import logging
from typing import Any

from backend import run


def test_main_starts_uvicorn_with_application_settings(
    monkeypatch,
) -> None:
    """启动入口应把应用配置传给 Uvicorn。"""

    received: dict[str, Any] = {}

    def fake_uvicorn_run(
        application: str,
        **kwargs: Any,
    ) -> None:
        received["application"] = (
            application
        )

        received.update(
            kwargs
        )

    monkeypatch.setattr(
        run.uvicorn,
        "run",
        fake_uvicorn_run,
    )

    monkeypatch.setattr(
        run,
        "APP_HOST",
        "127.0.0.1",
    )

    monkeypatch.setattr(
        run,
        "APP_PORT",
        9000,
    )

    monkeypatch.setattr(
        run,
        "DEBUG",
        False,
    )

    monkeypatch.setattr(
        run,
        "LOG_LEVEL",
        logging.INFO,
    )

    run.main()

    assert received == {
        "application": (
            "backend.main:app"
        ),
        "host": "127.0.0.1",
        "port": 9000,
        "reload": False,
        "log_level": "info",
    }