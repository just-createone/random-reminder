document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const submitButton = document.getElementById("loginSubmitButton");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        submitButton.disabled = true;
        submitButton.textContent = "登录中...";

        try {
            await apiPost("/api/auth/login", { email, password });
            window.location.replace("/");
        } catch (error) {
            showMessage("登录失败，请检查邮箱和密码后重试。", "error");
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "登录";
        }
    });
});
