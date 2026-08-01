import argparse
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from backend.config import (
    BACKUP_DIRECTORY,
    get_db_path,
    logger,
)
from backend.maintenance.backup_database import (
    backup_database,
)


def validate_sqlite_database(
    database_path: str | Path,
) -> None:
    """检查 SQLite 数据库是否完整。"""

    path = Path(
        database_path
    ).expanduser().resolve()

    if not path.is_file():
        raise FileNotFoundError(
            f"数据库文件不存在：{path}"
        )

    try:
        with closing(
            sqlite3.connect(path)
        ) as connection:
            result = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()

    except sqlite3.DatabaseError as exc:
        raise ValueError(
            f"数据库文件无效或已损坏：{path}"
        ) from exc

    if (
        result is None
        or str(result[0]).lower() != "ok"
    ):
        detail = (
            result[0]
            if result
            else "没有返回检查结果"
        )

        raise ValueError(
            "数据库完整性检查失败："
            f"{detail}"
        )


def restore_database(
    backup_path: str | Path,
    target_path: str | Path | None = None,
    *,
    safety_backup_directory: (
        str | Path | None
    ) = None,
    create_safety_backup: bool = True,
    timestamp: datetime | None = None,
) -> tuple[Path, Path | None]:
    """
    从备份文件恢复 SQLite 数据库。

    恢复前默认会为当前数据库创建安全备份。
    """

    backup = Path(
        backup_path
    ).expanduser().resolve()

    target = Path(
        target_path or get_db_path()
    ).expanduser().resolve()

    if not backup.is_file():
        raise FileNotFoundError(
            f"备份文件不存在：{backup}"
        )

    if backup == target:
        raise ValueError(
            "备份文件不能与目标数据库相同"
        )

    # 在修改当前数据库之前，
    # 先验证备份文件是否有效。
    validate_sqlite_database(
        backup
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    safety_backup: Path | None = None

    if (
        create_safety_backup
        and target.is_file()
    ):
        safety_backup = backup_database(
            source_path=target,
            backup_directory=(
                safety_backup_directory
                or BACKUP_DIRECTORY
            ),
            timestamp=timestamp,
        )

    temporary_target = target.with_name(
        f"{target.name}.restore.tmp"
    )

    temporary_target.unlink(
        missing_ok=True
    )

    try:
        # 使用 SQLite backup API，
        # 把备份写入临时数据库。
        with closing(
            sqlite3.connect(backup)
        ) as source_connection:
            with closing(
                sqlite3.connect(
                    temporary_target
                )
            ) as target_connection:
                source_connection.backup(
                    target_connection
                )

                target_connection.commit()

        # 临时数据库也必须通过完整性检查。
        validate_sqlite_database(
            temporary_target
        )

        # 检查通过后再替换正式数据库。
        temporary_target.replace(
            target
        )

    except PermissionError as exc:
        temporary_target.unlink(
            missing_ok=True
        )

        raise RuntimeError(
            "目标数据库正在被其他程序使用，"
            "请先停止应用或容器后再恢复"
        ) from exc

    except Exception:
        temporary_target.unlink(
            missing_ok=True
        )
        raise

    logger.info(
        "Database restored: "
        "backup=%s, target=%s, "
        "safety_backup=%s",
        backup,
        target,
        safety_backup,
    )

    return target, safety_backup


def build_argument_parser(
) -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        description=(
            "从 SQLite 备份文件恢复"
            "随机提醒器数据库"
        )
    )

    parser.add_argument(
        "backup_path",
        type=Path,
        help="要恢复的备份数据库路径",
    )

    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help=(
            "目标数据库路径；"
            "默认使用应用数据库路径"
        ),
    )

    parser.add_argument(
        "--safety-backup-dir",
        type=Path,
        default=None,
        help=(
            "恢复前安全备份的保存目录"
        ),
    )

    parser.add_argument(
        "--no-safety-backup",
        action="store_true",
        help=(
            "不为当前数据库创建安全备份"
        ),
    )

    return parser


def main() -> None:
    """执行一次数据库恢复。"""

    parser = build_argument_parser()
    arguments = parser.parse_args()

    try:
        restored_path, safety_backup = (
            restore_database(
                backup_path=(
                    arguments.backup_path
                ),
                target_path=(
                    arguments.target
                ),
                safety_backup_directory=(
                    arguments
                    .safety_backup_dir
                ),
                create_safety_backup=(
                    not arguments
                    .no_safety_backup
                ),
            )
        )

    except Exception:
        logger.exception(
            "Database restore failed"
        )
        raise SystemExit(1)

    if safety_backup is not None:
        print(
            "Safety backup created: "
            f"{safety_backup}"
        )

    print(
        "Database restored: "
        f"{restored_path}"
    )


if __name__ == "__main__":
    main()