import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/models/subscription.dart';
import '../../router/app_router.dart';
import '../paywall/subscription_controller.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final sub = ref.watch(subscriptionProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Verhaaltjesmaker'),
        actions: [
          // Gear routes through the parental gate (see Routes.gated).
          IconButton(
            tooltip: 'Instellingen',
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => context.push(Routes.settings),
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Icon(Icons.nightlight_round,
                      size: 96, color: theme.colorScheme.tertiary),
                  const SizedBox(height: 24),
                  Text(
                    'Welke droom wil je vannacht?',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 40),
                  FilledButton.icon(
                    onPressed: () => context.push(Routes.topics),
                    icon: const Icon(Icons.auto_stories_rounded),
                    label: const Text('Maak een verhaaltje'),
                  ),
                  const SizedBox(height: 16),
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size.fromHeight(60),
                    ),
                    onPressed: () => context.push(Routes.library),
                    icon: const Icon(Icons.favorite_rounded),
                    label: const Text('Mijn verhaaltjes'),
                  ),
                  const SizedBox(height: 12),
                  _QuotaHint(sub: sub.valueOrNull),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _QuotaHint extends StatelessWidget {
  const _QuotaHint({required this.sub});
  final Subscription? sub;

  @override
  Widget build(BuildContext context) {
    final s = sub;
    if (s == null || s.isSubscriber) return const SizedBox.shrink();
    final q = s.quota;
    final theme = Theme.of(context);
    final text = q.exhausted
        ? 'Deze week op — maandag weer ${q.limit} gratis'
        : 'Deze week nog ${q.remaining} van ${q.limit} gratis';
    return Text(
      text,
      textAlign: TextAlign.center,
      style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
    );
  }
}
