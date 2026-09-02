import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'auth_controller.dart';

/// Parent sign-in. Two steps: enter e-mail -> receive a 6-digit code -> enter
/// it. On success the auth stream fires and the router leaves this screen.
class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

enum _Step { email, code }

class _AuthScreenState extends ConsumerState<AuthScreen> {
  final _emailController = TextEditingController();
  final _codeController = TextEditingController();

  _Step _step = _Step.email;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _emailController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _run(Future<void> Function() action, {_Step? advanceTo}) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
      if (mounted && advanceTo != null) setState(() => _step = advanceTo);
    } on AuthException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Er ging iets mis. Probeer het opnieuw.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final auth = ref.read(authControllerProvider);
    final email = _emailController.text.trim();

    return Scaffold(
      appBar: AppBar(title: const Text('Inloggen')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Icon(Icons.auto_stories_rounded,
                    size: 64, color: theme.colorScheme.primary),
                const SizedBox(height: 16),
                Text(
                  'Een account voor de ouders.\n'
                  'Zo blijven de verhaaltjes van je kind bewaard.',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodyLarge,
                ),
                const SizedBox(height: 32),
                if (_step == _Step.email) ...[
                  TextField(
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const [AutofillHints.email],
                    decoration: const InputDecoration(
                      labelText: 'E-mailadres',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _submitEmail(auth),
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: _busy ? null : () => _submitEmail(auth),
                    child: _busy
                        ? const _Spinner()
                        : const Text('Stuur mij een code'),
                  ),
                ] else ...[
                  Text('We stuurden een code naar $email',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _codeController,
                    keyboardType: TextInputType.number,
                    // Supabase's OTP length is configurable (6–10) and differs
                    // between signup-confirm and magic-link, so don't pin it.
                    inputFormatters: [
                      FilteringTextInputFormatter.digitsOnly,
                      LengthLimitingTextInputFormatter(10),
                    ],
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineSmall,
                    decoration: const InputDecoration(
                      labelText: 'Code uit de e-mail',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _submitCode(auth),
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: _busy ? null : () => _submitCode(auth),
                    child:
                        _busy ? const _Spinner() : const Text('Inloggen'),
                  ),
                  TextButton(
                    onPressed:
                        _busy ? null : () => setState(() => _step = _Step.email),
                    child: const Text('Ander e-mailadres'),
                  ),
                ],
                if (_error != null) ...[
                  const SizedBox(height: 16),
                  Text(_error!,
                      textAlign: TextAlign.center,
                      style: TextStyle(color: theme.colorScheme.error)),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _submitEmail(AuthController auth) {
    final email = _emailController.text.trim();
    if (!email.contains('@')) {
      setState(() => _error = 'Vul een geldig e-mailadres in.');
      return;
    }
    _run(() => auth.sendCode(email), advanceTo: _Step.code);
  }

  void _submitCode(AuthController auth) {
    final email = _emailController.text.trim();
    if (_codeController.text.trim().length < 6) {
      setState(() => _error = 'Vul de volledige code uit de e-mail in.');
      return;
    }
    _run(() => auth.verifyCode(email, _codeController.text));
  }
}

class _Spinner extends StatelessWidget {
  const _Spinner();

  @override
  Widget build(BuildContext context) => const SizedBox(
        height: 22,
        width: 22,
        child: CircularProgressIndicator(strokeWidth: 2.5),
      );
}
