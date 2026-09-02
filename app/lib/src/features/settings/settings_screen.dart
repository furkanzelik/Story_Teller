import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/parental_gate/parental_gate_controller.dart';
import '../../router/app_router.dart';
import '../auth/auth_controller.dart';

/// Reached only after the parental gate (see Routes.gated). Content is a
/// placeholder; the toggles are not wired yet.
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);

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
              // Router's refreshListenable picks up the sign-out and shows /auth.
            },
          ),
          const _SectionHeader('Abonnement'),
          ListTile(
            leading: const Icon(Icons.workspace_premium_outlined),
            title: const Text('Abonnement beheren'),
            subtitle: const Text('Gratis · 2 verhalen per week'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push(Routes.paywall),
          ),
          const _SectionHeader('Voorlezen'),
          SwitchListTile(
            secondary: const Icon(Icons.record_voice_over_outlined),
            title: const Text('Automatisch voorlezen'),
            value: true,
            onChanged: null, // wired up in Fase 3
          ),
          const _SectionHeader('Privacy'),
          const ListTile(
            leading: Icon(Icons.privacy_tip_outlined),
            title: Text('Geen tracking of advertenties'),
            subtitle: Text(
                'Deze app verzamelt geen gegevens van kinderen en toont geen '
                'advertenties.'),
          ),
          const SizedBox(height: 24),
          Padding(
            padding: const EdgeInsets.all(16),
            child: OutlinedButton(
              onPressed: () {
                ref.read(parentalGateControllerProvider.notifier).reset();
                context.go('/');
              },
              child: const Text('Ouder-sessie vergrendelen'),
            ),
          ),
        ],
      ),
    );
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
