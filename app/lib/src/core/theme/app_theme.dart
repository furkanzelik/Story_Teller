import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// App-wide theme.
///
/// Design goals for a kids' bedtime app:
///  - warm, low-contrast night palette (nothing harsh before sleep)
///  - large tap targets (min 56dp) and generous spacing
///  - rounded, friendly shapes
///  - a rounded, highly legible typeface (Baloo 2 / Nunito)
class AppTheme {
  const AppTheme._();

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

    final baseText = brightness == Brightness.dark
        ? Typography.material2021().white
        : Typography.material2021().black;

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: scheme.surface,
      textTheme: GoogleFonts.baloo2TextTheme(baseText).copyWith(
        bodyLarge: GoogleFonts.nunito(
          textStyle: baseText.bodyLarge,
          fontSize: 18,
          height: 1.5,
        ),
        bodyMedium: GoogleFonts.nunito(
          textStyle: baseText.bodyMedium,
          fontSize: 16,
          height: 1.5,
        ),
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
          textStyle: GoogleFonts.baloo2(fontSize: 20, fontWeight: FontWeight.w600),
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
