import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from backend.config import (
    BACKUP_DIRECTORY,
    get_db_path,
    logger,
)

from backend.maintenance.cleanup_backups import (
    cleanup_backups,
)


def backup_database(
    source_path: str | Path | None = None,
    backup_directory: str | Path | None = None,
    *,
    timestamp: datetime | None = None,
) -> Path:
    """
    创建 SQLite 数据库备份。

    使用 SQLite backup API 生成一致性快照，
    可以在应用运行期间执行。
    """

    source = Path(
        source_path or get_db_path()
    ).expanduser().resolve()

    destination_directory = Path(
        backup_directory or BACKUP_DIRECTORY
    ).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(
            f"数据库文件不存在：{source}"
        )

    destination_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_time = (
        timestamp
        or datetime.now(
            timezone.utc
        )
    )

    filename = (
        "random_reminder_"
        f"{backup_time:%Y%m%d_%H%M%S_%f}"
        ".db"
    )

    destination = (
        destination_directory
        / filename
    )

    temporary_destination = (
        destination_directory
        / f"{filename}.tmp"
    )

    # 清理上一次失败时可能残留的临时文件。
    temporary_destination.unlink(
        missing_ok=True
    )

    try:
        # sqlite3.Connection 的普通 with 语句不会关闭连接，
        # closing() 可以保证离开代码块时真正调用 close()。
        with closing(
            sqlite3.connect(source)
        ) as source_connection:
            with closing(
                sqlite3.connect(
                    temporary_destination
                )
            ) as destination_connection:
                source_connection.backup(
                    destination_connection
                )

                destination_connection.commit()

        # 两个数据库连接都已关闭，
        # Windows 此时才允许重命名临时文件。
        temporary_destination.replace(
            destination
        )

    except Exception:
        temporary_destination.unlink(
            missing_ok=True
        )
        raise

    logger.info(
        "Database backup created: %s",
        destination,
    )

    return destination


def main() -> None:
    """执行备份，并自动清理过期文件。"""

    try:
        destination = backup_database()

        removed_files = (
            cleanup_backups()
        )

    except Exception:
        logger.exception(
            "Database backup or cleanup failed"
        )
        raise SystemExit(1)

    print(
        "Database backup created: "
        f"{destination}"
    )

    print(
        "Expired backups removed: "
        f"{len(removed_files)}"
    )


if __name__ == "__main__":
    main()