import 'package:flutter/material.dart';

import '../services/store_api.dart';
import 'checkout_screen.dart';

class CartScreen extends StatefulWidget {
  const CartScreen({super.key});
  @override
  State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  final _api = StoreApi.instance;
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _items = [];
  Map<String, Map<String, dynamic>> _pratos = {};

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final results = await Future.wait([_api.obterCarrinho(), _api.cardapio()]);
      final products = {for (final p in results[1]) p['id'].toString(): p};
      if (mounted) setState(() { _items = results[0]; _pratos = products; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString().replaceFirst('Exception: ', ''); _loading = false; });
    }
  }

  Future<void> _change(String id, int qty) async {
    try {
      final updated = qty == 0 ? await _api.removerItem(id) : await _api.atualizarItem(id, qty);
      if (mounted) setState(() => _items = updated);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))));
    }
  }

  double get _subtotal => _items.fold<double>(0, (total, item) {
    final prato = _pratos[item['prato_id']];
    return total + (double.tryParse(prato?['preco']?.toString() ?? '') ?? 0) * (item['quantidade'] as int);
  });
  String _money(double v) => 'R\$ ${v.toStringAsFixed(2).replaceAll('.', ',')}';

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Meu carrinho')),
        body: _loading ? const Center(child: CircularProgressIndicator())
            : _error != null ? Center(child: Padding(padding: const EdgeInsets.all(24), child: Column(mainAxisSize: MainAxisSize.min, children: [Text(_error!, textAlign: TextAlign.center), TextButton(onPressed: _load, child: const Text('Tentar novamente'))])))
            : _items.isEmpty ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [const Icon(Icons.shopping_bag_outlined, size: 64, color: Color(0xFFB93A1E)), const SizedBox(height: 12), Text('Seu carrinho está vazio', style: Theme.of(context).textTheme.titleLarge), const SizedBox(height: 8), const Text('Escolha algo gostoso no cardápio.'), const SizedBox(height: 16), FilledButton(onPressed: () => Navigator.pop(context), child: const Text('Ver cardápio'))]))
            : Column(children: [
                Expanded(child: ListView.separated(padding: const EdgeInsets.all(16), itemCount: _items.length, separatorBuilder: (_, __) => const SizedBox(height: 10), itemBuilder: (context, index) {
                  final item = _items[index]; final id = item['prato_id'].toString(); final prato = _pratos[id]; final qtd = item['quantidade'] as int;
                  return Card(child: Padding(padding: const EdgeInsets.all(14), child: Row(children: [
                    const CircleAvatar(backgroundColor: Color(0xFFF7E8DA), child: Icon(Icons.restaurant, color: Color(0xFFB93A1E))), const SizedBox(width: 12),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(prato?['nome']?.toString() ?? 'Prato indisponível', style: Theme.of(context).textTheme.titleMedium), Text(_money((double.tryParse(prato?['preco']?.toString() ?? '') ?? 0) * qtd)), if (prato == null) const Text('Este prato não está mais no cardápio.', style: TextStyle(color: Colors.red))])),
                    IconButton(onPressed: () => _change(id, qtd - 1), icon: Icon(qtd == 1 ? Icons.delete_outline : Icons.remove_circle_outline)), Text('$qtd'), IconButton(onPressed: qtd < 50 ? () => _change(id, qtd + 1) : null, icon: const Icon(Icons.add_circle_outline)),
                  ])));
                })),
                SafeArea(top: false, child: Container(padding: const EdgeInsets.fromLTRB(20, 16, 20, 16), decoration: const BoxDecoration(color: Colors.white, border: Border(top: BorderSide(color: Color(0xFFE9DFD5)))), child: Column(children: [Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('Subtotal estimado'), Text(_money(_subtotal), style: Theme.of(context).textTheme.titleLarge)]), const SizedBox(height: 12), FilledButton(onPressed: _items.any((i) => _pratos.containsKey(i['prato_id'].toString())) ? () async {
                  final result = await Navigator.push<bool>(context, MaterialPageRoute(builder: (_) => CheckoutScreen(itens: _items.where((i) => _pratos.containsKey(i['prato_id'].toString())).toList(), pratos: _pratos, subtotalEstimado: _subtotal)));
                  if (result == true) _load();
                } : null, child: const Text('Continuar para entrega e pagamento'))]))),
              ]),
      );
}
