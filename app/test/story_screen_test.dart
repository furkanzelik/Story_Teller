import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import 'package:story_teller_app/src/app.dart';
import 'package:story_teller_app/src/data/api/api_client.dart';
import 'package:story_teller_app/src/data/models/age_group.dart';
import 'package:story_teller_app/src/data/models/story.dart';
import 'package:story_teller_app/src/data/models/subscription.dart';
import 'package:story_teller_app/src/data/models/topic.dart';
import 'package:story_teller_app/src/data/story_repository.dart';
import 'package:story_teller_app/src/features/auth/auth_controller.dart';
import 'package:story_teller_app/src/features/story/audio_controller.dart';
import 'package:story_teller_app/src/features/topic_selection/topic_selection_screen.dart';
import 'package:story_teller_app/src/router/app_router.dart';

class _FakeRepo implements StoryRepository {
  _FakeRepo({this.result, this.error});

  final Story? result;
  final Object? error;
  int calls = 0;

  @override
  Future<Story> generateStory({
    required String topicId,
    required String ageGroup,
  }) async {
    calls++;
    if (error != null) throw error!;
    return result!;
  }

  @override
  Future<String> fetchStoryAudio(String storyId) async =>
      throw UnimplementedError();

  @override
  Future<List<Story>> listSavedStories() async => [];

  @override
  Future<Story> setStorySaved(String storyId, {required bool saved}) async =>
      (result ?? _story()).copyWith(isSaved: saved);

  @override
  Future<Subscription> fetchSubscription() async => freeSubscription();
}

Subscription freeSubscription({int used = 0}) => Subscription(
      status: SubscriptionStatus.free,
      quota: Quota(
        unlimited: false,
        limit: 2,
        used: used,
        remaining: 2 - used,
        resetsAt: DateTime(2026, 1, 5),
      ),
    );

Story _story() => Story(
      id: 'abc',
      title: 'De maanhaas',
      body: 'Er was eens een haas die naar de maan wilde.',
      topicLabel: 'De ruimte',
      ageGroup: AgeGroup.preschool,
      createdAt: DateTime(2026, 1, 1),
    );

/// Keeps the audio bar in its loading state — the real player uses platform
/// channels that aren't available under `flutter test`.
class _StubAudioController extends AudioController {
  @override
  Future<AudioPlayer> build() => Completer<AudioPlayer>().future;
}

Future<ProviderContainer> _pump(WidgetTester tester, StoryRepository repo) async {
  final container = ProviderContainer(overrides: [
    authStatusProvider.overrideWithValue(AuthStatus.signedIn),
    storyRepositoryProvider.overrideWithValue(repo),
    audioControllerProvider.overrideWith(_StubAudioController.new),
  ]);
  addTearDown(container.dispose);
  await tester.pumpWidget(
    UncontrolledProviderScope(container: container, child: const StoryTellerApp()),
  );
  await tester.pumpAndSettle();
  container.read(storySelectionProvider.notifier).chooseTopic(topicCatalog.first);
  container.read(goRouterProvider).go('/story');
  // Not pumpAndSettle: the audio bar shows a perpetual spinner in tests.
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 50));
  await tester.pump(const Duration(milliseconds: 50));
  return container;
}

void main() {
  testWidgets('renders the generated story', (tester) async {
    await _pump(tester, _FakeRepo(result: _story()));

    expect(find.text('De maanhaas'), findsOneWidget);
    expect(find.textContaining('naar de maan wilde'), findsOneWidget);
    expect(find.text('Opnieuw'), findsOneWidget);
    expect(find.textContaining('Voorlezen wordt klaargemaakt'), findsOneWidget);
  });

  testWidgets('shows a kid-safe message when moderation rejects', (tester) async {
    await _pump(
      tester,
      _FakeRepo(
        error: const StoryGenerationException(StoryGenerationFailure.moderation),
      ),
    );

    expect(find.textContaining('niet goedgekeurd'), findsOneWidget);
    expect(find.text('Ander onderwerp'), findsOneWidget);
  });

  testWidgets('regenerate calls the repository again', (tester) async {
    final repo = _FakeRepo(result: _story());
    final container = await _pump(tester, repo);
    expect(repo.calls, 1);

    await tester.tap(find.text('Opnieuw'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(repo.calls, 2);
    container.dispose();
  });

  testWidgets('free-quota exhausted shows the paywall CTA', (tester) async {
    await _pump(
      tester,
      _FakeRepo(
        error:
            const StoryGenerationException(StoryGenerationFailure.limitReached),
      ),
    );

    expect(find.textContaining('gratis verhaaltjes voor deze week'),
        findsOneWidget);
    expect(find.widgetWithText(OutlinedButton, 'Abonnement'), findsOneWidget);
  });

  testWidgets('heart toggles the saved state', (tester) async {
    final repo = _SpyRepo(result: _story());
    await _pump(tester, repo);

    expect(find.byIcon(Icons.favorite_border_rounded), findsOneWidget);

    await tester.tap(find.byIcon(Icons.favorite_border_rounded));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(repo.savedCalls, [true]);
    expect(find.byIcon(Icons.favorite_rounded), findsOneWidget);
  });
}

class _SpyRepo extends _FakeRepo {
  _SpyRepo({super.result});
  final List<bool> savedCalls = [];

  @override
  Future<Story> setStorySaved(String storyId, {required bool saved}) async {
    savedCalls.add(saved);
    return (result ?? _story()).copyWith(isSaved: saved);
  }
}
