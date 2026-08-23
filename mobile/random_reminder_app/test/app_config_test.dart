import 'package:flutter_test/flutter_test.dart';
import 'package:random_reminder_app/config/app_config.dart';

void main() {
  group('AppConfig', () {
    test('accepts HTTPS and resolves API paths', () {
      final config = AppConfig.parse('https://example.com');

      expect(
        config.endpoint('/api/reminders').toString(),
        'https://example.com/api/reminders',
      );
    });

    test('allows emulator HTTP only for local development', () {
      expect(
        AppConfig.parse('http://10.0.2.2:8000').apiBaseUri.host,
        '10.0.2.2',
      );
      expect(
        () => AppConfig.parse('http://example.com'),
        throwsFormatException,
      );
    });

    test('rejects embedded credentials and query parameters', () {
      expect(
        () => AppConfig.parse('https://user:pass@example.com'),
        throwsFormatException,
      );
      expect(
        () => AppConfig.parse('https://example.com?token=value'),
        throwsFormatException,
      );
    });
  });
}
