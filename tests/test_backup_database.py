import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.maintenance.backup_database import (
    backup_database,
)


def test_backup_database_copies_database_contents(
    tmp_path: Path,
) -> None:
    """备份文件应包含源数据库中的数据。"""

    source = tmp_path / "source.db"
    backup_directory = (
        tmp_path / "backups"
    )

    with sqlite3.connect(
        source
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
            ("测试提醒",),
        )

        connection.commit()

    timestamp = datetime(
        2026,
        8,
        1,
        12,
        30,
        45,
        tzinfo=timezone.utc,
    )

    destination = backup_database(
        source_path=source,
        backup_directory=(
            backup_directory
        ),
        timestamp=timestamp,
    )

    expected_destination = (
        backup_directory
        / (
            "random_reminder_"
            "20260801_123045_000000.db"
        )
    )

    assert (
        destination
        == expected_destination
    )

    assert destination.is_file()

    with sqlite3.connect(
        destination
    ) as connection:
        result = connection.execute(
            """
            SELECT content
            FROM reminders
            """
        ).fetchone()

    assert result == (
        "测试提醒",
    )


def test_backup_database_creates_destination_directory(
    tmp_path: Path,
) -> None:
    """备份目录不存在时应自动创建。"""

    source = tmp_path / "source.db"
    backup_directory = (
        tmp_path
        / "nested"
        / "backups"
    )

    with sqlite3.connect(
        source
    ) as connection:
        connection.execute(
            """
            CREATE TABLE example (
                id INTEGER PRIMARY KEY
            )
            """
        )

        connection.commit()

    destination = backup_database(
        source_path=source,
        backup_directory=(
            backup_directory
        ),
    )

    assert backup_directory.is_dir()
    assert destination.is_file()


def test_backup_database_rejects_missing_source(
    tmp_path: Path,
) -> None:
    """源数据库不存在时应明确报错。"""

    missing_source = (
        tmp_path / "missing.db"
    )

    with pytest.raises(
        FileNotFoundError,
        match="数据库文件不存在",
    ):
        backup_database(
            source_path=missing_source,
            backup_directory=(
                tmp_path / "backups"
            ),
        )