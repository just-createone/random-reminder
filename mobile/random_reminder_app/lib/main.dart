import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import 'app.dart';
import 'config/app_config.dart';
import 'services/api_client.dart';
import 'services/app_storage.dart';
import 'services/local_notification_service.dart';
import 'state/app_controller.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  final config = AppConfig.fromEnvironment();
  final storage = SecureAppStorage(FlutterSecureStorage());
  final api = ApiClient(
    config: config,
    sessionStore: storage,
    client: http.Client(),
  );
  final notifications = LocalNotificationService(preferenceStore: storage);
  final controller = AppController(api: api, notifications: notifications);

  runApp(RandomReminderApp(controller: controller));
  unawaited(controller.initialize());
}
