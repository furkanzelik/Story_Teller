import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Placeholder for Fase 5 (RevenueCat). Reached only after the parental gate.
/// No purchase controls are functional yet.
class PaywallScreen extends StatelessWidget {
  const PaywallScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Onbeperkt voorlezen')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(),
              Icon(Icons.workspace_premium_rounded,
                  size: 80, color: theme.colorScheme.tertiary),
              const SizedBox(height: 24),
              Text('Verhaaltjesmaker Plus',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.headlineSmall),
              const SizedBox(height: 12),
              Text(
                '• Onbeperkt nieuwe verhaaltjes\n'
                '• Alle stemmen\n'
                '• Verhalen offline bewaren',
                style: theme.textTheme.bodyLarge,
              ),
              const Spacer(),
              FilledButton(
                onPressed: null, // RevenueCat hookup in Fase 5
                child: const Text('Binnenkort beschikbaar'),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => context.pop(),
                child: const Text('Misschien later'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
