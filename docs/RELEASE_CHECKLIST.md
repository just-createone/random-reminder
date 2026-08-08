# 随机提醒器版本发布检查清单

本文档用于规范随机提醒器每次正式版本发布流程，避免遗漏测试、备份、版本号、镜像和部署验证。

当前正式版本：`v0.1.4`

---

## 一、确定发布范围

发布前先明确：

- [ ] 本次版本解决的问题已经确定
- [ ] 不再临时增加无关功能
- [ ] 功能范围与版本目标一致
- [ ] 已知问题已经记录
- [ ] 阻塞性问题已经解决
- [ ] 发布说明已经准备

版本类型：

| 类型     | 示例            | 适用情况             |
| -------- | --------------- | -------------------- |
| 修复版本 | `0.1.4 → 0.1.5` | 修复问题、小幅优化   |
| 功能版本 | `0.1.4 → 0.2.0` | 增加一组新功能       |
| 正式版本 | `0.x.x → 1.0.0` | 达到正式商业发布标准 |

---

## 二、代码状态检查

确认位于项目根目录：

```powershell
Get-Location
```

检查 Git 状态：

```powershell
git status
```

发布前应显示：

```text
nothing to commit, working tree clean
```

检查最近提交：

```powershell
git log --oneline -5
```

确认：

- [ ] 所有功能已经提交
- [ ] 所有文档已经提交
- [ ] 没有临时测试文件
- [ ] 没有未解决的合并冲突
- [ ] 当前分支为 `master`
- [ ] 本地分支与远程分支一致

---

## 三、敏感信息检查

检查工作区：

```powershell
git status
```

检查关键文件是否被忽略：

```powershell
git check-ignore -v .env.release
git check-ignore -v .\data\random_reminder.db
git check-ignore -v .\backups\*.db
git check-ignore -v .\secrets\vapid\*
```

搜索文档中的敏感信息：

```powershell
$privateEmail = Read-Host "输入需要检查的私人邮箱"
$privateIdentifier = Read-Host "输入需要检查的私人编号"
$privateKeyToken = "private" + "_key"

git grep -n -I -F -e $privateEmail
git grep -n -I -F -e $privateIdentifier
git grep -n -I -F -e $privateKeyToken
git grep -n -I -E -e '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'
```

发布前确认：

- [ ] `.env.release` 未被 Git 跟踪
- [ ] SQLite 数据库未被 Git 跟踪
- [ ] 数据库备份未被 Git 跟踪
- [ ] VAPID 私钥未被 Git 跟踪
- [ ] 文档中没有真实邮箱
- [ ] 文档中没有密钥内容
- [ ] 日志文件未被提交
- [ ] Release 镜像本身不包含 `.env.release`、数据库或 VAPID 私钥
- [ ] 运行日志未输出 VAPID 私钥、Push auth key 或 Authorization Header

---

## 四、自动化测试

检查 Python 语法：

```powershell
python -m compileall backend tests
```

运行全部测试：

```powershell
python -m pytest -v
```

发布前确认：

- [ ] 所有测试通过
- [ ] 没有 `failed`
- [ ] 没有 `error`
- [ ] 没有测试收集错误
- [ ] 新增功能有对应测试
- [ ] Windows 测试通过
- [ ] Ubuntu 测试通过

---

## 五、数据库检查

发布前创建数据库备份。

本地执行：

```powershell
python -m backend.maintenance.backup_database
```

正式容器执行：

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

发布前确认：

- [ ] 已创建最新数据库备份
- [ ] 备份文件真实存在
- [ ] 备份文件能够打开
- [ ] SQLite 完整性检查通过
- [ ] 数据库恢复命令可用
- [ ] 旧备份清理预览正常

---

## 六、版本号更新

需要同步检查以下位置：

```text
backend/config.py
.env.release.example
.env.release
README.md
docs/DEPLOYMENT.md
docs/ACCEPTANCE.md
docs/PRODUCT_ROADMAP.md
```

其中：

```text
.env.release
```

只修改本地，不提交 Git。

版本号示例：

```python
VERSION = "0.1.4"
```

正式镜像示例：

```dotenv
RANDOM_REMINDER_IMAGE=ghcr.io/just-createone/random-reminder:0.1.4
```

发布前确认：

- [ ] 后端版本号正确
- [ ] 示例镜像版本正确
- [ ] 本地正式部署镜像版本正确
- [ ] README 当前版本正确
- [ ] 相关文档版本正确
- [ ] 没有残留旧版本号

搜索旧版本号：

```powershell
Select-String `
    -Path README.md,backend\*.py,.env.release.example,docs\*.md `
    -Pattern "0\.1\.4"
```

根据发布目标判断哪些位置需要更新。

---

## 七、Compose 配置检查

解析本地 Compose：

```powershell
docker compose config
```

解析正式 Compose：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    config
```

重点检查：

- [ ] 镜像版本正确
- [ ] 宿主机端口正确
- [ ] 容器内部端口正确
- [ ] 数据库目录正确
- [ ] 备份目录正确
- [ ] VAPID 目录正确
- [ ] 备份保留配置正确
- [ ] 没有未定义环境变量
- [ ] 没有 Compose 语法错误

---

## 八、本地 Docker 验证

重新构建：

```powershell
docker compose down
docker compose up --build -d
```

查看状态：

```powershell
docker compose ps
```

查看日志：

```powershell
docker compose logs --tail=100 app
```

检查健康接口：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

本地验证项目：

- [ ] 容器状态为 `healthy`
- [ ] 首页可以打开
- [ ] API 文档可以打开
- [ ] 提醒可以创建
- [ ] 提醒可以删除
- [ ] 设置可以保存
- [ ] 今日计划可以生成
- [ ] 数据重启后仍然存在
- [ ] 数据库备份可以创建
- [ ] 日志没有严重错误
- [ ] 容器运行 UID 不是 `0`
- [ ] `/app/data` 和 `/app/backups` 在非 root 用户下可写
- [ ] `/app/secrets/vapid` 正式挂载保持只读
- [ ] production OpenAPI 不显示 `/api/push/test-send`

---

## 九、稳定性检查

根据版本风险选择测试时长。

### 一小时快速测试

适用于：

- 文档更新
- 小型功能
- 小范围修复

检查：

- [ ] 容器持续运行
- [ ] 健康接口持续正常
- [ ] 重启次数为 `0`
- [ ] 内存没有持续异常增长
- [ ] 日志没有 `Traceback`

### 二十四小时测试

适用于：

- 执行器修改
- 通知修改
- 数据库修改
- Docker 部署修改
- 正式 MVP 发布

检查：

- [ ] 容器连续运行二十四小时
- [ ] 健康接口没有失败
- [ ] 重启次数为 `0`
- [ ] 提醒能够按计划触发
- [ ] 通知能够正常发送
- [ ] 数据没有丢失
- [ ] 日志没有严重异常

---

## 十、提交发布准备修改

先检查：

```powershell
git status
```

提交：

```powershell
git add .
git status
git commit -m "release: prepare version x.y.z"
```

推送：

```powershell
git push
```

网络失败时：

```powershell
git -c http.proxy=http://127.0.0.1:7897 `
    -c http.version=HTTP/1.1 `
    push
```

最后检查：

```powershell
git log --oneline -5
git status
```

确认工作区干净。

---

## 十一、创建版本标签

确认标签不存在：

```powershell
git tag --list vx.y.z
```

创建标签：

```powershell
git tag -a vx.y.z -m "Release vx.y.z"
```

检查标签：

```powershell
git show vx.y.z --stat
```

推送标签：

```powershell
git push origin vx.y.z
```

网络失败时：

```powershell
git -c http.proxy=http://127.0.0.1:7897 `
    -c http.version=HTTP/1.1 `
    push origin vx.y.z
```

确认：

- [ ] 标签指向正确提交
- [ ] 标签已经推送
- [ ] GitHub 可以看到版本标签

---

## 十二、GitHub Actions 检查

进入 GitHub 仓库：

```text
Actions
```

确认：

- [ ] Windows 测试通过
- [ ] Ubuntu 测试通过
- [ ] AMD64 镜像构建通过
- [ ] ARM64 镜像构建通过
- [ ] 镜像推送成功
- [ ] 发布工作流显示绿色

工作流失败时，不要继续正式部署。

---

## 十三、GHCR 镜像检查

进入：

```text
GitHub 仓库
→ Packages
→ random-reminder
```

确认出现：

```text
x.y.z
x.y
latest
```

正式镜像示例：

```text
ghcr.io/just-createone/random-reminder:x.y.z
```

确认：

- [ ] 完整版本标签存在
- [ ] 次版本标签存在
- [ ] `latest` 已更新
- [ ] 镜像支持 AMD64
- [ ] 镜像支持 ARM64
- [ ] `docker buildx imagetools inspect` 同时显示 `linux/amd64` 和 `linux/arm64`
- [ ] 镜像内包含 `/app/scripts/generate_vapid_keys.py`

---

## 十四、正式升级

升级前再次创建数据库备份。

拉取新镜像：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    pull
```

启动新版本：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    up -d
```

查看状态：

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

---

## 十五、正式部署验证

检查健康接口：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
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

检查页面和功能：

- [ ] 首页可以打开
- [ ] 版本号正确
- [ ] 原有提醒数据存在
- [ ] 设置数据存在
- [ ] 今日计划正常
- [ ] 提醒可以创建
- [ ] 提醒可以删除
- [ ] 通知可以触发
- [ ] 数据库备份可以创建
- [ ] 日志没有严重错误

---

## 十六、回滚准备

发布前记录旧版本：

```text
旧版本：
新版本：
数据库备份：
发布时间：
```

发生严重问题时：

1. 将 `.env.release` 镜像改回旧版本。
2. 拉取旧镜像。
3. 重新创建容器。
4. 检查应用状态。
5. 必要时恢复数据库备份。

回滚命令：

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

数据库没有发生不兼容变化时，不要随意恢复旧数据库。

---

## 十七、发布完成记录

每次发布后填写：

| 项目         | 内容 |
| ------------ | ---- |
| 版本号       |      |
| 发布日期     |      |
| Git 提交     |      |
| Git 标签     |      |
| Docker 镜像  |      |
| 数据库备份   |      |
| 自动化测试   |      |
| 稳定性测试   |      |
| 部署结果     |      |
| 已知问题     |      |
| 是否发生回滚 |      |

---

## 十八、发布完成标准

以下条件全部满足，版本才算发布完成：

- [ ] 代码和文档已经提交
- [ ] 工作区干净
- [ ] 全部测试通过
- [ ] 数据库备份完成
- [ ] 版本号一致
- [ ] Git 标签已经推送
- [ ] GitHub Actions 全部通过
- [ ] GHCR 镜像已经生成
- [ ] 正式容器状态为 `healthy`
- [ ] 正式功能验证通过
- [ ] 原有数据没有丢失
- [ ] 日志没有严重错误
- [ ] 回滚方案已经确认
