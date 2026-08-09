import argparse
import os
from pathlib import Path


DEFAULT_UID = 10001
DEFAULT_GID = 10001

DEFAULT_DATABASE_PATH = (
    "/app/data/random_reminder.db"
)

DEFAULT_BACKUP_DIRECTORY = (
    "/app/backups"
)


def get_database_path(
    database_path: str | Path | None = None,
) -> Path:
    """获取需要迁移权限的 SQLite 数据库路径。"""

    configured_path = (
        database_path
        or os.getenv(
            "RANDOM_REMINDER_DB_PATH",
            DEFAULT_DATABASE_PATH,
        )
    )

    return Path(
        configured_path
    ).expanduser().resolve()


def get_backup_directory(
    backup_directory: str | Path | None = None,
) -> Path:
    """获取数据库备份目录。"""

    configured_path = (
        backup_directory
        or os.getenv(
            "RANDOM_REMINDER_BACKUP_DIR",
            DEFAULT_BACKUP_DIRECTORY,
        )
    )

    return Path(
        configured_path
    ).expanduser().resolve()


def find_sqlite_files(
    database_path: Path,
) -> list[Path]:
    """
    查找数据库文件以及可能存在的 SQLite
    WAL、SHM 和 journal 文件。
    """

    candidates = [
        database_path,
        Path(f"{database_path}-wal"),
        Path(f"{database_path}-shm"),
        Path(f"{database_path}-journal"),
    ]

    return [
        path
        for path in candidates
        if path.is_file()
    ]


def collect_migration_targets(
    database_path: Path,
    backup_directory: Path,
) -> list[Path]:
    """
    收集需要迁移 ownership 的对象。

    只处理：
    - 数据库所在目录
    - 数据库及 SQLite 辅助文件
    - 备份目录

    不修改 VAPID 密钥。
    """

    targets: list[Path] = []

    if database_path.parent.is_dir():
        targets.append(
            database_path.parent
        )

    targets.extend(
        find_sqlite_files(
            database_path
        )
    )

    if backup_directory.is_dir():
        targets.append(
            backup_directory
        )

    # 去除可能重复的路径，同时保持顺序。
    return list(
        dict.fromkeys(targets)
    )


def migrate_runtime_permissions(
    database_path: str | Path | None = None,
    backup_directory: str | Path | None = None,
    *,
    uid: int = DEFAULT_UID,
    gid: int = DEFAULT_GID,
    dry_run: bool = False,
) -> list[Path]:
    """
    将旧版本运行数据迁移给非 root app 用户。

    dry_run=True 时只返回准备修改的路径，
    不实际修改 ownership。
    """

    resolved_database_path = (
        get_database_path(
            database_path
        )
    )

    resolved_backup_directory = (
        get_backup_directory(
            backup_directory
        )
    )

    targets = collect_migration_targets(
        resolved_database_path,
        resolved_backup_directory,
    )

    if dry_run:
        return targets

    chown = getattr(
        os,
        "chown",
        None,
    )

    if chown is None:
        raise RuntimeError(
            "当前操作系统不支持 chown；"
            "权限迁移应在 Linux Docker 容器中执行"
        )

    geteuid = getattr(
        os,
        "geteuid",
        None,
    )

    if (
        geteuid is not None
        and geteuid() != 0
    ):
        raise PermissionError(
            "权限迁移需要 root 权限；"
            "请使用 --user 0 的一次性容器执行"
        )

    for target in targets:
        chown(
            target,
            uid,
            gid,
        )

    return targets


def build_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        description=(
            "迁移随机提醒器旧部署的运行时文件权限"
        )
    )

    parser.add_argument(
        "--database",
        default=None,
        help=(
            "SQLite 数据库路径；"
            "默认读取 RANDOM_REMINDER_DB_PATH"
        ),
    )

    parser.add_argument(
        "--backup-directory",
        default=None,
        help=(
            "数据库备份目录；"
            "默认读取 RANDOM_REMINDER_BACKUP_DIR"
        ),
    )

    parser.add_argument(
        "--uid",
        type=int,
        default=DEFAULT_UID,
        help="目标运行用户 UID，默认 10001",
    )

    parser.add_argument(
        "--gid",
        type=int,
        default=DEFAULT_GID,
        help="目标运行用户 GID，默认 10001",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示准备修改的路径，不修改权限",
    )

    return parser


def main() -> None:
    """命令行入口。"""

    parser = build_argument_parser()
    arguments = parser.parse_args()

    try:
        affected_paths = (
            migrate_runtime_permissions(
                database_path=arguments.database,
                backup_directory=(
                    arguments.backup_directory
                ),
                uid=arguments.uid,
                gid=arguments.gid,
                dry_run=arguments.dry_run,
            )
        )

    except (
        PermissionError,
        RuntimeError,
        OSError,
    ) as exc:
        parser.error(str(exc))

    action = (
        "Would migrate"
        if arguments.dry_run
        else "Migrated"
    )

    print(
        f"{action} "
        f"{len(affected_paths)} path(s) "
        f"to UID/GID "
        f"{arguments.uid}:{arguments.gid}"
    )

    for path in affected_paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()