import 'api_client.dart';

class CartApiService {
  CartApiService._();

  static final CartApiService instance = CartApiService._();
  final ApiClient _client = ApiClient.instance;

  Future<List<Map<String, dynamic>>> obter() async {
    final data = await _client.request(
      'GET',
      '/carrinho',
      autenticado: true,
    ) as Map<String, dynamic>;
    return (data['itens'] as List<dynamic>).cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> adicionar(
    String pratoId,
    int quantidade,
  ) async {
    final data = await _client.request(
      'POST',
      '/carrinho/itens',
      autenticado: true,
      body: {'prato_id': pratoId, 'quantidade': quantidade},
    );
    return ((data as Map<String, dynamic>)['itens'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> atualizar(
    String pratoId,
    int quantidade,
  ) async {
    final path = '/carrinho/itens/${Uri.encodeComponent(pratoId)}';
    final data = await _client.request(
      'PATCH',
      path,
      autenticado: true,
      body: {'quantidade': quantidade},
    );
    return ((data as Map<String, dynamic>)['itens'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> remover(String pratoId) async {
    final path = '/carrinho/itens/${Uri.encodeComponent(pratoId)}';
    final data = await _client.request('DELETE', path, autenticado: true);
    return ((data as Map<String, dynamic>)['itens'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  Future<void> limpar() async =>
      _client.request('DELETE', '/carrinho', autenticado: true);
}
