from pathlib import Path

import pytest

from backend import config


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("off", False),
    ],
)
def test_read_bool_accepts_supported_values(
    monkeypatch,
    raw_value: str,
    expected: bool,
) -> None:
    """布尔环境变量应支持常见写法。"""

    variable_name = (
        "TEST_BOOLEAN_SETTING"
    )

    monkeypatch.setenv(
        variable_name,
        raw_value,
    )

    result = config._read_bool(
        variable_name,
        default=False,
    )

    assert result is expected


def test_read_bool_uses_default_when_missing(
    monkeypatch,
) -> None:
    """环境变量不存在时应使用默认值。"""

    variable_name = (
        "TEST_MISSING_BOOLEAN"
    )

    monkeypatch.delenv(
        variable_name,
        raising=False,
    )

    assert (
        config._read_bool(
            variable_name,
            default=True,
        )
        is True
    )


def test_read_bool_rejects_invalid_value(
    monkeypatch,
) -> None:
    """无效布尔值应明确报错。"""

    variable_name = (
        "TEST_INVALID_BOOLEAN"
    )

    monkeypatch.setenv(
        variable_name,
        "maybe",
    )

    with pytest.raises(
        ValueError,
        match=variable_name,
    ):
        config._read_bool(
            variable_name,
            default=False,
        )


def test_resolve_path_uses_project_root_for_relative_path(
) -> None:
    """相对路径应基于项目根目录解析。"""

    result = config._resolve_path(
        "data/test.db",
        Path("unused.db"),
    )

    expected = (
        config.BASE_DIR
        / "data"
        / "test.db"
    ).resolve()

    assert result == expected