import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

/// Cliente HTTP compartilhado; concentra URL base, headers e renovação JWT.
class ApiClient {
  ApiClient._();

  static final ApiClient instance = ApiClient._();
  static const FlutterSecureStorage _storage = FlutterSecureStorage();
  static const String _sessionKey = 'auth_tokens';
  static const String _configuredBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  static String get baseUrl => _configuredBaseUrl.isNotEmpty
      ? _configuredBaseUrl
      : kIsWeb
      ? 'http://localhost:8000'
      : 'http://10.0.2.2:8000';

  String? _accessToken;
  String? _refreshToken;
  Future<void>? _initialization;

  String? get accessToken => _accessToken;
  String? get refreshToken => _refreshToken;
  bool get autenticado => _accessToken != null;

  Future<void> inicializar() => _initialization ??= _carregarTokens();

  Future<void> _carregarTokens() async {
    final saved = await _storage.read(key: _sessionKey);
    if (saved == null) return;

    dynamic decoded;
    try {
      decoded = jsonDecode(saved);
    } on FormatException {
      await _storage.delete(key: _sessionKey);
      return;
    }
    if (decoded is! Map<String, dynamic>) {
      await _storage.delete(key: _sessionKey);
      return;
    }

    final accessToken = decoded['access_token'];
    final refreshToken = decoded['refresh_token'];
    if (accessToken is! String || refreshToken is! String) {
      await _storage.delete(key: _sessionKey);
      return;
    }
    _accessToken = accessToken;
    _refreshToken = refreshToken;
  }

  Future<void> definirTokens(Map<String, dynamic> tokens) async {
    final accessToken = tokens['access_token'] as String?;
    final refreshToken = tokens['refresh_token'] as String?;
    if (accessToken == null || refreshToken == null) {
      await limparSessao();
      return;
    }
    await _storage.write(
      key: _sessionKey,
      value: jsonEncode({
        'access_token': accessToken,
        'refresh_token': refreshToken,
      }),
    );
    _accessToken = accessToken;
    _refreshToken = refreshToken;
  }

  Future<dynamic> request(
    String method,
    String path, {
    Object? body,
    bool autenticado = false,
    bool tentarRefresh = true,
  }) async {
    await inicializar();
    final uri = Uri.parse('$baseUrl$path');
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (autenticado && _accessToken != null) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }

    late http.Response response;
    try {
      final requestBody = body == null ? null : jsonEncode(body);
      switch (method) {
        case 'GET':
          response = await http.get(uri, headers: headers);
          break;
        case 'POST':
          response = await http.post(uri, headers: headers, body: requestBody);
          break;
        case 'PUT':
          response = await http.put(uri, headers: headers, body: requestBody);
          break;
        case 'PATCH':
          response = await http.patch(uri, headers: headers, body: requestBody);
          break;
        case 'DELETE':
          response = await http.delete(
            uri,
            headers: headers,
            body: requestBody,
          );
          break;
        default:
          throw StateError('Método HTTP não suportado');
      }
    } on Exception catch (error) {
      throw Exception('Não foi possível conectar à API em $baseUrl. $error');
    }

    final decoded = response.body.isEmpty ? null : jsonDecode(response.body);
    if (response.statusCode == 401 &&
        autenticado &&
        tentarRefresh &&
        _refreshToken != null) {
      try {
        final tokens = await request(
          'POST',
          '/auth/refresh',
          body: {'refresh_token': _refreshToken},
        ) as Map<String, dynamic>;
        await definirTokens(tokens);
        return request(
          method,
          path,
          body: body,
          autenticado: autenticado,
          tentarRefresh: false,
        );
      } catch (_) {
        await limparSessao();
      }
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final message = decoded is Map
          ? (decoded['detail'] ?? decoded['message'] ?? 'Erro na solicitação')
          : 'Erro ${response.statusCode} na solicitação';
      throw Exception(message.toString());
    }
    return decoded;
  }

  Future<void> limparSessao() async {
    _accessToken = null;
    _refreshToken = null;
    await _storage.delete(key: _sessionKey);
  }
}
