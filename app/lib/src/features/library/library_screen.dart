import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/models/story.dart';
import '../../data/models/topic.dart';
import '../../data/story_repository.dart';
import '../story/story_controller.dart';

/// Fase 4 stap 13. Lists the parent's saved stories; tapping one reopens it
/// on the story screen (text + audio replay, no regeneration).
final savedStoriesProvider = FutureProvider.autoDispose<List<Story>>((ref) {
  return ref.watch(storyRepositoryProvider).listSavedStories();
});

class LibraryScreen extends ConsumerWidget {
  const LibraryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stories = ref.watch(savedStoriesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Mijn verhaaltjes')),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(savedStoriesProvider.future),
        child: stories.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (_, _) => _Message(
            icon: Icons.cloud_off_rounded,
            text: 'Kon je verhaaltjes niet laden.\nTrek naar beneden om opnieuw te proberen.',
          ),
          data: (list) => list.isEmpty
              ? _Message(
                  icon: Icons.favorite_border_rounded,
                  text: 'Nog geen opgeslagen verhaaltjes.\n'
                      'Maak er eentje en tik op het hartje om het te bewaren.',
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: list.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 12),
                  itemBuilder: (context, i) => _StoryCard(
                    story: list[i],
                    onTap: () {
                      ref.read(storyRequestProvider.notifier).state =
                          ViewStoryRequest(list[i]);
                      context.push('/story');
                    },
                  ),
                ),
        ),
      ),
    );
  }
}

class _StoryCard extends StatelessWidget {
  const _StoryCard({required this.story, required this.onTap});

  final Story story;
  final VoidCallback onTap;

  String get _emoji => topicCatalog
      .where((t) => t.id == story.topicId)
      .map((t) => t.emoji)
      .followedBy(['✨']).first;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Material(
      color: theme.colorScheme.surfaceContainerHighest,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Text(_emoji, style: const TextStyle(fontSize: 32)),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(story.title,
                        style: theme.textTheme.titleMedium,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 4),
                    Text('${story.topicLabel} · ${story.ageGroup.label}',
                        style: theme.textTheme.bodySmall),
                  ],
                ),
              ),
              if (story.hasAudio)
                Icon(Icons.volume_up_rounded,
                    color: theme.colorScheme.outline, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    // Wrapped in a scroll view so RefreshIndicator works over the empty state.
    return ListView(
      children: [
        SizedBox(
          height: MediaQuery.sizeOf(context).height * 0.6,
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, size: 72, color: theme.colorScheme.outline),
                  const SizedBox(height: 16),
                  Text(text,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyLarge),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
