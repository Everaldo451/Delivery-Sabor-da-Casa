import 'api_client.dart';

class UserApiService {
  UserApiService._();

  static final UserApiService instance = UserApiService._();
  final ApiClient _client = ApiClient.instance;

  Future<Map<String, dynamic>> perfil() async =>
      await _client.request('GET', '/users/me', autenticado: true)
          as Map<String, dynamic>;
}
