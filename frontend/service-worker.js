const CACHE_NAME =
    "random-reminder-v3";

const APP_SHELL = [
    "/",
    "/index.html",
    "/css/style.css",
    "/js/api.js",
    "/js/ui.js",
    "/js/modal.js",
    "/js/dashboard.js",
    "/js/browser-notifications.js",
    "/manifest.json",
    "/assets/icon-192.png",
    "/assets/icon-512.png",
    
];


/**
 * 安装 Service Worker 并缓存基础资源。
 */
self.addEventListener(
    "install",
    event => {
        event.waitUntil(
            (async () => {
                const cache =
                    await caches.open(
                        CACHE_NAME
                    );

                await cache.addAll(
                    APP_SHELL
                );

                await self.skipWaiting();
            })()
        );
    }
);


/**
 * 激活新版 Service Worker，并删除旧缓存。
 */
self.addEventListener(
    "activate",
    event => {
        event.waitUntil(
            (async () => {
                const cacheNames =
                    await caches.keys();

                await Promise.all(
                    cacheNames
                        .filter(
                            cacheName =>
                                cacheName !==
                                CACHE_NAME
                        )
                        .map(
                            cacheName =>
                                caches.delete(
                                    cacheName
                                )
                        )
                );

                await self.clients.claim();
            })()
        );
    }
);


/**
 * 优先访问网络，网络不可用时再读取缓存。
 */
self.addEventListener(
    "fetch",
    event => {
        const request = event.request;

        if (request.method !== "GET") {
            return;
        }

        const url = new URL(
            request.url
        );

        if (
            url.origin !==
            self.location.origin
        ) {
            return;
        }

        /*
         * API 数据始终从后端读取，
         * 不使用静态缓存。
         */
        if (
            url.pathname.startsWith(
                "/api/"
            )
        ) {
            return;
        }

        event.respondWith(
            (async () => {
                try {
                    const response =
                        await fetch(request);

                    if (response.ok) {
                        const cache =
                            await caches.open(
                                CACHE_NAME
                            );

                        await cache.put(
                            request,
                            response.clone()
                        );
                    }

                    return response;

                } catch {
                    const cachedResponse =
                        await caches.match(
                            request
                        );

                    if (cachedResponse) {
                        return cachedResponse;
                    }

                    if (
                        request.mode ===
                        "navigate"
                    ) {
                        return caches.match(
                            "/index.html"
                        );
                    }

                    return Response.error();
                }
            })()
        );
    }
);
/**
 * 用户点击通知时，聚焦或重新打开应用。
 */
self.addEventListener(
    "notificationclick",
    event => {
        event.notification.close();

        const targetPath =
            event.notification.data?.url || "/";

        const targetUrl = new URL(
            targetPath,
            self.location.origin
        ).href;

        event.waitUntil(
            (async () => {
                const windowClients =
                    await clients.matchAll({
                        type: "window",
                        includeUncontrolled: true,
                    });

                for (
                    const client
                    of windowClients
                ) {
                    if (
                        client.url.startsWith(
                            self.location.origin
                        ) &&
                        "focus" in client
                    ) {
                        await client.focus();
                        return;
                    }
                }

                if ("openWindow" in clients) {
                    await clients.openWindow(
                        targetUrl
                    );
                }
            })()
        );
    }
);