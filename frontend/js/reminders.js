/**
 * 加载提醒列表
 */
async function loadReminders() {
  const container = document.getElementById("reminderList");

  try {
    const result = await apiGet("/api/reminders");

    const reminders = result.data;

    if (reminders.length === 0) {
      container.innerHTML = `
            <p>
            暂无提醒内容
            </p>
            `;

      return;
    }

    container.innerHTML = reminders.map(createReminderHtml).join("");
  } catch (error) {
    container.innerHTML = `
        <p class="error-message">
        加载失败：
        ${escapeHtml(error.message)}
        </p>
        `;
  }
}

/**
 * 创建提醒
 */
async function createReminder() {
  const textarea = document.getElementById("reminderContent");

  const content = textarea.value.trim();

  if (!content) {
    showMessage("请输入提醒内容", "error");

    return;
  }

  try {
    await apiPost("/api/reminders", {
      content: content,
    });

    textarea.value = "";

    showMessage(
    "提醒添加成功"
);

    await loadReminders();
  } catch (error) {
    showMessage(
        error.message,
        "error"
    );
  }
}

/**
 * 删除提醒
 */
async function deleteReminder(id) {
  const confirmed = await showConfirmModal(
        "确定删除这个提醒吗？"
    );

  if (!confirmed) {
    return;
  }

  try {
    await apiDelete(`/api/reminders/${id}`);
    showMessage(
    "提醒删除成功"
);
    await loadReminders();
  } catch (error) {
    showMessage(error.message, "error");
  }
}

/**
 * 修改启用状态
 */
async function toggleReminder(id, enabled) {
  try {
    await apiPatch(`/api/reminders/${id}/enabled`, {
      enabled: enabled,
    });

    await loadReminders();
  } catch (error) {
    alert(error.message);
  }
}

/**
 * 生成提醒 HTML
 */
function createReminderHtml(reminder) {
  return `

    <div class="reminder-item">


        <div class="reminder-content">

            ${escapeHtml(reminder.content)}

        </div>



        <div class="reminder-actions">


            <label>


            <input
            type="checkbox"
            ${reminder.enabled ? "checked" : ""}

            onchange="
            toggleReminder(
                ${reminder.id},
                this.checked
            )
            "

            >


            启用


            </label>




            <button

            onclick="
            deleteReminder(
                ${reminder.id}
            )
            "

            >

            删除

            </button>



        </div>


    </div>


    `;
}

function escapeHtml(value) {
  const div = document.createElement("div");

  div.textContent = String(value);

  return div.innerHTML;
}

loadReminders();
