import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/config/env.dart';
import '../../core/parental_gate/parental_gate_controller.dart';
import '../../data/story_repository.dart';
import '../../router/app_router.dart';
import '../auth/auth_controller.dart';
import '../paywall/subscription_controller.dart';

/// Reached only after the parental gate (see Routes.gated).
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final sub = ref.watch(subscriptionProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Instellingen')),
      body: ListView(
        children: [
          const _SectionHeader('Account'),
          ListTile(
            leading: const Icon(Icons.person_outline),
            title: const Text('Ingelogd als'),
            subtitle: Text(user?.email ?? 'Onbekend'),
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Uitloggen'),
            onTap: () async {
              await ref.read(authControllerProvider).signOut();
              ref.read(parentalGateControllerProvider.notifier).reset();
            },
          ),
          const _SectionHeader('Abonnement'),
          ListTile(
            leading: const Icon(Icons.workspace_premium_outlined),
            title: const Text('Abonnement'),
            subtitle: Text(
              sub.maybeWhen(
                data: (s) => s.isSubscriber
                    ? 'Plus · onbeperkt'
                    : 'Gratis · ${s.quota.limit} verhalen per week',
                orElse: () => 'Gratis',
              ),
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push(Routes.paywall),
          ),
          const _SectionHeader('Privacy'),
          const ListTile(
            leading: Icon(Icons.privacy_tip_outlined),
            title: Text('Geen tracking of advertenties'),
            subtitle: Text(
                'Deze app verzamelt geen gegevens van kinderen en toont geen '
                'advertenties.'),
          ),
          ListTile(
            leading: const Icon(Icons.description_outlined),
            title: const Text('Privacybeleid'),
            enabled: Env.privacyPolicyUrl.isNotEmpty,
            subtitle: Env.privacyPolicyUrl.isEmpty
                ? const Text('Binnenkort online')
                : null,
            trailing: const Icon(Icons.open_in_new_rounded, size: 18),
            onTap: Env.privacyPolicyUrl.isEmpty
                ? null
                : () => launchUrl(
                      Uri.parse(Env.privacyPolicyUrl),
                      mode: LaunchMode.externalApplication,
                    ),
          ),
          const SizedBox(height: 12),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: OutlinedButton(
              onPressed: () {
                ref.read(parentalGateControllerProvider.notifier).reset();
                context.go('/');
              },
              child: const Text('Ouder-sessie vergrendelen'),
            ),
          ),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: TextButton(
              style: TextButton.styleFrom(
                foregroundColor: Theme.of(context).colorScheme.error,
              ),
              onPressed: () => _confirmDelete(context, ref),
              child: const Text('Account verwijderen'),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Account verwijderen?'),
        content: const Text(
          'Je account, je bewaarde verhaaltjes en de bijbehorende audio worden '
          'definitief verwijderd. Dit kan niet ongedaan worden gemaakt.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Annuleren'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(ctx).colorScheme.error,
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Verwijderen'),
          ),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;

    try {
      await ref.read(storyRepositoryProvider).deleteAccount();
      await ref.read(authControllerProvider).signOut();
      ref.read(parentalGateControllerProvider.notifier).reset();
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Verwijderen lukte niet. Probeer opnieuw.')),
        );
      }
    }
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
      child: Text(
        text.toUpperCase(),
        style: theme.textTheme.labelMedium?.copyWith(
          color: theme.colorScheme.primary,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}
