from datetime import datetime, timezone
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


def test_cleanup_backups_respects_max_age_boundary(
    tmp_path: Path,
) -> None:
    """
    Files older than the age limit are deleted.
    Files exactly on the boundary are preserved.
    """

    created_files = create_backup_files(
        tmp_path,
        5,
    )

    reference_time = datetime(
        2026,
        8,
        5,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    preview = cleanup_backups(
        backup_directory=tmp_path,
        keep_latest=2,
        max_age_days=2,
        dry_run=True,
        reference_time=reference_time,
    )

    # The cutoff is 2026-08-03 12:00 UTC.
    # August 1 and 2 are expired.
    # August 3 is exactly on the boundary.
    assert preview == [
        created_files[1],
        created_files[0],
    ]

    assert all(
        backup_file.is_file()
        for backup_file in created_files
    )

    deleted_files = cleanup_backups(
        backup_directory=tmp_path,
        keep_latest=2,
        max_age_days=2,
        reference_time=reference_time,
    )

    assert deleted_files == preview

    assert find_backup_files(tmp_path) == [
        created_files[4],
        created_files[3],
        created_files[2],
    ]


def test_cleanup_backups_always_preserves_latest_files(
    tmp_path: Path,
) -> None:
    """
    The newest protected files remain even when all
    backups are older than the configured age limit.
    """

    created_files = create_backup_files(
        tmp_path,
        5,
    )

    deleted_files = cleanup_backups(
        backup_directory=tmp_path,
        keep_latest=2,
        max_age_days=1,
        reference_time=datetime(
            2026,
            8,
            10,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert deleted_files == [
        created_files[2],
        created_files[1],
        created_files[0],
    ]

    assert find_backup_files(tmp_path) == [
        created_files[4],
        created_files[3],
    ]


def test_cleanup_backups_preserves_unparseable_backup_name(
    tmp_path: Path,
) -> None:
    """
    A matching filename with an invalid timestamp
    must be preserved rather than deleted.
    """

    created_files = create_backup_files(
        tmp_path,
        2,
    )

    unparseable_file = (
        tmp_path
        / "random_reminder_00000000_invalid.db"
    )

    unparseable_file.write_text(
        "preserve this file",
        encoding="utf-8",
    )

    deleted_files = cleanup_backups(
        backup_directory=tmp_path,
        keep_latest=1,
        max_age_days=1,
        reference_time=datetime(
            2026,
            8,
            10,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert created_files[0] in deleted_files
    assert created_files[1].is_file()
    assert unparseable_file.is_file()


def test_cleanup_backups_rejects_invalid_max_age_days(
    tmp_path: Path,
) -> None:
    """The maximum age must be at least one day."""

    with pytest.raises(ValueError):
        cleanup_backups(
            backup_directory=tmp_path,
            keep_latest=1,
            max_age_days=0,
        )


def test_cleanup_backups_rejects_conflicting_keep_values(
    tmp_path: Path,
) -> None:
    """
    Conflicting legacy and current keep values
    must be rejected.
    """

    with pytest.raises(ValueError):
        cleanup_backups(
            backup_directory=tmp_path,
            keep_latest=2,
            keep_count=3,
        )
