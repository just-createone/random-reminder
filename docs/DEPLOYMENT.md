# 随机提醒器部署指南

本文档记录随机提醒器的正式部署、版本升级、版本回滚、数据库备份和数据库恢复流程。

当前正式版本：`v0.1.3`

---

## 一、部署要求

正式部署需要：

- Docker Desktop
- Docker Compose
- Git
- Windows PowerShell
- 可访问 GitHub Container Registry 的网络环境

正式镜像地址：

```text
ghcr.io/just-createone/random-reminder
```

当前版本镜像：

```text
ghcr.io/just-createone/random-reminder:0.1.3
```

---

## 二、首次部署

### 1. 获取项目

```powershell
git clone https://github.com/just-createone/random-reminder.git
cd random-reminder
```

已经存在项目目录时，不需要重新克隆。

### 2. 创建正式环境配置

```powershell
Copy-Item `
    .env.release.example `
    .env.release
```

打开配置文件：

```powershell
code .env.release
```

示例配置：

```dotenv
RANDOM_REMINDER_IMAGE=ghcr.io/just-createone/random-reminder:0.1.3
RANDOM_REMINDER_HOST_PORT=8000
RANDOM_REMINDER_LOG_LEVEL=INFO

RANDOM_REMINDER_BACKUP_DIR=/app/backups
RANDOM_REMINDER_BACKUP_KEEP_LATEST=30
RANDOM_REMINDER_BACKUP_MAX_AGE_DAYS=90

VAPID_SUBJECT=mailto:your-email@example.com
```

`.env.release` 可能包含真实邮箱等部署信息，不应提交到 Git。

### 3. 创建持久化目录

```powershell
New-Item -ItemType Directory -Force .\data |
    Out-Null

New-Item -ItemType Directory -Force .\backups |
    Out-Null

New-Item -ItemType Directory -Force .\secrets\vapid |
    Out-Null
```

目录作用：

| 目录             | 作用               |
| ---------------- | ------------------ |
| `data/`          | 保存 SQLite 数据库 |
| `backups/`       | 保存数据库备份     |
| `secrets/vapid/` | 保存 Web Push 密钥 |

VAPID 私钥不能提交到公开仓库。

### 4. 检查 Compose 配置

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    config
```

重点确认：

- 镜像版本正确
- 宿主机端口正确
- 数据库目录为 `/app/data`
- 备份目录为 `/app/backups`
- VAPID 目录为 `/app/secrets/vapid`
- 备份保留配置正确

### 5. 拉取正式镜像

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    pull
```

### 6. 启动正式容器

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

### 7. 查看容器状态

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps -a
```

正常状态应包含：

```text
Up
healthy
```

### 8. 检查健康接口

```powershell
Invoke-RestMethod `
    http://127.0.0.1:8000/health
```

### 9. 打开应用

```text
http://127.0.0.1:8000/
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

---

## 三、查看正式容器日志

查看最近 100 行日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

持续查看日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    -f `
    app
```

停止持续查看时按：

```text
Ctrl + C
```

---

## 四、正式版本升级

以下示例表示从旧版本升级到 `0.1.3`。

### 1. 升级前创建数据库备份

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    exec app `
    python -m backend.maintenance.backup_database
```

查看最新备份：

```powershell
Get-ChildItem `
    .\backups\random_reminder_*.db |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 5
```

确认已经生成新备份后再继续。

### 2. 修改镜像版本

打开：

```powershell
code .env.release
```

修改：

```dotenv
RANDOM_REMINDER_IMAGE=ghcr.io/just-createone/random-reminder:0.1.3
```

### 3. 检查配置

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    config
```

确认输出中的镜像版本正确。

### 4. 拉取新镜像

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    pull
```

### 5. 使用新镜像重新创建容器

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

Docker Compose 会根据镜像变化重新创建应用容器。

### 6. 验证升级结果

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps
```

确认容器使用的镜像：

```powershell
docker inspect `
    random-reminder-release `
    --format "{{.Config.Image}}"
```

检查健康接口：

```powershell
Invoke-RestMethod `
    http://127.0.0.1:8000/health
```

检查日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

最后检查页面、提醒数据和通知功能。

---

## 五、版本回滚

版本回滚表示将应用镜像恢复到之前的版本。

应用镜像回滚和数据库恢复是两项独立操作。

### 1. 修改镜像版本

打开：

```powershell
code .env.release
```

将镜像改成需要回滚的版本，例如：

```dotenv
RANDOM_REMINDER_IMAGE=ghcr.io/just-createone/random-reminder:0.1.2
```

### 2. 拉取旧版本镜像

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    pull
```

### 3. 使用旧镜像重新创建容器

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

### 4. 检查回滚状态

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps
```

确认镜像：

```powershell
docker inspect `
    random-reminder-release `
    --format "{{.Config.Image}}"
```

检查日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

仅在数据库结构或数据出现问题时，才考虑恢复数据库备份。

---

## 六、数据库备份

### 创建正式数据库备份

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    exec app `
    python -m backend.maintenance.backup_database
```

备份默认保存在：

```text
backups/
```

容器内对应路径：

```text
/app/backups
```

### 查看备份文件

```powershell
Get-ChildItem `
    .\backups\random_reminder_*.db |
    Sort-Object LastWriteTime -Descending
```

### 预览旧备份清理

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    exec app `
    python -m backend.maintenance.cleanup_backups `
    --dry-run
```

`--dry-run` 不会删除文件。

---

## 七、数据库恢复

数据库恢复会覆盖当前数据库，属于高风险操作。

恢复前必须：

1. 确认备份文件存在。
2. 额外复制当前数据库。
3. 停止正式应用。
4. 记录准备恢复的备份文件名。
5. 恢复完成后检查数据和日志。

### 1. 手动复制当前数据库

```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Copy-Item `
    .\data\random_reminder.db `
    ".\backups\manual_before_restore_$timestamp.db"
```

### 2. 查看可用备份

```powershell
Get-ChildItem `
    .\backups\*.db |
    Sort-Object LastWriteTime -Descending
```

### 3. 停止正式应用

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    stop app
```

### 4. 使用一次性容器恢复

将下面的 `备份文件名.db` 替换为真实文件名：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    run `
    --rm `
    --no-deps `
    app `
    python -m backend.maintenance.restore_database `
    /app/backups/备份文件名.db
```

默认情况下，恢复命令会在覆盖当前数据库前创建安全备份。

### 5. 重新启动应用

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

### 6. 验证恢复结果

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps
```

检查健康接口：

```powershell
Invoke-RestMethod `
    http://127.0.0.1:8000/health
```

检查日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

最后在页面中确认提醒内容和设置是否已经恢复。

---

## 八、停止和重新启动

### 停止容器但保留容器记录

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    stop
```

### 重新启动

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    start
```

### 删除容器和网络

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    down
```

由于项目使用宿主机目录挂载，执行 `down` 不会删除：

```text
data/
backups/
secrets/vapid/
```

不要手动删除这些目录，除非已经确认数据不再需要。

---

## 九、常见问题

### 1. `docker compose ps` 只有表头

说明正式容器尚未启动或已经被删除。

执行：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

再查看：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps -a
```

### 2. 容器状态为 `Exited`

查看日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

重点查找：

```text
ERROR
Traceback
Database
Permission
ModuleNotFoundError
```

### 3. 容器一直显示 `health: starting`

等待约 20 至 30 秒后重新查看：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps
```

长时间未变为健康状态时查看日志。

### 4. 拉取镜像出现 `EOF`

检查 Docker Desktop 和代理设置。

网络恢复后重新执行：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    pull
```

### 5. 端口 8000 被占用

查看端口：

```powershell
netstat -ano | findstr :8000
```

也可以在 `.env.release` 中修改：

```dotenv
RANDOM_REMINDER_HOST_PORT=8001
```

修改后访问：

```text
http://127.0.0.1:8001/
```

### 6. 数据库恢复提示文件被占用

先停止正式应用：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    stop app
```

然后重新执行恢复命令。

---

## 十、部署检查清单

首次部署或升级后检查：

- [ ] Docker Desktop 正常运行
- [ ] `.env.release` 配置正确
- [ ] 镜像版本正确
- [ ] 容器状态为 `healthy`
- [ ] 健康接口正常
- [ ] 首页可以打开
- [ ] 提醒数据仍然存在
- [ ] 设置页面可以使用
- [ ] 浏览器通知可以使用
- [ ] 数据库备份可以创建
- [ ] 日志中没有异常
- [ ] `.env.release` 和私钥没有提交到 Git
