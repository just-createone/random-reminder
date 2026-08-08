import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.config import (
    BACKUP_DIRECTORY,
    BACKUP_KEEP_LATEST,
    BACKUP_MAX_AGE_DAYS,
    logger,
)


BACKUP_PATTERN = "random_reminder_*.db"
BACKUP_TIMESTAMP_FORMAT = (
    "random_reminder_%Y%m%d_%H%M%S_%f.db"
)


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


def _parse_backup_time(
    backup_file: Path,
) -> datetime | None:
    """从标准备份文件名中解析 UTC 创建时间。"""

    try:
        parsed_time = datetime.strptime(
            backup_file.name,
            BACKUP_TIMESTAMP_FORMAT,
        )

    except ValueError:
        return None

    return parsed_time.replace(
        tzinfo=timezone.utc
    )


def cleanup_backups(
    backup_directory: str | Path | None = None,
    *,
    keep_latest: int | None = None,
    max_age_days: int | None = None,
    keep_count: int | None = None,
    dry_run: bool = False,
    reference_time: datetime | None = None,
) -> list[Path]:
    """
    清理过期数据库备份。

    新策略：
    1. 始终保护最新 keep_latest 份备份；
    2. 在保护范围之外，只删除超过 max_age_days
       的标准备份文件；
    3. dry_run=True 时只返回候选文件，不实际删除。

    keep_count 是旧接口的兼容参数。旧调用只传
    keep_count 时，继续保持原有的纯数量清理行为。
    """

    directory = Path(
        backup_directory
        or BACKUP_DIRECTORY
    ).expanduser().resolve()

    if (
        keep_latest is not None
        and keep_count is not None
        and keep_latest != keep_count
    ):
        raise ValueError(
            "keep_latest 与 keep_count 不能设置为不同值"
        )

    resolved_keep_latest = (
        keep_latest
        if keep_latest is not None
        else (
            keep_count
            if keep_count is not None
            else BACKUP_KEEP_LATEST
        )
    )

    resolved_max_age_days = (
        max_age_days
        if max_age_days is not None
        else BACKUP_MAX_AGE_DAYS
    )

    if resolved_keep_latest < 1:
        raise ValueError(
            "备份保留数量不能小于 1"
        )

    if resolved_max_age_days < 1:
        raise ValueError(
            "备份最大保存天数不能小于 1"
        )

    backup_files = find_backup_files(
        directory
    )

    # 兼容旧的纯数量调用，避免已有代码和测试立即失效。
    legacy_count_only = (
        keep_count is not None
        and keep_latest is None
        and max_age_days is None
    )

    if legacy_count_only:
        files_to_delete = backup_files[
            resolved_keep_latest:
        ]

    else:
        resolved_reference_time = (
            reference_time
            or datetime.now(timezone.utc)
        )

        if (
            resolved_reference_time.tzinfo
            is None
        ):
            resolved_reference_time = (
                resolved_reference_time.replace(
                    tzinfo=timezone.utc
                )
            )
        else:
            resolved_reference_time = (
                resolved_reference_time.astimezone(
                    timezone.utc
                )
            )

        expiration_time = (
            resolved_reference_time
            - timedelta(
                days=resolved_max_age_days
            )
        )

        files_to_delete: list[Path] = []

        # 最新指定数量的备份始终保留。
        for backup_file in backup_files[
            resolved_keep_latest:
        ]:
            backup_time = _parse_backup_time(
                backup_file
            )

            if backup_time is None:
                logger.warning(
                    "Backup filename timestamp "
                    "could not be parsed; file preserved: %s",
                    backup_file,
                )
                continue

            if backup_time < expiration_time:
                files_to_delete.append(
                    backup_file
                )

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
        "directory=%s, keep_latest=%s, "
        "max_age_days=%s, deleted=%s",
        directory,
        resolved_keep_latest,
        resolved_max_age_days,
        len(deleted_files),
    )

    return deleted_files


def build_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        description="清理随机提醒器的过期数据库备份"
    )

    parser.add_argument(
        "--directory",
        type=Path,
        default=None,
        help="备份目录",
    )

    parser.add_argument(
        "--keep-latest",
        "--keep",
        dest="keep_latest",
        type=int,
        default=None,
        help="始终保留最新多少份备份",
    )

    parser.add_argument(
        "--max-age-days",
        type=int,
        default=None,
        help="删除保护范围之外超过多少天的备份",
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
            keep_latest=arguments.keep_latest,
            max_age_days=arguments.max_age_days,
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
        print(f"- {backup_file}")


if __name__ == "__main__":
    main()