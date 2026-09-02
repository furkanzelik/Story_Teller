import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/api/api_client.dart';
import '../../data/models/story.dart';
import '../../data/story_repository.dart';
import '../topic_selection/topic_selection_screen.dart';

/// What the story screen should show: generate a fresh one, or display an
/// already-loaded story (reopened from the library).
sealed class StoryRequest {
  const StoryRequest();
}

class GenerateStoryRequest extends StoryRequest {
  const GenerateStoryRequest();
}

class ViewStoryRequest extends StoryRequest {
  const ViewStoryRequest(this.story);
  final Story story;
}

/// Set this before navigating to `/story`.
final storyRequestProvider =
    StateProvider<StoryRequest>((_) => const GenerateStoryRequest());

/// Holds the story currently on screen. Auto-disposed with the screen.
class StoryController extends AutoDisposeAsyncNotifier<Story> {
  @override
  Future<Story> build() async {
    final request = ref.read(storyRequestProvider);
    if (request is ViewStoryRequest) return request.story;
    return _generate();
  }

  Future<Story> _generate() {
    final selection = ref.read(storySelectionProvider);
    final topic = selection.topic;
    if (topic == null) {
      throw const StoryGenerationException(StoryGenerationFailure.unknown);
    }
    return ref.read(storyRepositoryProvider).generateStory(
          topicId: topic.id,
          ageGroup: selection.ageGroup.id,
        );
  }

  /// Only meaningful in generate mode (the button is hidden otherwise).
  Future<void> regenerate() async {
    ref.read(storyRequestProvider.notifier).state =
        const GenerateStoryRequest();
    state = const AsyncValue.loading();
    ref.invalidateSelf();
    await future;
  }

  /// Optimistic save/unsave; reverts on failure.
  Future<void> setSaved(bool saved) async {
    final current = state.valueOrNull;
    if (current == null) return;
    state = AsyncValue.data(current.copyWith(isSaved: saved));
    try {
      final updated = await ref
          .read(storyRepositoryProvider)
          .setStorySaved(current.id, saved: saved);
      state = AsyncValue.data(updated);
    } catch (_) {
      state = AsyncValue.data(current); // revert
      rethrow;
    }
  }
}

final storyControllerProvider =
    AsyncNotifierProvider.autoDispose<StoryController, Story>(
  StoryController.new,
);
