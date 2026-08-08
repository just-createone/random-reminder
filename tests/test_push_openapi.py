import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_python(
    script: str,
    *,
    environment: str,
) -> dict:
    env = os.environ.copy()
    env["RANDOM_REMINDER_ENV"] = environment
    env.pop(
        "RANDOM_REMINDER_DEBUG",
        None,
    )

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
        ],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    marker = "TEST_RESULT="

    for line in result.stdout.splitlines():
        if line.startswith(marker):
            return json.loads(
                line[len(marker):]
            )

    raise AssertionError(
        "Child process did not return "
        "TEST_RESULT."
    )


def test_test_send_hidden_from_production_openapi():
    script = """
import json
from backend.main import app

paths = app.openapi()["paths"]

print(
    "TEST_RESULT="
    + json.dumps(
        {
            "test_send_in_openapi":
                "/api/push/test-send"
                in paths,
        }
    )
)
"""

    result = _run_python(
        script,
        environment="production",
    )

    assert (
        result["test_send_in_openapi"]
        is False
    )


def test_test_send_visible_in_development_openapi():
    script = """
import json
from backend.main import app

paths = app.openapi()["paths"]

print(
    "TEST_RESULT="
    + json.dumps(
        {
            "test_send_in_openapi":
                "/api/push/test-send"
                in paths,
        }
    )
)
"""

    result = _run_python(
        script,
        environment="development",
    )

    assert (
        result["test_send_in_openapi"]
        is True
    )


def test_test_send_returns_404_in_production():
    script = """
import json
from fastapi import HTTPException

from backend.api.push_subscriptions import (
    WebPushTestRequest,
    send_test_web_push,
)

request = WebPushTestRequest(
    message="production-test",
)

status_code = None

try:
    send_test_web_push(request)
except HTTPException as error:
    status_code = error.status_code

print(
    "TEST_RESULT="
    + json.dumps(
        {
            "status_code": status_code,
        }
    )
)
"""

    result = _run_python(
        script,
        environment="production",
    )

    assert result["status_code"] == 404
