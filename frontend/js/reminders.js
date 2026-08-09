let editingReminder = null;

/**
 * 加载提醒列表
 */
async function loadReminders() {
  const container = document.getElementById("reminderList");

  try {
    const result = await apiGet("/api/reminders");

    const reminders = result.data;

    editingReminder = null;

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

    <div
        class="reminder-item"
        data-reminder-id="${reminder.id}"
        data-reminder-enabled="${reminder.enabled}"
    >


        <div class="reminder-content">

            ${escapeHtml(reminder.content)}

        </div>



        <div class="reminder-actions">

            ${createReminderActionsHtml(reminder)}

        </div>


    </div>


    `;
}

function createReminderActionsHtml(reminder) {
  return `


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
            type="button"
            onclick="
            startEditingReminder(
                ${reminder.id}
            )
            "

            >

            编辑

            </button>




            <button
            type="button"

            onclick="
            deleteReminder(
                ${reminder.id}
            )
            "

            >

            删除

            </button>



    `;
}

function startEditingReminder(id) {
  if (editingReminder) {
    if (editingReminder.id === id) {
      editingReminder.textarea.focus();
      return;
    }

    cancelEditingReminder();
  }

  const item = document.querySelector(
    `[data-reminder-id="${id}"]`
  );
  const contentElement = item.querySelector(".reminder-content");
  const actionsElement = item.querySelector(".reminder-actions");
  const textarea = document.createElement("textarea");

  textarea.className = "reminder-edit-input";
  textarea.rows = 4;
  textarea.setAttribute("aria-label", "编辑提醒内容");
  textarea.value = contentElement.textContent.trim();

  editingReminder = {
    id: id,
    item: item,
    content: textarea.value,
    enabled: item.dataset.reminderEnabled === "true",
    contentElement: contentElement,
    actionsElement: actionsElement,
    textarea: textarea,
  };

  contentElement.replaceChildren(textarea);
  actionsElement.innerHTML = createReminderEditActionsHtml(id);
  textarea.focus();
}

function createReminderEditActionsHtml(id) {
  return `

            <button
            type="button"
            onclick="saveReminderEdit(${id})"
            >
            保存
            </button>

            <button
            type="button"
            class="secondary-button"
            onclick="cancelEditingReminder()"
            >
            取消
            </button>

    `;
}

function cancelEditingReminder() {
  if (!editingReminder) {
    return;
  }

  const reminder = editingReminder;

  reminder.contentElement.textContent = reminder.content;
  reminder.actionsElement.innerHTML = createReminderActionsHtml(reminder);
  editingReminder = null;
}

async function saveReminderEdit(id) {
  if (!editingReminder || editingReminder.id !== id) {
    return;
  }

  const content = editingReminder.textarea.value.trim();

  if (!content) {
    showMessage("提醒内容不能为空", "error");
    editingReminder.textarea.focus();
    return;
  }

  try {
    const result = await apiPut(`/api/reminders/${id}`, {
      content: content,
    });
    const reminder = result.data;

    editingReminder.item.dataset.reminderEnabled = String(reminder.enabled);
    editingReminder.contentElement.textContent = reminder.content;
    editingReminder.actionsElement.innerHTML = createReminderActionsHtml(
      reminder
    );
    editingReminder = null;

    showMessage("提醒保存成功");
  } catch (error) {
    showMessage(error.message, "error");
  }
}

function escapeHtml(value) {
  const div = document.createElement("div");

  div.textContent = String(value);

  return div.innerHTML;
}

loadReminders();
