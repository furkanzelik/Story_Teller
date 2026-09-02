/// A story theme the child can pick. For the MVP the catalogue is a fixed list
/// shipped with the app (see `topicCatalog`); a free-text field comes later and
/// will sit behind the parental gate because it widens the moderation surface.
class Topic {
  const Topic({
    required this.id,
    required this.label,
    required this.emoji,
  });

  final String id;
  final String label;
  final String emoji;

  factory Topic.fromJson(Map<String, dynamic> json) => Topic(
        id: json['id'] as String,
        label: json['label'] as String,
        emoji: json['emoji'] as String? ?? '✨',
      );

  Map<String, dynamic> toJson() => {'id': id, 'label': label, 'emoji': emoji};
}

/// Fixed starter set. Safe, evergreen, easy to illustrate.
const List<Topic> topicCatalog = [
  Topic(id: 'space', label: 'De ruimte', emoji: '🚀'),
  Topic(id: 'animals', label: 'Dieren in het bos', emoji: '🦊'),
  Topic(id: 'ocean', label: 'Onder de zee', emoji: '🐳'),
  Topic(id: 'dinosaurs', label: 'Dinosauriërs', emoji: '🦕'),
  Topic(id: 'dragons', label: 'Vriendelijke draken', emoji: '🐲'),
  Topic(id: 'pirates', label: 'Op de piratenboot', emoji: '🏴‍☠️'),
  Topic(id: 'farm', label: 'Op de boerderij', emoji: '🐄'),
  Topic(id: 'magic', label: 'Toverland', emoji: '🪄'),
  Topic(id: 'trains', label: 'Grote treinen', emoji: '🚂'),
];
