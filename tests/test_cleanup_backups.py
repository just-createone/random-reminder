from pathlib import Path

import pytest

from backend.maintenance.cleanup_backups import (
    cleanup_backups,
    find_backup_files,
)


def create_backup_files(
    directory: Path,
    count: int,
) -> list[Path]:
    """创建按时间命名的测试备份文件。"""

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    created_files: list[Path] = []

    for index in range(1, count + 1):
        backup_file = (
            directory
            / (
                "random_reminder_"
                f"202608{index:02d}_"
                "120000_000000.db"
            )
        )

        backup_file.write_text(
            f"backup {index}",
            encoding="utf-8",
        )

        created_files.append(
            backup_file
        )

    return created_files


def test_find_backup_files_returns_newest_first(
    tmp_path: Path,
) -> None:
    """备份文件应按名称从新到旧排列。"""

    created_files = create_backup_files(
        tmp_path,
        3,
    )

    result = find_backup_files(
        tmp_path
    )

    assert result == [
        created_files[2],
        created_files[1],
        created_files[0],
    ]


def test_cleanup_backups_keeps_latest_files(
    tmp_path: Path,
) -> None:
    """清理应只保留最近指定数量的备份。"""

    created_files = create_backup_files(
        tmp_path,
        5,
    )

    deleted_files = cleanup_backups(
        backup_directory=tmp_path,
        keep_count=2,
    )

    assert deleted_files == [
        created_files[2],
        created_files[1],
        created_files[0],
    ]

    remaining_files = find_backup_files(
        tmp_path
    )

    assert remaining_files == [
        created_files[4],
        created_files[3],
    ]


def test_cleanup_backups_dry_run_does_not_delete_files(
    tmp_path: Path,
) -> None:
    """预览模式不应实际删除文件。"""

    created_files = create_backup_files(
        tmp_path,
        4,
    )

    affected_files = cleanup_backups(
        backup_directory=tmp_path,
        keep_count=2,
        dry_run=True,
    )

    assert affected_files == [
        created_files[1],
        created_files[0],
    ]

    assert len(
        find_backup_files(tmp_path)
    ) == 4


def test_cleanup_backups_ignores_unrelated_files(
    tmp_path: Path,
) -> None:
    """非标准备份文件不能被删除。"""

    create_backup_files(
        tmp_path,
        3,
    )

    unrelated_file = (
        tmp_path
        / "restore_validation_target.db"
    )

    unrelated_file.write_text(
        "do not delete",
        encoding="utf-8",
    )

    cleanup_backups(
        backup_directory=tmp_path,
        keep_count=1,
    )

    assert unrelated_file.is_file()


def test_cleanup_backups_rejects_invalid_keep_count(
    tmp_path: Path,
) -> None:
    """保留数量小于 1 时应报错。"""

    with pytest.raises(
        ValueError,
        match="备份保留数量不能小于 1",
    ):
        cleanup_backups(
            backup_directory=tmp_path,
            keep_count=0,
        )