# 随机提醒器开发与贡献规范

本文档用于规范随机提醒器的功能开发、测试、文档维护、Git 提交和版本发布流程。

当前项目版本：`v0.1.4`

---

## 一、开发原则

项目开发遵守以下原则：

1. 先保证提醒可靠，再增加功能。
2. 数据安全优先于界面效果。
3. 移动端体验优先。
4. 每个阶段只解决一组明确问题。
5. 新功能必须对应真实需求。
6. 不为了展示技术而增加复杂架构。
7. 重要功能必须增加自动化测试。
8. 数据库修改必须考虑备份和恢复。
9. 每个完整阶段结束后必须提交 Git。
10. 发布新版本前必须完成回归测试。

---

## 二、项目目录

```text
random-reminder/
├─ backend/                 # 后端程序
│  ├─ api/                  # API 路由
│  ├─ database/             # 数据库初始化和连接
│  ├─ domain/               # 领域模型
│  ├─ executor/             # 提醒执行器
│  ├─ maintenance/          # 数据库维护命令
│  ├─ notification/         # 通知服务
│  ├─ repository/           # 数据访问层
│  ├─ config.py             # 配置
│  ├─ main.py               # FastAPI 应用
│  └─ run.py                # 统一启动入口
├─ frontend/                # 前端页面和 PWA
├─ scripts/                 # 部署和维护辅助脚本
├─ tests/                   # 自动化测试
├─ docs/                    # 项目文档
├─ data/                    # 本地数据库
├─ backups/                 # 数据库备份
├─ secrets/                 # 本地密钥
├─ compose.yaml             # 本地 Docker 配置
├─ compose.release.yaml     # 正式部署配置
├─ Dockerfile
├─ requirements.txt
└─ README.md
```

---

## 三、开发环境

推荐环境：

- Windows 11
- Python 3.14 或项目当前兼容版本
- VSCode
- PowerShell
- Git
- Docker Desktop
- Docker Compose

所有开发命令均在项目根目录执行。

进入项目：

```powershell
cd "D:\Project\随机提醒器\random-reminder"
```

---

## 四、Python 虚拟环境

### 首次创建

```powershell
python -m venv .venv
```

### 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

激活后命令行应包含：

```text
(.venv)
```

### 安装依赖

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

已有 `.venv` 时不要重复创建。

---

## 五、本地启动

统一使用：

```powershell
python -m backend.run
```

默认地址：

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

不要将多个启动方式混合使用。

---

## 六、功能开发流程

每个功能按照以下顺序完成：

```text
明确需求
→ 确定影响范围
→ 修改代码
→ 增加测试
→ 运行单项测试
→ 运行全部测试
→ 手动验证
→ 更新文档
→ Git 提交
```

开发前应明确：

- 要解决的问题是什么
- 涉及哪些文件
- 是否修改数据库
- 是否修改 API
- 是否影响通知
- 是否影响 Docker
- 是否需要增加环境变量
- 是否需要增加测试

---

## 七、代码修改原则

### 后端

- API 路由放在 `backend/api/`
- 数据库访问放在 `backend/repository/`
- 数据模型放在 `backend/domain/`
- 通知逻辑放在 `backend/notification/`
- 后台执行逻辑放在 `backend/executor/`
- 数据库维护命令放在 `backend/maintenance/`
- 配置统一放在 `backend/config.py`

不要在 API 路由中直接堆积大量 SQL 或复杂业务逻辑。

### 前端

- HTML 页面放在 `frontend/`
- 样式放在 `frontend/css/`
- JavaScript 放在 `frontend/js/`
- 通用消息提示放在统一模块
- 确认框使用自定义弹窗
- 修改 PWA 缓存时注意 Service Worker 更新

### 配置

新增环境变量时，应同步检查：

```text
backend/config.py
.env.example
.env.release.example
compose.yaml
compose.release.yaml
README.md
docs/DEPLOYMENT.md
```

本机 `.env.release` 可以修改，但不能提交。

---

## 八、测试规范

### 检查 Python 语法

```powershell
python -m compileall backend tests
```

### 运行全部测试

```powershell
python -m pytest -v
```

### 运行单个测试文件

```powershell
python -m pytest tests/test_文件名.py -v
```

### 运行单个测试

```powershell
python -m pytest `
    tests/test_文件名.py::test_测试名称 `
    -v
```

提交业务代码前必须确认：

- 没有 `failed`
- 没有 `error`
- 没有测试收集错误
- 新功能有对应测试
- 原有测试仍然通过

只修改 Markdown 文档时，可以不运行全部测试，但必须执行：

```powershell
git diff --check
```

---

## 九、数据库修改规范

修改数据库相关代码前必须考虑：

- 是否影响已有数据库
- 是否需要迁移
- 是否会丢失数据
- 是否需要升级数据库结构
- 旧版本能否读取新数据库
- 是否需要备份
- 是否需要恢复测试

创建备份：

```powershell
python -m backend.maintenance.backup_database
```

正式容器备份：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    exec app `
    python -m backend.maintenance.backup_database
```

恢复数据库前必须停止正在使用目标数据库的应用。

---

## 十、Docker 验证

修改以下内容后需要重新验证 Docker：

- `Dockerfile`
- `compose.yaml`
- `compose.release.yaml`
- 环境变量
- 启动入口
- 数据目录
- 备份目录
- VAPID 密钥目录

检查配置：

```powershell
docker compose config
```

检查正式配置：

```powershell
docker compose `
    --env-file .env.release `
    -f compose.release.yaml `
    config
```

本地重新构建：

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

修改 Dockerfile 或正式部署配置后，还应确认：

- 容器运行 UID 不是 `0`
- `/app/data` 和 `/app/backups` 在非 root 用户下可写
- `/app/secrets/vapid` 在正式运行时保持只读
- VAPID 密钥生成脚本可以在一次性容器中运行
- production OpenAPI 不展示测试推送接口

---

## 十一、稳定性测试规范

以下修改需要考虑稳定性测试：

- 提醒执行器
- 通知发送
- 数据库连接
- 后台任务
- Docker 启动
- 健康检查
- 数据备份和恢复

测试级别：

| 测试           | 适用范围                       |
| -------------- | ------------------------------ |
| 手动快速验证   | 小型文档或界面修改             |
| 一小时测试     | 小型功能和修复                 |
| 二十四小时测试 | 执行器、通知、数据库和正式发布 |
| 七天测试       | 公开测试或长期运行验证         |

稳定性测试期间不要：

- 停止容器
- 重启 Docker Desktop
- 让电脑睡眠
- 修改测试数据库
- 修改测试环境代码
- 中断监控终端

---

## 十二、文档维护规范

新增或修改功能后，应同步检查：

- `README.md`
- `CHANGELOG.md`
- `docs/DEPLOYMENT.md`
- `docs/TROUBLESHOOTING.md`
- `docs/ACCEPTANCE.md`
- `docs/RELEASE_CHECKLIST.md`

检查 Markdown：

```powershell
git diff --check
```

检查敏感信息：

```powershell
$privateEmail = Read-Host "输入需要检查的私人邮箱"
$privateIdentifier = Read-Host "输入需要检查的私人编号"
$privateKeyToken = "private" + "_key"

git grep -n -I -F -e $privateEmail
git grep -n -I -F -e $privateIdentifier
git grep -n -I -F -e $privateKeyToken
git grep -n -I -E -e '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'
```

文档中不要包含：

- 真实邮箱
- 私钥
- 数据库内容
- 用户个人资料
- 账号密码

示例邮箱使用：

```text
your-email@example.com
```

---

## 十三、Git 操作流程

完成一个阶段后，依次执行：

```powershell
git status
git add .
git status
git commit -m "提交说明"
git push
git log --oneline -5
git status
```

第一次 `git status` 用于确认修改范围。

第二次 `git status` 用于确认暂存内容。

最后一次 `git status` 应显示：

```text
nothing to commit, working tree clean
```

网络失败时：

```powershell
git -c http.proxy=http://127.0.0.1:7897 `
    -c http.version=HTTP/1.1 `
    push
```

---

## 十四、提交信息规范

推荐格式：

```text
类型: 简短说明
```

常用类型：

| 类型       | 用途         |
| ---------- | ------------ |
| `feat`     | 新功能       |
| `fix`      | 修复问题     |
| `docs`     | 文档更新     |
| `test`     | 测试更新     |
| `refactor` | 代码重构     |
| `chore`    | 工程和维护   |
| `release`  | 版本发布准备 |

示例：

```text
feat: add reminder editing
fix: prevent overdue notifications
docs: add deployment guide
test: add backup cleanup tests
release: prepare version 0.2.0
```

一次提交应尽量只包含一类相关修改。

---

## 十五、分支规范

当前项目主要使用：

```text
master
```

小型个人开发可以直接在 `master` 上按阶段提交。

较大功能建议创建功能分支：

```powershell
git switch -c feature/reminder-editing
```

完成后合并回 `master`。

分支名称示例：

```text
feature/reminder-editing
fix/notification-timeout
docs/user-guide
release/0.2.0
```

不要在稳定性测试目录中进行功能开发或 Git 提交。

---

## 十六、版本发布流程

发布前必须完成：

1. 功能开发完成。
2. 自动化测试通过。
3. 数据库备份完成。
4. 稳定性测试完成。
5. 文档更新完成。
6. 版本号更新完成。
7. Git 工作区干净。
8. 发布准备提交完成。
9. 创建 Git 标签。
10. 推送 Git 标签。
11. GitHub Actions 通过。
12. GHCR 镜像发布成功。
13. 正式容器升级完成。
14. 正式功能验证通过。

详细流程参考：

```text
docs/RELEASE_CHECKLIST.md
```

---

## 十七、安全要求

以下文件和内容不能提交：

```text
.env
.env.release
data/*.db
backups/*.db
secrets/vapid/*
*.log
```

提交前检查：

```powershell
git status
```

检查忽略规则：

```powershell
git check-ignore -v .env.release
git check-ignore -v .\data\random_reminder.db
git check-ignore -v .\backups\*.db
git check-ignore -v .\secrets\vapid\*
```

禁止：

- 将私钥写进代码
- 将真实邮箱写进公开文档
- 将数据库上传到公开仓库
- 将用户数据用于测试样例
- 在日志中输出完整密钥

---

## 十八、问题处理流程

发现问题后依次记录：

```text
问题表现
→ 完整错误信息
→ 复现步骤
→ 影响范围
→ 根本原因
→ 修复方案
→ 自动化测试
→ 手动验证
→ 文档更新
→ Git 提交
```

提供错误信息时不要只复制最后一行，应包括：

- 执行的命令
- 完整 Traceback
- 当前目录
- Python 版本
- 容器状态
- 镜像版本
- 修改前做过的操作

---

## 十九、功能完成标准

一个功能只有满足以下条件才算完成：

- [ ] 需求已经实现
- [ ] 核心路径可以使用
- [ ] 异常情况有明确处理
- [ ] 自动化测试通过
- [ ] 全部回归测试通过
- [ ] 手动验证通过
- [ ] 文档已经更新
- [ ] 敏感信息检查通过
- [ ] Git 已经提交
- [ ] 远程仓库已经推送

---

## 二十、当前开发重点

当前阶段重点：

```text
完成 v0.1.4 发布准备
→ 完成 PWA 独立窗口最终验收
→ 完成 Git 完整历史敏感信息检查
→ 启动首批真实用户测试
→ 根据反馈决定 v0.2.0 功能范围
```

当前不优先开发：

- 用户账号系统
- 在线支付
- 云端同步
- 大型管理后台
- 复杂团队协作

这些功能应在真实用户测试后决定。
