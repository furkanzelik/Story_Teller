import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'parental_gate_controller.dart';

/// Full-screen challenge that must be solved before entering settings or the
/// paywall. On success it records the pass and continues to [redirectTo]
/// (defaults to the previous screen).
class ParentalGateScreen extends ConsumerStatefulWidget {
  const ParentalGateScreen({super.key, this.redirectTo});

  final String? redirectTo;

  @override
  ConsumerState<ParentalGateScreen> createState() => _ParentalGateScreenState();
}

class _ParentalGateScreenState extends ConsumerState<ParentalGateScreen> {
  final _controller = TextEditingController();
  bool _showError = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit(ParentalChallenge challenge) {
    final entered = int.tryParse(_controller.text.trim());
    if (entered == challenge.answer) {
      ref.read(parentalGateControllerProvider.notifier).markVerified();
      final target = widget.redirectTo;
      if (target != null && target.isNotEmpty) {
        context.go(target);
      } else if (context.canPop()) {
        context.pop();
      } else {
        context.go('/');
      }
      return;
    }
    setState(() => _showError = true);
    _controller.clear();
    // Swap in a new sum so repeated guessing does not converge.
    ref.invalidate(parentalChallengeProvider);
  }

  @override
  Widget build(BuildContext context) {
    final challenge = ref.watch(parentalChallengeProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Even voor de ouders')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Icon(Icons.lock_outline_rounded,
                    size: 56, color: theme.colorScheme.primary),
                const SizedBox(height: 16),
                Text(
                  'Dit gedeelte is voor volwassenen.\nLos de som op om verder te gaan.',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodyLarge,
                ),
                const SizedBox(height: 32),
                Text(
                  '${challenge.question} = ?',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.headlineMedium,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _controller,
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  textAlign: TextAlign.center,
                  autofocus: true,
                  style: theme.textTheme.headlineSmall,
                  decoration: InputDecoration(
                    border: const OutlineInputBorder(),
                    errorText: _showError ? 'Dat klopt niet, probeer opnieuw.' : null,
                  ),
                  onSubmitted: (_) => _submit(challenge),
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: () => _submit(challenge),
                  child: const Text('Verder'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
