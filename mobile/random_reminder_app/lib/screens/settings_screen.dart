import 'package:flutter/material.dart';

import '../models/models.dart';
import '../state/app_controller.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({required this.controller, super.key});

  final AppController controller;

  Future<void> _edit(BuildContext context, ReminderSettings settings) async {
    final result = await showDialog<ReminderSettings>(
      context: context,
      builder: (context) => _SettingsDialog(initial: settings),
    );
    if (result != null) {
      await controller.saveSettings(result);
    }
  }

  Future<void> _deleteAccount(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('永久删除账号？'),
        content: const Text('这会永久删除你的提醒、计划、推送订阅和账号信息，且无法恢复。'),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('永久删除'),
          ),
        ],
      ),
    );
    if (confirmed ?? false) {
      await controller.deleteAccount();
    }
  }

  @override
  Widget build(BuildContext context) {
    final settings = controller.settings;
    return RefreshIndicator(
      onRefresh: controller.refresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        children: <Widget>[
          if (settings == null)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(28),
                child: Center(child: CircularProgressIndicator()),
              ),
            )
          else
            Card(
              child: Column(
                children: <Widget>[
                  SwitchListTile(
                    value: settings.enabled,
                    onChanged: null,
                    secondary: const Icon(Icons.power_settings_new),
                    title: const Text('随机提醒总开关'),
                    subtitle: Text(settings.enabled ? '已开启' : '已关闭'),
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.schedule_outlined),
                    title: const Text('提醒时段'),
                    subtitle: Text(
                      settings.allDay
                          ? '全天'
                          : '${settings.startTime} 至 ${settings.endTime}',
                    ),
                  ),
                  ListTile(
                    leading: const Icon(Icons.repeat),
                    title: const Text('每天提醒次数'),
                    trailing: Text('${settings.timesPerDay} 次'),
                  ),
                  ListTile(
                    leading: const Icon(Icons.space_bar),
                    title: const Text('最小间隔'),
                    trailing: Text('${settings.minimumInterval} 分钟'),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        onPressed: controller.busy
                            ? null
                            : () => _edit(context, settings),
                        icon: const Icon(Icons.edit_outlined),
                        label: const Text('编辑设置'),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text('生效规则', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  const Text('保存设置不会静默替换今天已有的计划。需要当天立即生效时，请回到“今日”页显式重新生成。'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: ListTile(
              leading: const Icon(Icons.public),
              title: const Text('账号时区'),
              subtitle: Text(controller.user?.timeZone ?? '—'),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: ListTile(
              leading: Icon(
                Icons.delete_forever_outlined,
                color: Theme.of(context).colorScheme.error,
              ),
              title: const Text('删除账号'),
              subtitle: const Text('永久删除账号及所有数据，无法恢复'),
              trailing: const Icon(Icons.chevron_right),
              enabled: !controller.busy,
              onTap: controller.busy ? null : () => _deleteAccount(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingsDialog extends StatefulWidget {
  const _SettingsDialog({required this.initial});

  final ReminderSettings initial;

  @override
  State<_SettingsDialog> createState() => _SettingsDialogState();
}

class _SettingsDialogState extends State<_SettingsDialog> {
  final _formKey = GlobalKey<FormState>();
  late bool _enabled;
  late bool _allDay;
  late TimeOfDay _start;
  late TimeOfDay _end;
  late final TextEditingController _timesController;
  late final TextEditingController _intervalController;

  @override
  void initState() {
    super.initState();
    _enabled = widget.initial.enabled;
    _allDay = widget.initial.allDay;
    _start = _parseTime(widget.initial.startTime ?? '09:00');
    _end = _parseTime(widget.initial.endTime ?? '22:00');
    _timesController = TextEditingController(
      text: widget.initial.timesPerDay.toString(),
    );
    _intervalController = TextEditingController(
      text: widget.initial.minimumInterval.toString(),
    );
  }

  @override
  void dispose() {
    _timesController.dispose();
    _intervalController.dispose();
    super.dispose();
  }

  static TimeOfDay _parseTime(String value) {
    final parts = value.split(':');
    return TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
  }

  static String _formatTime(TimeOfDay value) =>
      '${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';

  Future<void> _pickTime({required bool start}) async {
    final value = await showTimePicker(
      context: context,
      initialTime: start ? _start : _end,
    );
    if (value != null) {
      setState(() {
        if (start) {
          _start = value;
        } else {
          _end = value;
        }
      });
    }
  }

  void _save() {
    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }
    if (!_allDay) {
      final startMinutes = _start.hour * 60 + _start.minute;
      final endMinutes = _end.hour * 60 + _end.minute;
      if (startMinutes >= endMinutes) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('开始时间必须早于结束时间')));
        return;
      }
    }
    Navigator.pop(
      context,
      widget.initial.copyWith(
        enabled: _enabled,
        allDay: _allDay,
        startTime: _formatTime(_start),
        endTime: _formatTime(_end),
        timesPerDay: int.parse(_timesController.text),
        minimumInterval: int.parse(_intervalController.text),
      ),
    );
  }

  String? _validateInteger(String? raw, int minimum, int maximum) {
    final value = int.tryParse(raw ?? '');
    if (value == null || value < minimum || value > maximum) {
      return '请输入 $minimum–$maximum';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('编辑提醒设置'),
    content: SizedBox(
      width: 420,
      child: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _enabled,
                onChanged: (value) => setState(() => _enabled = value),
                title: const Text('开启随机提醒'),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _allDay,
                onChanged: (value) => setState(() => _allDay = value),
                title: const Text('全天提醒'),
              ),
              if (!_allDay) ...<Widget>[
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('开始时间'),
                  trailing: TextButton(
                    onPressed: () => _pickTime(start: true),
                    child: Text(_formatTime(_start)),
                  ),
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('结束时间'),
                  trailing: TextButton(
                    onPressed: () => _pickTime(start: false),
                    child: Text(_formatTime(_end)),
                  ),
                ),
              ],
              const SizedBox(height: 8),
              TextFormField(
                controller: _timesController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: '每天提醒次数'),
                validator: (value) => _validateInteger(value, 1, 20),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _intervalController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: '最小间隔（分钟）'),
                validator: (value) => _validateInteger(value, 5, 720),
              ),
            ],
          ),
        ),
      ),
    ),
    actions: <Widget>[
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('取消'),
      ),
      FilledButton(onPressed: _save, child: const Text('保存')),
    ],
  );
}
