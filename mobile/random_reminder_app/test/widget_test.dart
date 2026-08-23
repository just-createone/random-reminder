import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:random_reminder_app/app.dart';
import 'package:random_reminder_app/models/models.dart';
import 'package:random_reminder_app/services/api_client.dart';
import 'package:random_reminder_app/services/app_storage.dart';
import 'package:random_reminder_app/services/local_notification_service.dart';
import 'package:random_reminder_app/state/app_controller.dart';

void main() {
  testWidgets('shows login after finding no stored session', (tester) async {
    final controller = AppController(
      api: _SignedOutApi(),
      notifications: _FakeNotifications(),
    );

    await tester.pumpWidget(RandomReminderApp(controller: controller));
    await controller.initialize();
    await tester.pumpAndSettle();

    expect(find.text('随机提醒器'), findsOneWidget);
    expect(find.text('登录'), findsOneWidget);
    expect(find.text('没有账号？创建账号'), findsOneWidget);
  });

  testWidgets('returns to the reminder list after saving an editor', (
    tester,
  ) async {
    final controller = AppController(
      api: _SignedInApi(),
      notifications: _FakeNotifications(),
    );

    await tester.pumpWidget(RandomReminderApp(controller: controller));
    await controller.initialize();
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.format_list_bulleted_outlined));
    await tester.pumpAndSettle();
    await tester.tap(find.text('添加提醒内容'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '测试提醒');
    await tester.tap(find.text('保存'));
    await tester.pumpAndSettle();

    expect(find.text('测试提醒'), findsOneWidget);
  });
}

class _SignedOutApi implements ReminderApi {
  @override
  Future<AppUser?> restoreSession() async => null;

  @override
  void close() {}

  @override
  Future<Reminder> createReminder(String content) => throw UnimplementedError();
  @override
  Future<void> deleteReminder(int id) => throw UnimplementedError();
  @override
  Future<void> deleteAccount() => throw UnimplementedError();
  @override
  Future<int> clearTodaySchedules() => throw UnimplementedError();
  @override
  Future<List<DailySchedule>> generateTodaySchedules({required bool force}) =>
      throw UnimplementedError();
  @override
  Future<List<Reminder>> getReminders() => throw UnimplementedError();
  @override
  Future<ReminderSettings> getSettings() => throw UnimplementedError();
  @override
  Future<List<DailySchedule>> getTodaySchedules() => throw UnimplementedError();
  @override
  Future<AppUser> login(String email, String password) =>
      throw UnimplementedError();
  @override
  Future<void> logout() => throw UnimplementedError();
  @override
  Future<AppUser> register(String email, String password, String timeZone) =>
      throw UnimplementedError();
  @override
  Future<Reminder> setReminderEnabled(int id, bool enabled) =>
      throw UnimplementedError();
  @override
  Future<Reminder> updateReminder(int id, String content) =>
      throw UnimplementedError();
  @override
  Future<ReminderSettings> updateSettings(ReminderSettings settings) =>
      throw UnimplementedError();
}

class _SignedInApi extends _SignedOutApi {
  static const _now = '2026-08-21T00:00:00Z';

  @override
  Future<AppUser?> restoreSession() async => const AppUser(
    id: 1,
    email: 'test@example.invalid',
    timeZone: 'Asia/Shanghai',
    createdAt: _now,
    updatedAt: _now,
  );

  @override
  Future<Reminder> createReminder(String content) async => Reminder(
    id: 1,
    content: content,
    enabled: true,
    createdAt: _now,
    updatedAt: _now,
  );

  @override
  Future<List<Reminder>> getReminders() async => const <Reminder>[];

  @override
  Future<ReminderSettings> getSettings() async => const ReminderSettings(
    id: 1,
    userId: 1,
    enabled: true,
    allDay: true,
    startTime: null,
    endTime: null,
    timesPerDay: 3,
    minimumInterval: 60,
    createdAt: _now,
    updatedAt: _now,
  );

  @override
  Future<List<DailySchedule>> getTodaySchedules() async =>
      const <DailySchedule>[];
}

class _FakeNotifications implements DeviceNotificationService {
  @override
  Future<void> disableAndCancel() async {}
  @override
  Future<bool> openBatteryOptimizationSettings() async => true;
  @override
  Future<void> initialize() async {}
  @override
  Future<NotificationPreference> preference() async =>
      const NotificationPreference(enabled: false, preferExactAlarms: false);
  @override
  Future<NotificationPermissionResult> requestPermission() async =>
      const NotificationPermissionResult(
        granted: true,
        exactAlarmsGranted: false,
      );
  @override
  Future<NotificationSyncResult> sync(
    List<DailySchedule> schedules,
    String timeZone,
  ) async =>
      const NotificationSyncResult(scheduledCount: 0, usedExactAlarms: false);
}
