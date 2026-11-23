import 'package:flutter/material.dart';

import '../services/store_api.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = StoreApi.instance;
  List<Map<String, dynamic>> _categorias = [];
  List<Map<String, dynamic>> _pratos = [];
  Set<String> _favoritos = {};
  String? _categoria;
  bool _carregando = true;
  String? _erro;

  @override
  void initState() { super.initState(); _carregar(); }

  Future<void> _carregar() async {
    setState(() { _carregando = true; _erro = null; });
    try {
      final resultados = await Future.wait([_api.categorias(), _api.cardapio(categoria: _categoria), _api.favoritos()]);
      if (!mounted) return;
      setState(() { _categorias = resultados[0]; _pratos = resultados[1]; _favoritos = resultados[2].map((f) => f['prato_id'].toString()).toSet(); _carregando = false; });
    } catch (e) {
      if (mounted) setState(() { _erro = e.toString().replaceFirst('Exception: ', ''); _carregando = false; });
    }
  }

  Future<void> _adicionar(Map<String, dynamic> prato) async {
    try {
      await _api.adicionarItem(prato['id'].toString(), 1);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${prato['nome']} adicionado ao carrinho')));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))));
    }
  }

  Future<void> _alternarFavorito(Map<String, dynamic> prato) async {
    final id = prato['id'].toString();
    final removendo = _favoritos.contains(id);
    try {
      if (removendo) { await _api.removerFavorito(id); } else { await _api.adicionarFavorito(id); }
      if (mounted) setState(() { removendo ? _favoritos.remove(id) : _favoritos.add(id); });
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(removendo ? 'Prato removido dos favoritos.' : 'Prato salvo nos favoritos.')));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))));
    }
  }

  String _preco(dynamic valor) => 'R\$ ${(double.tryParse(valor.toString()) ?? 0).toStringAsFixed(2).replaceAll('.', ',')}';

  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: _carregar,
        child: ListView(padding: const EdgeInsets.fromLTRB(20, 12, 20, 100), children: [
          Container(padding: const EdgeInsets.all(22), decoration: BoxDecoration(color: const Color(0xFFB93A1E), borderRadius: BorderRadius.circular(22)),
            child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('SABOR DE CASA', style: TextStyle(color: Colors.white70, letterSpacing: 1.4, fontWeight: FontWeight.bold)),
              SizedBox(height: 10), Text('Seu almoço\ncom gostinho de lar.', style: TextStyle(color: Colors.white, fontSize: 26, height: 1.2, fontWeight: FontWeight.bold)),
              SizedBox(height: 8), Text('Feito na hora, entregue com carinho.', style: TextStyle(color: Colors.white)),
            ])),
          const SizedBox(height: 24),
          Text('Nosso cardápio', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 12),
          if (_categorias.isNotEmpty) SizedBox(height: 42, child: ListView(scrollDirection: Axis.horizontal, children: [
            Padding(padding: const EdgeInsets.only(right: 8), child: ChoiceChip(label: const Text('Todos'), selected: _categoria == null, onSelected: (_) { setState(() => _categoria = null); _carregar(); })),
            ..._categorias.map((c) { final nome = c['nome'].toString(); return Padding(padding: const EdgeInsets.only(right: 8), child: ChoiceChip(label: Text(nome), selected: _categoria == nome, onSelected: (_) { setState(() => _categoria = nome); _carregar(); })); }),
          ])),
          const SizedBox(height: 12),
          if (_carregando) const Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator()))
          else if (_erro != null) Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(children: [Text(_erro!, textAlign: TextAlign.center), TextButton(onPressed: _carregar, child: const Text('Tentar novamente'))])))
          else if (_pratos.isEmpty) const Padding(padding: EdgeInsets.all(24), child: Text('Nenhum prato disponível nesta categoria.'))
          else ..._pratos.where((p) => p['disponivel'] == true).map((p) => _PratoCard(prato: p, preco: _preco(p['preco']), favoritado: _favoritos.contains(p['id'].toString()), favoritar: () => _alternarFavorito(p), adicionar: () => _adicionar(p))),
        ]),
      );
}

class _PratoCard extends StatelessWidget {
  const _PratoCard({required this.prato, required this.preco, required this.adicionar, required this.favoritado, required this.favoritar});
  final Map<String, dynamic> prato;
  final String preco;
  final VoidCallback adicionar;
  final bool favoritado;
  final VoidCallback favoritar;

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.only(bottom: 12),
        child: Padding(padding: const EdgeInsets.all(16), child: Row(children: [
          Container(width: 66, height: 66, decoration: BoxDecoration(color: const Color(0xFFF7E8DA), borderRadius: BorderRadius.circular(16)), child: const Icon(Icons.restaurant, color: Color(0xFFB93A1E), size: 30)),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(prato['nome'].toString(), style: Theme.of(context).textTheme.titleMedium), const SizedBox(height: 4), Text(prato['descricao'].toString(), maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall), const SizedBox(height: 8), Text(preco, style: const TextStyle(color: Color(0xFFB93A1E), fontWeight: FontWeight.bold))])),
          Column(mainAxisSize: MainAxisSize.min, children: [IconButton(onPressed: favoritar, icon: Icon(favoritado ? Icons.favorite : Icons.favorite_border, color: const Color(0xFFB93A1E))), IconButton.filled(onPressed: adicionar, icon: const Icon(Icons.add_shopping_cart))]),
        ])),
      );
}
