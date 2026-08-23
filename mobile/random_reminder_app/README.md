# 随机提醒器 Flutter Android MVP

该应用复用仓库现有 FastAPI 账号、提醒、设置和今日计划 API，不修改 Web/PWA 的路由或 Web Push 协议。

## 已实现

- 注册、登录、会话恢复和退出登录；
- 会话令牌使用 Android Keystore / iOS Keychain 支持的安全存储；
- 提醒的新增、查看、编辑、启停和删除；
- 随机提醒设置查看与保存；
- 今日计划查看、生成和显式重新生成；
- 用户主动授权后，把未来的 pending 计划排程为本地通知；
- Android 13+ 通知权限和 Android 14+ 精确闹钟权限请求；
- 精确闹钟不可用时自动退回允许空闲模式的非精确排程；
- 重启后恢复已排程通知所需的 Receiver；
- Dart 业务层保持平台无关，后续可生成 iOS runner 复用。

## 工具版本

- Flutter 3.44.6 stable
- Dart 3.12.2
- Android minSdk 24（Flutter 3.44 默认值）
- Java 17 bytecode

## 运行

默认连接公开 HTTPS 服务：

```powershell
flutter run
```

连接 Android 模拟器上的本机后端：

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Release 只允许 HTTPS；Debug Manifest 才允许本机明文 HTTP。`API_BASE_URL` 会拒绝远程 HTTP、URL 内嵌凭据、查询参数和片段。

## 验证

```powershell
flutter pub get
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
flutter build apk --debug
```

项目位于中文路径时，Flutter 3.44.6 的 analysis server 可能错误计算 LSP 消息长度。可以从指向仓库的纯 ASCII 目录联接运行 `flutter analyze`；这不需要复制项目。

## 当前通知边界

Android 原生应用不能直接提交浏览器 Push API 的 endpoint/p256dh/auth。MVP 因此采用本地排程：App 打开并同步到今日计划后，Android 负责在相应时间显示通知。它不会在 App 从未同步的情况下自动生成下一天计划。

后续若需要无需打开 App 的跨日、跨设备可靠触达，应新增独立的移动设备注册表和 FCM/APNs 服务端通道，不能把 FCM token 写入现有 Web Push 订阅表。

## 发布注意事项

- Release 签名没有写入仓库，也没有使用 debug key；发布方需通过本机或 CI 的安全变量配置签名。
- 不要把账号、密码、Cookie、服务端私钥或平台推送凭据写入 `--dart-define`、源码或日志。
- 部分 Android 厂商会限制后台闹钟，真实设备仍需执行锁屏、重启、省电模式和权限撤销测试。
