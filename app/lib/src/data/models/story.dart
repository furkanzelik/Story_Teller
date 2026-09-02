import 'age_group.dart';

/// A generated (and moderation-approved) bedtime story.
///
/// `audioUrl` is null until TTS has run (Fase 3). The backend only ever
/// returns stories that already passed the moderation check, so the app does
/// not re-validate content.
class Story {
  const Story({
    required this.id,
    required this.title,
    required this.body,
    required this.topicLabel,
    required this.ageGroup,
    required this.createdAt,
    this.topicId,
    this.audioUrl,
    this.isSaved = false,
  });

  final String id;
  final String title;
  final String body;
  final String topicLabel;
  final String? topicId;
  final AgeGroup ageGroup;
  final DateTime createdAt;
  final String? audioUrl;
  final bool isSaved;

  bool get hasAudio => audioUrl != null && audioUrl!.isNotEmpty;

  Story copyWith({bool? isSaved}) => Story(
        id: id,
        title: title,
        body: body,
        topicLabel: topicLabel,
        topicId: topicId,
        ageGroup: ageGroup,
        createdAt: createdAt,
        audioUrl: audioUrl,
        isSaved: isSaved ?? this.isSaved,
      );

  factory Story.fromJson(Map<String, dynamic> json) => Story(
        id: json['id'] as String,
        title: json['title'] as String,
        body: json['body'] as String,
        topicLabel: json['topic_label'] as String,
        topicId: json['topic_id'] as String?,
        ageGroup: AgeGroup.fromId(json['age_group'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
        audioUrl: json['audio_url'] as String?,
        isSaved: json['is_saved'] as bool? ?? false,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'body': body,
        'topic_label': topicLabel,
        'topic_id': topicId,
        'age_group': ageGroup.id,
        'created_at': createdAt.toIso8601String(),
        'audio_url': audioUrl,
        'is_saved': isSaved,
      };
}
