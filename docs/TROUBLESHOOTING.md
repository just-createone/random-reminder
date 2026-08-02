# 随机提醒器故障排查指南

本文档整理随机提醒器在本地开发、Docker 部署、数据库维护、通知和 PWA 使用过程中可能遇到的问题。

当前版本：`v0.1.3`

---

## 一、终端目录错误

### 问题表现

执行命令时出现：

```text
Could not open requirements file
No such file or directory
```

或者命令行位于：

```text
PS C:\Windows\System32>
```

### 原因

终端当前目录不是项目根目录。

### 解决方法

进入项目目录：

```powershell
cd "D:\Project\随机提醒器\random-reminder"
```

确认位置：

```powershell
Get-Location
```

预期：

```text
D:\Project\随机提醒器\random-reminder
```

检查项目文件：

```powershell
Test-Path .\requirements.txt
Test-Path .\backend
Test-Path .\compose.yaml
```

正常应返回：

```text
True
```

---

## 二、虚拟环境问题

### 1. 虚拟环境没有激活

激活项目虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

成功后命令行应类似：

```text
(.venv) PS D:\Project\随机提醒器\random-reminder>
```

### 2. PowerShell 禁止执行脚本

可能出现：

```text
running scripts is disabled on this system
```

在当前 PowerShell 会话中临时允许：

```powershell
Set-ExecutionPolicy `
    -Scope Process `
    -ExecutionPolicy Bypass
```

然后重新激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 虚拟环境位于错误目录

不要在以下目录创建项目虚拟环境：

```text
C:\Windows\System32
```

项目虚拟环境应位于：

```text
D:\Project\随机提醒器\random-reminder\.venv
```

检查：

```powershell
Test-Path .\.venv\Scripts\Activate.ps1
```

---

## 三、Python 依赖问题

### 问题表现

出现：

```text
ModuleNotFoundError
ImportError
```

### 解决方法

确认虚拟环境已经激活，然后执行：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

确认当前 Python 路径：

```powershell
python -c "import sys; print(sys.executable)"
```

输出路径应包含：

```text
random-reminder\.venv
```

---

## 四、应用无法启动

### 1. 找不到模块

出现：

```text
Could not import module
ModuleNotFoundError: No module named 'backend'
```

确认当前目录是项目根目录，然后使用统一启动命令：

```powershell
python -m backend.run
```

不要在项目根目录外直接运行后端文件。

### 2. 端口被占用

出现：

```text
Address already in use
Only one usage of each socket address
```

检查端口：

```powershell
netstat -ano | findstr :8000
```

根据最后一列的进程编号查看进程：

```powershell
tasklist | findstr 进程编号
```

确认可以关闭后执行：

```powershell
taskkill /PID 进程编号 /F
```

也可以修改应用端口。

### 3. 查看本地启动日志

```powershell
python -m backend.run
```

重点检查：

```text
ERROR
Traceback
ModuleNotFoundError
Database
Permission
```

---

## 五、健康检查失败

### 检查接口

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

浏览器也可以访问：

```text
http://127.0.0.1:8000/health
```

连接失败时依次确认：

1. 应用或容器是否已经启动。
2. 端口是否为 `8000`。
3. 容器状态是否为健康。
4. 后端日志中是否存在异常。

---

## 六、Docker Desktop 问题

### 1. Docker 命令无法连接

出现：

```text
Cannot connect to the Docker daemon
```

处理步骤：

1. 启动 Docker Desktop。
2. 等待 Docker Desktop 显示运行正常。
3. 检查版本：

```powershell
docker version
docker compose version
```

4. 重新执行 Docker 命令。

### 2. Docker 拉取镜像出现 EOF

出现：

```text
EOF
unexpected EOF
failed to resolve source metadata
```

处理步骤：

1. 检查网络连接。
2. 检查 Clash Verge 是否正常运行。
3. 必要时临时切换到全局模式。
4. 检查 Docker Desktop 代理：

```text
http://127.0.0.1:7897
```

5. 重新执行：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    pull
```

---

## 七、Docker Compose 没有显示容器

### 问题表现

执行：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps
```

只有表头，没有容器。

### 原因

正式容器尚未启动，或者已经执行过 `down`。

### 解决方法

启动：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

查看全部状态：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps -a
```

---

## 八、容器状态异常

### 1. 状态为 `health: starting`

应用刚启动时属于正常现象。

等待约 20 至 30 秒，再执行：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps
```

### 2. 状态为 `unhealthy`

查看日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

检查健康接口：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 3. 状态为 `Exited`

查看退出日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=200 `
    app
```

重点检查：

```text
Traceback
PermissionError
ModuleNotFoundError
Database
VAPID
```

---

## 九、Compose 环境变量没有生效

查看最终解析结果：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    config
```

正式配置应包含类似内容：

```text
RANDOM_REMINDER_BACKUP_DIR: /app/backups
RANDOM_REMINDER_BACKUP_KEEP_LATEST: "30"
RANDOM_REMINDER_BACKUP_MAX_AGE_DAYS: "90"
RANDOM_REMINDER_DB_PATH: /app/data/random_reminder.db
```

检查 `.env.release`：

```powershell
Get-Content .env.release
```

注意：

- 变量名必须完全一致。
- 等号两边不要添加多余空格。
- 修改配置后需要重新创建容器。

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

---

## 十、镜像版本不正确

确认容器实际使用的镜像：

```powershell
docker inspect `
    random-reminder-release `
    --format "{{.Config.Image}}"
```

预期类似：

```text
ghcr.io/just-createone/random-reminder:0.1.3
```

版本不正确时：

1. 修改 `.env.release` 中的镜像标签。
2. 检查 Compose 配置。
3. 拉取镜像。
4. 重新创建容器。

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    pull

docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

---

## 十一、数据库文件被占用

### 问题表现

恢复数据库时出现：

```text
PermissionError
目标数据库正在被其他程序使用
```

### 原因

应用或容器仍然连接着 SQLite 数据库。

### 解决方法

停止正式应用：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    stop app
```

确认容器已停止：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps -a
```

然后再执行恢复操作。

---

## 十二、数据库备份失败

### 查看备份目录

```powershell
Test-Path .\backups
Get-ChildItem .\backups
```

目录不存在时创建：

```powershell
New-Item `
    -ItemType Directory `
    -Force `
    .\backups |
    Out-Null
```

### 本地执行备份

```powershell
python -m backend.maintenance.backup_database
```

### 容器执行备份

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    exec app `
    python -m backend.maintenance.backup_database
```

检查日志中是否包含：

```text
Database backup failed
Backup cleanup failed
PermissionError
```

---

## 十三、旧备份清理异常

先使用预览模式：

```powershell
python -m backend.maintenance.cleanup_backups --dry-run
```

正式容器预览：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    exec app `
    python -m backend.maintenance.cleanup_backups `
    --dry-run
```

检查当前配置：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    config
```

确认包含：

```text
RANDOM_REMINDER_BACKUP_KEEP_LATEST
RANDOM_REMINDER_BACKUP_MAX_AGE_DAYS
```

不确定清理结果时，不要直接执行正式删除。

---

## 十四、数据库恢复失败

恢复前检查备份是否存在：

```powershell
Test-Path .\backups\备份文件名.db
```

查看可用备份：

```powershell
Get-ChildItem .\backups\*.db |
    Sort-Object LastWriteTime -Descending
```

检查备份完整性：

```powershell
@'
import sqlite3

database_path = "backups/备份文件名.db"

connection = sqlite3.connect(database_path)

result = connection.execute(
    "PRAGMA integrity_check"
).fetchone()[0]

print(result)

connection.close()
'@ | python -
```

预期：

```text
ok
```

备份损坏时，不要继续覆盖当前数据库。

---

## 十五、浏览器通知没有出现

依次检查：

1. 浏览器是否允许该网站发送通知。
2. 系统通知权限是否开启。
3. 浏览器是否支持 Service Worker 和 Push API。
4. PWA 是否使用正确地址打开。
5. Web Push 订阅是否成功保存。
6. VAPID 密钥是否存在。

检查浏览器通知权限：

```javascript
Notification.permission;
```

正常允许状态：

```text
granted
```

权限为 `denied` 时，需要在浏览器的网站权限设置中重新允许通知。

---

## 十六、VAPID 密钥问题

检查密钥目录：

```powershell
Get-ChildItem .\secrets\vapid -Force
```

检查正式 Compose 挂载：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    config
```

容器中的密钥目录应为：

```text
/app/secrets/vapid
```

宿主机目录应为：

```text
secrets/vapid/
```

不要将私钥内容复制到 README、日志或 Git 仓库中。

检查是否被 Git 忽略：

```powershell
git check-ignore -v .\secrets\vapid\*
```

---

## 十七、PWA 无法安装

检查以下文件是否可以访问：

```text
http://127.0.0.1:8000/manifest.json
http://127.0.0.1:8000/service-worker.js
```

检查图标：

```text
frontend/assets/icons/icon-192.png
frontend/assets/icons/icon-512.png
```

浏览器开发者工具中检查：

```text
Application
→ Manifest
→ Service Workers
```

修改 Service Worker 后，旧缓存可能仍然存在。

可以执行：

```text
Application
→ Storage
→ Clear site data
```

然后刷新页面。

---

## 十八、页面数据没有自动更新

检查浏览器开发者工具：

```text
F12
→ Console
```

查看是否存在 JavaScript 错误。

再检查：

```text
F12
→ Network
```

确认 API 请求：

- 状态码是否为 `200`
- 是否出现 `404`
- 是否出现 `500`
- 请求地址是否正确

后端同时查看日志：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=100 `
    app
```

---

## 十九、Git 推送失败

### 普通推送

```powershell
git push
```

### 使用本地代理

```powershell
git -c http.proxy=http://127.0.0.1:7897 `
    -c http.version=HTTP/1.1 `
    push
```

推送标签：

```powershell
git -c http.proxy=http://127.0.0.1:7897 `
    -c http.version=HTTP/1.1 `
    push origin v0.1.3
```

检查远程：

```powershell
git remote -v
```

---

## 二十、测试出现导入错误

### 问题表现

```text
ImportError
cannot import name
```

先确认目标名称是否存在：

```powershell
Select-String `
    -Path backend\config.py `
    -Pattern "目标配置名称"
```

检查模块能否直接导入：

```powershell
python -c "from backend.config import VERSION; print(VERSION)"
```

清除 Python 缓存：

```powershell
Get-ChildItem `
    -Path . `
    -Directory `
    -Filter __pycache__ `
    -Recurse |
    Remove-Item `
        -Recurse `
        -Force
```

重新运行测试：

```powershell
python -m pytest -v
```

---

## 二十一、查看完整诊断信息

出现未知故障时，依次收集：

```powershell
Get-Location

python --version

python -c "import sys; print(sys.executable)"

docker version

docker compose version

git status

docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    ps -a

docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    logs `
    --tail=200 `
    app
```

同时记录：

- 执行的完整命令
- 完整错误信息
- 错误发生前做过的操作
- 当前运行方式
- 当前镜像版本
- 容器状态

不要只提供错误信息的最后一行。

---

## 二十二、安全检查

提交前检查：

```powershell
git status
```

检查敏感文件是否被忽略：

```powershell
git check-ignore -v .env.release
git check-ignore -v .\data\random_reminder.db
git check-ignore -v .\backups\*.db
git check-ignore -v .\secrets\vapid\*
```

搜索敏感信息：

```powershell
Select-String `
    -Path README.md,docs\*.md `
    -Pattern "qq\.com|BEGIN PRIVATE KEY|private_key"
```

README 和文档中的邮箱示例应使用：

```text
your-email@example.com
```
