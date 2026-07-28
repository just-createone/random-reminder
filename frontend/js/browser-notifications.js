/**
 * 初始化浏览器通知区域。
 */
function initializeBrowserNotifications() {
    const button = document.getElementById(
        "browserNotificationButton"
    );

    if (!button) {
        return;
    }

    button.addEventListener(
        "click",
        handleBrowserNotificationAction
    );

    updateBrowserNotificationStatus();
}


/**
 * 根据当前权限更新页面显示。
 */
function updateBrowserNotificationStatus() {
    const button = document.getElementById(
        "browserNotificationButton"
    );

    const description = document.getElementById(
        "browserNotificationDescription"
    );

    if (!button || !description) {
        return;
    }

    if (
        !("Notification" in window) ||
        !("serviceWorker" in navigator)
    ) {
        description.textContent =
            "当前浏览器不支持通知功能。";

        button.textContent = "浏览器不支持";
        button.disabled = true;

        return;
    }

    if (Notification.permission === "granted") {
        description.textContent =
            "浏览器通知已经启用，可以发送测试通知。";

        button.textContent = "发送测试通知";
        button.disabled = false;

        return;
    }

    if (Notification.permission === "denied") {
        description.textContent =
            "通知权限已被阻止，请在浏览器的网站权限中重新允许。";

        button.textContent = "通知权限已阻止";
        button.disabled = true;

        return;
    }

    description.textContent =
        "启用后，随机提醒器可以显示浏览器系统通知。";

    button.textContent = "启用浏览器通知";
    button.disabled = false;
}


/**
 * 处理启用权限或发送测试通知。
 */
async function handleBrowserNotificationAction() {
    const button = document.getElementById(
        "browserNotificationButton"
    );

    if (!button) {
        return;
    }

    button.disabled = true;

    try {
        if (Notification.permission === "default") {
            const permission =
                await Notification.requestPermission();

            updateBrowserNotificationStatus();

            if (permission !== "granted") {
                return;
            }
        }

        if (Notification.permission !== "granted") {
            updateBrowserNotificationStatus();
            return;
        }

        await showBrowserTestNotification();

        const description = document.getElementById(
            "browserNotificationDescription"
        );

        if (description) {
            description.textContent =
                "测试通知已发送，请查看系统通知区域。";
        }

    } catch (error) {
        const description = document.getElementById(
            "browserNotificationDescription"
        );

        if (description) {
            description.textContent =
                `通知发送失败：${error.message}`;
        }

    } finally {
        updateBrowserNotificationButton();
    }
}


/**
 * 通过当前 Service Worker 显示通知。
 */
async function showBrowserTestNotification() {
    const registration =
        await navigator.serviceWorker.ready;

    await registration.showNotification(
        "随机提醒器",
        {
            body: "浏览器通知已经启用，随机提醒器可以向你发送提醒。",
            icon: "/assets/icon-192.png",
            badge: "/assets/icon-192.png",
            tag: "random-reminder-browser-test",
            data: {
                url: "/",
            },
        }
    );
}


/**
 * 单独恢复按钮状态，避免覆盖刚刚显示的成功信息。
 */
function updateBrowserNotificationButton() {
    const button = document.getElementById(
        "browserNotificationButton"
    );

    if (!button) {
        return;
    }

    if (Notification.permission === "granted") {
        button.textContent = "发送测试通知";
        button.disabled = false;
        return;
    }

    if (Notification.permission === "denied") {
        button.textContent = "通知权限已阻止";
        button.disabled = true;
        return;
    }

    button.textContent = "启用浏览器通知";
    button.disabled = false;
}


initializeBrowserNotifications();