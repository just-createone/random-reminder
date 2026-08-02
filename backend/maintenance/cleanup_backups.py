import argparse
from pathlib import Path

from backend.config import (
    BACKUP_DIRECTORY,
    BACKUP_RETENTION_COUNT,
    logger,
)


BACKUP_PATTERN = "random_reminder_*.db"


def find_backup_files(
    backup_directory: str | Path,
) -> list[Path]:
    """查找备份文件，并按名称从新到旧排列。"""

    directory = Path(
        backup_directory
    ).expanduser().resolve()

    if not directory.exists():
        return []

    backup_files = [
        path
        for path in directory.glob(
            BACKUP_PATTERN
        )
        if path.is_file()
    ]

    return sorted(
        backup_files,
        key=lambda path: path.name,
        reverse=True,
    )


def cleanup_backups(
    backup_directory: str | Path | None = None,
    *,
    keep_count: int | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """
    删除超出保留数量的旧备份。

    dry_run=True 时只返回准备删除的文件，
    不实际删除文件。
    """

    directory = Path(
        backup_directory
        or BACKUP_DIRECTORY
    ).expanduser().resolve()

    resolved_keep_count = (
        keep_count
        if keep_count is not None
        else BACKUP_RETENTION_COUNT
    )

    if resolved_keep_count < 1:
        raise ValueError(
            "备份保留数量不能小于 1"
        )

    backup_files = find_backup_files(
        directory
    )

    files_to_delete = backup_files[
        resolved_keep_count:
    ]

    if dry_run:
        return files_to_delete

    deleted_files: list[Path] = []

    for backup_file in files_to_delete:
        try:
            backup_file.unlink()

        except FileNotFoundError:
            continue

        deleted_files.append(
            backup_file
        )

    logger.info(
        "Backup cleanup completed: "
        "directory=%s, kept=%s, deleted=%s",
        directory,
        resolved_keep_count,
        len(deleted_files),
    )

    return deleted_files


def build_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        description="清理随机提醒器的旧数据库备份"
    )

    parser.add_argument(
        "--directory",
        type=Path,
        default=None,
        help="备份目录",
    )

    parser.add_argument(
        "--keep",
        type=int,
        default=None,
        help="保留最近多少份备份",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示准备删除的文件，不实际删除",
    )

    return parser


def main() -> None:
    """执行一次旧备份清理。"""

    parser = build_argument_parser()
    arguments = parser.parse_args()

    try:
        affected_files = cleanup_backups(
            backup_directory=arguments.directory,
            keep_count=arguments.keep,
            dry_run=arguments.dry_run,
        )

    except Exception:
        logger.exception(
            "Backup cleanup failed"
        )
        raise SystemExit(1)

    operation_name = (
        "Would delete"
        if arguments.dry_run
        else "Deleted"
    )

    print(
        f"{operation_name} "
        f"{len(affected_files)} "
        "backup file(s)"
    )

    for backup_file in affected_files:
        print(
            f"- {backup_file}"
        )


if __name__ == "__main__":
    main()