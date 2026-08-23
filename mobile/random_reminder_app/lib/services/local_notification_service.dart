import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest.dart' as timezone_data;
import 'package:timezone/timezone.dart' as tz;

import '../models/models.dart';
import 'app_storage.dart';

class NotificationPermissionResult {
  const NotificationPermissionResult({
    required this.granted,
    required this.exactAlarmsGranted,
  });

  final bool granted;
  final bool exactAlarmsGranted;
}

class NotificationSyncResult {
  const NotificationSyncResult({
    required this.scheduledCount,
    required this.usedExactAlarms,
  });

  final int scheduledCount;
  final bool usedExactAlarms;
}

abstract interface class DeviceNotificationService {
  Future<void> initialize();
  Future<NotificationPreference> preference();
  Future<NotificationPermissionResult> requestPermission();
  Future<bool> openBatteryOptimizationSettings();
  Future<NotificationSyncResult> sync(
    List<DailySchedule> schedules,
    String timeZone,
  );
  Future<void> disableAndCancel();
}

class LocalNotificationService implements DeviceNotificationService {
  factory LocalNotificationService({
    required NotificationPreferenceStore preferenceStore,
    FlutterLocalNotificationsPlugin? plugin,
  }) => LocalNotificationService._(
    preferenceStore,
    plugin ?? FlutterLocalNotificationsPlugin(),
  );

  LocalNotificationService._(this._preferenceStore, this._plugin);

  static const _details = NotificationDetails(
    android: AndroidNotificationDetails(
      'random_reminders',
      '随机提醒',
      channelDescription: '按每日随机计划发送的提醒',
      importance: Importance.high,
      priority: Priority.high,
    ),
    iOS: DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    ),
  );

  final NotificationPreferenceStore _preferenceStore;
  final FlutterLocalNotificationsPlugin _plugin;
  static const _deviceSettings = MethodChannel(
    'getpromptide.com/random_reminder/device_settings',
  );
  bool _initialized = false;

  @override
  Future<void> initialize() async {
    if (_initialized) {
      return;
    }
    timezone_data.initializeTimeZones();
    await _plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('ic_stat_notification'),
        iOS: DarwinInitializationSettings(
          requestAlertPermission: false,
          requestBadgePermission: false,
          requestSoundPermission: false,
        ),
      ),
    );
    _initialized = true;
  }

  @override
  Future<NotificationPreference> preference() =>
      _preferenceStore.readNotificationPreference();

  @override
  Future<bool> openBatteryOptimizationSettings() async {
    if (!Platform.isAndroid) {
      return false;
    }
    try {
      await _deviceSettings.invokeMethod<void>(
        'openBatteryOptimizationSettings',
      );
      return true;
    } on PlatformException {
      return false;
    } on MissingPluginException {
      return false;
    }
  }

  @override
  Future<NotificationPermissionResult> requestPermission() async {
    await initialize();
    var granted = true;
    var exact = false;

    final android = _plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    if (android != null) {
      granted = await android.requestNotificationsPermission() ?? true;
      if (granted) {
        exact = await android.requestExactAlarmsPermission() ?? false;
      }
    }

    final ios = _plugin
        .resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin
        >();
    if (ios != null) {
      granted =
          await ios.requestPermissions(alert: true, badge: true, sound: true) ??
          false;
    }

    await _preferenceStore.writeNotificationPreference(
      NotificationPreference(enabled: granted, preferExactAlarms: exact),
    );
    return NotificationPermissionResult(
      granted: granted,
      exactAlarmsGranted: exact,
    );
  }

  @override
  Future<NotificationSyncResult> sync(
    List<DailySchedule> schedules,
    String timeZone,
  ) async {
    await initialize();
    var currentPreference = await preference();
    if (!currentPreference.enabled) {
      return const NotificationSyncResult(
        scheduledCount: 0,
        usedExactAlarms: false,
      );
    }

    final location = tz.getLocation(timeZone);
    tz.setLocalLocation(location);
    final pending = await _plugin.pendingNotificationRequests();
    for (final request in pending) {
      await _plugin.cancel(id: request.id);
    }

    var scheduledCount = 0;
    var useExact = currentPreference.preferExactAlarms;
    for (final schedule in schedules.where((item) => item.isPending)) {
      final scheduledAt = _parseSchedule(schedule, location);
      if (!scheduledAt.isAfter(tz.TZDateTime.now(location))) {
        continue;
      }

      try {
        await _schedule(schedule, scheduledAt, exact: useExact);
      } on PlatformException {
        if (!useExact) {
          rethrow;
        }
        useExact = false;
        currentPreference = const NotificationPreference(
          enabled: true,
          preferExactAlarms: false,
        );
        await _preferenceStore.writeNotificationPreference(currentPreference);
        await _schedule(schedule, scheduledAt, exact: false);
      }
      scheduledCount += 1;
    }

    return NotificationSyncResult(
      scheduledCount: scheduledCount,
      usedExactAlarms: useExact,
    );
  }

  Future<void> _schedule(
    DailySchedule schedule,
    tz.TZDateTime scheduledAt, {
    required bool exact,
  }) => _plugin.zonedSchedule(
    id: schedule.id & 0x7fffffff,
    title: '随机提醒器',
    body: schedule.content,
    scheduledDate: scheduledAt,
    notificationDetails: _details,
    androidScheduleMode: exact
        ? AndroidScheduleMode.exactAllowWhileIdle
        : AndroidScheduleMode.inexactAllowWhileIdle,
    payload: 'schedule:${schedule.id}',
  );

  static tz.TZDateTime _parseSchedule(
    DailySchedule schedule,
    tz.Location location,
  ) {
    final dateParts = schedule.scheduleDate.split('-').map(int.parse).toList();
    final timeParts = schedule.scheduledTime.split(':').map(int.parse).toList();
    if (dateParts.length != 3 || timeParts.length < 2) {
      throw const FormatException('计划时间格式不正确');
    }
    return tz.TZDateTime(
      location,
      dateParts[0],
      dateParts[1],
      dateParts[2],
      timeParts[0],
      timeParts[1],
    );
  }

  @override
  Future<void> disableAndCancel() async {
    await initialize();
    await _plugin.cancelAll();
    await _preferenceStore.writeNotificationPreference(
      const NotificationPreference(enabled: false, preferExactAlarms: false),
    );
  }
}
