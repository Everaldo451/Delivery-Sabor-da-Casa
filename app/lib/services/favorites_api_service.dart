import 'api_client.dart';

class FavoritesApiService {
  FavoritesApiService._();

  static final FavoritesApiService instance = FavoritesApiService._();
  final ApiClient _client = ApiClient.instance;

  Future<List<Map<String, dynamic>>> listar() async {
    final data = await _client.request(
      'GET',
      '/favoritos',
      autenticado: true,
    ) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  Future<void> adicionar(String pratoId) async {
    await _client.request(
      'PUT',
      '/favoritos/${Uri.encodeComponent(pratoId)}',
      autenticado: true,
    );
  }

  Future<void> remover(String pratoId) async {
    await _client.request(
      'DELETE',
      '/favoritos/${Uri.encodeComponent(pratoId)}',
      autenticado: true,
    );
  }
}
