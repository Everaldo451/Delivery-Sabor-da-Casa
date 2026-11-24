import 'api_client.dart';

class AuthApiService {
  AuthApiService._();

  static final AuthApiService instance = AuthApiService._();
  final ApiClient _client = ApiClient.instance;

  String? get accessToken => _client.accessToken;

  Future<void> restaurarSessao() => _client.inicializar();

  Future<void> login(String email, String senha) async {
    final tokens = await _client.request(
      'POST',
      '/auth/login',
      body: {'email': email.trim(), 'senha': senha},
    ) as Map<String, dynamic>;
    await _client.definirTokens(tokens);
  }

  Future<void> cadastrar(String nome, String email, String senha) async {
    await _client.request(
      'POST',
      '/users',
      body: {'nome': nome.trim(), 'email': email.trim(), 'senha': senha},
    );
    await login(email, senha);
  }

  Future<void> sair() async {
    try {
      if (_client.accessToken != null) {
        await _client.request(
          'POST',
          '/auth/logout',
          autenticado: true,
          body: {'refresh_token': _client.refreshToken},
        );
      }
    } finally {
      await _client.limparSessao();
    }
  }

  Future<void> limparSessao() => _client.limparSessao();
}
