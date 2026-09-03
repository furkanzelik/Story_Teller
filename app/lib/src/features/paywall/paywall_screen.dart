import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/models/subscription.dart';
import 'subscription_controller.dart';

/// Fase 5. Reached only after the parental gate (see Routes.gated). Shows this
/// week's free usage and the upgrade pitch. The buy button is inert until
/// RevenueCat is configured ([PurchasesService.isConfigured]).
class PaywallScreen extends ConsumerWidget {
  const PaywallScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final sub = ref.watch(subscriptionProvider);
    final purchases = ref.watch(purchasesServiceProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Onbeperkt voorlezen')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),
              sub.when(
                loading: () => const SizedBox.shrink(),
                error: (_, _) => const SizedBox.shrink(),
                data: (s) => _QuotaBanner(subscription: s),
              ),
              const Spacer(),
              Icon(Icons.workspace_premium_rounded,
                  size: 80, color: theme.colorScheme.tertiary),
              const SizedBox(height: 24),
              Text('Verhaaltjesmaker Plus',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.headlineSmall),
              const SizedBox(height: 16),
              const _Benefit('Onbeperkt nieuwe verhaaltjes'),
              const _Benefit('Elk verhaal voorgelezen'),
              const _Benefit('Alles bewaren in de bibliotheek'),
              const Spacer(),
              FilledButton(
                onPressed: purchases.isConfigured
                    ? () => purchases.buy()
                    : null,
                child: Text(purchases.isConfigured
                    ? 'Abonnement starten'
                    : 'Binnenkort beschikbaar'),
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

class _QuotaBanner extends StatelessWidget {
  const _QuotaBanner({required this.subscription});
  final Subscription subscription;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final q = subscription.quota;

    final String text;
    if (subscription.isSubscriber) {
      text = 'Je hebt Plus — onbeperkt verhaaltjes. Dankjewel! 💛';
    } else if (q.exhausted) {
      text = 'Je gratis verhaaltjes voor deze week zijn op. '
          'Op maandag krijg je er weer ${q.limit}.';
    } else {
      text = 'Deze week nog ${q.remaining} van ${q.limit} gratis verhaaltjes.';
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(text, style: theme.textTheme.bodyMedium),
    );
  }
}

class _Benefit extends StatelessWidget {
  const _Benefit(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(Icons.check_circle_rounded,
              color: Theme.of(context).colorScheme.primary, size: 22),
          const SizedBox(width: 12),
          Expanded(child: Text(text, style: Theme.of(context).textTheme.bodyLarge)),
        ],
      ),
    );
  }
}
