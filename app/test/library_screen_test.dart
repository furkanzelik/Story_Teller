import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import 'package:story_teller_app/src/app.dart';
import 'package:story_teller_app/src/data/models/age_group.dart';
import 'package:story_teller_app/src/data/models/story.dart';
import 'package:story_teller_app/src/data/story_repository.dart';
import 'package:story_teller_app/src/features/auth/auth_controller.dart';
import 'package:story_teller_app/src/features/story/audio_controller.dart';
import 'package:story_teller_app/src/router/app_router.dart';

class _LibRepo implements StoryRepository {
  _LibRepo(this._saved);
  final List<Story> _saved;

  @override
  Future<List<Story>> listSavedStories() async => _saved;

  @override
  Future<Story> generateStory({
    required String topicId,
    required String ageGroup,
  }) async =>
      throw UnimplementedError();

  @override
  Future<String> fetchStoryAudio(String storyId) async =>
      throw UnimplementedError();

  @override
  Future<Story> setStorySaved(String storyId, {required bool saved}) async =>
      throw UnimplementedError();
}

class _StubAudio extends AudioController {
  @override
  Future<AudioPlayer> build() => Completer<AudioPlayer>().future;
}

Story _s(String id, String title) => Story(
      id: id,
      title: title,
      body: 'body van $title',
      topicLabel: 'De ruimte',
      topicId: 'space',
      ageGroup: AgeGroup.preschool,
      createdAt: DateTime(2026, 1, 1),
      isSaved: true,
    );

Future<ProviderContainer> _open(WidgetTester tester, _LibRepo repo) async {
  final container = ProviderContainer(overrides: [
    authStatusProvider.overrideWithValue(AuthStatus.signedIn),
    storyRepositoryProvider.overrideWithValue(repo),
    audioControllerProvider.overrideWith(_StubAudio.new),
  ]);
  addTearDown(container.dispose);
  await tester.pumpWidget(
    UncontrolledProviderScope(container: container, child: const StoryTellerApp()),
  );
  await tester.pumpAndSettle();
  container.read(goRouterProvider).go('/library');
  await tester.pumpAndSettle();
  return container;
}

void main() {
  testWidgets('lists saved stories', (tester) async {
    await _open(tester, _LibRepo([_s('1', 'De maanhaas'), _s('2', 'Sterrenjantje')]));

    expect(find.text('De maanhaas'), findsOneWidget);
    expect(find.text('Sterrenjantje'), findsOneWidget);
  });

  testWidgets('shows empty state when nothing saved', (tester) async {
    await _open(tester, _LibRepo([]));
    expect(find.textContaining('Nog geen opgeslagen'), findsOneWidget);
  });

  testWidgets('tapping a card reopens that story', (tester) async {
    await _open(tester, _LibRepo([_s('1', 'De maanhaas')]));

    await tester.tap(find.text('De maanhaas'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    // Story screen now shows the reopened story's body, no "Opnieuw" button
    // (view mode).
    expect(find.textContaining('body van De maanhaas'), findsOneWidget);
    expect(find.widgetWithText(OutlinedButton, 'Opnieuw'), findsNothing);
  });
}
