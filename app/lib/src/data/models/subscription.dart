/// Subscription status + this week's free-tier usage (GET /me/subscription).
class Quota {
  const Quota({
    required this.unlimited,
    required this.limit,
    required this.used,
    required this.remaining,
    required this.resetsAt,
  });

  final bool unlimited;
  final int limit;
  final int used;
  final int remaining; // -1 when unlimited
  final DateTime resetsAt;

  bool get exhausted => !unlimited && remaining <= 0;

  factory Quota.fromJson(Map<String, dynamic> json) => Quota(
        unlimited: json['unlimited'] as bool,
        limit: json['limit'] as int,
        used: json['used'] as int,
        remaining: json['remaining'] as int,
        resetsAt: DateTime.parse(json['resets_at'] as String),
      );
}

enum SubscriptionStatus { free, active, inGrace, expired }

SubscriptionStatus _statusFrom(String s) => switch (s) {
      'active' => SubscriptionStatus.active,
      'in_grace' => SubscriptionStatus.inGrace,
      'expired' => SubscriptionStatus.expired,
      _ => SubscriptionStatus.free,
    };

class Subscription {
  const Subscription({
    required this.status,
    required this.quota,
    this.plan,
  });

  final SubscriptionStatus status;
  final String? plan;
  final Quota quota;

  bool get isSubscriber =>
      status == SubscriptionStatus.active ||
      status == SubscriptionStatus.inGrace;

  factory Subscription.fromJson(Map<String, dynamic> json) => Subscription(
        status: _statusFrom(json['status'] as String),
        plan: json['plan'] as String?,
        quota: Quota.fromJson(json['quota'] as Map<String, dynamic>),
      );
}
