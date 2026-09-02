import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

/// How long a successful parental gate stays valid before it must be solved
/// again. Short by design: the gate protects settings + purchase screens, and
/// a child should not be able to walk back into them minutes later.
const kParentalGateValidity = Duration(minutes: 5);

/// Holds the moment the parental gate was last solved (null = never / expired).
///
/// This is intentionally *not* persisted. Every fresh app launch requires the
/// gate again before settings or the paywall can be opened.
class ParentalGateController extends Notifier<DateTime?> {
  @override
  DateTime? build() => null;

  bool get isVerified {
    final at = state;
    if (at == null) return false;
    return DateTime.now().difference(at) < kParentalGateValidity;
  }

  void markVerified() => state = DateTime.now();

  void reset() => state = null;
}

final parentalGateControllerProvider =
    NotifierProvider<ParentalGateController, DateTime?>(
  ParentalGateController.new,
);

/// A single arithmetic challenge shown to the parent.
class ParentalChallenge {
  ParentalChallenge(this.a, this.b);

  final int a;
  final int b;

  int get answer => a + b;
  String get question => '$a + $b';

  /// Two-digit sums that are awkward for a young child but trivial for an adult.
  factory ParentalChallenge.random([Random? rng]) {
    final r = rng ?? Random();
    final a = 11 + r.nextInt(78); // 11..88
    final b = 11 + r.nextInt(78);
    return ParentalChallenge(a, b);
  }
}

/// Rebuilds a fresh challenge each time it is invalidated.
final parentalChallengeProvider = Provider.autoDispose<ParentalChallenge>((ref) {
  return ParentalChallenge.random();
});
