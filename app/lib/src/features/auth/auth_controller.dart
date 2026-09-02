import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../core/config/env.dart';

enum AuthStatus { signedOut, signedIn }

/// The Supabase client, or null when the app was started without Supabase
/// config or `Supabase.initialize` failed / timed out (see `main.dart`).
/// Everything downstream treats null as "signed out".
final supabaseClientProvider = Provider<SupabaseClient?>((ref) {
  if (!Env.hasSupabaseConfig) return null;
  try {
    return Supabase.instance.client;
  } catch (_) {
    return null; // initialize() never completed
  }
});

/// Emits on every sign-in / sign-out / token refresh. Drives router refresh.
final authChangesProvider = StreamProvider<AuthState>((ref) {
  final client = ref.watch(supabaseClientProvider);
  if (client == null) return const Stream.empty();
  return client.auth.onAuthStateChange;
});

final currentUserProvider = Provider<User?>((ref) {
  final client = ref.watch(supabaseClientProvider);
  ref.watch(authChangesProvider); // rebuild when auth changes
  return client?.auth.currentUser;
});

final authStatusProvider = Provider<AuthStatus>((ref) {
  final client = ref.watch(supabaseClientProvider);
  if (client == null) return AuthStatus.signedOut;

  // `Supabase.initialize` restores any persisted session before it returns, so
  // `currentSession` is already accurate on first read. Watching the stream
  // just triggers a rebuild on later sign-in / sign-out.
  ref.watch(authChangesProvider);
  return client.auth.currentSession != null
      ? AuthStatus.signedIn
      : AuthStatus.signedOut;
});

/// Actions for the sign-in screen. Passwordless e-mail OTP (6-digit code) so
/// there is no deep-link setup and the parent never types a password.
class AuthController {
  AuthController(this._client);

  final SupabaseClient? _client;

  Future<void> sendCode(String email) async {
    final client = _client;
    if (client == null) throw const AuthException('Supabase niet geconfigureerd.');
    await client.auth.signInWithOtp(email: email.trim(), shouldCreateUser: true);
  }

  Future<void> verifyCode(String email, String code) async {
    final client = _client;
    if (client == null) throw const AuthException('Supabase niet geconfigureerd.');
    await client.auth.verifyOTP(
      email: email.trim(),
      token: code.trim(),
      type: OtpType.email,
    );
  }

  Future<void> signOut() async => _client?.auth.signOut();
}

final authControllerProvider = Provider<AuthController>((ref) {
  return AuthController(ref.watch(supabaseClientProvider));
});
