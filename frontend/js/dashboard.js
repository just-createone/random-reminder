let currentSchedules = [];
let countdownTimer = null;


/**
 * 初始化首页。
 */
async function initializeDashboard() {
    await Promise.all([
        loadReminderStatus(),
        loadTodaySchedule(),
        loadNotificationHistory(),
    ]);

    startCountdownTimer();
}


/**
 * 加载随机提醒总开关状态。
 */
async function loadReminderStatus() {
    const badge = document.getElementById(
        "reminderStatusBadge"
    );

    const description = document.getElementById(
        "reminderStatusDescription"
    );

    try {
        const result = await apiGet(
            "/api/settings"
        );

        const settings = result.data;

        if (settings.enabled) {
            badge.textContent = "运行中";
            badge.className =
                "status-badge status-badge-enabled";

            description.textContent =
                createSettingsDescription(settings);

        } else {
            badge.textContent = "已关闭";
            badge.className =
                "status-badge status-badge-disabled";

            description.textContent =
                "随机提醒总开关当前处于关闭状态。";
        }

    } catch (error) {
        badge.textContent = "读取失败";
        badge.className =
            "status-badge status-badge-error";

        description.textContent =
            `无法读取设置：${error.message}`;
    }
}


/**
 * 把设置转换为可读文字。
 */
function createSettingsDescription(settings) {
    const timeDescription = settings.all_day
        ? "全天提醒"
        : `${settings.start_time} 至 ${settings.end_time}`;

    return (
        `${timeDescription}，每天 ${settings.times_per_day} 次，` +
        `最小间隔 ${settings.minimum_interval} 分钟。`
    );
}


/**
 * 加载今天的提醒计划。
 */
async function loadTodaySchedule() {
    const container = document.getElementById(
        "todaySchedule"
    );

    const summary = document.getElementById(
        "scheduleSummary"
    );

    try {
        const result = await apiGet(
            "/api/schedules/today"
        );

        currentSchedules = result.data;

        if (currentSchedules.length === 0) {
            summary.textContent =
                "今天还没有生成提醒计划。";

            container.innerHTML = `
                <div class="empty-state">
                    <p>当前没有今日计划。</p>

                    <button
                        type="button"
                        onclick="generateTodaySchedule()"
                    >
                        生成今日计划
                    </button>
                </div>
            `;

            updateNextReminder();

            return;
        }

        updateScheduleSummary();

        container.innerHTML = currentSchedules
            .map(createScheduleHtml)
            .join("");

        updateNextReminder();

    } catch (error) {
        summary.textContent = "计划读取失败";

        container.innerHTML = `
            <p class="error-message">
                加载失败：${escapeHtml(error.message)}
            </p>
        `;

        currentSchedules = [];
        updateNextReminder();
    }
}


/**
 * 根据计划数量显示摘要。
 */
function updateScheduleSummary() {
    const summary = document.getElementById(
        "scheduleSummary"
    );

    const sentCount = currentSchedules.filter(
        schedule => schedule.status === "sent"
    ).length;

    const pendingCount = currentSchedules.filter(
        schedule => schedule.status === "pending"
    ).length;

    const skippedCount = currentSchedules.filter(
        schedule => schedule.status === "skipped"
    ).length;
    const failedCount = currentSchedules.filter(
    schedule => schedule.status === "failed"
).length;

    summary.textContent =
        `共 ${currentSchedules.length} 条，` +
        `${sentCount} 条已提醒，` +
        `${pendingCount} 条等待中，` +
        `${skippedCount} 条已跳过。`+
        `${failedCount} 条发送失败。`;
}


/**
 * 首次生成今日计划。
 */
async function generateTodaySchedule() {
    setRegenerateButtonLoading(true);

    try {
        await apiPost(
            "/api/schedules/today/generate?force=false"
        );

        await Promise.all([
    loadTodaySchedule(),
    loadNotificationHistory(),
]);

    } catch (error) {
        alert(`生成失败：${error.message}`);

    } finally {
        setRegenerateButtonLoading(false);
    }
}


/**
 * 强制重新生成今日计划。
 */
async function regenerateTodaySchedule() {
    const confirmed = confirm(
        "重新生成会替换今天现有的提醒时间，确定继续吗？"
    );

    if (!confirmed) {
        return;
    }

    setRegenerateButtonLoading(true);

    try {
        await apiPost(
            "/api/schedules/today/generate?force=true"
        );

        await Promise.all([
    loadTodaySchedule(),
    loadNotificationHistory(),
]);

    } catch (error) {
        alert(`重新生成失败：${error.message}`);

    } finally {
        setRegenerateButtonLoading(false);
    }
}


/**
 * 控制重新生成按钮的加载状态。
 */
function setRegenerateButtonLoading(loading) {
    const button = document.getElementById(
        "regenerateButton"
    );

    button.disabled = loading;

    button.textContent = loading
        ? "处理中……"
        : "重新生成";
}


/**
 * 找到今天尚未到达的下一条 pending 计划。
 */
function findNextReminder() {
    const now = new Date();

    return currentSchedules.find(schedule => {
        if (schedule.status !== "pending") {
            return false;
        }

        const scheduledDate = createScheduleDate(
            schedule
        );

        return scheduledDate > now;
    }) || null;
}


/**
 * 根据计划日期和时间创建 Date 对象。
 */
function createScheduleDate(schedule) {
    return new Date(
        `${schedule.schedule_date}T` +
        `${schedule.scheduled_time}:00`
    );
}


/**
 * 更新下一次提醒区域。
 */
function updateNextReminder() {
    const timeElement = document.getElementById(
        "nextReminderTime"
    );

    const countdownElement = document.getElementById(
        "nextReminderCountdown"
    );

    const contentElement = document.getElementById(
        "nextReminderContent"
    );

    const nextReminder = findNextReminder();

    if (!nextReminder) {
        timeElement.textContent = "--:--";
        countdownElement.textContent =
            "今天没有等待中的提醒";
        contentElement.textContent = "";

        return;
    }

    timeElement.textContent =
        nextReminder.scheduled_time;

    contentElement.textContent =
        nextReminder.content;

    const targetDate = createScheduleDate(
        nextReminder
    );

    countdownElement.textContent =
        createCountdownText(targetDate);
}


/**
 * 计算倒计时文字。
 */
function createCountdownText(targetDate) {
    const now = new Date();

    const differenceMilliseconds =
        targetDate.getTime() - now.getTime();

    if (differenceMilliseconds <= 0) {
        return "即将提醒";
    }

    const totalMinutes = Math.ceil(
        differenceMilliseconds / 60000
    );

    const hours = Math.floor(
        totalMinutes / 60
    );

    const minutes = totalMinutes % 60;

    if (hours > 0 && minutes > 0) {
        return `还有 ${hours} 小时 ${minutes} 分钟`;
    }

    if (hours > 0) {
        return `还有 ${hours} 小时`;
    }

    return `还有 ${minutes} 分钟`;
}


/**
 * 启动首页自动刷新计时器。
 */
function startCountdownTimer() {
    if (countdownTimer !== null) {
        clearInterval(countdownTimer);
    }

    countdownTimer = setInterval(
        async () => {
            await Promise.all([
                loadTodaySchedule(),
                loadNotificationHistory(),
            ]);
        },
        60000
    );
}


/**
 * 把一条计划转换为 HTML。
 */
function createScheduleHtml(schedule) {
    return `
        <div class="schedule-item">
            <span class="schedule-time">
                ${escapeHtml(schedule.scheduled_time)}
            </span>

            <span class="schedule-content">
                ${escapeHtml(schedule.content)}
            </span>

            <span
                class="
                    schedule-status
                    schedule-status-${escapeHtml(schedule.status)}
                "
            >
                ${escapeHtml(getStatusText(schedule.status))}
            </span>
        </div>
    `;
}


/**
 * 将后端计划状态转换为中文。
 */
function getStatusText(status) {
    const statusMap = {
        pending: "等待提醒",
        sent: "已提醒",
        skipped: "已跳过",
        failed: "发送失败",
    };

    return statusMap[status] || status;
}


/**
 * 转义用户输入，避免被浏览器当作 HTML。
 */
function escapeHtml(value) {
    const element = document.createElement(
        "div"
    );

    element.textContent = String(value);

    return element.innerHTML;
}

/**
 * 加载最近的通知记录。
 */
async function loadNotificationHistory() {
    const container = document.getElementById(
        "notificationHistory"
    );

    const summary = document.getElementById(
        "notificationHistorySummary"
    );

    if (!container || !summary) {
        return;
    }

    try {
        const items = await apiGet(
            "/api/notifications/history?limit=10"
        );

        if (!Array.isArray(items)) {
            throw new Error(
                "通知历史返回格式不正确"
            );
        }

        updateNotificationHistorySummary(
            items
        );

        if (items.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>当前还没有通知记录。</p>
                </div>
            `;

            return;
        }

        container.innerHTML = items
            .map(createNotificationHistoryHtml)
            .join("");

    } catch (error) {
        summary.textContent =
            "通知记录读取失败";

        container.innerHTML = `
            <p class="error-message">
                加载失败：${escapeHtml(error.message)}
            </p>
        `;
    }
}
/**
 * 更新通知历史摘要。
 */
function updateNotificationHistorySummary(
    items
) {
    const summary = document.getElementById(
        "notificationHistorySummary"
    );

    const sentCount = items.filter(
        item =>
            item.notification_status === "sent"
    ).length;

    const pendingCount = items.filter(
        item =>
            item.notification_status === "pending"
    ).length;

    const failedCount = items.filter(
        item =>
            item.notification_status === "failed"
    ).length;

    summary.textContent =
        `最近 ${items.length} 条，` +
        `${sentCount} 条已发送，` +
        `${pendingCount} 条等待中，` +
        `${failedCount} 条发送失败。`;
}
/**
 * 把一条通知记录转换成 HTML。
 */
function createNotificationHistoryHtml(
    item
) {
    const normalizedStatus =
        normalizeNotificationStatus(
            item.notification_status
        );

    return `
        <div class="notification-history-item">
            <div class="notification-history-time">
                <strong>
                    ${escapeHtml(item.scheduled_time)}
                </strong>

                <span>
                    ${escapeHtml(item.schedule_date)}
                </span>
            </div>

            <div class="notification-history-content">
                ${escapeHtml(item.content)}
            </div>

            <span
                class="
                    notification-status
                    notification-status-${normalizedStatus}
                "
            >
                ${escapeHtml(
                    getNotificationStatusText(
                        item.notification_status
                    )
                )}
            </span>
        </div>
    `;
}

/**
 * 把未知状态转换为安全的 CSS 类名。
 */
function normalizeNotificationStatus(
    status
) {
    const supportedStatuses = [
        "pending",
        "sent",
        "failed",
    ];

    if (supportedStatuses.includes(status)) {
        return status;
    }

    return "unknown";
}
/**
 * 将通知状态转换为中文。
 */
function getNotificationStatusText(
    status
) {
    const statusMap = {
        pending: "等待发送",
        sent: "已发送",
        failed: "发送失败",
    };

    return statusMap[status] || "未知状态";
}
initializeDashboard();