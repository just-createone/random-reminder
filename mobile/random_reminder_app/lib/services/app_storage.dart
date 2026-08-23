import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class NotificationPreference {
  const NotificationPreference({
    required this.enabled,
    required this.preferExactAlarms,
  });

  final bool enabled;
  final bool preferExactAlarms;
}

abstract interface class SessionStore {
  Future<String?> readSessionToken();
  Future<void> writeSessionToken(String token);
  Future<void> clearSessionToken();
}

abstract interface class NotificationPreferenceStore {
  Future<NotificationPreference> readNotificationPreference();
  Future<void> writeNotificationPreference(NotificationPreference preference);
}

class SecureAppStorage implements SessionStore, NotificationPreferenceStore {
  SecureAppStorage(this._storage);

  static const _sessionKey = 'session_token';
  static const _notificationsEnabledKey = 'notifications_enabled';
  static const _exactAlarmsKey = 'exact_alarms_preferred';

  final FlutterSecureStorage _storage;

  @override
  Future<String?> readSessionToken() => _storage.read(key: _sessionKey);

  @override
  Future<void> writeSessionToken(String token) =>
      _storage.write(key: _sessionKey, value: token);

  @override
  Future<void> clearSessionToken() => _storage.delete(key: _sessionKey);

  @override
  Future<NotificationPreference> readNotificationPreference() async {
    final values = await Future.wait<String?>(<Future<String?>>[
      _storage.read(key: _notificationsEnabledKey),
      _storage.read(key: _exactAlarmsKey),
    ]);
    return NotificationPreference(
      enabled: values[0] == 'true',
      preferExactAlarms: values[1] == 'true',
    );
  }

  @override
  Future<void> writeNotificationPreference(
    NotificationPreference preference,
  ) async {
    await Future.wait<void>(<Future<void>>[
      _storage.write(
        key: _notificationsEnabledKey,
        value: preference.enabled.toString(),
      ),
      _storage.write(
        key: _exactAlarmsKey,
        value: preference.preferExactAlarms.toString(),
      ),
    ]);
  }
}
