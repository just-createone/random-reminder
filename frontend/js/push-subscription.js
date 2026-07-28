/**
 * 初始化 Web Push 订阅区域。
 */
async function initializePushSubscription() {
    const button = document.getElementById(
        "pushSubscriptionButton"
    );

    if (!button) {
        return;
    }

    if (
        !("serviceWorker" in navigator) ||
        !("PushManager" in window) ||
        !("Notification" in window)
    ) {
        setPushSubscriptionMessage(
            "当前浏览器不支持 Web Push。"
        );

        button.textContent = "浏览器不支持";
        button.disabled = true;

        return;
    }

    button.addEventListener(
        "click",
        handlePushSubscription
    );

    await refreshPushSubscriptionStatus();
}


/**
 * 读取当前浏览器是否已经订阅。
 */
async function refreshPushSubscriptionStatus() {
    const button = document.getElementById(
        "pushSubscriptionButton"
    );

    if (!button) {
        return;
    }

    try {
        const registration =
            await navigator.serviceWorker.ready;

        const subscription =
            await registration.pushManager
                .getSubscription();

        if (subscription) {
            setPushSubscriptionMessage(
                "浏览器已经创建推送订阅，" +
                "可以同步到后端。"
            );

            button.textContent = "同步推送订阅";
            button.disabled = false;

            return;
        }

        setPushSubscriptionMessage(
            "启用后，即使页面不在前台，" +
            "浏览器也能够接收服务端推送。"
        );

        button.textContent = "启用后台推送";
        button.disabled = false;

    } catch (error) {
        setPushSubscriptionMessage(
            `订阅状态读取失败：${error.message}`
        );

        button.textContent = "重新检查";
        button.disabled = false;
    }
}


/**
 * 创建或同步浏览器推送订阅。
 */
async function handlePushSubscription() {
    const button = document.getElementById(
        "pushSubscriptionButton"
    );

    if (!button) {
        return;
    }

    button.disabled = true;
    button.textContent = "处理中……";

    try {
        if (Notification.permission === "default") {
            const permission =
                await Notification.requestPermission();

            if (permission !== "granted") {
                throw new Error(
                    "未获得浏览器通知权限"
                );
            }
        }

        if (Notification.permission !== "granted") {
            throw new Error(
                "浏览器通知权限未开启"
            );
        }

        const registration =
            await navigator.serviceWorker.ready;

        let subscription =
            await registration.pushManager
                .getSubscription();

        if (!subscription) {
            const keyResult = await apiGet(
                "/api/push/vapid-public-key"
            );

            if (!keyResult.public_key) {
                throw new Error(
                    "后端未返回 VAPID 公钥"
                );
            }

            subscription =
                await registration.pushManager
                    .subscribe({
                        userVisibleOnly: true,
                        applicationServerKey:
                            urlBase64ToUint8Array(
                                keyResult.public_key
                            ),
                    });
        }

        const subscriptionData =
            subscription.toJSON();

        if (
            !subscriptionData.endpoint ||
            !subscriptionData.keys?.p256dh ||
            !subscriptionData.keys?.auth
        ) {
            throw new Error(
                "浏览器生成的订阅数据不完整"
            );
        }

        await apiPost(
            "/api/push/subscriptions",
            {
                endpoint:
                    subscriptionData.endpoint,

                keys: {
                    p256dh:
                        subscriptionData
                            .keys
                            .p256dh,

                    auth:
                        subscriptionData
                            .keys
                            .auth,
                },
            }
        );

        setPushSubscriptionMessage(
            "后台推送订阅已创建并保存。"
        );

        button.textContent = "同步推送订阅";
        button.disabled = false;

    } catch (error) {
        setPushSubscriptionMessage(
            `后台推送启用失败：${error.message}`
        );

        button.textContent = "重新尝试";
        button.disabled = false;
    }
}


/**
 * 将 Base64 URL 公钥转换为 Uint8Array。
 */
function urlBase64ToUint8Array(
    base64String
) {
    const padding = "=".repeat(
        (4 - base64String.length % 4) % 4
    );

    const base64 = (
        base64String + padding
    )
        .replace(/-/g, "+")
        .replace(/_/g, "/");

    const rawData = window.atob(
        base64
    );

    return Uint8Array.from(
        rawData,
        character =>
            character.charCodeAt(0)
    );
}


/**
 * 更新推送订阅提示文字。
 */
function setPushSubscriptionMessage(
    message
) {
    const description = document.getElementById(
        "pushSubscriptionDescription"
    );

    if (description) {
        description.textContent = message;
    }
}


initializePushSubscription();