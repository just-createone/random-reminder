import logging
import os
from pathlib import Path


PROJECT_NAME = "random-reminder"
VERSION = "0.1.0"
DEBUG = True


# 项目根目录：
# random-reminder/
BASE_DIR = Path(__file__).resolve().parent.parent


# SQLite 数据库文件的完整路径
DATABASE_PATH = (
    BASE_DIR
    / "random_reminder.db"
)


# VAPID 密钥目录：
# random-reminder/secrets/vapid/
VAPID_DIRECTORY = (
    BASE_DIR
    / "secrets"
    / "vapid"
)


# 服务端发送 Web Push 时使用的私钥
VAPID_PRIVATE_KEY_PATH = (
    VAPID_DIRECTORY
    / "private_key.pem"
)


# 浏览器创建推送订阅时使用的 Base64URL 公钥
VAPID_APPLICATION_SERVER_KEY_PATH = (
    VAPID_DIRECTORY
    / "application_server_key.txt"
)
VAPID_SUBJECT = os.getenv(
    "VAPID_SUBJECT",
    "mailto:admin@example.com",
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


def get_db_path() -> str:
    """返回 SQLite 数据库文件的绝对路径。"""

    return str(DATABASE_PATH)


def get_vapid_public_key() -> str:
    """读取浏览器订阅所需的 VAPID 公钥。"""

    if not VAPID_APPLICATION_SERVER_KEY_PATH.exists():
        raise RuntimeError(
            "VAPID 公钥不存在，"
            "请先运行密钥生成脚本"
        )

    public_key = (
        VAPID_APPLICATION_SERVER_KEY_PATH
        .read_text(
            encoding="utf-8",
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

    return str(VAPID_PRIVATE_KEY_PATH)