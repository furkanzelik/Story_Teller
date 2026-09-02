import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/api/api_client.dart';
import '../../data/models/story.dart';
import '../topic_selection/topic_selection_screen.dart';
import 'audio_bar.dart';
import 'story_controller.dart';

/// Generates a story on entry, or shows one reopened from the library
/// ([storyRequestProvider]). Calm loading state while Claude + moderation run,
/// then the story with a save (heart) action, the audio player (Fase 3) and —
/// in generate mode — an "opnieuw" button.
class StoryScreen extends ConsumerWidget {
  const StoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selection = ref.watch(storySelectionProvider);
    final storyState = ref.watch(storyControllerProvider);
    final isGenerateMode =
        ref.watch(storyRequestProvider) is GenerateStoryRequest;
    final controller = ref.read(storyControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          storyState.valueOrNull?.topicLabel ??
              selection.topic?.label ??
              'Jouw verhaal',
        ),
        actions: [
          if (storyState.valueOrNull case final story?)
            IconButton(
              tooltip: story.isSaved ? 'Uit bibliotheek' : 'Bewaren',
              icon: Icon(
                story.isSaved
                    ? Icons.favorite_rounded
                    : Icons.favorite_border_rounded,
              ),
              onPressed: () async {
                try {
                  await controller.setSaved(!story.isSaved);
                } catch (_) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Bewaren lukte niet.')),
                    );
                  }
                }
              },
            ),
        ],
      ),
      body: SafeArea(
        child: storyState.when(
          loading: () => const _Loading(),
          error: (err, _) => _Error(
            error: err,
            onRetry: controller.regenerate,
          ),
          data: (story) => _StoryView(
            story: story,
            onRegenerate: isGenerateMode ? controller.regenerate : null,
          ),
        ),
      ),
    );
  }
}

class _Loading extends StatelessWidget {
  const _Loading();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.auto_stories_rounded,
              size: 72, color: theme.colorScheme.primary),
          const SizedBox(height: 24),
          const SizedBox(
            width: 32,
            height: 32,
            child: CircularProgressIndicator(strokeWidth: 3),
          ),
          const SizedBox(height: 24),
          Text('De verhaaltjesmaker denkt na…',
              style: theme.textTheme.titleMedium),
          const SizedBox(height: 4),
          Text('Dit duurt heel even.',
              style: theme.textTheme.bodyMedium),
        ],
      ),
    );
  }
}

class _StoryView extends StatelessWidget {
  const _StoryView({required this.story, this.onRegenerate});

  final Story story;
  final Future<void> Function()? onRegenerate;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 16, 24, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(story.title, style: theme.textTheme.headlineSmall),
                const SizedBox(height: 16),
                Text(
                  story.body,
                  style: theme.textTheme.bodyLarge?.copyWith(height: 1.6),
                ),
              ],
            ),
          ),
        ),
        const AudioBar(),
        _BottomBar(
          children: [
            if (onRegenerate != null)
              OutlinedButton.icon(
                onPressed: onRegenerate,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Opnieuw'),
              ),
            FilledButton.icon(
              onPressed: () => context.go('/'),
              icon: const Icon(Icons.home_rounded),
              label: const Text('Naar start'),
            ),
          ],
        ),
      ],
    );
  }
}

class _Error extends StatelessWidget {
  const _Error({required this.error, required this.onRetry});

  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final failure = error is StoryGenerationException
        ? (error as StoryGenerationException).kind
        : StoryGenerationFailure.unknown;
    final message = error is StoryGenerationException
        ? (error as StoryGenerationException).message
        : 'Er ging iets mis. Probeer het opnieuw.';
    final isModeration = failure == StoryGenerationFailure.moderation;

    return Column(
      children: [
        Expanded(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    isModeration
                        ? Icons.shield_outlined
                        : Icons.cloud_off_rounded,
                    size: 64,
                    color: theme.colorScheme.outline,
                  ),
                  const SizedBox(height: 16),
                  Text(message,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyLarge),
                ],
              ),
            ),
          ),
        ),
        _BottomBar(
          children: [
            OutlinedButton.icon(
              onPressed: () => context.go('/topics'),
              icon: const Icon(Icons.grid_view_rounded),
              label: const Text('Ander onderwerp'),
            ),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: Text(isModeration ? 'Opnieuw proberen' : 'Nog eens'),
            ),
          ],
        ),
      ],
    );
  }
}

class _BottomBar extends StatelessWidget {
  const _BottomBar({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      child: Row(
        children: [
          for (var i = 0; i < children.length; i++) ...[
            if (i > 0) const SizedBox(width: 12),
            Expanded(child: children[i]),
          ],
        ],
      ),
    );
  }
}
