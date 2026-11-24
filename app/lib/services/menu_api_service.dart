import 'api_client.dart';

class MenuApiService {
  MenuApiService._();

  static final MenuApiService instance = MenuApiService._();
  final ApiClient _client = ApiClient.instance;

  Future<List<Map<String, dynamic>>> cardapio({String? categoria}) async {
    final path = categoria == null
        ? '/cardapio'
        : '/cardapio?categoria=${Uri.encodeQueryComponent(categoria)}';
    final data = await _client.request('GET', path) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> categorias() async {
    final data =
        await _client.request('GET', '/cardapio/categorias') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }
}
