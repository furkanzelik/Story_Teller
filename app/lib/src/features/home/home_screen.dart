import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../router/app_router.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

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
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
