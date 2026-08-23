class AppConfig {
  AppConfig._(this.apiBaseUri);

  static const _configuredApiBase = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://getpromptide.com',
  );

  final Uri apiBaseUri;

  factory AppConfig.fromEnvironment() => AppConfig.parse(_configuredApiBase);

  factory AppConfig.parse(String value) {
    final uri = Uri.tryParse(value.trim());
    if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
      throw const FormatException('API_BASE_URL 必须是完整的网址');
    }

    final isLocalDevelopment = <String>{
      'localhost',
      '127.0.0.1',
      '10.0.2.2',
    }.contains(uri.host.toLowerCase());

    if (uri.scheme != 'https' &&
        !(uri.scheme == 'http' && isLocalDevelopment)) {
      throw const FormatException('API_BASE_URL 必须使用 HTTPS');
    }
    if (uri.userInfo.isNotEmpty || uri.hasQuery || uri.hasFragment) {
      throw const FormatException('API_BASE_URL 不能包含凭据、查询参数或片段');
    }

    return AppConfig._(
      uri.replace(path: uri.path.endsWith('/') ? uri.path : '${uri.path}/'),
    );
  }

  Uri endpoint(String path, {Map<String, String>? queryParameters}) {
    final relativePath = path.startsWith('/') ? path.substring(1) : path;
    return apiBaseUri
        .resolve(relativePath)
        .replace(queryParameters: queryParameters);
  }
}
