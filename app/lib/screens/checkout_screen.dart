import 'dart:async';

import 'package:flutter/material.dart';

import '../services/store_api.dart';

class CheckoutScreen extends StatefulWidget {
  const CheckoutScreen({super.key, required this.itens, required this.pratos, required this.subtotalEstimado});
  final List<Map<String, dynamic>> itens;
  final Map<String, Map<String, dynamic>> pratos;
  final double subtotalEstimado;
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
  final _cupom = TextEditingController();
  Timer? _debounceSugestoes;
  int _idBuscaEndereco = 0;
  List<Map<String, dynamic>> _sugestoesEndereco = [];
  Map<String, dynamic>? _localizacao;
  String? _cidadeEstado;
  String? _enderecoSelecionado;
  String _forma = 'pix';
  bool _loading = false;
  bool _consultandoCep = false;
  bool _buscandoEndereco = false;
  bool _validandoCupom = false;
  double? _descontoCupom;

  @override
  void dispose() { _debounceSugestoes?.cancel(); _rua.dispose(); _numero.dispose(); _bairro.dispose(); _cep.dispose(); _complemento.dispose(); _cupom.dispose(); super.dispose(); }

  String? _required(String? v) => v == null || v.trim().isEmpty ? 'Campo obrigatório' : null;

  String _money(double value) => 'R\$ ${value.toStringAsFixed(2).replaceAll('.', ',')}';

  Future<void> _consultarCep() async {
    _debounceSugestoes?.cancel();
    _idBuscaEndereco++;
    final cep = _cep.text.replaceAll(RegExp(r'\D'), '');
    if (cep.length != 8) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Informe um CEP com 8 dígitos.')));
      return;
    }
    setState(() => _consultandoCep = true);
    try {
      final endereco = await StoreApi.instance.consultarCep(cep);
      if (!mounted) return;
      setState(() {
        _rua.text = endereco['rua']?.toString() ?? '';
        _bairro.text = endereco['bairro']?.toString() ?? '';
        _cidadeEstado = '${endereco['cidade']}, ${endereco['estado']}';
        _localizacao = null;
        _enderecoSelecionado = null;
        _sugestoesEndereco = [];
        _buscandoEndereco = false;
      });
      if (_numero.text.trim().isNotEmpty) _agendarBuscaEndereco();
    } catch (e) {
      if (mounted) {
        setState(() { _localizacao = null; _cidadeEstado = null; _buscandoEndereco = false; });
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))));
      }
    } finally {
      if (mounted) setState(() => _consultandoCep = false);
    }
  }

  void _agendarBuscaEndereco() {
    _debounceSugestoes?.cancel();
    _idBuscaEndereco++;
    final consulta = [
      _rua.text.trim(),
      _numero.text.trim(),
      _bairro.text.trim(),
      _cidadeEstado ?? '',
      _cep.text.replaceAll(RegExp(r'\D'), ''),
      'Brasil',
    ].where((parte) => parte.isNotEmpty).join(', ');

    setState(() {
      _localizacao = null;
      _enderecoSelecionado = null;
      _sugestoesEndereco = [];
      _buscandoEndereco = false;
    });
    if (_rua.text.trim().length < 4 || consulta.length < 8) return;

    final idBusca = _idBuscaEndereco;
    _debounceSugestoes = Timer(const Duration(milliseconds: 600), () async {
      if (!mounted || idBusca != _idBuscaEndereco) return;
      setState(() => _buscandoEndereco = true);
      try {
        final sugestoes = await StoreApi.instance.sugerirEndereco(consulta);
        if (mounted && idBusca == _idBuscaEndereco) {
          setState(() => _sugestoesEndereco = sugestoes);
        }
      } catch (e) {
        if (mounted && idBusca == _idBuscaEndereco) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e.toString().replaceFirst('Exception: ', '')),
          ));
        }
      } finally {
        if (mounted && idBusca == _idBuscaEndereco) {
          setState(() => _buscandoEndereco = false);
        }
      }
    });
  }

  void _selecionarEndereco(Map<String, dynamic> sugestao) {
    _debounceSugestoes?.cancel();
    _idBuscaEndereco++;
    setState(() {
      _buscandoEndereco = false;
      final rua = sugestao['rua']?.toString();
      final numero = sugestao['numero']?.toString();
      final bairro = sugestao['bairro']?.toString();
      if (rua != null && rua.isNotEmpty) _rua.text = rua;
      if (numero != null && numero.isNotEmpty) _numero.text = numero;
      if (bairro != null && bairro.isNotEmpty) _bairro.text = bairro;
      _localizacao = {
        'latitude': sugestao['latitude'],
        'longitude': sugestao['longitude'],
      };
      _enderecoSelecionado = sugestao['descricao']?.toString();
      _sugestoesEndereco = [];
    });
  }

  Future<void> _validarCupom() async {
    if (_cupom.text.trim().isEmpty) return;
    setState(() => _validandoCupom = true);
    try {
      final result = await StoreApi.instance.validarCupom(_cupom.text.trim(), widget.subtotalEstimado);
      if (mounted) setState(() => _descontoCupom = double.tryParse(result['desconto'].toString()) ?? 0);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cupom válido para este pedido.')));
    } catch (e) {
      if (mounted) setState(() => _descontoCupom = null);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))));
    } finally {
      if (mounted) setState(() => _validandoCupom = false);
    }
  }

  Future<void> _mostrarCupons() async {
    try {
      final cupons = await StoreApi.instance.cuponsDisponiveis();
      if (!mounted) return;
      await showModalBottomSheet<void>(context: context, builder: (context) => SafeArea(child: ListView(padding: const EdgeInsets.all(16), shrinkWrap: true, children: [
        Text('Cupons disponíveis', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        if (cupons.isEmpty) const ListTile(title: Text('Nenhum cupom disponível no momento.')),
        ...cupons.map((cupom) => ListTile(leading: const Icon(Icons.sell_outlined), title: Text(cupom['codigo'].toString()), subtitle: Text(cupom['descricao'].toString()), onTap: () { _cupom.text = cupom['codigo'].toString(); setState(() => _descontoCupom = null); Navigator.pop(context); })),
      ])));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))));
    }
  }

  Future<void> _finalizar() async {
    final formState = _form.currentState;
    if (formState == null || !formState.validate()) return;
    final localizacao = _localizacao;
    if (localizacao == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Selecione uma sugestão de endereço para confirmar a localização.'),
      ));
      return;
    }
    setState(() => _loading = true);
    try {
      final pedido = await StoreApi.instance.criarPedido(
        itens: widget.itens.map((item) => {'prato_id': item['prato_id'], 'quantidade': item['quantidade'], if (item['observacao'] != null) 'observacao': item['observacao']}).toList(),
        endereco: {
          'rua': _rua.text.trim(), 'numero': _numero.text.trim(), 'bairro': _bairro.text.trim(),
          'cep': _cep.text.replaceAll(RegExp(r'[^0-9]'), ''),
          if (_complemento.text.trim().isNotEmpty) 'complemento': _complemento.text.trim(),
          'localizacao': localizacao,
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
      Text('Resumo do pedido', style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(height: 8),
      Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(children: [
        ...widget.itens.map((item) {
          final dish = widget.pratos[item['prato_id'].toString()];
          final quantity = int.tryParse(item['quantidade'].toString()) ?? 0;
          final price = double.tryParse(dish?['preco']?.toString() ?? '') ?? 0;
          return Padding(padding: const EdgeInsets.symmetric(vertical: 7), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('${quantity}x ${dish?['nome'] ?? 'Prato indisponível'}', style: Theme.of(context).textTheme.titleSmall),
              if ((item['observacao']?.toString().trim().isNotEmpty ?? false)) Text(item['observacao'].toString(), style: Theme.of(context).textTheme.bodySmall),
            ])),
            const SizedBox(width: 12),
            Text(_money(price * quantity)),
          ]));
        }),
        const Divider(height: 20),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('Subtotal'), Text(_money(widget.subtotalEstimado), style: Theme.of(context).textTheme.titleMedium)]),
        const SizedBox(height: 4),
        Align(alignment: Alignment.centerLeft, child: Text('A taxa de entrega e os descontos serão calculados pelo servidor.', style: Theme.of(context).textTheme.bodySmall)),
      ]))),
      const SizedBox(height: 24),
      Text('Onde entregamos?', style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(height: 12),
      TextFormField(controller: _rua, onChanged: (_) => _agendarBuscaEndereco(), decoration: const InputDecoration(labelText: 'Rua', prefixIcon: Icon(Icons.signpost_outlined)), validator: _required),
      const SizedBox(height: 12),
      Row(children: [Expanded(flex: 2, child: TextFormField(controller: _numero, onChanged: (_) => _agendarBuscaEndereco(), decoration: const InputDecoration(labelText: 'Número'), validator: _required)), const SizedBox(width: 12), Expanded(flex: 3, child: TextFormField(controller: _bairro, onChanged: (_) => _agendarBuscaEndereco(), decoration: const InputDecoration(labelText: 'Bairro'), validator: _required))]),
      const SizedBox(height: 12),
      Row(children: [Expanded(child: TextFormField(controller: _cep, keyboardType: TextInputType.number, onChanged: (_) { _debounceSugestoes?.cancel(); _idBuscaEndereco++; setState(() { if (_cidadeEstado != null) { _rua.clear(); _bairro.clear(); } _localizacao = null; _enderecoSelecionado = null; _cidadeEstado = null; _sugestoesEndereco = []; _buscandoEndereco = false; }); }, onFieldSubmitted: (_) => _consultarCep(), decoration: const InputDecoration(labelText: 'CEP', prefixIcon: Icon(Icons.local_post_office_outlined)), validator: (v) => v == null || v.replaceAll(RegExp(r'\D'), '').length != 8 ? 'Informe um CEP com 8 dígitos' : null)), const SizedBox(width: 8), IconButton.filled(tooltip: 'Buscar endereço pelo CEP', onPressed: _consultandoCep ? null : _consultarCep, icon: _consultandoCep ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.search))]),
      if (_cidadeEstado != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text('$_cidadeEstado', style: Theme.of(context).textTheme.bodySmall)),
      if (_buscandoEndereco) const LinearProgressIndicator(),
      if (_sugestoesEndereco.isNotEmpty) ..._sugestoesEndereco.map((sugestao) => Card(
        margin: const EdgeInsets.only(top: 6),
        child: ListTile(
          leading: const Icon(Icons.location_on_outlined),
          title: Text(sugestao['descricao']?.toString() ?? 'Endereço sugerido'),
          onTap: () => _selecionarEndereco(sugestao),
        ),
      )),
      if (_sugestoesEndereco.isNotEmpty || _enderecoSelecionado != null)
        Text('Dados do mapa: © OpenStreetMap contributors', style: Theme.of(context).textTheme.bodySmall),
      if (_enderecoSelecionado != null) Padding(
        padding: const EdgeInsets.only(top: 6),
        child: Text('Local selecionado: $_enderecoSelecionado', style: const TextStyle(color: Colors.green, fontWeight: FontWeight.w600)),
      ),
      const SizedBox(height: 12),
      TextFormField(controller: _complemento, decoration: const InputDecoration(labelText: 'Complemento (opcional)')),
      const SizedBox(height: 24),
      Text('Como deseja pagar?', style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(height: 8),
      RadioListTile<String>(contentPadding: EdgeInsets.zero, value: 'pix', groupValue: _forma, onChanged: (value) { if (value != null) setState(() => _forma = value); }, title: const Text('Pix'), secondary: const Icon(Icons.qr_code_2)),
      RadioListTile<String>(contentPadding: EdgeInsets.zero, value: 'cartao', groupValue: _forma, onChanged: (value) { if (value != null) setState(() => _forma = value); }, title: const Text('Cartão'), secondary: const Icon(Icons.credit_card)),
      RadioListTile<String>(contentPadding: EdgeInsets.zero, value: 'dinheiro', groupValue: _forma, onChanged: (value) { if (value != null) setState(() => _forma = value); }, title: const Text('Dinheiro'), secondary: const Icon(Icons.payments_outlined)),
      const SizedBox(height: 12),
      TextFormField(controller: _cupom, textCapitalization: TextCapitalization.characters, onChanged: (_) => setState(() => _descontoCupom = null), decoration: const InputDecoration(labelText: 'Cupom de desconto (opcional)', prefixIcon: Icon(Icons.sell_outlined))),
      Row(children: [TextButton.icon(onPressed: _mostrarCupons, icon: const Icon(Icons.local_offer_outlined), label: const Text('Ver cupons')), const SizedBox(width: 8), OutlinedButton(style: OutlinedButton.styleFrom(minimumSize: const Size(0, 48), padding: const EdgeInsets.symmetric(horizontal: 16)), onPressed: _validandoCupom ? null : _validarCupom, child: _validandoCupom ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Aplicar'))]),
      if (_descontoCupom != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text('Desconto aplicado: ${_money(_descontoCupom!)}', style: const TextStyle(color: Colors.green, fontWeight: FontWeight.w600))),
      const SizedBox(height: 24),
      FilledButton(onPressed: _loading ? null : _finalizar, child: _loading ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Text('Confirmar pedido e pagar')),
      const SizedBox(height: 12),
      Text('O valor do pedido e a taxa de entrega são calculados pelo servidor.', textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
    ])),
  );
}
