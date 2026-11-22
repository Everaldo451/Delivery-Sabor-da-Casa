import 'package:flutter/material.dart';

import 'app_colors.dart';


class AppSpacing {
  AppSpacing._();
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
}


class AppRadius {
  AppRadius._();
  static const double campo = 14;
  static const double card = 20;
  static const double imagem = 16;
}

class AppTheme {
  AppTheme._();

  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: AppColors.urucum,
      brightness: Brightness.light,
    ).copyWith(
      primary: AppColors.urucum,
      onPrimary: Colors.white,
      secondary: AppColors.milho,
      onSecondary: AppColors.cafe,
      surface: AppColors.superficie,
      onSurface: AppColors.cafe,
      error: AppColors.erro,
      outline: AppColors.borda,
    );

    
        final corpo = ThemeData.light()
        .textTheme
        .apply(bodyColor: AppColors.cafe, displayColor: AppColors.cafe);

    final textTheme = corpo.copyWith(
      headlineLarge: corpo.headlineLarge?.copyWith(fontWeight: FontWeight.w700),
      headlineMedium: corpo.headlineMedium?.copyWith(fontWeight: FontWeight.w700),
      headlineSmall: corpo.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
      titleLarge: corpo.titleLarge?.copyWith(fontWeight: FontWeight.w700),
      titleMedium: corpo.titleMedium?.copyWith(fontWeight: FontWeight.w600),
      bodySmall: corpo.bodySmall?.copyWith(color: AppColors.cafeSuave),
    );

    final formaBotao = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppRadius.campo),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: AppColors.tapioca,
      textTheme: textTheme,

      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.tapioca,
        foregroundColor: AppColors.cafe,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: textTheme.titleLarge,
      ),

      cardTheme: CardThemeData(
        color: AppColors.superficie,
        elevation: 0,
        margin: EdgeInsets.zero,
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.card),
          side: const BorderSide(color: AppColors.borda),
        ),
      ),

      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.urucum,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(52),
          shape: formaBotao,
          textStyle: textTheme.titleMedium,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.urucum,
          minimumSize: const Size.fromHeight(52),
          side: const BorderSide(color: AppColors.urucum),
          shape: formaBotao,
          textStyle: textTheme.titleMedium,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.urucumEscuro,
          textStyle: textTheme.titleMedium,
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.superficie,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: 14,
        ),
        hintStyle: textTheme.bodyMedium?.copyWith(color: AppColors.cafeSuave),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.campo),
          borderSide: const BorderSide(color: AppColors.borda),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.campo),
          borderSide: const BorderSide(color: AppColors.borda),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.campo),
          borderSide: const BorderSide(color: AppColors.urucum, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.campo),
          borderSide: const BorderSide(color: AppColors.erro),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.campo),
          borderSide: const BorderSide(color: AppColors.erro, width: 2),
        ),
      ),

      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.superficie,
        surfaceTintColor: Colors.transparent,
        indicatorColor: AppColors.urucum.withValues(alpha: 0.12),
        iconTheme: WidgetStateProperty.resolveWith((estados) {
          final ativo = estados.contains(WidgetState.selected);
          return IconThemeData(
            color: ativo ? AppColors.urucum : AppColors.cafeSuave,
          );
        }),
        labelTextStyle: WidgetStateProperty.resolveWith((estados) {
          final ativo = estados.contains(WidgetState.selected);
          return textTheme.labelMedium?.copyWith(
            color: ativo ? AppColors.urucum : AppColors.cafeSuave,
            fontWeight: ativo ? FontWeight.w700 : FontWeight.w500,
          );
        }),
      ),

      chipTheme: ChipThemeData(
        backgroundColor: AppColors.superficie,
        selectedColor: AppColors.urucum,
        side: const BorderSide(color: AppColors.borda),
        labelStyle: textTheme.labelLarge,
        secondaryLabelStyle: textTheme.labelLarge?.copyWith(color: Colors.white),
        shape: const StadiumBorder(),
      ),

      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: AppColors.urucum,
        foregroundColor: Colors.white,
        elevation: 2,
        shape: StadiumBorder(),
      ),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.cafe,
        contentTextStyle: textTheme.bodyMedium?.copyWith(color: Colors.white),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.campo),
        ),
      ),

      dividerTheme: const DividerThemeData(color: AppColors.borda, space: 1),
    );
  }
}