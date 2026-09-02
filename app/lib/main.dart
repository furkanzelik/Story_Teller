import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'src/app.dart';
import 'src/core/config/env.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load runtime config from assets/.env (see assets/.env.example).
  // Wrapped so a missing file in CI / fresh checkout does not crash startup.
  try {
    await dotenv.load(fileName: 'assets/.env');
  } catch (_) {
    // Fall back to compile-time defaults defined in Env.
  }

  // Auth (Fase 1 stap 4). Never let this block first paint: on a bad key or a
  // flaky network `Supabase.initialize` can stall, and awaiting it before
  // runApp() would leave a blank screen. Time-box it and carry on; auth-gated
  // routes just stay locked if it fails.
  if (Env.hasSupabaseConfig) {
    try {
      await Supabase.initialize(
        url: Env.supabaseUrl,
        // Works with both the new `sb_publishable_…` key and legacy anon JWTs.
        publishableKey: Env.supabaseAnonKey,
        debug: Env.debugLogging,
      ).timeout(const Duration(seconds: 8));
    } catch (e, st) {
      debugPrint('Supabase.initialize failed: $e\n$st');
    }
  }

  runApp(
    const ProviderScope(
      child: StoryTellerApp(),
    ),
  );
}
