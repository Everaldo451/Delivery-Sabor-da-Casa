import 'package:flutter/material.dart';

import '../services/store_api.dart';

class FavoritesScreen extends StatefulWidget {
  const FavoritesScreen({super.key, required this.active});
  final bool active;

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  late Future<List<Map<String, dynamic>>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void didUpdateWidget(covariant FavoritesScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active && !oldWidget.active) {
      _future = _load();
    }
  }

  Future<List<Map<String, dynamic>>> _load() async {
    final results = await Future.wait([
      StoreApi.instance.favoritos(),
      StoreApi.instance.cardapio(),
    ]);
    final ids = results[0].map((item) => item['prato_id'].toString()).toSet();
    return results[1].where((dish) => ids.contains(dish['id'].toString())).toList();
  }

  Future<void> _remove(String id) async {
    try {
      await StoreApi.instance.removerFavorito(id);
      if (mounted) setState(() => _future = _load());
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.toString().replaceFirst('Exception: ', ''))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [Text(snapshot.error.toString(), textAlign: TextAlign.center), TextButton(onPressed: () => setState(() => _future = _load()), child: const Text('Tentar novamente'))]));
          }
          final dishes = snapshot.data ?? [];
          if (dishes.isEmpty) {
            return const Center(child: Text('Seus pratos favoritos aparecerão aqui.'));
          }
          return RefreshIndicator(
            onRefresh: () async => setState(() => _future = _load()),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('Seus favoritos', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 12),
                ...dishes.map((dish) => Card(
                      child: ListTile(
                        leading: const CircleAvatar(child: Icon(Icons.restaurant)),
                        title: Text(dish['nome'].toString()),
                        subtitle: Text(dish['descricao'].toString(), maxLines: 2, overflow: TextOverflow.ellipsis),
                        trailing: IconButton(
                          tooltip: 'Remover dos favoritos',
                          onPressed: () => _remove(dish['id'].toString()),
                          icon: const Icon(Icons.favorite, color: Color(0xFFB93A1E)),
                        ),
                      ),
                    )),
              ],
            ),
          );
        },
      );
}
