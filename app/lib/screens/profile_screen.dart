import 'package:flutter/material.dart';

import '../services/store_api.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = StoreApi.instance.perfil();
  }

  Future<void> _logout() async {
    try {
      await StoreApi.instance.sair();
    } catch (_) {
      StoreApi.instance.limparSessao();
    }
    if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/', (_) => false);
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Text(snapshot.error.toString(), textAlign: TextAlign.center),
                TextButton(onPressed: () => setState(() => _future = StoreApi.instance.perfil()), child: const Text('Tentar novamente')),
              ]),
            );
          }
          final user = snapshot.data!;
          return ListView(padding: const EdgeInsets.all(24), children: [
            const SizedBox(height: 20),
            const CircleAvatar(radius: 38, child: Icon(Icons.person, size: 40)),
            const SizedBox(height: 18),
            Center(child: Text(user['nome'].toString(), style: Theme.of(context).textTheme.headlineSmall)),
            const SizedBox(height: 6),
            Center(child: Text(user['email'].toString(), style: Theme.of(context).textTheme.bodyLarge)),
            const SizedBox(height: 28),
            const Divider(),
            ListTile(leading: const Icon(Icons.badge_outlined), title: const Text('Nome'), subtitle: Text(user['nome'].toString())),
            ListTile(leading: const Icon(Icons.email_outlined), title: const Text('E-mail'), subtitle: Text(user['email'].toString())),
            const SizedBox(height: 20),
            OutlinedButton.icon(onPressed: _logout, icon: const Icon(Icons.logout), label: const Text('Sair da conta')),
          ]);
        },
      );
}
