import 'package:flutter_test/flutter_test.dart';
import 'package:random_reminder_app/models/models.dart';

void main() {
  test('ReminderSettings parses the backend shape and emits update fields', () {
    final settings = ReminderSettings.fromJson(<String, dynamic>{
      'id': 4,
      'user_id': 9,
      'enabled': true,
      'all_day': false,
      'start_time': '09:00',
      'end_time': '18:00',
      'times_per_day': 4,
      'minimum_interval': 60,
      'created_at': '2026-08-21 00:00:00',
      'updated_at': '2026-08-21 00:00:00',
    });

    expect(settings.userId, 9);
    expect(settings.toUpdateJson(), <String, dynamic>{
      'enabled': true,
      'all_day': false,
      'start_time': '09:00',
      'end_time': '18:00',
      'times_per_day': 4,
      'minimum_interval': 60,
    });
  });

  test('DailySchedule exposes pending state', () {
    final schedule = DailySchedule.fromJson(<String, dynamic>{
      'id': 1,
      'schedule_date': '2026-08-21',
      'scheduled_time': '12:30',
      'reminder_id': 3,
      'content': '起来走走',
      'status': 'pending',
      'created_at': '2026-08-21 00:00:00',
    });

    expect(schedule.isPending, isTrue);
  });
}
