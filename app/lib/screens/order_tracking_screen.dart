import 'dart:async';

import 'package:flutter/material.dart';

import '../services/orders_api_service.dart';

class OrderTrackingScreen extends StatefulWidget {
  const OrderTrackingScreen({super.key, required this.pedidoId});

  final String pedidoId;

  @override
  State<OrderTrackingScreen> createState() => _OrderTrackingScreenState();
}

class _OrderTrackingScreenState extends State<OrderTrackingScreen> {
  Timer? _timer;
  Map<String, dynamic>? _pedido;
  String? _erro;
  bool _carregando = true;

  @override
  void initState() {
    super.initState();
    _atualizar();
    _timer = Timer.periodic(
      const Duration(seconds: 15),
      (_) => _atualizar(silencioso: true),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _atualizar({bool silencioso = false}) async {
    if (!silencioso && mounted) {
      setState(() {
        _carregando = true;
        _erro = null;
      });
    }
    try {
      final pedido = await OrdersApiService.instance.detalhe(widget.pedidoId);
      if (mounted) {
        setState(() {
          _pedido = pedido;
          _erro = null;
          _carregando = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _erro = e.toString().replaceFirst('Exception: ', '');
          _carregando = false;
        });
      }
    }
  }

  String _statusLabel(String status) => switch (status) {
    'aguardando_pagamento' => 'Aguardando pagamento',
    'recebido' => 'Pedido recebido',
    'em_preparo' => 'Em preparo',
    'saiu_para_entrega' => 'Saiu para entrega',
    'entregue' => 'Entregue',
    'cancelado' => 'Cancelado',
    _ => status.replaceAll('_', ' '),
  };

  String _money(dynamic value) =>
      'R\$ ${(double.tryParse(value.toString()) ?? 0).toStringAsFixed(2).replaceAll('.', ',')}';

  @override
  Widget build(BuildContext context) {
    final pedido = _pedido;
    final itens = pedido?['itens'] as List<dynamic>? ?? const <dynamic>[];
    final endereco =
        pedido?['endereco_entrega'] as Map<String, dynamic>? ?? const {};

    return Scaffold(
      appBar: AppBar(
        title: Text('Pedido #${widget.pedidoId}'),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: _atualizar,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _carregando && pedido == null
          ? const Center(child: CircularProgressIndicator())
          : pedido == null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(_erro ?? 'Não foi possível carregar o pedido.'),
                    TextButton(
                      onPressed: _atualizar,
                      child: const Text('Tentar novamente'),
                    ),
                  ],
                ),
              ),
            )
          : RefreshIndicator(
              onRefresh: _atualizar,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  if (_erro != null)
                    MaterialBanner(
                      content: Text('Falha ao atualizar: $_erro'),
                      actions: [
                        TextButton(
                          onPressed: _atualizar,
                          child: const Text('Tentar'),
                        ),
                      ],
                    ),
                  Text(
                    'Acompanhe seu pedido',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 12),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _statusLabel(pedido['status'].toString()),
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'O status é atualizado automaticamente a cada 15 segundos.',
                          ),
                          if (pedido['atualizado_em'] != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Text(
                                'Última atualização: ${pedido['atualizado_em']}',
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text('Itens', style: Theme.of(context).textTheme.titleLarge),
                  for (final item in itens)
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text('${item['quantidade']}x ${item['nome']}'),
                      subtitle: item['observacao'] == null
                          ? null
                          : Text(item['observacao'].toString()),
                      trailing: Text(
                        _money(
                          (double.tryParse(item['preco_unitario'].toString()) ??
                                  0) *
                              (int.tryParse(item['quantidade'].toString()) ??
                                  0),
                        ),
                      ),
                    ),
                  const Divider(),
                  _linha('Subtotal', _money(pedido['subtotal'])),
                  _linha('Taxa de entrega', _money(pedido['taxa_entrega'])),
                  if ((double.tryParse(pedido['desconto'].toString()) ?? 0) > 0)
                    _linha('Desconto', '- ${_money(pedido['desconto'])}'),
                  _linha('Total', _money(pedido['total']), destaque: true),
                  const SizedBox(height: 16),
                  Text(
                    'Endereço de entrega',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Text(
                    [
                          endereco['rua'],
                          endereco['numero'],
                          endereco['bairro'],
                          endereco['cep'],
                        ]
                        .where(
                          (value) =>
                              value != null && value.toString().isNotEmpty,
                        )
                        .join(', '),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _linha(String label, String valor, {bool destaque = false}) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: destaque ? const TextStyle(fontWeight: FontWeight.bold) : null,
        ),
        Text(
          valor,
          style: destaque ? const TextStyle(fontWeight: FontWeight.bold) : null,
        ),
      ],
    ),
  );
}
