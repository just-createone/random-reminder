import sqlite3

from backend.config import get_db_path


def get_connection() -> sqlite3.Connection:
    """创建并返回一个 SQLite 数据库连接。"""

    connection = sqlite3.connect(
        get_db_path(),
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    return connection