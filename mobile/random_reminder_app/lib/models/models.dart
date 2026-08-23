typedef JsonMap = Map<String, dynamic>;

JsonMap requireJsonMap(Object? value, String context) {
  if (value is! Map<String, dynamic>) {
    throw FormatException('$context 返回格式不正确');
  }
  return value;
}

String requireString(JsonMap json, String key) {
  final value = json[key];
  if (value is! String) {
    throw FormatException('字段 $key 格式不正确');
  }
  return value;
}

int requireInt(JsonMap json, String key) {
  final value = json[key];
  if (value is! int) {
    throw FormatException('字段 $key 格式不正确');
  }
  return value;
}

bool requireBool(JsonMap json, String key) {
  final value = json[key];
  if (value is! bool) {
    throw FormatException('字段 $key 格式不正确');
  }
  return value;
}

class AppUser {
  const AppUser({
    required this.id,
    required this.email,
    required this.timeZone,
    required this.createdAt,
    required this.updatedAt,
  });

  factory AppUser.fromJson(JsonMap json) => AppUser(
    id: requireInt(json, 'id'),
    email: requireString(json, 'email'),
    timeZone: requireString(json, 'time_zone'),
    createdAt: requireString(json, 'created_at'),
    updatedAt: requireString(json, 'updated_at'),
  );

  final int id;
  final String email;
  final String timeZone;
  final String createdAt;
  final String updatedAt;
}

class Reminder {
  const Reminder({
    required this.id,
    required this.content,
    required this.enabled,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Reminder.fromJson(JsonMap json) => Reminder(
    id: requireInt(json, 'id'),
    content: requireString(json, 'content'),
    enabled: requireBool(json, 'enabled'),
    createdAt: requireString(json, 'created_at'),
    updatedAt: requireString(json, 'updated_at'),
  );

  final int id;
  final String content;
  final bool enabled;
  final String createdAt;
  final String updatedAt;
}

class ReminderSettings {
  const ReminderSettings({
    required this.id,
    required this.userId,
    required this.enabled,
    required this.allDay,
    required this.startTime,
    required this.endTime,
    required this.timesPerDay,
    required this.minimumInterval,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ReminderSettings.fromJson(JsonMap json) => ReminderSettings(
    id: requireInt(json, 'id'),
    userId: json['user_id'] as int?,
    enabled: requireBool(json, 'enabled'),
    allDay: requireBool(json, 'all_day'),
    startTime: json['start_time'] as String?,
    endTime: json['end_time'] as String?,
    timesPerDay: requireInt(json, 'times_per_day'),
    minimumInterval: requireInt(json, 'minimum_interval'),
    createdAt: requireString(json, 'created_at'),
    updatedAt: requireString(json, 'updated_at'),
  );

  final int id;
  final int? userId;
  final bool enabled;
  final bool allDay;
  final String? startTime;
  final String? endTime;
  final int timesPerDay;
  final int minimumInterval;
  final String createdAt;
  final String updatedAt;

  JsonMap toUpdateJson() => <String, dynamic>{
    'enabled': enabled,
    'all_day': allDay,
    'start_time': allDay ? null : startTime,
    'end_time': allDay ? null : endTime,
    'times_per_day': timesPerDay,
    'minimum_interval': minimumInterval,
  };

  ReminderSettings copyWith({
    bool? enabled,
    bool? allDay,
    String? startTime,
    String? endTime,
    int? timesPerDay,
    int? minimumInterval,
  }) => ReminderSettings(
    id: id,
    userId: userId,
    enabled: enabled ?? this.enabled,
    allDay: allDay ?? this.allDay,
    startTime: startTime ?? this.startTime,
    endTime: endTime ?? this.endTime,
    timesPerDay: timesPerDay ?? this.timesPerDay,
    minimumInterval: minimumInterval ?? this.minimumInterval,
    createdAt: createdAt,
    updatedAt: updatedAt,
  );
}

class DailySchedule {
  const DailySchedule({
    required this.id,
    required this.scheduleDate,
    required this.scheduledTime,
    required this.reminderId,
    required this.content,
    required this.status,
    required this.createdAt,
  });

  factory DailySchedule.fromJson(JsonMap json) => DailySchedule(
    id: requireInt(json, 'id'),
    scheduleDate: requireString(json, 'schedule_date'),
    scheduledTime: requireString(json, 'scheduled_time'),
    reminderId: json['reminder_id'] as int?,
    content: requireString(json, 'content'),
    status: requireString(json, 'status'),
    createdAt: requireString(json, 'created_at'),
  );

  final int id;
  final String scheduleDate;
  final String scheduledTime;
  final int? reminderId;
  final String content;
  final String status;
  final String createdAt;

  bool get isPending => status == 'pending';
}
