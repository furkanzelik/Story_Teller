import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Central place for runtime configuration.
///
/// Values are read from `assets/.env` at startup (see `main.dart`). Each getter
/// also honours a `--dart-define` override so CI / release builds can inject
/// config without shipping a `.env` file. `String.fromEnvironment` needs a
/// const key, so every supported key is spelled out explicitly below.
class Env {
  const Env._();

  /// Safe accessor: `dotenv.get`/`maybeGet` throw if `load()` never ran
  /// (e.g. in widget tests), so guard on `isInitialized` first.
  static String? _env(String key) =>
      dotenv.isInitialized ? dotenv.maybeGet(key) : null;

  /// Base URL of the FastAPI backend.
  ///
  /// Defaults per platform when unset:
  ///  - iOS simulator / web / desktop: http://localhost:8000
  ///  - Android emulator: use http://10.0.2.2:8000 in your `.env`
  static String get apiBaseUrl {
    const fromDefine = String.fromEnvironment('API_BASE_URL');
    if (fromDefine.isNotEmpty) return fromDefine;
    return _env('API_BASE_URL') ?? 'http://localhost:8000';
  }

  /// Supabase project URL, e.g. https://xxxx.supabase.co
  static String get supabaseUrl {
    const fromDefine = String.fromEnvironment('SUPABASE_URL');
    if (fromDefine.isNotEmpty) return fromDefine;
    return _env('SUPABASE_URL') ?? '';
  }

  /// Supabase publishable / anon key. Safe to ship in the client.
  static String get supabaseAnonKey {
    const fromDefine = String.fromEnvironment('SUPABASE_ANON_KEY');
    if (fromDefine.isNotEmpty) return fromDefine;
    return _env('SUPABASE_ANON_KEY') ?? '';
  }

  static bool get hasSupabaseConfig =>
      supabaseUrl.isNotEmpty && supabaseAnonKey.isNotEmpty;

  /// Public URL of the published privacy policy (empty until it's online).
  static String get privacyPolicyUrl {
    const fromDefine = String.fromEnvironment('PRIVACY_POLICY_URL');
    if (fromDefine.isNotEmpty) return fromDefine;
    return _env('PRIVACY_POLICY_URL') ?? '';
  }

  /// Toggles verbose network / provider logging.
  static bool get debugLogging {
    const fromDefine =
        bool.fromEnvironment('DEBUG_LOGGING', defaultValue: false);
    final fromEnv = _env('DEBUG_LOGGING');
    if (fromEnv != null) return fromEnv.toLowerCase() == 'true';
    return fromDefine;
  }
}
