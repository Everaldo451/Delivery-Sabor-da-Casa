import 'api_client.dart';

class OrdersApiService {
  OrdersApiService._();

  static final OrdersApiService instance = OrdersApiService._();
  final ApiClient _client = ApiClient.instance;

  Future<List<Map<String, dynamic>>> listar() async {
    final data = await _client.request(
      'GET',
      '/pedidos',
      autenticado: true,
    ) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> detalhe(String pedidoId) async =>
      await _client.request(
        'GET',
        '/pedidos/${Uri.encodeComponent(pedidoId)}',
        autenticado: true,
      ) as Map<String, dynamic>;

  Future<Map<String, dynamic>> criar({
    required List<Map<String, dynamic>> itens,
    required Map<String, dynamic> endereco,
    required String formaPagamento,
    String? cupom,
  }) async => await _client.request(
    'POST',
    '/pedidos',
    autenticado: true,
    body: {
      'itens': itens,
      'endereco_entrega': endereco,
      'forma_pagamento': formaPagamento,
      if (cupom != null && cupom.isNotEmpty) 'cupom_codigo': cupom,
    },
  ) as Map<String, dynamic>;

  Future<Map<String, dynamic>> consultarCep(String cep) async =>
      await _client.request('GET', '/pedidos/cep/${Uri.encodeComponent(cep)}')
          as Map<String, dynamic>;

  Future<List<Map<String, dynamic>>> sugerirEndereco(String consulta) async {
    final path = '/enderecos/sugestoes?q=${Uri.encodeQueryComponent(consulta)}';
    final data =
        await _client.request('GET', path, autenticado: true) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }
}
