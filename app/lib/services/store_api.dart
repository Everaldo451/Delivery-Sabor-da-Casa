import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

/// Client for the Sabor da Casa API. Android emulador usa 10.0.2.2 para o host.
class StoreApi {
  StoreApi._();
  static final StoreApi instance = StoreApi._();
  static const String _apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );
  static String get baseUrl => _apiBaseUrl.isNotEmpty
      ? _apiBaseUrl
      : kIsWeb
          ? 'http://localhost:8000'
          : 'http://10.0.2.2:8000';

  String? _accessToken;
  String? _refreshToken;
  String? get accessToken => _accessToken;
  bool get autenticado => _accessToken != null;

  Future<dynamic> _request(
    String method,
    String path, {
    Object? body,
    bool autenticado = false,
    bool tentarRefresh = true,
  }) async {
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
          response = await http.delete(uri, headers: headers, body: requestBody);
          break;
        default:
          throw StateError('Método HTTP não suportado');
      }
    } on Exception catch (e) {
      throw Exception('Não foi possível conectar à API em $baseUrl. $e');
    }
    final decoded = response.body.isEmpty ? null : jsonDecode(response.body);
    if (response.statusCode == 401 &&
        autenticado &&
        tentarRefresh &&
        _refreshToken != null) {
      try {
        final tokens = await _request(
          'POST',
          '/auth/refresh',
          body: {'refresh_token': _refreshToken},
        ) as Map<String, dynamic>;
        _accessToken = tokens['access_token'] as String?;
        _refreshToken = tokens['refresh_token'] as String?;
        return _request(method, path,
            body: body, autenticado: autenticado, tentarRefresh: false);
      } catch (_) {
        limparSessao();
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

  Future<void> login(String email, String senha) async {
    final data = await _request('POST', '/auth/login', body: {
      'email': email.trim(),
      'senha': senha,
    }) as Map<String, dynamic>;
    _accessToken = data['access_token'] as String?;
    _refreshToken = data['refresh_token'] as String?;
  }

  Future<void> cadastrar(String nome, String email, String senha) async {
    await _request('POST', '/users', body: {
      'nome': nome.trim(),
      'email': email.trim(),
      'senha': senha,
    });
    await login(email, senha);
  }

  Future<List<Map<String, dynamic>>> cardapio({String? categoria}) async {
    final path = categoria == null
        ? '/cardapio'
        : '/cardapio?categoria=${Uri.encodeQueryComponent(categoria)}';
    final data = await _request('GET', path) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> categorias() async {
    final data = await _request('GET', '/cardapio/categorias') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> obterCarrinho() async {
    final data = await _request('GET', '/carrinho', autenticado: true)
        as Map<String, dynamic>;
    return (data['itens'] as List<dynamic>).cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> adicionarItem(
      String pratoId, int quantidade) async {
    final data = await _request('POST', '/carrinho/itens',
        autenticado: true,
        body: {'prato_id': pratoId, 'quantidade': quantidade});
    return ((data as Map<String, dynamic>)['itens'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> atualizarItem(
      String pratoId, int quantidade) async {
    final data = await _request('PATCH', '/carrinho/itens/${Uri.encodeComponent(pratoId)}',
        autenticado: true, body: {'quantidade': quantidade});
    return ((data as Map<String, dynamic>)['itens'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> removerItem(String pratoId) async {
    final data = await _request(
        'DELETE', '/carrinho/itens/${Uri.encodeComponent(pratoId)}',
        autenticado: true);
    return ((data as Map<String, dynamic>)['itens'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  Future<void> limparCarrinho() async =>
      _request('DELETE', '/carrinho', autenticado: true);

  Future<List<Map<String, dynamic>>> requestPedidos() async {
    final data = await _request('GET', '/pedidos', autenticado: true)
        as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> criarPedido({
    required List<Map<String, dynamic>> itens,
    required Map<String, dynamic> endereco,
    required String formaPagamento,
    String? cupom,
  }) async =>
      await _request('POST', '/pedidos', autenticado: true, body: {
        'itens': itens,
        'endereco_entrega': endereco,
        'forma_pagamento': formaPagamento,
        if (cupom != null && cupom.isNotEmpty) 'cupom_codigo': cupom,
      }) as Map<String, dynamic>;

  Future<Map<String, dynamic>> checkout(String pedidoId, String method) async =>
      await _request('POST', '/checkout', autenticado: true, body: {
        'pedido_id': pedidoId,
        'method': method,
      }) as Map<String, dynamic>;

  Future<void> sair() async {
    final refreshToken = _refreshToken;
    try {
      if (_accessToken != null) {
        await _request('POST', '/auth/logout', autenticado: true,
            body: {'refresh_token': refreshToken});
      }
    } finally {
      limparSessao();
    }
  }

  void limparSessao() {
    _accessToken = null;
    _refreshToken = null;
  }
}
