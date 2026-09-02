import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:story_teller_app/src/core/parental_gate/parental_gate_controller.dart';

void main() {
  test('gate starts unverified and expires after the validity window', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final gate = container.read(parentalGateControllerProvider.notifier);
    expect(gate.isVerified, isFalse);

    gate.markVerified();
    expect(gate.isVerified, isTrue);

    gate.reset();
    expect(gate.isVerified, isFalse);
  });

  test('challenge answer is the sum of its operands', () {
    final challenge = ParentalChallenge.random(Random(42));
    expect(challenge.answer, challenge.a + challenge.b);
    expect(challenge.a, inInclusiveRange(11, 88));
    expect(challenge.b, inInclusiveRange(11, 88));
  });
}
