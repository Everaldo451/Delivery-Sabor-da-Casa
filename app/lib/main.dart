import 'package:flutter/material.dart';

import 'screens/cart_screen.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/favorites_screen.dart';
import 'services/store_api.dart';
import 'theme/app_theme.dart';

void main() => runApp(const SaborDaCasaApp());

class SaborDaCasaApp extends StatelessWidget {
  const SaborDaCasaApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Sabor da Casa',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        home: const LoginScreen(),
        routes: {'/home': (_) => const CasaShell()},
      );
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
          actions: [IconButton(tooltip: 'Carrinho', onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CartScreen())), icon: const Icon(Icons.shopping_bag_outlined))],
        ),
        body: IndexedStack(index: _aba, children: [
          const HomeScreen(),
          FavoritesScreen(active: _aba == 1),
          const _PedidosScreen(),
          const ProfileScreen(),
        ]),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _aba,
          onDestinationSelected: (i) => setState(() => _aba = i),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Início'),
            NavigationDestination(icon: Icon(Icons.favorite_outline), selectedIcon: Icon(Icons.favorite), label: 'Favoritos'),
            NavigationDestination(icon: Icon(Icons.receipt_long_outlined), selectedIcon: Icon(Icons.receipt_long), label: 'Pedidos'),
            NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Perfil'),
          ],
        ),
      );
}

class _PedidosScreen extends StatefulWidget {
  const _PedidosScreen();
  @override
  State<_PedidosScreen> createState() => _PedidosScreenState();
}

class _PedidosScreenState extends State<_PedidosScreen> {
  late Future<List<Map<String, dynamic>>> _future;
  Future<List<Map<String, dynamic>>> _buscar() async {
    final data = StoreApi.instance.accessToken;
    if (data == null) throw Exception('Entre na sua conta para ver os pedidos.');
    // GET /pedidos is a customer-scoped endpoint.
    final result = await StoreApi.instance.requestPedidos();
    return result;
  }
  @override
  void initState() { super.initState(); _future = _buscar(); }
  @override
  Widget build(BuildContext context) => FutureBuilder<List<Map<String, dynamic>>>(future: _future, builder: (context, snapshot) {
    if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
    if (snapshot.hasError) return Center(child: Padding(padding: const EdgeInsets.all(24), child: Column(mainAxisSize: MainAxisSize.min, children: [Text(snapshot.error.toString()), TextButton(onPressed: () => setState(() => _future = _buscar()), child: const Text('Atualizar'))])));
    final pedidos = snapshot.data ?? [];
    if (pedidos.isEmpty) return const Center(child: Text('Você ainda não fez pedidos.'));
    return RefreshIndicator(onRefresh: () async => setState(() => _future = _buscar()), child: ListView(padding: const EdgeInsets.all(16), children: [Text('Seus pedidos', style: Theme.of(context).textTheme.headlineSmall), const SizedBox(height: 16), ...pedidos.map((p) => Card(child: ListTile(leading: const CircleAvatar(child: Icon(Icons.receipt_long)), title: Text('Pedido #${p['id']}'), subtitle: Text('${p['status']} · ${p['itens'] is List ? (p['itens'] as List).length : 0} itens'), trailing: Text('R\$ ${(p['total'] as num).toStringAsFixed(2).replaceAll('.', ',')}'))))]));
  });
}

