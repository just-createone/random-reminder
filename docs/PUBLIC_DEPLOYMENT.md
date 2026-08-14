# 公网 HTTPS 部署准备指南

本文适用于当前 `v0.3.0` 开发分支的小范围真实用户测试；它不是正式发布声明。

## 部署结构

```text
用户浏览器
    ↓ HTTPS（80 自动跳转到 443）
Caddy
    ↓ Docker 内部网络
Random Reminder 应用（不公开 8000 端口）
    ↓
SQLite 数据库、备份、VAPID 密钥
```

`compose.public.yaml` 使用 Caddy 自动申请和续期 HTTPS 证书。应用容器不发布 `8000` 端口，因此公网只能通过 Caddy 访问。

## 何时可以使用

开始前必须同时具备：

- 一台允许公开网站服务的服务器；
- 一个自己控制的域名；
- 域名 A（以及需要时的 AAAA）记录已指向该服务器；
- 防火墙和云安全组只允许 TCP `80`、TCP `443`，以及 UDP `443`；
- `data/`、`backups/`、`secrets/vapid/` 已准备为持久化目录；
- 已生成并安全保管 VAPID 密钥。

当前免费上海服务器只用于私有部署和运维学习。中国大陆面向公众提供网站服务需要先完成相应备案；在未完成前，不应把它用于公开用户测试。

## 首次配置

在未来选择的公网服务器中，从项目根目录执行：

```bash
cp .env.public.example .env.public
```

然后只在服务器本机编辑 `.env.public`：

- `APP_DOMAIN`：你的实际域名，例如 `app.example.com`；
- `CADDY_EMAIL`：可接收证书通知的邮箱；
- `VAPID_SUBJECT`：Web Push 使用的联系地址。

`.env.public`、`caddy/data/`、`caddy/config/` 和 `secrets/` 都不能提交到 Git。Caddy 的数据目录保存 HTTPS 证书及其私钥，必须在服务器上持久保留。

## 启动与验证

在域名解析生效、端口开放后：

```bash
sudo docker compose --env-file .env.public -f compose.public.yaml up --build -d
sudo docker compose --env-file .env.public -f compose.public.yaml ps
```

浏览器访问 `https://你的域名/health`。预期返回 `200`，并且地址栏显示有效 HTTPS 连接。再用无痕窗口完成注册、登录、退出、数据隔离和 Web Push 验收。

不要开放 `8000` 端口；不要用裸 IP 或纯 HTTP 验收登录功能。登录会话在生产环境要求 HTTPS，PWA 与 Web Push 也依赖 HTTPS。
