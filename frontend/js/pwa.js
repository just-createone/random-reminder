/**
 * Provides the small amount of browser-specific glue needed to install the
 * application as a PWA. Authentication and reminder data still require an
 * active network connection.
 */
(() => {
    let deferredInstallPrompt = null;

    const installCard = document.getElementById("pwaInstallCard");
    const installButton = document.getElementById("pwaInstallButton");
    const installDescription = document.getElementById("pwaInstallDescription");
    const isStandalone = window.matchMedia("(display-mode: standalone)").matches
        || window.navigator.standalone === true;
    const isAppleMobile = /iPhone|iPad|iPod/.test(navigator.userAgent);

    function showInstallCard(description, showButton) {
        if (!installCard || !installDescription) {
            return;
        }

        installDescription.textContent = description;
        installCard.hidden = false;

        if (installButton) {
            installButton.hidden = !showButton;
        }
    }

    if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("/service-worker.js").catch((error) => {
            console.error("Service Worker registration failed:", error);
        });
    }

    if (isStandalone) {
        return;
    }

    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        deferredInstallPrompt = event;
        showInstallCard("安装后可从桌面或应用列表更方便地打开随机提醒器。", true);
    });

    window.addEventListener("appinstalled", () => {
        deferredInstallPrompt = null;

        if (installCard) {
            installCard.hidden = true;
        }

        if (typeof showMessage === "function") {
            showMessage("应用已安装。打开后可在通知设置中启用提醒通知。", "success");
        }
    });

    if (isAppleMobile) {
        showInstallCard(
            "在 Safari 中点击分享按钮，再选择“添加到主屏幕”，即可像 App 一样使用。",
            false,
        );
    }

    installButton?.addEventListener("click", async () => {
        if (!deferredInstallPrompt) {
            return;
        }

        installButton.disabled = true;
        deferredInstallPrompt.prompt();
        await deferredInstallPrompt.userChoice;
        installButton.disabled = false;
    });
})();
