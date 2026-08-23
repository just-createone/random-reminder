import 'package:flutter/material.dart';

import 'screens/auth_screen.dart';
import 'screens/home_shell.dart';
import 'state/app_controller.dart';

class RandomReminderApp extends StatelessWidget {
  const RandomReminderApp({required this.controller, super.key});

  final AppController controller;

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: '随机提醒器',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xff4f46e5),
        brightness: Brightness.light,
      ),
      useMaterial3: true,
      inputDecorationTheme: const InputDecorationTheme(
        border: OutlineInputBorder(),
      ),
      cardTheme: const CardThemeData(
        margin: EdgeInsets.zero,
        clipBehavior: Clip.antiAlias,
      ),
    ),
    home: AnimatedBuilder(
      animation: controller,
      builder: (context, _) => switch (controller.phase) {
        AppPhase.booting => const _LoadingScreen(),
        AppPhase.signedOut => AuthScreen(controller: controller),
        AppPhase.signedIn => HomeShell(controller: controller),
        AppPhase.startupError => _StartupErrorScreen(controller: controller),
      },
    ),
  );
}

class _LoadingScreen extends StatelessWidget {
  const _LoadingScreen();

  @override
  Widget build(BuildContext context) => const Scaffold(
    body: Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          CircularProgressIndicator(),
          SizedBox(height: 20),
          Text('正在恢复安全会话…'),
        ],
      ),
    ),
  );
}

class _StartupErrorScreen extends StatelessWidget {
  const _StartupErrorScreen({required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Icon(
                Icons.cloud_off_outlined,
                size: 56,
                color: Theme.of(context).colorScheme.error,
              ),
              const SizedBox(height: 16),
              Text(
                controller.errorMessage ?? '应用初始化失败',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: controller.initialize,
                icon: const Icon(Icons.refresh),
                label: const Text('重试'),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}
