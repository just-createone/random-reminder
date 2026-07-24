const API_BASE = "";


/**
 * 统一处理后端响应。
 */
async function handleResponse(response) {
    const result = await response.json();

    if (!response.ok) {
        const message =
            result.detail ||
            result.message ||
            "请求失败";

        throw new Error(message);
    }

    return result;
}


/**
 * 发送 GET 请求。
 */
async function apiGet(url) {
    const response = await fetch(
        API_BASE + url
    );

    return handleResponse(response);
}


/**
 * 发送 POST 请求。
 */
async function apiPost(url, data = null) {
    const options = {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    };

    if (data !== null) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(
        API_BASE + url,
        options
    );

    return handleResponse(response);
}


/**
 * 发送 PUT 请求。
 */
async function apiPut(url, data) {
    const response = await fetch(
        API_BASE + url,
        {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        }
    );

    return handleResponse(response);
}


/**
 * 发送 PATCH 请求。
 */
async function apiPatch(url, data) {
    const response = await fetch(
        API_BASE + url,
        {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        }
    );

    return handleResponse(response);
}


/**
 * 发送 DELETE 请求。
 */
async function apiDelete(url) {
    const response = await fetch(
        API_BASE + url,
        {
            method: "DELETE",
        }
    );

    return handleResponse(response);
}