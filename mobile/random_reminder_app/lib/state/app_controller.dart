import 'package:flutter/foundation.dart';

import '../models/models.dart';
import '../services/api_client.dart';
import '../services/local_notification_service.dart';

enum AppPhase { booting, signedOut, signedIn, startupError }

class AppController extends ChangeNotifier {
  factory AppController({
    required ReminderApi api,
    required DeviceNotificationService notifications,
  }) => AppController._(api, notifications);

  AppController._(this._api, this._notifications);

  final ReminderApi _api;
  final DeviceNotificationService _notifications;

  AppPhase phase = AppPhase.booting;
  AppUser? user;
  List<Reminder> reminders = const <Reminder>[];
  List<DailySchedule> schedules = const <DailySchedule>[];
  ReminderSettings? settings;
  bool busy = false;
  bool refreshing = false;
  bool notificationsEnabled = false;
  int scheduledNotificationCount = 0;
  String? errorMessage;
  String? noticeMessage;

  Future<void> initialize() async {
    phase = AppPhase.booting;
    notifyListeners();
    try {
      await _notifications.initialize();
      notificationsEnabled = (await _notifications.preference()).enabled;
      user = await _api.restoreSession();
      if (user == null) {
        phase = AppPhase.signedOut;
      } else {
        phase = AppPhase.signedIn;
        await _refreshData(syncNotifications: notificationsEnabled);
      }
    } catch (error) {
      errorMessage = _messageFor(error);
      phase = AppPhase.startupError;
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) =>
      _authenticate(() => _api.login(email, password));

  Future<bool> register(
    String email,
    String password, {
    String timeZone = 'Asia/Shanghai',
  }) => _authenticate(() => _api.register(email, password, timeZone));

  Future<bool> _authenticate(Future<AppUser> Function() action) =>
      _run(() async {
        user = await action();
        phase = AppPhase.signedIn;
        await _refreshData(syncNotifications: notificationsEnabled);
      }, successMessage: '登录成功');

  Future<void> logout() async {
    busy = true;
    notifyListeners();
    try {
      await _api.logout();
    } catch (_) {
      // Local sign-out must still complete when the network is unavailable.
    } finally {
      await _notifications.disableAndCancel();
      user = null;
      settings = null;
      reminders = const <Reminder>[];
      schedules = const <DailySchedule>[];
      notificationsEnabled = false;
      scheduledNotificationCount = 0;
      phase = AppPhase.signedOut;
      busy = false;
      notifyListeners();
    }
  }

  Future<bool> deleteAccount() => _run(() async {
    await _api.deleteAccount();
    await _notifications.disableAndCancel();
    user = null;
    settings = null;
    reminders = const <Reminder>[];
    schedules = const <DailySchedule>[];
    notificationsEnabled = false;
    scheduledNotificationCount = 0;
    phase = AppPhase.signedOut;
  }, successMessage: '账号及全部数据已永久删除');

  Future<void> refresh() async {
    refreshing = true;
    errorMessage = null;
    notifyListeners();
    try {
      await _refreshData(syncNotifications: notificationsEnabled);
    } catch (error) {
      await _handleError(error);
    } finally {
      refreshing = false;
      notifyListeners();
    }
  }

  Future<void> _refreshData({required bool syncNotifications}) async {
    final results = await Future.wait<Object>(<Future<Object>>[
      _api.getReminders(),
      _api.getSettings(),
      _api.getTodaySchedules(),
    ]);
    reminders = results[0] as List<Reminder>;
    settings = results[1] as ReminderSettings;
    schedules = results[2] as List<DailySchedule>;
    if (syncNotifications && user != null) {
      final result = await _notifications.sync(schedules, user!.timeZone);
      scheduledNotificationCount = result.scheduledCount;
    }
  }

  Future<bool> createReminder(String content) => _run(() async {
    final reminder = await _api.createReminder(content.trim());
    reminders = <Reminder>[reminder, ...reminders];
  }, successMessage: '提醒已添加；今日已有计划不会自动改变');

  Future<bool> updateReminder(int id, String content) => _run(() async {
    final updated = await _api.updateReminder(id, content.trim());
    _replaceReminder(updated);
  }, successMessage: '提醒已保存；今日已有计划不会自动改变');

  Future<bool> setReminderEnabled(int id, bool enabled) => _run(() async {
    final updated = await _api.setReminderEnabled(id, enabled);
    _replaceReminder(updated);
  });

  Future<bool> deleteReminder(int id) => _run(() async {
    await _api.deleteReminder(id);
    reminders = reminders
        .where((item) => item.id != id)
        .toList(growable: false);
  }, successMessage: '提醒已删除；今日已有计划不会自动改变');

  void _replaceReminder(Reminder updated) {
    reminders = reminders
        .map((item) => item.id == updated.id ? updated : item)
        .toList(growable: false);
  }

  Future<bool> saveSettings(ReminderSettings value) => _run(() async {
    settings = await _api.updateSettings(value);
  }, successMessage: '设置已保存；如需立即生效，请重新生成今日计划');

  Future<bool> generateSchedules({required bool force}) => _run(() async {
    schedules = await _api.generateTodaySchedules(force: force);
    if (notificationsEnabled && user != null) {
      final result = await _notifications.sync(schedules, user!.timeZone);
      scheduledNotificationCount = result.scheduledCount;
    }
  }, successMessage: force ? '今日计划已重新生成' : '今日计划已生成');

  Future<bool> clearTodaySchedules() => _run(() async {
    final deletedCount = await _api.clearTodaySchedules();
    schedules = await _api.getTodaySchedules();
    if (notificationsEnabled && user != null) {
      final result = await _notifications.sync(schedules, user!.timeZone);
      scheduledNotificationCount = result.scheduledCount;
    }
    noticeMessage = deletedCount == 0
        ? '没有可清理的今日计划'
        : '已清理 $deletedCount 条未执行计划';
  });

  Future<bool> enableNotifications() => _run(() async {
    final permission = await _notifications.requestPermission();
    notificationsEnabled = permission.granted;
    if (!permission.granted) {
      throw const ApiException('通知权限未开启，请在系统设置中允许通知');
    }
    if (user != null) {
      final result = await _notifications.sync(schedules, user!.timeZone);
      scheduledNotificationCount = result.scheduledCount;
      noticeMessage = permission.exactAlarmsGranted
          ? '已精确排程 ${result.scheduledCount} 条本地通知'
          : '已排程 ${result.scheduledCount} 条通知；系统可能延迟触发';
    }
  });

  Future<bool> openBatteryOptimizationSettings() => _run(() async {
    if (!await _notifications.openBatteryOptimizationSettings()) {
      throw const ApiException('无法打开系统电池设置，请手动在系统设置中允许后台运行');
    }
  }, successMessage: '已打开系统电池设置');

  Future<bool> _run(
    Future<void> Function() action, {
    String? successMessage,
  }) async {
    if (busy) {
      return false;
    }
    busy = true;
    errorMessage = null;
    noticeMessage = null;
    notifyListeners();
    try {
      await action();
      noticeMessage ??= successMessage;
      return true;
    } catch (error) {
      await _handleError(error);
      return false;
    } finally {
      busy = false;
      notifyListeners();
    }
  }

  Future<void> _handleError(Object error) async {
    if (error is ApiException && error.isUnauthorized) {
      await _notifications.disableAndCancel();
      user = null;
      phase = AppPhase.signedOut;
      notificationsEnabled = false;
      errorMessage = '登录已过期，请重新登录';
      return;
    }
    errorMessage = _messageFor(error);
  }

  static String _messageFor(Object error) {
    if (error is ApiException) {
      return error.message;
    }
    if (error is FormatException) {
      return error.message;
    }
    return '操作失败，请稍后重试';
  }

  void clearMessages() {
    errorMessage = null;
    noticeMessage = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }
}
