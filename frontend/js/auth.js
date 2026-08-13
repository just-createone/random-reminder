const AUTH_LOGIN_PATH = "/pages/login.html";


async function getCurrentUser() {
    const result = await apiGet("/api/auth/me");

    return result.data;
}


async function requireAuthenticatedUser() {
    try {
        return await getCurrentUser();
    } catch (error) {
        if (error.message === "请先登录") {
            window.location.replace(AUTH_LOGIN_PATH);
            return null;
        }

        throw error;
    }
}


async function logoutCurrentUser() {
    await apiPost("/api/auth/logout");
    window.location.replace(AUTH_LOGIN_PATH);
}


function renderAuthenticatedUser(user) {
    const userEmail = document.getElementById("currentUserEmail");
    const logoutButton = document.getElementById("logoutButton");

    if (userEmail) {
        userEmail.textContent = user.email;
    }

    if (logoutButton) {
        logoutButton.addEventListener("click", async () => {
            try {
                await logoutCurrentUser();
            } catch (error) {
                showMessage("退出登录失败，请稍后重试。", "error");
            }
        });
    }
}


const authenticatedUserReady = (async () => {
    if (document.body.dataset.authPage === "public") {
        return null;
    }

    try {
        const user = await requireAuthenticatedUser();

        if (user) {
            renderAuthenticatedUser(user);
            document.body.classList.remove("auth-pending");
        }

        return user;
    } catch (error) {
        console.error("Unable to check the current user", error);
        document.body.classList.remove("auth-pending");
        showMessage("暂时无法验证登录状态，请稍后重试。", "error");
        return null;
    }
})();
