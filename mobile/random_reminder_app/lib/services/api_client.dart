import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/models.dart';
import 'app_storage.dart';

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode, this.cause});

  final String message;
  final int? statusCode;
  final Object? cause;

  bool get isUnauthorized => statusCode == 401;

  @override
  String toString() => message;
}

abstract interface class ReminderApi {
  Future<AppUser?> restoreSession();
  Future<AppUser> login(String email, String password);
  Future<AppUser> register(String email, String password, String timeZone);
  Future<void> logout();
  Future<void> deleteAccount();
  Future<List<Reminder>> getReminders();
  Future<Reminder> createReminder(String content);
  Future<Reminder> updateReminder(int id, String content);
  Future<Reminder> setReminderEnabled(int id, bool enabled);
  Future<void> deleteReminder(int id);
  Future<ReminderSettings> getSettings();
  Future<ReminderSettings> updateSettings(ReminderSettings settings);
  Future<List<DailySchedule>> getTodaySchedules();
  Future<List<DailySchedule>> generateTodaySchedules({required bool force});
  Future<int> clearTodaySchedules();
  void close();
}

class ApiClient implements ReminderApi {
  factory ApiClient({
    required AppConfig config,
    required SessionStore sessionStore,
    required http.Client client,
    Duration timeout = const Duration(seconds: 15),
  }) => ApiClient._(config, sessionStore, client, timeout);

  ApiClient._(this._config, this._sessionStore, this._client, this.timeout);

  static const _cookieName = 'random_reminder_session';

  final AppConfig _config;
  final SessionStore _sessionStore;
  final http.Client _client;
  final Duration timeout;

  @override
  Future<AppUser?> restoreSession() async {
    if (await _sessionStore.readSessionToken() == null) {
      return null;
    }
    try {
      final payload = await _request('GET', _config.endpoint('/api/auth/me'));
      return AppUser.fromJson(_responseDataMap(payload, '当前用户'));
    } on ApiException catch (error) {
      if (error.isUnauthorized) {
        return null;
      }
      rethrow;
    }
  }

  @override
  Future<AppUser> login(String email, String password) => _authenticate(
    '/api/auth/login',
    <String, dynamic>{'email': email.trim(), 'password': password},
  );

  @override
  Future<AppUser> register(String email, String password, String timeZone) =>
      _authenticate('/api/auth/register', <String, dynamic>{
        'email': email.trim(),
        'password': password,
        'time_zone': timeZone,
      });

  Future<AppUser> _authenticate(String path, JsonMap body) async {
    final response = await _send('POST', _config.endpoint(path), body: body);
    final payload = _decodeResponse(response);
    final token = _extractSessionToken(response.headers['set-cookie']);
    if (token == null) {
      throw const ApiException('登录响应缺少安全会话，请稍后重试');
    }
    await _sessionStore.writeSessionToken(token);
    return AppUser.fromJson(_responseDataMap(payload, '登录'));
  }

  @override
  Future<void> logout() async {
    try {
      await _request('POST', _config.endpoint('/api/auth/logout'));
    } finally {
      await _sessionStore.clearSessionToken();
    }
  }

  @override
  Future<void> deleteAccount() async {
    await _request('DELETE', _config.endpoint('/api/auth/account'));
    await _sessionStore.clearSessionToken();
  }

  @override
  Future<List<Reminder>> getReminders() async {
    final payload = await _request('GET', _config.endpoint('/api/reminders'));
    return _responseDataList(payload, '提醒列表')
        .map((item) => Reminder.fromJson(requireJsonMap(item, '提醒')))
        .toList(growable: false);
  }

  @override
  Future<Reminder> createReminder(String content) async {
    final payload = await _request(
      'POST',
      _config.endpoint('/api/reminders'),
      body: <String, dynamic>{'content': content},
    );
    return Reminder.fromJson(_responseDataMap(payload, '创建提醒'));
  }

  @override
  Future<Reminder> updateReminder(int id, String content) async {
    final payload = await _request(
      'PUT',
      _config.endpoint('/api/reminders/$id'),
      body: <String, dynamic>{'content': content},
    );
    return Reminder.fromJson(_responseDataMap(payload, '修改提醒'));
  }

  @override
  Future<Reminder> setReminderEnabled(int id, bool enabled) async {
    final payload = await _request(
      'PATCH',
      _config.endpoint('/api/reminders/$id/enabled'),
      body: <String, dynamic>{'enabled': enabled},
    );
    return Reminder.fromJson(_responseDataMap(payload, '修改提醒状态'));
  }

  @override
  Future<void> deleteReminder(int id) async {
    await _request('DELETE', _config.endpoint('/api/reminders/$id'));
  }

  @override
  Future<ReminderSettings> getSettings() async {
    final payload = await _request('GET', _config.endpoint('/api/settings'));
    return ReminderSettings.fromJson(_responseDataMap(payload, '提醒设置'));
  }

  @override
  Future<ReminderSettings> updateSettings(ReminderSettings settings) async {
    final payload = await _request(
      'PUT',
      _config.endpoint('/api/settings'),
      body: settings.toUpdateJson(),
    );
    return ReminderSettings.fromJson(_responseDataMap(payload, '保存设置'));
  }

  @override
  Future<List<DailySchedule>> getTodaySchedules() async {
    final payload = await _request(
      'GET',
      _config.endpoint('/api/schedules/today'),
    );
    return _scheduleList(payload);
  }

  @override
  Future<List<DailySchedule>> generateTodaySchedules({
    required bool force,
  }) async {
    final payload = await _request(
      'POST',
      _config.endpoint(
        '/api/schedules/today/generate',
        queryParameters: <String, String>{'force': force.toString()},
      ),
    );
    return _scheduleList(payload);
  }

  @override
  Future<int> clearTodaySchedules() async {
    final payload = await _request(
      'DELETE',
      _config.endpoint('/api/schedules/today'),
    );
    final data = _responseDataMap(payload, '今日计划清理');
    final deletedCount = data['deleted_count'];
    if (deletedCount is! int) {
      throw const FormatException('今日计划清理返回格式不正确');
    }
    return deletedCount;
  }

  List<DailySchedule> _scheduleList(Object? payload) =>
      _responseDataList(payload, '今日计划')
          .map((item) => DailySchedule.fromJson(requireJsonMap(item, '计划')))
          .toList(growable: false);

  Future<Object?> _request(String method, Uri uri, {JsonMap? body}) async {
    final response = await _send(method, uri, body: body);
    if (response.statusCode == 401) {
      await _sessionStore.clearSessionToken();
    }
    return _decodeResponse(response);
  }

  Future<http.Response> _send(String method, Uri uri, {JsonMap? body}) async {
    try {
      final request = http.Request(method, uri);
      request.headers['Accept'] = 'application/json';
      final token = await _sessionStore.readSessionToken();
      if (token != null && token.isNotEmpty) {
        request.headers['Cookie'] = '$_cookieName=$token';
      }
      if (body != null) {
        request.headers['Content-Type'] = 'application/json; charset=utf-8';
        request.body = jsonEncode(body);
      }
      final streamed = await _client.send(request).timeout(timeout);
      return await http.Response.fromStream(streamed).timeout(timeout);
    } on TimeoutException catch (error) {
      throw ApiException('请求超时，请检查网络后重试', cause: error);
    } on ApiException {
      rethrow;
    } catch (error) {
      throw ApiException('无法连接服务器，请检查网络后重试', cause: error);
    }
  }

  Object? _decodeResponse(http.Response response) {
    Object? payload;
    final bodyText = utf8.decode(response.bodyBytes).trim();
    if (bodyText.isNotEmpty) {
      try {
        payload = jsonDecode(bodyText);
      } on FormatException catch (error) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          throw ApiException('服务器返回格式不正确', cause: error);
        }
      }
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        _errorMessage(payload, response.statusCode),
        statusCode: response.statusCode,
      );
    }
    return payload;
  }

  static JsonMap _responseDataMap(Object? payload, String context) {
    final envelope = requireJsonMap(payload, context);
    return requireJsonMap(envelope['data'], context);
  }

  static List<dynamic> _responseDataList(Object? payload, String context) {
    final envelope = requireJsonMap(payload, context);
    final data = envelope['data'];
    if (data is! List<dynamic>) {
      throw FormatException('$context 返回格式不正确');
    }
    return data;
  }

  static String _errorMessage(Object? payload, int statusCode) {
    if (payload is Map<String, dynamic>) {
      final detail = payload['detail'] ?? payload['message'];
      if (detail is String && detail.trim().isNotEmpty) {
        return detail;
      }
      if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map && first['msg'] is String) {
          return first['msg'] as String;
        }
      }
    }
    return '请求失败（HTTP $statusCode）';
  }

  static String? _extractSessionToken(String? setCookie) {
    if (setCookie == null || setCookie.isEmpty) {
      return null;
    }
    final match = RegExp(
      r'(?:^|[,\s])random_reminder_session=([^;,\s]+)',
    ).firstMatch(setCookie);
    return match?.group(1);
  }

  @override
  void close() => _client.close();
}
