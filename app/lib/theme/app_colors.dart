import 'package:flutter/material.dart';


class AppColors {
  AppColors._();


  static const Color urucum = Color(0xFFB93A1E); // principal (botões, destaques)
  static const Color urucumEscuro = Color(0xFF8F2A14); // botão pressionado, textos sobre claro
  static const Color milho = Color(0xFFF2A93B); // secundária (promoções, cupons, selos)

 
  static const Color tapioca = Color(0xFFFBF7F2); // fundo das telas
  static const Color superficie = Color(0xFFFFFFFF); // cards, campos, barra inferior

  
  static const Color cafe = Color(0xFF2B1D17); // texto principal
  static const Color cafeSuave = Color(0xFF76655B); // texto secundário, legendas

  
  static const Color borda = Color(0xFFE9DFD5);

 
  static const Color sucesso = Color(0xFF2E7D4F);
  static const Color erro = Color(0xFF9B1C31);


  static const Color statusRecebido = cafeSuave;
  static const Color statusPreparo = milho;
  static const Color statusEntrega = urucum;
  static const Color statusEntregue = sucesso;
}