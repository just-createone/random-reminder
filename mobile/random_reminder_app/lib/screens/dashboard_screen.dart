import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/models.dart';
import '../state/app_controller.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({required this.controller, super.key});

  final AppController controller;

  Future<void> _regenerate(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('重新生成今日计划？'),
        content: const Text('尚未触发的今日计划会被替换，已经发送或失败的记录会保留。'),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('重新生成'),
          ),
        ],
      ),
    );
    if (confirmed ?? false) {
      await controller.generateSchedules(force: true);
    }
  }

  Future<void> _clearTodaySchedules(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('清理今日计划？'),
        content: const Text('仅清理尚未执行或已跳过的计划；已发送和失败记录会保留。'),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('清理'),
          ),
        ],
      ),
    );
    if (confirmed ?? false) {
      await controller.clearTodaySchedules();
    }
  }

  @override
  Widget build(BuildContext context) {
    final settings = controller.settings;
    final schedules = controller.schedules;
    return RefreshIndicator(
      onRefresh: controller.refresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        children: <Widget>[
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: <Widget>[
                  CircleAvatar(
                    backgroundColor: settings?.enabled == true
                        ? Theme.of(context).colorScheme.primaryContainer
                        : Theme.of(context).colorScheme.surfaceContainerHighest,
                    child: Icon(
                      settings?.enabled == true
                          ? Icons.notifications_active
                          : Icons.notifications_off_outlined,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          settings?.enabled == true ? '随机提醒运行中' : '随机提醒已关闭',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 4),
                        Text(_settingsDescription(settings)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      const Icon(Icons.phone_android),
                      const SizedBox(width: 10),
                      Text(
                        '本机通知',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    controller.notificationsEnabled
                        ? '已为本机排程 ${controller.scheduledNotificationCount} 条未来通知。'
                        : '授权后，App 会把服务端今日计划排程为 Android 本地通知。',
                  ),
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerRight,
                    child: FilledButton.tonalIcon(
                      onPressed: controller.busy
                          ? null
                          : controller.enableNotifications,
                      icon: const Icon(Icons.notifications_outlined),
                      label: Text(
                        controller.notificationsEnabled ? '重新同步' : '启用本机通知',
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (defaultTargetPlatform == TargetPlatform.android) ...<Widget>[
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        const Icon(Icons.battery_saver_outlined),
                        const SizedBox(width: 10),
                        Text(
                          '后台运行设置',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      '部分 Android 机型会在锁屏后限制提醒。请在系统设置中将本应用的电池使用设为“不受限制”或允许后台运行。',
                    ),
                    const SizedBox(height: 12),
                    Align(
                      alignment: Alignment.centerRight,
                      child: OutlinedButton.icon(
                        onPressed: controller.busy
                            ? null
                            : controller.openBatteryOptimizationSettings,
                        icon: const Icon(Icons.open_in_new),
                        label: const Text('打开电池设置'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 24),
          Row(
            children: <Widget>[
              Expanded(
                child: Text(
                  '今日计划',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              if (schedules.isNotEmpty)
                IconButton(
                  onPressed: controller.busy
                      ? null
                      : () => _regenerate(context),
                  tooltip: '重新生成',
                  icon: const Icon(Icons.shuffle),
                ),
              if (schedules.any(
                (schedule) =>
                    schedule.status == 'pending' ||
                    schedule.status == 'skipped',
              ))
                IconButton(
                  onPressed: controller.busy
                      ? null
                      : () => _clearTodaySchedules(context),
                  tooltip: '清理未执行计划',
                  icon: const Icon(Icons.delete_outline),
                ),
            ],
          ),
          const SizedBox(height: 8),
          if (schedules.isEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: <Widget>[
                    const Icon(Icons.event_busy_outlined, size: 42),
                    const SizedBox(height: 12),
                    const Text('今天还没有提醒计划'),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: controller.busy
                          ? null
                          : () => controller.generateSchedules(force: false),
                      icon: const Icon(Icons.auto_awesome),
                      label: const Text('生成今日计划'),
                    ),
                  ],
                ),
              ),
            )
          else
            ...schedules.map(
              (schedule) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: _ScheduleCard(schedule: schedule),
              ),
            ),
        ],
      ),
    );
  }

  static String _settingsDescription(ReminderSettings? settings) {
    if (settings == null) {
      return '正在读取设置…';
    }
    if (!settings.enabled) {
      return '在设置页开启后才能生成计划。';
    }
    final range = settings.allDay
        ? '全天'
        : '${settings.startTime}–${settings.endTime}';
    return '$range · 每天 ${settings.timesPerDay} 次 · 间隔至少 ${settings.minimumInterval} 分钟';
  }
}

class _ScheduleCard extends StatelessWidget {
  const _ScheduleCard({required this.schedule});

  final DailySchedule schedule;

  @override
  Widget build(BuildContext context) {
    final (label, icon, color) = switch (schedule.status) {
      'sent' => ('已提醒', Icons.check_circle_outline, Colors.green),
      'failed' => (
        '发送失败',
        Icons.error_outline,
        Theme.of(context).colorScheme.error,
      ),
      'skipped' => ('已跳过', Icons.skip_next_outlined, Colors.orange),
      _ => ('等待提醒', Icons.schedule, Theme.of(context).colorScheme.primary),
    };
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withValues(alpha: 0.12),
          foregroundColor: color,
          child: Text(schedule.scheduledTime.substring(0, 2)),
        ),
        title: Text(schedule.content),
        subtitle: Text('${schedule.scheduledTime} · $label'),
        trailing: Icon(icon, color: color),
      ),
    );
  }
}
