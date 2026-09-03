import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/models/subscription.dart';
import '../../data/story_repository.dart';

/// Status + this week's free-tier usage. Auto-disposed; re-fetched each time a
/// screen that needs it mounts.
final subscriptionProvider = FutureProvider.autoDispose<Subscription>((ref) {
  return ref.watch(storyRepositoryProvider).fetchSubscription();
});

/// Buying a subscription. The real implementation (RevenueCat `purchases_flutter`)
/// lands once the App Store / Play Console products + API keys exist; until then
/// [isConfigured] is false and the paywall shows a "coming soon" state.
abstract class PurchasesService {
  bool get isConfigured;
  Future<void> buy();
}

class StubPurchasesService implements PurchasesService {
  const StubPurchasesService();

  @override
  bool get isConfigured => false;

  @override
  Future<void> buy() async =>
      throw UnsupportedError('Purchases are not configured yet.');
}

final purchasesServiceProvider =
    Provider<PurchasesService>((_) => const StubPurchasesService());
