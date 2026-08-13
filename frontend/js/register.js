document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    const submitButton = document.getElementById("registerSubmitButton");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirmPassword").value;
        const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone
            || "Asia/Shanghai";

        if (password !== confirmPassword) {
            showMessage("两次输入的密码不一致。", "error");
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "注册中...";

        try {
            await apiPost("/api/auth/register", {
                email,
                password,
                time_zone: timeZone,
            });
            window.location.replace("/");
        } catch (error) {
            const message = error.message === "该邮箱已注册，请直接登录"
                ? error.message
                : "注册失败，请检查邮箱和密码后重试。";

            showMessage(message, "error");
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "创建账户";
        }
    });
});
