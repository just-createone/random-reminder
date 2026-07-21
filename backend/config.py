import logging
from pathlib import Path


PROJECT_NAME = "random-reminder"
VERSION = "0.1.0"
DEBUG = True

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite 数据库文件的完整路径
DATABASE_PATH = BASE_DIR / "random_reminder.db"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def get_db_path() -> str:
    """返回 SQLite 数据库文件的绝对路径。"""
    return str(DATABASE_PATH)