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


def test_reminder_editing_uses_existing_put_api() -> None:
    content = (
        PROJECT_ROOT
        / "frontend"
        / "js"
        / "reminders.js"
    ).read_text(
        encoding="utf-8",
    )

    assert "startEditingReminder" in content
    assert "saveReminderEdit" in content
    assert "cancelEditingReminder" in content
    assert "let editingReminder = null;" in content
    assert "textarea.value.trim()" in content
    assert "提醒内容不能为空" in content
    assert 'apiPut(`/api/reminders/${id}`, {' in content
    assert "content: content" in content
    assert "提醒保存成功" in content
    assert "fetch(" not in content


def test_reminder_editing_restores_existing_actions() -> None:
    content = (
        PROJECT_ROOT
        / "frontend"
        / "js"
        / "reminders.js"
    ).read_text(
        encoding="utf-8",
    )

    assert "createReminderActionsHtml" in content
    assert "data-reminder-enabled" in content
    assert "cancelEditingReminder();" in content
    assert "apiPatch(`/api/reminders/${id}/enabled`" in content
