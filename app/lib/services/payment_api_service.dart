import 'api_client.dart';

class PaymentApiService {
  PaymentApiService._();

  static final PaymentApiService instance = PaymentApiService._();
  final ApiClient _client = ApiClient.instance;

  Future<Map<String, dynamic>> checkout(String pedidoId, String method) async =>
      await _client.request(
        'POST',
        '/checkout',
        autenticado: true,
        body: {'pedido_id': pedidoId, 'method': method},
      ) as Map<String, dynamic>;
}
