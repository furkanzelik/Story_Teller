import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:story_teller_app/src/app.dart';
import 'package:story_teller_app/src/core/parental_gate/parental_gate_controller.dart';
import 'package:story_teller_app/src/features/auth/auth_controller.dart';
import 'package:story_teller_app/src/router/app_router.dart';

/// Pretend the parent is already signed in. Supabase is not initialised in
/// tests, so without this override the router parks on the sign-in screen.
final _signedIn = authStatusProvider.overrideWithValue(AuthStatus.signedIn);

void main() {
  testWidgets('signed-out users land on the sign-in screen', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: StoryTellerApp()));
    await tester.pumpAndSettle();

    expect(find.text('Inloggen'), findsOneWidget);
    expect(find.text('Stuur mij een code'), findsOneWidget);
  });

  testWidgets('home renders once signed in', (tester) async {
    await tester.pumpWidget(
      ProviderScope(overrides: [_signedIn], child: const StoryTellerApp()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Maak een verhaaltje'), findsOneWidget);
    expect(find.text('Mijn verhaaltjes'), findsOneWidget);
  });

  testWidgets('opening settings is blocked by the parental gate', (tester) async {
    await tester.pumpWidget(
      ProviderScope(overrides: [_signedIn], child: const StoryTellerApp()),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Instellingen'));
    await tester.pumpAndSettle();

    expect(find.text('Even voor de ouders'), findsOneWidget);
    expect(find.text('Instellingen'), findsNothing);
  });

  testWidgets('solving the gate lets the parent through to settings',
      (tester) async {
    final container = ProviderContainer(overrides: [_signedIn]);
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const StoryTellerApp(),
      ),
    );
    await tester.pumpAndSettle();

    final router = container.read(goRouterProvider);
    router.go('/parental-gate?redirect=%2Fsettings');
    await tester.pumpAndSettle();

    final challenge = container.read(parentalChallengeProvider);
    await tester.enterText(find.byType(TextField), '${challenge.answer}');
    await tester.tap(find.text('Verder'));
    await tester.pumpAndSettle();

    expect(find.text('Instellingen'), findsOneWidget);
  });
}
