from pathlib import Path

import pytest

import scripts.migrate_runtime_permissions as migration


def create_test_layout(
    tmp_path: Path,
) -> tuple[Path, Path]:
    """创建模拟的运行时数据目录。"""

    data_directory = tmp_path / "data"
    backup_directory = tmp_path / "backups"

    data_directory.mkdir()
    backup_directory.mkdir()

    database_path = (
        data_directory
        / "random_reminder.db"
    )

    database_path.write_bytes(b"database")

    return (
        database_path,
        backup_directory,
    )


def test_collect_migration_targets(
    tmp_path: Path,
) -> None:
    """只收集数据库运行文件和备份目录。"""

    (
        database_path,
        backup_directory,
    ) = create_test_layout(tmp_path)

    wal_file = Path(
        f"{database_path}-wal"
    )

    shm_file = Path(
        f"{database_path}-shm"
    )

    journal_file = Path(
        f"{database_path}-journal"
    )

    wal_file.write_bytes(b"wal")
    shm_file.write_bytes(b"shm")
    journal_file.write_bytes(b"journal")

    targets = (
        migration.collect_migration_targets(
            database_path,
            backup_directory,
        )
    )

    assert targets == [
        database_path.parent,
        database_path,
        wal_file,
        shm_file,
        journal_file,
        backup_directory,
    ]


def test_dry_run_does_not_change_ownership(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """dry-run 不应调用 chown。"""

    (
        database_path,
        backup_directory,
    ) = create_test_layout(tmp_path)

    def fail_chown(
        path: str | Path,
        uid: int,
        gid: int,
    ) -> None:
        raise AssertionError(
            "dry-run must not call chown"
        )

    monkeypatch.setattr(
        migration.os,
        "chown",
        fail_chown,
        raising=False,
    )

    targets = (
        migration.migrate_runtime_permissions(
            database_path=database_path,
            backup_directory=(
                backup_directory
            ),
            dry_run=True,
        )
    )

    assert targets == [
        database_path.parent,
        database_path,
        backup_directory,
    ]


def test_migration_changes_expected_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """root 模式下应修改所有目标 ownership。"""

    (
        database_path,
        backup_directory,
    ) = create_test_layout(tmp_path)

    calls: list[
        tuple[Path, int, int]
    ] = []

    def fake_chown(
        path: str | Path,
        uid: int,
        gid: int,
    ) -> None:
        calls.append(
            (
                Path(path),
                uid,
                gid,
            )
        )

    monkeypatch.setattr(
        migration.os,
        "chown",
        fake_chown,
        raising=False,
    )

    monkeypatch.setattr(
        migration.os,
        "geteuid",
        lambda: 0,
        raising=False,
    )

    targets = (
        migration.migrate_runtime_permissions(
            database_path=database_path,
            backup_directory=(
                backup_directory
            ),
        )
    )

    expected_targets = [
        database_path.parent.resolve(),
        database_path.resolve(),
        backup_directory.resolve(),
    ]

    assert targets == expected_targets

    assert calls == [
        (
            path,
            migration.DEFAULT_UID,
            migration.DEFAULT_GID,
        )
        for path in expected_targets
    ]


def test_migration_rejects_non_root_user(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """真正迁移必须由 root 执行。"""

    (
        database_path,
        backup_directory,
    ) = create_test_layout(tmp_path)

    monkeypatch.setattr(
        migration.os,
        "chown",
        lambda *_args: None,
        raising=False,
    )

    monkeypatch.setattr(
        migration.os,
        "geteuid",
        lambda: 10001,
        raising=False,
    )

    with pytest.raises(
        PermissionError,
    ):
        migration.migrate_runtime_permissions(
            database_path=database_path,
            backup_directory=(
                backup_directory
            ),
        )


def test_missing_database_is_not_created(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    数据库不存在时迁移脚本不能创建空数据库。
    """

    data_directory = tmp_path / "data"
    backup_directory = tmp_path / "backups"

    data_directory.mkdir()
    backup_directory.mkdir()

    database_path = (
        data_directory
        / "random_reminder.db"
    )

    calls: list[Path] = []

    def fake_chown(
        path: str | Path,
        uid: int,
        gid: int,
    ) -> None:
        calls.append(Path(path))

    monkeypatch.setattr(
        migration.os,
        "chown",
        fake_chown,
        raising=False,
    )

    monkeypatch.setattr(
        migration.os,
        "geteuid",
        lambda: 0,
        raising=False,
    )

    targets = (
        migration.migrate_runtime_permissions(
            database_path=database_path,
            backup_directory=(
                backup_directory
            ),
        )
    )

    assert database_path.exists() is False

    assert targets == [
        data_directory.resolve(),
        backup_directory.resolve(),
    ]

    assert calls == targets