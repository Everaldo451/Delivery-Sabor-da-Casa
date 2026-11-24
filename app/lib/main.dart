import 'package:flutter/material.dart';

import 'screens/cart_screen.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/favorites_screen.dart';
import 'screens/order_tracking_screen.dart';
import 'services/auth_api_service.dart';
import 'services/orders_api_service.dart';
import 'theme/app_theme.dart';

void main() => runApp(const SaborDaCasaApp());

class SaborDaCasaApp extends StatelessWidget {
  const SaborDaCasaApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Sabor da Casa',
    debugShowCheckedModeBanner: false,
    theme: AppTheme.light,
    home: const _AuthGate(),
    routes: {'/home': (_) => const CasaShell()},
  );
}

class _AuthGate extends StatefulWidget {
  const _AuthGate();

  @override
  State<_AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<_AuthGate> {
  bool _carregando = true;
  bool _autenticado = false;

  @override
  void initState() {
    super.initState();
    _restaurarSessao();
  }

  Future<void> _restaurarSessao() async {
    try {
      await AuthApiService.instance.restaurarSessao();
      _autenticado = AuthApiService.instance.accessToken != null;
    } catch (_) {
      _autenticado = false;
    } finally {
      if (mounted) {
        setState(() => _carregando = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_carregando) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return _autenticado ? const CasaShell() : const LoginScreen();
  }
}

class CasaShell extends StatefulWidget {
  const CasaShell({super.key});
  @override
  State<CasaShell> createState() => _CasaShellState();
}

class _CasaShellState extends State<CasaShell> {
  int _aba = 0;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: const Text('Sabor da Casa'),
      actions: [
        IconButton(
          tooltip: 'Carrinho',
          onPressed: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const CartScreen()),
          ),
          icon: const Icon(Icons.shopping_bag_outlined),
        ),
      ],
    ),
    body: IndexedStack(
      index: _aba,
      children: [
        const HomeScreen(),
        FavoritesScreen(active: _aba == 1),
        _PedidosScreen(active: _aba == 2),
        const ProfileScreen(),
      ],
    ),
    bottomNavigationBar: NavigationBar(
      selectedIndex: _aba,
      onDestinationSelected: (i) => setState(() => _aba = i),
      destinations: const [
        NavigationDestination(
          icon: Icon(Icons.home_outlined),
          selectedIcon: Icon(Icons.home),
          label: 'Início',
        ),
        NavigationDestination(
          icon: Icon(Icons.favorite_outline),
          selectedIcon: Icon(Icons.favorite),
          label: 'Favoritos',
        ),
        NavigationDestination(
          icon: Icon(Icons.receipt_long_outlined),
          selectedIcon: Icon(Icons.receipt_long),
          label: 'Pedidos',
        ),
        NavigationDestination(
          icon: Icon(Icons.person_outline),
          selectedIcon: Icon(Icons.person),
          label: 'Perfil',
        ),
      ],
    ),
  );
}

class _PedidosScreen extends StatefulWidget {
  const _PedidosScreen({required this.active});
  final bool active;
  @override
  State<_PedidosScreen> createState() => _PedidosScreenState();
}

class _PedidosScreenState extends State<_PedidosScreen> {
  late Future<List<Map<String, dynamic>>> _future;

  Future<List<Map<String, dynamic>>> _buscar() async {
    final data = AuthApiService.instance.accessToken;
    if (data == null) {
      throw Exception('Entre na sua conta para ver os pedidos.');
    }
    return OrdersApiService.instance.listar();
  }

  @override
  void initState() {
    super.initState();
    _future = _buscar();
  }

  @override
  void didUpdateWidget(covariant _PedidosScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active && !oldWidget.active) {
      _future = _buscar();
    }
  }

  @override
  Widget build(
    BuildContext context,
  ) => FutureBuilder<List<Map<String, dynamic>>>(
    future: _future,
    builder: (context, snapshot) {
      if (snapshot.connectionState == ConnectionState.waiting) {
        return const Center(child: CircularProgressIndicator());
      }

      if (snapshot.hasError) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(snapshot.error.toString()),
                TextButton(
                  onPressed: () => setState(() => _future = _buscar()),
                  child: const Text('Atualizar'),
                ),
              ],
            ),
          ),
        );
      }

      final pedidos = snapshot.data ?? [];
      return RefreshIndicator(
        onRefresh: () async => setState(() => _future = _buscar()),
        child: pedidos.isEmpty
            ? ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                children: const [
                  SizedBox(height: 180),
                  Center(child: Text('Você ainda não fez pedidos.')),
                ],
              )
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Text(
                    'Seus pedidos',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 16),
                  for (final pedido in pedidos)
                    Card(
                      child: ListTile(
                        leading: const CircleAvatar(
                          child: Icon(Icons.receipt_long),
                        ),
                        title: Text('Pedido #${pedido['id']}'),
                        subtitle: Text(
                          '${pedido['status']} · '
                          '${pedido['itens'] is List ? (pedido['itens'] as List).length : 0} itens',
                        ),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              'R\$ ${(pedido['total'] as num).toStringAsFixed(2).replaceAll('.', ',')}',
                            ),
                            const Icon(Icons.chevron_right, size: 18),
                          ],
                        ),
                        onTap: () async {
                          await Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => OrderTrackingScreen(
                                pedidoId: pedido['id'].toString(),
                              ),
                            ),
                          );
                          if (mounted) {
                            setState(() => _future = _buscar());
                          }
                        },
                      ),
                    ),
                ],
              ),
      );
    },
  );
}
