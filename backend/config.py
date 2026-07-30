import logging
import os
from pathlib import Path


PROJECT_NAME = "random-reminder"
VERSION = "0.1.0"

BASE_DIR = Path(__file__).resolve().parent.parent


def _read_bool(
    variable_name: str,
    default: bool,
) -> bool:
    """读取布尔类型环境变量。"""

    raw_value = os.getenv(variable_name)

    if raw_value is None:
        return default

    normalized_value = (
        raw_value.strip().lower()
    )

    true_values = {
        "1",
        "true",
        "yes",
        "on",
    }

    false_values = {
        "0",
        "false",
        "no",
        "off",
    }

    if normalized_value in true_values:
        return True

    if normalized_value in false_values:
        return False

    raise ValueError(
        f"环境变量 {variable_name} "
        "必须是 true/false、yes/no、"
        "on/off 或 1/0"
    )


def _resolve_path(
    configured_value: str | None,
    default_path: Path,
) -> Path:
    """
    解析配置路径。

    相对路径以项目根目录为基准；
    绝对路径保持不变。
    """

    if configured_value:
        path = Path(
            configured_value
        ).expanduser()

    else:
        path = default_path

    if not path.is_absolute():
        path = BASE_DIR / path

    return path.resolve()


ENVIRONMENT = (
    os.getenv(
        "RANDOM_REMINDER_ENV",
        "development",
    )
    .strip()
    .lower()
)

DEBUG = _read_bool(
    "RANDOM_REMINDER_DEBUG",
    default=(
        ENVIRONMENT != "production"
    ),
)

DATABASE_PATH = _resolve_path(
    os.getenv(
        "RANDOM_REMINDER_DB_PATH"
    ),
    BASE_DIR / "random_reminder.db",
)

VAPID_DIRECTORY = _resolve_path(
    os.getenv(
        "RANDOM_REMINDER_VAPID_DIR"
    ),
    BASE_DIR / "secrets" / "vapid",
)

VAPID_PRIVATE_KEY_PATH = (
    VAPID_DIRECTORY
    / "private_key.pem"
)

VAPID_APPLICATION_SERVER_KEY_PATH = (
    VAPID_DIRECTORY
    / "application_server_key.txt"
)

VAPID_SUBJECT = (
    os.getenv(
        "VAPID_SUBJECT",
        "mailto:admin@example.com",
    ).strip()
    or "mailto:admin@example.com"
)

LOG_LEVEL_NAME = (
    os.getenv(
        "RANDOM_REMINDER_LOG_LEVEL",
        "INFO",
    )
    .strip()
    .upper()
)

LOG_LEVEL = getattr(
    logging,
    LOG_LEVEL_NAME,
    logging.INFO,
)

logging.basicConfig(
    level=LOG_LEVEL,
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
)

logger = logging.getLogger(
    __name__
)


def get_db_path() -> str:
    """返回 SQLite 数据库路径。"""

    return str(
        DATABASE_PATH
    )


def get_vapid_public_key() -> str:
    """读取浏览器订阅使用的 VAPID 公钥。"""

    if (
        not VAPID_APPLICATION_SERVER_KEY_PATH
        .exists()
    ):
        raise RuntimeError(
            "VAPID 公钥不存在，"
            "请先运行密钥生成脚本"
        )

    if (
        not VAPID_APPLICATION_SERVER_KEY_PATH
        .is_file()
    ):
        raise RuntimeError(
            "VAPID 公钥路径不是有效文件"
        )

    public_key = (
        VAPID_APPLICATION_SERVER_KEY_PATH
        .read_text(
            encoding="utf-8"
        )
        .strip()
    )

    if not public_key:
        raise RuntimeError(
            "VAPID 公钥文件为空"
        )

    return public_key


def get_vapid_private_key_path() -> str:
    """返回 Web Push 使用的 VAPID 私钥路径。"""

    if not VAPID_PRIVATE_KEY_PATH.exists():
        raise RuntimeError(
            "VAPID 私钥不存在，"
            "请先运行密钥生成脚本"
        )

    if not VAPID_PRIVATE_KEY_PATH.is_file():
        raise RuntimeError(
            "VAPID 私钥路径不是有效文件"
        )

    return str(
        VAPID_PRIVATE_KEY_PATH
    )