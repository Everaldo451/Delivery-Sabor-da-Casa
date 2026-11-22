import 'package:flutter/material.dart';

import 'theme/app_theme.dart';
import 'screens/login_screen.dart';

void main() => runApp(const SaborDaCasaApp());

class SaborDaCasaApp extends StatelessWidget {
  const SaborDaCasaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sabor da Casa',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      home: const LoginScreen(),
      routes: {
        '/home': (_) => const CasaShell(),
      },
    );
  }
}

class CasaShell extends StatefulWidget {
  const CasaShell({super.key});

  @override
  State<CasaShell> createState() => _CasaShellState();
}

class _CasaShellState extends State<CasaShell> {
  int _aba = 0;

  static const _telas = <Widget>[
    _Placeholder('Início'),
    _Placeholder('Cardápio'),
    _Placeholder('Pedidos'),
    _Placeholder('Perfil'),
  ];
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sabor da Casa')),
      body: _telas[_aba],
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
        },
        icon: const Icon(Icons.shopping_bag_outlined),
        label: const Text('Carrinho'),
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
            icon: Icon(Icons.restaurant_menu_outlined),
            selectedIcon: Icon(Icons.restaurant_menu),
            label: 'Cardápio',
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
}
class _Placeholder extends StatelessWidget {
  const _Placeholder(this.nome);
  final String nome;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(nome, style: Theme.of(context).textTheme.headlineMedium),
    );
  }
}