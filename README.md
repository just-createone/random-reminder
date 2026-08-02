# 随机提醒器

随机提醒器是一个基于 FastAPI、SQLite 和 PWA 构建的个人提醒应用。

用户可以维护自己的提醒文本，系统每天随机生成提醒计划，并在指定时间发送浏览器推送或本地系统通知。

当前版本：`v0.1.3`

---

## 主要功能

- 创建、查看和删除提醒内容
- 设置提醒总开关
- 设置全天提醒或指定提醒时间范围
- 自动生成每日随机提醒计划
- 查看下一次提醒倒计时
- 自动跳过过期提醒
- Windows 本地系统通知
- 浏览器通知和 Web Push
- PWA 安装
- SQLite 数据持久化
- 数据库备份
- 数据库恢复
- 旧备份自动清理
- Docker 和 Docker Compose 部署
- AMD64 和 ARM64 镜像支持
- GitHub Actions 自动测试和镜像发布

---

## 技术栈

### 后端

- Python
- FastAPI
- SQLite
- Uvicorn
- PyWebPush

### 前端

- HTML
- CSS
- JavaScript
- Progressive Web App
- Service Worker

### 工程化

- Pytest
- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry

---

## 项目结构

```text
random-reminder/
├─ backend/
│  ├─ api/                  # API 路由
│  ├─ database/             # 数据库连接与初始化
│  ├─ domain/               # 领域模型
│  ├─ executor/             # 提醒计划执行器
│  ├─ maintenance/          # 数据库备份、恢复和清理
│  ├─ notification/         # 本地通知和 Web Push
│  ├─ repository/           # 数据访问层
│  ├─ config.py             # 项目配置
│  ├─ main.py               # FastAPI 应用入口
│  └─ run.py                # 统一启动入口
├─ frontend/
│  ├─ assets/               # 图标等静态资源
│  ├─ css/                  # 页面样式
│  ├─ js/                   # 前端逻辑
│  ├─ index.html            # 首页
│  ├─ reminders.html        # 提醒管理页面
│  ├─ settings.html         # 设置页面
│  ├─ manifest.json         # PWA 配置
│  └─ service-worker.js     # Service Worker
├─ tests/                   # 自动化测试
├─ data/                    # SQLite 数据库
├─ backups/                 # 数据库备份
├─ secrets/
│  └─ vapid/                # Web Push 密钥
├─ .github/
│  └─ workflows/            # GitHub Actions
├─ compose.yaml             # 本地 Docker 配置
├─ compose.release.yaml     # 正式镜像部署配置
├─ Dockerfile
├─ requirements.txt
└─ README.md
```

---

## 运行要求

本地运行需要：

- Python 3.14 或兼容版本
- Git
- Docker Desktop，可选
- Windows PowerShell 或 VSCode 终端

Docker 部署需要：

- Docker Desktop
- Docker Compose

---

## 本地 Python 运行

所有命令都应在项目根目录执行：

```text
D:\Project\随机提醒器\random-reminder
```

### 1. 进入项目目录

```powershell
cd "D:\Project\随机提醒器\random-reminder"
```

### 2. 创建虚拟环境

首次运行时执行：

```powershell
python -m venv .venv
```

已经存在 `.venv` 时，不需要重复创建。

### 3. 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

命令行前缀应类似：

```text
(.venv) PS D:\Project\随机提醒器\random-reminder>
```

### 4. 安装依赖

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. 启动应用

```powershell
python -m backend.run
```

默认访问地址：

```text
http://127.0.0.1:8000/
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/health
```

停止服务时，在终端按：

```text
Ctrl + C
```

---

## 本地 Docker 运行

运行 Docker 命令前，需要先启动 Docker Desktop。

### 构建并启动

```powershell
docker compose up --build -d
```

### 查看状态

```powershell
docker compose ps
```

正常状态应包含：

```text
healthy
```

### 查看日志

```powershell
docker compose logs --tail=100 app
```

持续查看日志：

```powershell
docker compose logs -f app
```

### 停止容器

```powershell
docker compose down
```

执行 `docker compose down` 不会删除宿主机中的数据库、备份和密钥文件。

---

## 正式镜像部署

正式镜像地址：

```text
ghcr.io/just-createone/random-reminder
```

当前版本镜像：

```text
ghcr.io/just-createone/random-reminder:0.1.3
```

### 1. 创建正式环境配置

复制环境变量示例：

```powershell
Copy-Item .env.release.example .env.release
```

打开：

```text
.env.release
```

根据实际环境修改配置。

`.env.release` 可能包含邮箱等部署信息，不应提交到 Git。

### 2. 创建数据目录

```powershell
New-Item -ItemType Directory -Force .\data
New-Item -ItemType Directory -Force .\backups
New-Item -ItemType Directory -Force .\secrets\vapid
```

### 3. 准备 VAPID 密钥

Web Push 使用的 VAPID 密钥应存放在：

```text
secrets/vapid/
```

正式容器会将该目录只读挂载到：

```text
/app/secrets/vapid
```

不要将 VAPID 私钥提交到公开仓库。

### 4. 检查 Compose 配置

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    config
```

重点确认：

- 镜像版本正确
- 数据库路径正确
- 备份目录正确
- VAPID 目录正确
- 端口正确
- 环境变量已经展开

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

### 7. 查看运行状态

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps
```

正常状态应包含：

```text
Up
healthy
```

### 8. 查看正式容器日志

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

### 9. 停止正式容器

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    down
```

---

## 环境变量

常用环境变量如下：

| 变量                                  | 作用                   | 示例                                           |
| ------------------------------------- | ---------------------- | ---------------------------------------------- |
| `RANDOM_REMINDER_ENV`                 | 运行环境               | `production`                                   |
| `RANDOM_REMINDER_DEBUG`               | 是否启用调试模式       | `false`                                        |
| `RANDOM_REMINDER_HOST`                | 服务监听地址           | `0.0.0.0`                                      |
| `RANDOM_REMINDER_PORT`                | 服务监听端口           | `8000`                                         |
| `RANDOM_REMINDER_LOG_LEVEL`           | 日志级别               | `INFO`                                         |
| `RANDOM_REMINDER_DB_PATH`             | SQLite 数据库路径      | `/app/data/random_reminder.db`                 |
| `RANDOM_REMINDER_BACKUP_DIR`          | 数据库备份目录         | `/app/backups`                                 |
| `RANDOM_REMINDER_BACKUP_KEEP_LATEST`  | 始终保留的最新备份数量 | `30`                                           |
| `RANDOM_REMINDER_BACKUP_MAX_AGE_DAYS` | 备份最大保存天数       | `90`                                           |
| `RANDOM_REMINDER_VAPID_DIR`           | VAPID 密钥目录         | `/app/secrets/vapid`                           |
| `VAPID_SUBJECT`                       | Web Push 联系信息      | `mailto:your-email@example.com`                |
| `RANDOM_REMINDER_IMAGE`               | 正式 Docker 镜像       | `ghcr.io/just-createone/random-reminder:0.1.3` |
| `RANDOM_REMINDER_HOST_PORT`           | 宿主机端口             | `8000`                                         |

环境变量示例文件：

```text
.env.example
.env.release.example
```

---

## 数据库备份

### 本地执行备份

```powershell
python -m backend.maintenance.backup_database
```

### 正式容器执行备份

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    exec app `
    python -m backend.maintenance.backup_database
```

备份文件默认保存在：

```text
backups/
```

正式容器中的对应目录为：

```text
/app/backups
```

备份完成后，程序会按照备份保留策略检查并清理旧备份。

---

## 旧备份清理

备份清理策略由以下环境变量控制：

```text
RANDOM_REMINDER_BACKUP_KEEP_LATEST
RANDOM_REMINDER_BACKUP_MAX_AGE_DAYS
```

默认正式配置：

```text
保留最新 30 份备份
最大保存时间 90 天
```

属于最新保留数量范围内的备份不会因为时间较长而被删除。

### 查看清理命令帮助

```powershell
python -m backend.maintenance.cleanup_backups --help
```

### 预览清理结果

`--dry-run` 只显示准备删除的文件，不会真正删除：

```powershell
python -m backend.maintenance.cleanup_backups --dry-run
```

### 正式执行清理

```powershell
python -m backend.maintenance.cleanup_backups
```

### 在正式容器中预览

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    exec app `
    python -m backend.maintenance.cleanup_backups `
    --dry-run
```

正式执行前，建议先运行一次 `--dry-run`。

---

## 数据库恢复

数据库恢复会覆盖目标数据库，属于高风险操作。

恢复前应：

1. 确认备份文件完整。
2. 停止正在使用目标数据库的应用。
3. 额外复制一份当前数据库。
4. 记录准备恢复的备份文件名。

### 查看恢复命令帮助

```powershell
python -m backend.maintenance.restore_database --help
```

### 本地恢复示例

先停止正在运行的本地应用，然后执行：

```powershell
python -m backend.maintenance.restore_database `
    .\backups\备份文件名.db
```

默认情况下，恢复程序会在覆盖当前数据库前创建一份安全备份。

### 正式容器恢复

先停止正式应用：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    stop app
```

使用一次性容器执行恢复：

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

恢复完成后重新启动：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

检查状态：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps
```

---

## 自动化测试

### 检查 Python 语法

```powershell
python -m compileall backend tests
```

### 运行全部测试

```powershell
python -m pytest -v
```

### 运行数据库备份测试

```powershell
python -m pytest tests/test_backup_database.py -v
```

### 运行数据库恢复测试

```powershell
python -m pytest tests/test_restore_database.py -v
```

### 运行备份清理测试

```powershell
python -m pytest tests/test_cleanup_backups.py -v
```

测试文件名称应以项目中的实际文件为准。

---

## 健康检查

### 浏览器访问

```text
http://127.0.0.1:8000/health
```

### PowerShell 检查

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 本地 Docker 检查

```powershell
docker compose ps
```

### 正式容器检查

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps
```

---

## 日志查看

### 本地 Docker 日志

```powershell
docker compose logs --tail=100 app
```

### 正式容器日志

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

### 持续查看正式日志

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    -f `
    app
```

停止持续日志查看时按：

```text
Ctrl + C
```

---

## 数据目录

以下目录保存在宿主机中：

```text
data/
backups/
secrets/vapid/
```

各目录作用：

| 目录             | 作用               |
| ---------------- | ------------------ |
| `data/`          | 保存 SQLite 数据库 |
| `backups/`       | 保存数据库备份     |
| `secrets/vapid/` | 保存 Web Push 密钥 |

Docker 容器被删除或重新创建后，这些宿主机目录中的数据仍然保留。

执行：

```powershell
docker compose down
```

不会删除这些目录中的数据。

---

## 安全说明

以下内容不应提交到公开仓库：

- `.env`
- `.env.release`
- SQLite 数据库文件
- 数据库备份文件
- VAPID 私钥
- 日志文件
- 包含真实邮箱或其他敏感信息的配置文件

提交代码前执行：

```powershell
git status
```

也可以检查文件是否被 Git 忽略：

```powershell
git check-ignore -v .env.release
git check-ignore -v .\data\random_reminder.db
git check-ignore -v .\backups\*.db
```

README 和示例配置中应使用：

```text
your-email@example.com
```

不要写入真实邮箱或私钥内容。

---

## Git 提交规范

完成一个功能或文档阶段后，依次执行：

```powershell
git status
git add .
git status
git commit -m "提交说明"
git push
git log --oneline -5
git status
```

网络不稳定时，可以使用本地代理推送：

```powershell
git -c http.proxy=http://127.0.0.1:7897 `
    -c http.version=HTTP/1.1 `
    push
```

最终工作区应显示：

```text
nothing to commit, working tree clean
```

---

## 自动化流程

项目使用 GitHub Actions 完成以下任务：

- Windows 环境自动测试
- Ubuntu 环境自动测试
- Python 代码检查
- AMD64 Docker 镜像构建
- ARM64 Docker 镜像构建
- 版本标签触发正式镜像发布
- 推送镜像到 GitHub Container Registry

版本标签示例：

```text
v0.1.3
```

正式镜像标签示例：

```text
ghcr.io/just-createone/random-reminder:0.1.3
ghcr.io/just-createone/random-reminder:0.1
ghcr.io/just-createone/random-reminder:latest
```

---

## 常见问题

### `requirements.txt` 找不到

出现：

```text
Could not open requirements file
```

通常是因为终端不在项目根目录。

先执行：

```powershell
cd "D:\Project\随机提醒器\random-reminder"
```

再执行：

```powershell
python -m pip install -r requirements.txt
```

### Docker Compose 没有显示容器

执行：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps -a
```

只有表头而没有容器时，说明容器尚未启动。

执行：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

### 容器启动失败

查看日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

### Docker 拉取镜像出现 `EOF`

检查网络和代理设置，然后重新执行：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    pull
```

### 数据库恢复提示文件被占用

先停止应用或容器：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    stop app
```

然后重新执行恢复命令。

---

## 当前版本

```text
v0.1.3
```

当前版本已经完成：

- 提醒内容管理
- 提醒时间范围设置
- 每日随机计划生成
- 下一次提醒倒计时
- Windows 本地通知
- 浏览器通知和 Web Push
- PWA 安装
- SQLite 数据持久化
- Docker 部署
- AMD64 和 ARM64 镜像
- GitHub Actions 自动化测试
- GHCR 正式镜像发布
- 数据库备份
- 数据库恢复
- 旧备份自动清理

---

## 后续计划

- 完善部署和升级文档
- 完善故障排查文档
- 验证全新环境安装流程
- 进行长期运行稳定性测试
- 优化移动端通知体验
- 完善产品商业化方案

## 项目文档

- [正式部署、升级和回滚指南](docs/DEPLOYMENT.md)
- [故障排查指南](docs/TROUBLESHOOTING.md)
- [MVP 验收清单](docs/ACCEPTANCE.md)

---


