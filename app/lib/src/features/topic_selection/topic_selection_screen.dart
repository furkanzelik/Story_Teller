import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/models/age_group.dart';
import '../../data/models/topic.dart';
import '../../router/app_router.dart';
import '../story/story_controller.dart';

/// Holds what the child picked before generating. Kept app-wide so the story
/// screen (and later the "generate" call) can read it back.
class StorySelection {
  const StorySelection({this.topic, this.ageGroup = AgeGroup.preschool});

  final Topic? topic;
  final AgeGroup ageGroup;

  bool get isComplete => topic != null;

  StorySelection copyWith({Topic? topic, AgeGroup? ageGroup}) => StorySelection(
        topic: topic ?? this.topic,
        ageGroup: ageGroup ?? this.ageGroup,
      );
}

class StorySelectionController extends Notifier<StorySelection> {
  @override
  StorySelection build() => const StorySelection();

  void chooseTopic(Topic topic) => state = state.copyWith(topic: topic);
  void chooseAge(AgeGroup group) => state = state.copyWith(ageGroup: group);
}

final storySelectionProvider =
    NotifierProvider<StorySelectionController, StorySelection>(
  StorySelectionController.new,
);

class TopicSelectionScreen extends ConsumerWidget {
  const TopicSelectionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selection = ref.watch(storySelectionProvider);
    final controller = ref.read(storySelectionProvider.notifier);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Kies een onderwerp')),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: GridView.count(
                padding: const EdgeInsets.all(16),
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.1,
                children: [
                  for (final topic in topicCatalog)
                    _TopicTile(
                      topic: topic,
                      selected: selection.topic?.id == topic.id,
                      onTap: () => controller.chooseTopic(topic),
                    ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text('Leeftijd', style: theme.textTheme.titleMedium),
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 48,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: AgeGroup.values.length,
                separatorBuilder: (_, _) => const SizedBox(width: 8),
                itemBuilder: (_, i) {
                  final group = AgeGroup.values[i];
                  return ChoiceChip(
                    label: Text(group.label),
                    selected: selection.ageGroup == group,
                    onSelected: (_) => controller.chooseAge(group),
                  );
                },
              ),
            ),
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: FilledButton.icon(
                onPressed: selection.isComplete
                    ? () {
                        ref.read(storyRequestProvider.notifier).state =
                            const GenerateStoryRequest();
                        context.push(Routes.story);
                      }
                    : null,
                icon: const Icon(Icons.auto_awesome_rounded),
                label: const Text('Maak mijn verhaal'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TopicTile extends StatelessWidget {
  const _TopicTile({
    required this.topic,
    required this.selected,
    required this.onTap,
  });

  final Topic topic;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Material(
      color: selected
          ? theme.colorScheme.primaryContainer
          : theme.colorScheme.surfaceContainerHighest,
      borderRadius: BorderRadius.circular(24),
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(topic.emoji, style: const TextStyle(fontSize: 44)),
              const SizedBox(height: 12),
              Text(
                topic.label,
                textAlign: TextAlign.center,
                style: theme.textTheme.titleMedium,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
