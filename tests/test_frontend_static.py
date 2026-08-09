from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_settings_page_loads_ui_before_settings_script() -> None:
    content = (
        PROJECT_ROOT
        / "frontend"
        / "pages"
        / "settings.html"
    ).read_text(
        encoding="utf-8",
    )

    api_script = '<script src="/js/api.js"></script>'
    ui_script = '<script src="/js/ui.js"></script>'
    settings_script = '<script src="/js/settings.js"></script>'

    assert api_script in content
    assert ui_script in content
    assert settings_script in content
    assert (
        content.index(api_script)
        < content.index(ui_script)
        < content.index(settings_script)
    )


def test_index_notification_control_ids_are_unique() -> None:
    content = (
        PROJECT_ROOT
        / "frontend"
        / "index.html"
    ).read_text(
        encoding="utf-8",
    )

    for element_id in (
        "browserNotificationButton",
        "browserNotificationDescription",
        "pushSubscriptionButton",
        "pushSubscriptionDescription",
    ):
        assert content.count(f'id="{element_id}"') == 1
