import 'api_client.dart';

class CouponApiService {
  CouponApiService._();

  static final CouponApiService instance = CouponApiService._();
  final ApiClient _client = ApiClient.instance;

  Future<List<Map<String, dynamic>>> listarDisponiveis() async {
    final data = await _client.request('GET', '/cupons') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> validar(String codigo, double subtotal) async =>
      await _client.request(
        'POST',
        '/cupons/validar',
        autenticado: true,
        body: {'codigo': codigo, 'subtotal': subtotal.toStringAsFixed(2)},
      ) as Map<String, dynamic>;
}
