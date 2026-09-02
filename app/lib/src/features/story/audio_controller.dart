import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';

import '../../data/story_repository.dart';
import 'story_controller.dart';

/// Lets tests swap the real [AudioPlayer] (platform channels) for a fake.
typedef AudioPlayerFactory = AudioPlayer Function();

final audioPlayerFactoryProvider =
    Provider<AudioPlayerFactory>((_) => AudioPlayer.new);

/// Requests the read-aloud audio for the current story, loads it into a
/// player, and hands the player to the UI. Auto-disposed with the story
/// screen; the player is disposed on every rebuild/teardown.
class AudioController extends AutoDisposeAsyncNotifier<AudioPlayer> {
  @override
  Future<AudioPlayer> build() async {
    final story = ref.read(storyControllerProvider).valueOrNull;
    if (story == null) {
      throw StateError('Geen verhaal om voor te lezen.');
    }

    final url = await ref.read(storyRepositoryProvider).fetchStoryAudio(story.id);

    final player = ref.read(audioPlayerFactoryProvider)();
    ref.onDispose(player.dispose);
    await player.setUrl(url);
    return player;
  }

  Future<void> retry() async {
    state = const AsyncValue.loading();
    ref.invalidateSelf();
    await future;
  }
}

final audioControllerProvider =
    AsyncNotifierProvider.autoDispose<AudioController, AudioPlayer>(
  AudioController.new,
);
