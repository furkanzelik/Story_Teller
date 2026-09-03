import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api/api_client.dart';
import 'models/story.dart';
import 'models/subscription.dart';

/// Seam between [StoryController] and the network, so tests can inject a fake
/// without standing up Dio.
abstract class StoryRepository {
  Future<Story> generateStory({
    required String topicId,
    required String ageGroup,
  });

  Future<String> fetchStoryAudio(String storyId);

  Future<List<Story>> listSavedStories();

  Future<Story> setStorySaved(String storyId, {required bool saved});

  Future<Subscription> fetchSubscription();
}

class ApiStoryRepository implements StoryRepository {
  ApiStoryRepository(this._api);

  final ApiClient _api;

  @override
  Future<Story> generateStory({
    required String topicId,
    required String ageGroup,
  }) =>
      _api.generateStory(topicId: topicId, ageGroup: ageGroup);

  @override
  Future<String> fetchStoryAudio(String storyId) =>
      _api.fetchStoryAudio(storyId);

  @override
  Future<List<Story>> listSavedStories() => _api.listSavedStories();

  @override
  Future<Story> setStorySaved(String storyId, {required bool saved}) =>
      _api.setStorySaved(storyId, saved: saved);

  @override
  Future<Subscription> fetchSubscription() => _api.fetchSubscription();
}

final storyRepositoryProvider = Provider<StoryRepository>(
  (ref) => ApiStoryRepository(ref.watch(apiClientProvider)),
);
