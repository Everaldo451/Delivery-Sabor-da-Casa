import 'package:flutter/material.dart';

import '../services/store_api.dart';

class CheckoutScreen extends StatefulWidget {
  const CheckoutScreen({super.key, required this.itens});
  final List<Map<String, dynamic>> itens;
  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  final _form = GlobalKey<FormState>();
  final _rua = TextEditingController();
  final _numero = TextEditingController();
  final _bairro = TextEditingController();
  final _cep = TextEditingController();
  final _complemento = TextEditingController();
  final _lat = TextEditingController();
  final _lon = TextEditingController();
  final _cupom = TextEditingController();
  String _forma = 'pix';
  bool _loading = false;

  @override
  void dispose() { _rua.dispose(); _numero.dispose(); _bairro.dispose(); _cep.dispose(); _complemento.dispose(); _lat.dispose(); _lon.dispose(); _cupom.dispose(); super.dispose(); }

  String? _required(String? v) => v == null || v.trim().isEmpty ? 'Campo obrigatório' : null;

  Future<void> _finalizar() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      final pedido = await StoreApi.instance.criarPedido(
        itens: widget.itens.map((item) => {'prato_id': item['prato_id'], 'quantidade': item['quantidade'], if (item['observacao'] != null) 'observacao': item['observacao']}).toList(),
        endereco: {
          'rua': _rua.text.trim(), 'numero': _numero.text.trim(), 'bairro': _bairro.text.trim(),
          'cep': _cep.text.replaceAll(RegExp(r'[^0-9]'), ''),
          if (_complemento.text.trim().isNotEmpty) 'complemento': _complemento.text.trim(),
          'localizacao': {'latitude': double.parse(_lat.text.replaceAll(',', '.')), 'longitude': double.parse(_lon.text.replaceAll(',', '.'))},
        },
        formaPagamento: _forma,
        cupom: _cupom.text.trim().isEmpty ? null : _cupom.text.trim(),
      );
      final pagamento = await StoreApi.instance.checkout(pedido['id'].toString(), _forma);
      await StoreApi.instance.limparCarrinho();
      if (!mounted) return;
      final aprovado = pagamento['status'] == 'aprovado';
      await showDialog<void>(context: context, barrierDismissible: false, builder: (context) => AlertDialog(
        icon: Icon(aprovado ? Icons.check_circle_outline : Icons.error_outline, color: aprovado ? Colors.green : Colors.red, size: 42),
        title: Text(aprovado ? 'Pedido confirmado!' : 'Pagamento não aprovado'),
        content: Text('Pedido #${pedido['id']}\nTotal: R\$ ${(pedido['total'] as num).toStringAsFixed(2).replaceAll('.', ',')}\nPagamento: ${pagamento['status']}'),
        actions: [FilledButton(onPressed: () => Navigator.pop(context), child: const Text('Concluir'))],
      ));
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst('Exception: ', '')), duration: const Duration(seconds: 5)));
    } finally { if (mounted) setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Entrega e pagamento')),
    body: Form(key: _form, child: ListView(padding: const EdgeInsets.all(20), children: [
      Text('Onde entregamos?', style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(height: 12),
      TextFormField(controller: _rua, decoration: const InputDecoration(labelText: 'Rua', prefixIcon: Icon(Icons.signpost_outlined)), validator: _required),
      const SizedBox(height: 12),
      Row(children: [Expanded(flex: 2, child: TextFormField(controller: _numero, decoration: const InputDecoration(labelText: 'Número'), validator: _required)), const SizedBox(width: 12), Expanded(flex: 3, child: TextFormField(controller: _bairro, decoration: const InputDecoration(labelText: 'Bairro'), validator: _required))]),
      const SizedBox(height: 12),
      Row(children: [Expanded(child: TextFormField(controller: _cep, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'CEP', prefixIcon: Icon(Icons.local_post_office_outlined)), validator: (v) => v == null || v.replaceAll(RegExp(r'\D'), '').length != 8 ? 'Informe um CEP com 8 dígitos' : null)), const SizedBox(width: 12), Expanded(child: TextFormField(controller: _complemento, decoration: const InputDecoration(labelText: 'Complemento (opcional)')))]),
      const SizedBox(height: 12),
      const Text('Localização para calcular a entrega', style: TextStyle(fontWeight: FontWeight.w600)),
      const SizedBox(height: 4),
      Text('Informe a latitude e longitude do endereço. O pedido só é aceito dentro das zonas atendidas.', style: Theme.of(context).textTheme.bodySmall),
      const SizedBox(height: 10),
      Row(children: [Expanded(child: TextFormField(controller: _lat, keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true), decoration: const InputDecoration(labelText: 'Latitude'), validator: (v) => double.tryParse((v ?? '').replaceAll(',', '.')) == null ? 'Coordenada inválida' : null)), const SizedBox(width: 12), Expanded(child: TextFormField(controller: _lon, keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true), decoration: const InputDecoration(labelText: 'Longitude'), validator: (v) => double.tryParse((v ?? '').replaceAll(',', '.')) == null ? 'Coordenada inválida' : null))]),
      const SizedBox(height: 24),
      Text('Como deseja pagar?', style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(height: 8),
      RadioListTile<String>(contentPadding: EdgeInsets.zero, value: 'pix', groupValue: _forma, onChanged: (v) => setState(() => _forma = v!), title: const Text('Pix'), secondary: const Icon(Icons.qr_code_2)),
      RadioListTile<String>(contentPadding: EdgeInsets.zero, value: 'cartao', groupValue: _forma, onChanged: (v) => setState(() => _forma = v!), title: const Text('Cartão'), secondary: const Icon(Icons.credit_card)),
      RadioListTile<String>(contentPadding: EdgeInsets.zero, value: 'dinheiro', groupValue: _forma, onChanged: (v) => setState(() => _forma = v!), title: const Text('Dinheiro'), secondary: const Icon(Icons.payments_outlined)),
      const SizedBox(height: 12),
      TextFormField(controller: _cupom, textCapitalization: TextCapitalization.characters, decoration: const InputDecoration(labelText: 'Cupom de desconto (opcional)', prefixIcon: Icon(Icons.sell_outlined))),
      const SizedBox(height: 24),
      FilledButton(onPressed: _loading ? null : _finalizar, child: _loading ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Text('Confirmar pedido e pagar')),
      const SizedBox(height: 12),
      Text('O valor do pedido e a taxa de entrega são calculados pelo servidor.', textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
    ])),
  );
}
