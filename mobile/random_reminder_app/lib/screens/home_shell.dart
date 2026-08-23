import 'package:flutter/material.dart';

import '../state/app_controller.dart';
import 'dashboard_screen.dart';
import 'reminders_screen.dart';
import 'settings_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({required this.controller, super.key});

  final AppController controller;

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;
  bool _messageScheduled = false;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_handleControllerMessage);
  }

  @override
  void didUpdateWidget(covariant HomeShell oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.controller != widget.controller) {
      oldWidget.controller.removeListener(_handleControllerMessage);
      widget.controller.addListener(_handleControllerMessage);
    }
  }

  void _handleControllerMessage() {
    if (_messageScheduled ||
        (widget.controller.errorMessage == null &&
            widget.controller.noticeMessage == null)) {
      return;
    }
    _messageScheduled = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _messageScheduled = false;
      if (!mounted) {
        return;
      }
      final isError = widget.controller.errorMessage != null;
      final text =
          widget.controller.errorMessage ?? widget.controller.noticeMessage;
      if (text == null) {
        return;
      }
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(text),
            backgroundColor: isError
                ? Theme.of(context).colorScheme.error
                : null,
          ),
        );
      widget.controller.clearMessages();
    });
  }

  @override
  void dispose() {
    widget.controller.removeListener(_handleControllerMessage);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      DashboardScreen(controller: widget.controller),
      RemindersScreen(controller: widget.controller),
      SettingsScreen(controller: widget.controller),
    ];
    final titles = <String>['今日', '提醒内容', '设置'];

    return Scaffold(
      appBar: AppBar(
        title: Text(titles[_index]),
        actions: <Widget>[
          PopupMenuButton<String>(
            tooltip: '账号',
            onSelected: (value) {
              if (value == 'logout') {
                widget.controller.logout();
              }
            },
            itemBuilder: (context) => <PopupMenuEntry<String>>[
              PopupMenuItem<String>(
                enabled: false,
                child: Text(widget.controller.user?.email ?? ''),
              ),
              const PopupMenuDivider(),
              const PopupMenuItem<String>(
                value: 'logout',
                child: ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.logout),
                  title: Text('退出登录'),
                ),
              ),
            ],
            icon: const Icon(Icons.account_circle_outlined),
          ),
        ],
        bottom: widget.controller.busy || widget.controller.refreshing
            ? const PreferredSize(
                preferredSize: Size.fromHeight(3),
                child: LinearProgressIndicator(minHeight: 3),
              )
            : null,
      ),
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const <NavigationDestination>[
          NavigationDestination(
            icon: Icon(Icons.today_outlined),
            selectedIcon: Icon(Icons.today),
            label: '今日',
          ),
          NavigationDestination(
            icon: Icon(Icons.format_list_bulleted_outlined),
            selectedIcon: Icon(Icons.format_list_bulleted),
            label: '提醒',
          ),
          NavigationDestination(
            icon: Icon(Icons.tune_outlined),
            selectedIcon: Icon(Icons.tune),
            label: '设置',
          ),
        ],
      ),
    );
  }
}
