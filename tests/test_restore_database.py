import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.maintenance.restore_database import (
    restore_database,
    validate_sqlite_database,
)


def create_test_database(
    path: Path,
    content: str,
) -> None:
    """创建用于测试的 SQLite 数据库。"""

    with closing(
        sqlite3.connect(path)
    ) as connection:
        connection.execute(
            """
            CREATE TABLE reminders (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            INSERT INTO reminders (
                content
            )
            VALUES (?)
            """,
            (content,),
        )

        connection.commit()


def read_reminder_content(
    path: Path,
) -> str:
    """读取测试数据库中的提醒内容。"""

    with closing(
        sqlite3.connect(path)
    ) as connection:
        result = connection.execute(
            """
            SELECT content
            FROM reminders
            LIMIT 1
            """
        ).fetchone()

    assert result is not None

    return str(
        result[0]
    )

def test_restore_database_replaces_target_and_creates_safety_backup(
    tmp_path: Path,
) -> None:
    """恢复后应替换目标并保存原数据库。"""

    backup = (
        tmp_path / "backup.db"
    )

    target = (
        tmp_path / "target.db"
    )

    safety_directory = (
        tmp_path / "safety"
    )

    create_test_database(
        backup,
        "备份中的提醒",
    )

    create_test_database(
        target,
        "恢复前的提醒",
    )

    timestamp = datetime(
        2026,
        8,
        1,
        12,
        30,
        45,
        tzinfo=timezone.utc,
    )

    restored_path, safety_backup = (
        restore_database(
            backup_path=backup,
            target_path=target,
            safety_backup_directory=(
                safety_directory
            ),
            timestamp=timestamp,
        )
    )

    assert restored_path == (
        target.resolve()
    )

    assert safety_backup is not None
    assert safety_backup.is_file()

    assert read_reminder_content(
        target
    ) == "备份中的提醒"

    assert read_reminder_content(
        safety_backup
    ) == "恢复前的提醒"


def test_restore_database_can_create_new_target(
    tmp_path: Path,
) -> None:
    """目标不存在时应创建新数据库。"""

    backup = (
        tmp_path / "backup.db"
    )

    target = (
        tmp_path
        / "nested"
        / "target.db"
    )

    create_test_database(
        backup,
        "新数据库内容",
    )

    restored_path, safety_backup = (
        restore_database(
            backup_path=backup,
            target_path=target,
        )
    )

    assert restored_path.is_file()
    assert safety_backup is None

    assert read_reminder_content(
        target
    ) == "新数据库内容"


def test_restore_database_rejects_missing_backup(
    tmp_path: Path,
) -> None:
    """备份不存在时应明确报错。"""

    with pytest.raises(
        FileNotFoundError,
        match="备份文件不存在",
    ):
        restore_database(
            backup_path=(
                tmp_path / "missing.db"
            ),
            target_path=(
                tmp_path / "target.db"
            ),
        )


def test_restore_database_rejects_corrupted_backup_without_changing_target(
    tmp_path: Path,
) -> None:
    """损坏备份不能覆盖当前数据库。"""

    backup = (
        tmp_path / "corrupted.db"
    )

    target = (
        tmp_path / "target.db"
    )

    backup.write_text(
        "this is not sqlite",
        encoding="utf-8",
    )

    create_test_database(
        target,
        "原始内容",
    )

    with pytest.raises(
        ValueError,
        match="数据库文件无效或已损坏",
    ):
        restore_database(
            backup_path=backup,
            target_path=target,
            safety_backup_directory=(
                tmp_path / "safety"
            ),
        )

    assert read_reminder_content(
        target
    ) == "原始内容"


def test_validate_sqlite_database_accepts_valid_database(
    tmp_path: Path,
) -> None:
    """有效数据库应通过完整性检查。"""

    database = (
        tmp_path / "valid.db"
    )

    create_test_database(
        database,
        "测试内容",
    )

    validate_sqlite_database(
        database
    )