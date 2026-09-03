import 'package:flutter/material.dart';

/// App-wide theme.
///
/// Design goals for a kids' bedtime app:
///  - warm, low-contrast night palette (nothing harsh before sleep)
///  - large tap targets (min 56dp) and generous spacing
///  - rounded, friendly shapes
///  - a rounded, highly legible typeface (Baloo 2 for headings, Nunito for body)
///
/// Fonts are bundled (`assets/google_fonts/`), so the app never waits on the
/// network for text rendering.
class AppTheme {
  const AppTheme._();

  static const _heading = 'Baloo2';
  static const _body = 'Nunito';

  // Core palette — deep indigo "night sky" with warm accents.
  static const Color _seed = Color(0xFF5B4B8A);
  static const Color _accentPeach = Color(0xFFFFB4A2);
  static const Color _accentGold = Color(0xFFFFD98E);

  static ThemeData light() => _build(Brightness.light);
  static ThemeData dark() => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final scheme = ColorScheme.fromSeed(
      seedColor: _seed,
      brightness: brightness,
    ).copyWith(
      secondary: _accentPeach,
      tertiary: _accentGold,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      brightness: brightness,
      scaffoldBackgroundColor: scheme.surface,
      fontFamily: _heading,
    );

    return base.copyWith(
      textTheme: base.textTheme.copyWith(
        bodyLarge: base.textTheme.bodyLarge?.copyWith(
          fontFamily: _body,
          fontSize: 18,
          height: 1.5,
        ),
        bodyMedium: base.textTheme.bodyMedium?.copyWith(
          fontFamily: _body,
          fontSize: 16,
          height: 1.5,
        ),
        bodySmall: base.textTheme.bodySmall?.copyWith(fontFamily: _body),
      ),
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(60),
          textStyle: const TextStyle(
            fontFamily: _heading,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: scheme.surfaceContainerHighest,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
        ),
      ),
    );
  }
}
