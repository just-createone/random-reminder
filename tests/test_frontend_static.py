from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _source_between(
    content: str,
    start_marker: str,
    end_marker: str,
) -> str:
    start = content.index(start_marker)
    end = content.index(
        end_marker,
        start,
    )

    return content[start:end]


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


def test_reminder_feedback_uses_friendly_messages() -> None:
    content = (
        PROJECT_ROOT
        / "frontend"
        / "js"
        / "reminders.js"
    ).read_text(
        encoding="utf-8",
    )

    load_source = _source_between(
        content,
        "async function loadReminders",
        "/**\n * 创建提醒",
    )
    create_source = _source_between(
        content,
        "async function createReminder",
        "/**\n * 删除提醒",
    )
    delete_source = _source_between(
        content,
        "async function deleteReminder",
        "/**\n * 修改启用状态",
    )
    toggle_source = _source_between(
        content,
        "async function toggleReminder",
        "/**\n * 生成提醒 HTML",
    )
    edit_source = _source_between(
        content,
        "async function saveReminderEdit",
        "function escapeHtml",
    )

    assert "还没有提醒，先创建第一条提醒。" in load_source
    assert "暂时无法加载提醒，请稍后重试。" in load_source
    assert "error.message" not in load_source
    assert "添加提醒失败，请稍后重试。" in create_source
    assert "error.message" not in create_source
    assert "删除提醒失败，请稍后重试。" in delete_source
    assert "error.message" not in delete_source
    assert "alert(" not in toggle_source
    assert "更新提醒状态失败，请稍后重试。" in toggle_source
    assert "showMessage(" in toggle_source
    assert "保存提醒失败，请稍后重试。" in edit_source
    assert "error.message" not in edit_source


def test_reminder_toggle_rolls_back_checkbox_after_failure() -> None:
    content = (
        PROJECT_ROOT
        / "frontend"
        / "js"
        / "reminders.js"
    ).read_text(
        encoding="utf-8",
    )

    toggle_source = _source_between(
        content,
        "async function toggleReminder",
        "/**\n * 生成提醒 HTML",
    )

    assert "this.checked," in content
    assert "const previousEnabled = !desiredEnabled;" in toggle_source
    assert "const result = await apiPatch" in toggle_source
    assert "checkbox.checked = reminder.enabled;" in toggle_source
    assert "item.dataset.reminderEnabled = String(reminder.enabled);" in toggle_source
    assert "checkbox.checked = previousEnabled;" in toggle_source
    assert "更新提醒状态失败，请稍后重试。" in toggle_source


def test_settings_feedback_uses_friendly_messages() -> None:
    content = (
        PROJECT_ROOT
        / "frontend"
        / "js"
        / "settings.js"
    ).read_text(
        encoding="utf-8",
    )

    load_source = _source_between(
        content,
        "async function loadSettings",
        "/**\n * 保存设置",
    )
    save_source = _source_between(
        content,
        "async function saveSettings",
        "/**\n * 控制时间输入框显示",
    )

    assert "alert(" not in load_source
    assert "error.message" not in load_source
    assert "暂时无法加载设置，请稍后重试。" in load_source
    assert "showMessage(" in load_source
    assert "error.message" not in save_source
    assert "保存设置失败，请稍后重试。" in save_source


def test_settings_data_management_uses_existing_data_apis() -> None:
    page_content = (
        PROJECT_ROOT
        / "frontend"
        / "pages"
        / "settings.html"
    ).read_text(
        encoding="utf-8",
    )
    script_content = (
        PROJECT_ROOT
        / "frontend"
        / "js"
        / "settings.js"
    ).read_text(
        encoding="utf-8",
    )

    assert 'id="exportDataButton"' in page_content
    assert 'id="importDataFile"' in page_content
    assert 'id="importDataButton"' in page_content
    assert '<script src="/js/modal.js"></script>' in page_content
    assert "async function exportUserData" in script_content
    assert '"/api/data/export"' in script_content
    assert "URL.createObjectURL" in script_content
    assert "async function importUserData" in script_content
    assert "await file.text()" in script_content
    assert "JSON.parse" in script_content
    assert '"/api/data/import"' in script_content
    assert "showConfirmModal" in script_content
    assert "保留当前提醒、追加文件中的提醒，并恢复文件中的提醒设置" in script_content


def test_confirm_modal_supports_contextual_confirm_text() -> None:
    content = (
        PROJECT_ROOT
        / "frontend"
        / "js"
        / "modal.js"
    ).read_text(
        encoding="utf-8",
    )

    assert 'confirmText = "删除"' in content
    assert "confirmModalConfirmButton" in content


def test_authentication_pages_and_page_guard_use_existing_api_helpers() -> None:
    login_page = (
        PROJECT_ROOT / "frontend" / "pages" / "login.html"
    ).read_text(encoding="utf-8")
    register_page = (
        PROJECT_ROOT / "frontend" / "pages" / "register.html"
    ).read_text(encoding="utf-8")
    auth_script = (
        PROJECT_ROOT / "frontend" / "js" / "auth.js"
    ).read_text(encoding="utf-8")
    login_script = (
        PROJECT_ROOT / "frontend" / "js" / "login.js"
    ).read_text(encoding="utf-8")
    register_script = (
        PROJECT_ROOT / "frontend" / "js" / "register.js"
    ).read_text(encoding="utf-8")

    assert 'id="loginForm"' in login_page
    assert 'id="registerForm"' in register_page
    assert 'type="password"' in login_page
    assert 'type="password"' in register_page
    assert "requireAuthenticatedUser" in auth_script
    assert "const authenticatedUserReady" in auth_script
    assert 'apiGet("/api/auth/me")' in auth_script
    assert 'apiPost("/api/auth/logout")' in auth_script
    assert 'classList.remove("auth-pending")' in auth_script
    assert 'apiPost("/api/auth/login"' in login_script
    assert 'apiPost("/api/auth/register"' in register_script
    assert "Intl.DateTimeFormat" in register_script
    assert "time_zone: timeZone" in register_script
    assert "localStorage" not in auth_script

    for script_name in (
        "dashboard.js",
        "reminders.js",
        "settings.js",
    ):
        content = (
            PROJECT_ROOT / "frontend" / "js" / script_name
        ).read_text(encoding="utf-8")
        assert "authenticatedUserReady.then" in content


def test_pwa_install_support_is_available_on_the_user_journey() -> None:
    page_paths = (
        PROJECT_ROOT / "frontend" / "index.html",
        PROJECT_ROOT / "frontend" / "pages" / "login.html",
        PROJECT_ROOT / "frontend" / "pages" / "register.html",
        PROJECT_ROOT / "frontend" / "pages" / "reminders.html",
        PROJECT_ROOT / "frontend" / "pages" / "settings.html",
    )

    for page_path in page_paths:
        content = page_path.read_text(encoding="utf-8")
        assert 'rel="manifest" href="/manifest.json"' in content
        assert 'rel="apple-touch-icon" href="/assets/icon-192.png"' in content
        assert '<meta name="theme-color" content="#ffffff"' in content
        assert '<script src="/js/pwa.js"></script>' in content

    index_content = page_paths[0].read_text(encoding="utf-8")
    assert 'id="pwaInstallCard"' in index_content
    assert 'id="pwaInstallDescription"' in index_content
    assert 'id="pwaInstallButton"' in index_content
    assert index_content.index('/js/ui.js') < index_content.index('/js/pwa.js')
    assert index_content.index('/js/pwa.js') < index_content.index('/js/auth.js')


def test_pwa_install_script_uses_native_install_and_ios_fallback() -> None:
    content = (
        PROJECT_ROOT / "frontend" / "js" / "pwa.js"
    ).read_text(encoding="utf-8")

    assert 'navigator.serviceWorker.register("/service-worker.js")' in content
    assert 'beforeinstallprompt' in content
    assert 'event.preventDefault()' in content
    assert 'deferredInstallPrompt.prompt()' in content
    assert 'appinstalled' in content
    assert 'display-mode: standalone' in content
    assert 'iPhone|iPad|iPod' in content

    service_worker = (
        PROJECT_ROOT / "frontend" / "service-worker.js"
    ).read_text(encoding="utf-8")
    assert '"random-reminder-v5"' in service_worker


def test_dashboard_feedback_keeps_empty_states_and_hides_errors() -> None:
    content = (
        PROJECT_ROOT
        / "frontend"
        / "js"
        / "dashboard.js"
    ).read_text(
        encoding="utf-8",
    )

    status_source = _source_between(
        content,
        "async function loadReminderStatus",
        "/**\n * 把设置转换为可读文字",
    )
    schedule_source = _source_between(
        content,
        "async function loadTodaySchedule",
        "/**\n * 根据计划数量显示摘要",
    )
    generate_source = _source_between(
        content,
        "async function generateTodaySchedule",
        "/**\n * 强制重新生成今日计划",
    )
    regenerate_source = _source_between(
        content,
        "async function regenerateTodaySchedule",
        "/**\n * 控制重新生成按钮的加载状态",
    )
    history_source = _source_between(
        content,
        "async function loadNotificationHistory",
        "/**\n * 更新通知历史摘要",
    )

    assert "暂时无法读取提醒设置，请稍后重试。" in status_source
    assert "error.message" not in status_source
    assert "暂时无法加载今日计划，请稍后重试。" in schedule_source
    assert "error.message" not in schedule_source
    assert "暂时无法加载通知记录，请稍后重试。" in history_source
    assert "error.message" not in history_source
    assert "alert(" not in generate_source
    assert "生成今日计划失败，请稍后重试。" in generate_source
    assert "showMessage(" in generate_source
    assert "alert(" not in regenerate_source
    assert "重新生成今日计划失败，请稍后重试。" in regenerate_source
    assert "showMessage(" in regenerate_source
    assert "今天还没有生成提醒计划。" in content
    assert "当前没有今日计划。" in content
    assert "今天没有等待中的提醒" in content
    assert "当前还没有通知记录。" in content
