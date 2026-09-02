import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/parental_gate/parental_gate_controller.dart';
import '../core/parental_gate/parental_gate_screen.dart';
import '../features/auth/auth_controller.dart';
import '../features/auth/auth_screen.dart';
import '../features/home/home_screen.dart';
import '../features/library/library_screen.dart';
import '../features/paywall/paywall_screen.dart';
import '../features/settings/settings_screen.dart';
import '../features/story/story_screen.dart';
import '../features/topic_selection/topic_selection_screen.dart';

/// Route names kept in one place so screens can navigate without stringly-typed
/// paths scattered around the codebase.
abstract class Routes {
  static const auth = '/auth';
  static const home = '/';
  static const topics = '/topics';
  static const story = '/story';
  static const library = '/library';
  static const settings = '/settings';
  static const paywall = '/paywall';
  static const parentalGate = '/parental-gate';

  /// Routes that may only be entered after passing the parental gate.
  static const gated = <String>{settings, paywall};
}

final goRouterProvider = Provider<GoRouter>((ref) {
  // Re-run redirects whenever Supabase auth state changes (sign in / out).
  final refresh = ValueNotifier<int>(0);
  ref.onDispose(refresh.dispose);
  ref.listen(authChangesProvider, (_, _) => refresh.value++);

  return GoRouter(
    initialLocation: Routes.home,
    debugLogDiagnostics: true,
    refreshListenable: refresh,
    redirect: (context, state) {
      final status = ref.read(authStatusProvider);
      final loc = state.matchedLocation;

      // 1. Not signed in: only the auth screen is reachable.
      if (status == AuthStatus.signedOut) {
        return loc == Routes.auth ? null : Routes.auth;
      }

      // 2. Signed in but sitting on the auth screen -> go home.
      if (loc == Routes.auth) return Routes.home;

      // 3. Parental gate for settings / paywall.
      if (Routes.gated.contains(loc)) {
        final verified =
            ref.read(parentalGateControllerProvider.notifier).isVerified;
        if (!verified) {
          final encoded = Uri.encodeComponent(state.uri.toString());
          return '${Routes.parentalGate}?redirect=$encoded';
        }
      }
      return null;
    },
    routes: [
      GoRoute(
        path: Routes.auth,
        builder: (_, _) => const AuthScreen(),
      ),
      GoRoute(
        path: Routes.home,
        builder: (_, _) => const HomeScreen(),
      ),
      GoRoute(
        path: Routes.topics,
        builder: (_, _) => const TopicSelectionScreen(),
      ),
      GoRoute(
        path: Routes.story,
        builder: (_, _) => const StoryScreen(),
      ),
      GoRoute(
        path: Routes.library,
        builder: (_, _) => const LibraryScreen(),
      ),
      GoRoute(
        path: Routes.settings,
        builder: (_, _) => const SettingsScreen(),
      ),
      GoRoute(
        path: Routes.paywall,
        builder: (_, _) => const PaywallScreen(),
      ),
      GoRoute(
        path: Routes.parentalGate,
        builder: (_, state) {
          final raw = state.uri.queryParameters['redirect'];
          final decoded = raw == null ? null : Uri.decodeComponent(raw);
          return ParentalGateScreen(redirectTo: decoded);
        },
      ),
    ],
    errorBuilder: (_, state) => Scaffold(
      body: Center(child: Text('Pagina niet gevonden: ${state.uri}')),
    ),
  );
});
