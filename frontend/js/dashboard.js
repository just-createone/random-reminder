/**
 * 加载并显示今天的提醒计划。
 */
async function loadTodaySchedule() {
    const container =
        document.getElementById(
            "todaySchedule"
        );

    try {
        const result = await apiGet(
            "/api/schedules/today"
        );

        const schedules = result.data;

        if (schedules.length === 0) {
            container.innerHTML = `
                <p>今天还没有生成提醒计划。</p>

                <button
                    type="button"
                    onclick="generateTodaySchedule()"
                >
                    生成今日计划
                </button>
            `;

            return;
        }

        container.innerHTML = schedules
            .map(createScheduleHtml)
            .join("");

    } catch (error) {
        container.innerHTML = `
            <p class="error-message">
                加载失败：${escapeHtml(error.message)}
            </p>
        `;
    }
}


/**
 * 生成今天的随机提醒计划。
 */
async function generateTodaySchedule() {
    const container =
        document.getElementById(
            "todaySchedule"
        );

    container.textContent =
        "正在生成今日计划……";

    try {
        await apiPost(
            "/api/schedules/today/generate?force=false"
        );

        await loadTodaySchedule();

    } catch (error) {
        container.innerHTML = `
            <p class="error-message">
                生成失败：${escapeHtml(error.message)}
            </p>
        `;
    }
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

            <span class="schedule-status">
                ${getStatusText(schedule.status)}
            </span>
        </div>
    `;
}


/**
 * 把后端状态转换为用户可读文字。
 */
function getStatusText(status) {
    const statusMap = {
        pending: "等待提醒",
        sent: "已提醒",
        skipped: "已跳过",
    };

    return statusMap[status] || status;
}


/**
 * 转义用户内容，避免内容被当作 HTML 执行。
 */
function escapeHtml(value) {
    const element =
        document.createElement("div");

    element.textContent =
        String(value);

    return element.innerHTML;
}


loadTodaySchedule();