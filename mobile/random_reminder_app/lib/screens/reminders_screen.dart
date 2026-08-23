import 'package:flutter/material.dart';

import '../models/models.dart';
import '../state/app_controller.dart';

class RemindersScreen extends StatelessWidget {
  const RemindersScreen({required this.controller, super.key});

  final AppController controller;

  Future<String?> _showEditor(BuildContext context, {Reminder? reminder}) =>
      showDialog<String>(
        context: context,
        builder: (_) => _ReminderEditorDialog(
          initialContent: reminder?.content ?? '',
          isNewReminder: reminder == null,
        ),
      );

  Future<void> _add(BuildContext context) async {
    final content = await _showEditor(context);
    if (content != null) {
      await controller.createReminder(content);
    }
  }

  Future<void> _edit(BuildContext context, Reminder reminder) async {
    final content = await _showEditor(context, reminder: reminder);
    if (content != null && content != reminder.content) {
      await controller.updateReminder(reminder.id, content);
    }
  }

  Future<void> _delete(BuildContext context, Reminder reminder) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('删除提醒？'),
        content: Text('“${reminder.content}”将被删除。今日已生成的计划不会改变。'),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('删除'),
          ),
        ],
      ),
    );
    if (confirmed ?? false) {
      await controller.deleteReminder(reminder.id);
    }
  }

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: controller.refresh,
    child: ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
      children: <Widget>[
        FilledButton.icon(
          onPressed: controller.busy ? null : () => _add(context),
          icon: const Icon(Icons.add),
          label: const Text('添加提醒内容'),
        ),
        const SizedBox(height: 16),
        if (controller.reminders.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(28),
              child: Column(
                children: <Widget>[
                  Icon(Icons.notes_outlined, size: 44),
                  SizedBox(height: 12),
                  Text('还没有提醒，先创建第一条吧。'),
                ],
              ),
            ),
          )
        else
          ...controller.reminders.map(
            (reminder) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Card(
                child: ListTile(
                  title: Text(reminder.content),
                  subtitle: Text(reminder.enabled ? '已启用' : '已停用'),
                  leading: Switch(
                    value: reminder.enabled,
                    onChanged: controller.busy
                        ? null
                        : (value) =>
                              controller.setReminderEnabled(reminder.id, value),
                  ),
                  trailing: PopupMenuButton<String>(
                    enabled: !controller.busy,
                    onSelected: (value) {
                      if (value == 'edit') {
                        _edit(context, reminder);
                      } else if (value == 'delete') {
                        _delete(context, reminder);
                      }
                    },
                    itemBuilder: (context) => const <PopupMenuEntry<String>>[
                      PopupMenuItem<String>(
                        value: 'edit',
                        child: ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: Icon(Icons.edit_outlined),
                          title: Text('编辑'),
                        ),
                      ),
                      PopupMenuItem<String>(
                        value: 'delete',
                        child: ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: Icon(Icons.delete_outline),
                          title: Text('删除'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
      ],
    ),
  );
}

class _ReminderEditorDialog extends StatefulWidget {
  const _ReminderEditorDialog({
    required this.initialContent,
    required this.isNewReminder,
  });

  final String initialContent;
  final bool isNewReminder;

  @override
  State<_ReminderEditorDialog> createState() => _ReminderEditorDialogState();
}

class _ReminderEditorDialogState extends State<_ReminderEditorDialog> {
  late final TextEditingController _textController = TextEditingController(
    text: widget.initialContent,
  );

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text(widget.isNewReminder ? '添加提醒' : '编辑提醒'),
    content: TextField(
      controller: _textController,
      autofocus: true,
      minLines: 3,
      maxLines: 6,
      maxLength: 500,
      decoration: const InputDecoration(
        hintText: '例如：站起来活动两分钟',
        labelText: '提醒内容',
      ),
    ),
    actions: <Widget>[
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('取消'),
      ),
      FilledButton(
        onPressed: () {
          final value = _textController.text.trim();
          if (value.isNotEmpty) {
            Navigator.pop(context, value);
          }
        },
        child: const Text('保存'),
      ),
    ],
  );
}
