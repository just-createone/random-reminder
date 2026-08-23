import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:random_reminder_app/config/app_config.dart';
import 'package:random_reminder_app/services/api_client.dart';
import 'package:random_reminder_app/services/app_storage.dart';

void main() {
  group('ApiClient session handling', () {
    test('stores login cookie and sends it on protected requests', () async {
      final store = _MemorySessionStore();
      final requests = <http.Request>[];
      final client = MockClient((request) async {
        requests.add(request);
        if (request.url.path == '/api/auth/login') {
          return _jsonResponse(
            200,
            <String, dynamic>{
              'success': true,
              'data': _userJson,
              'message': '登录成功',
            },
            headers: <String, String>{
              'set-cookie':
                  'random_reminder_session=test-token; Path=/; HttpOnly; Secure',
            },
          );
        }
        return _jsonResponse(200, <String, dynamic>{
          'success': true,
          'data': <dynamic>[],
          'message': '',
        });
      });
      final api = ApiClient(
        config: AppConfig.parse('https://example.com'),
        sessionStore: store,
        client: client,
      );

      final user = await api.login(' User@Example.com ', 'password123');
      await api.getReminders();

      expect(user.email, 'user@example.com');
      expect(store.token, 'test-token');
      expect(
        requests[1].headers['Cookie'],
        'random_reminder_session=test-token',
      );
      expect(jsonDecode(requests[0].body), <String, dynamic>{
        'email': 'User@Example.com',
        'password': 'password123',
      });
    });

    test('clears an expired session after 401', () async {
      final store = _MemorySessionStore()..token = 'expired';
      final api = ApiClient(
        config: AppConfig.parse('https://example.com'),
        sessionStore: store,
        client: MockClient(
          (_) async => _jsonResponse(401, <String, dynamic>{'detail': '请先登录'}),
        ),
      );

      expect(await api.restoreSession(), isNull);
      expect(store.token, isNull);
    });

    test('preserves login error detail when no cookie is returned', () async {
      final api = ApiClient(
        config: AppConfig.parse('https://example.com'),
        sessionStore: _MemorySessionStore(),
        client: MockClient(
          (_) async =>
              _jsonResponse(401, <String, dynamic>{'detail': '邮箱或密码不正确'}),
        ),
      );

      expect(
        () => api.login('user@example.com', 'wrong-password'),
        throwsA(
          isA<ApiException>().having(
            (error) => error.message,
            'message',
            '邮箱或密码不正确',
          ),
        ),
      );
    });

    test(
      'keeps HTTP error detail without assuming a successful envelope',
      () async {
        final api = ApiClient(
          config: AppConfig.parse('https://example.com'),
          sessionStore: _MemorySessionStore(),
          client: MockClient(
            (_) async =>
                _jsonResponse(400, <String, dynamic>{'detail': '提醒内容不能为空'}),
          ),
        );

        expect(
          () => api.createReminder(''),
          throwsA(
            isA<ApiException>().having(
              (error) => error.message,
              'message',
              '提醒内容不能为空',
            ),
          ),
        );
      },
    );

    test('clears today schedules with a DELETE request', () async {
      final requestMethods = <String>[];
      final api = ApiClient(
        config: AppConfig.parse('https://example.com'),
        sessionStore: _MemorySessionStore(),
        client: MockClient((request) async {
          requestMethods.add(request.method);
          expect(request.url.path, '/api/schedules/today');
          return _jsonResponse(200, <String, dynamic>{
            'success': true,
            'data': <String, dynamic>{'deleted_count': 2},
            'message': '已清理今日未执行计划',
          });
        }),
      );

      expect(await api.clearTodaySchedules(), 2);
      expect(requestMethods, <String>['DELETE']);
    });

    test('clears the stored session after deleting an account', () async {
      final store = _MemorySessionStore()..token = 'delete-token';
      final api = ApiClient(
        config: AppConfig.parse('https://example.com'),
        sessionStore: store,
        client: MockClient((request) async {
          expect(request.method, 'DELETE');
          expect(request.url.path, '/api/auth/account');
          return _jsonResponse(200, <String, dynamic>{
            'success': true,
            'data': null,
            'message': '账号及其全部数据已永久删除',
          });
        }),
      );

      await api.deleteAccount();

      expect(store.token, isNull);
    });
  });
}

const _userJson = <String, dynamic>{
  'id': 1,
  'email': 'user@example.com',
  'time_zone': 'Asia/Shanghai',
  'created_at': '2026-08-21 00:00:00',
  'updated_at': '2026-08-21 00:00:00',
};

http.Response _jsonResponse(
  int status,
  Object body, {
  Map<String, String> headers = const <String, String>{},
}) => http.Response.bytes(
  utf8.encode(jsonEncode(body)),
  status,
  headers: <String, String>{
    'content-type': 'application/json; charset=utf-8',
    ...headers,
  },
);

class _MemorySessionStore implements SessionStore {
  String? token;

  @override
  Future<void> clearSessionToken() async {
    token = null;
  }

  @override
  Future<String?> readSessionToken() async => token;

  @override
  Future<void> writeSessionToken(String value) async {
    token = value;
  }
}
