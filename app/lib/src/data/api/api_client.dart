import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../core/config/env.dart';
import '../models/story.dart';
import '../models/subscription.dart';

/// Thin wrapper around [Dio] configured for the FastAPI backend.
///
/// Phase 1 only needs a reachable client + a health check. Story generation,
/// TTS and auth headers are layered on in later phases via the interceptor
/// placeholder below.
class ApiClient {
  ApiClient(this._dio);

  final Dio _dio;

  factory ApiClient.create() {
    final dio = Dio(
      BaseOptions(
        baseUrl: Env.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 60), // LLM + TTS can be slow
        headers: {'Content-Type': 'application/json'},
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final token = _currentAccessToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
      ),
    );

    if (Env.debugLogging) {
      dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
      ));
    }

    return ApiClient(dio);
  }

  /// Returns true when the backend answers `GET /health` with 200.
  Future<bool> health() async {
    try {
      final res = await _dio.get<Map<String, dynamic>>('/health');
      return res.statusCode == 200 && res.data?['status'] == 'ok';
    } on DioException {
      return false;
    }
  }

  /// POST /stories/generate — topic + age -> moderation-approved [Story].
  ///
  /// Throws [StoryGenerationException] with a [StoryGenerationFailure] kind the
  /// UI can branch on.
  Future<Story> generateStory({
    required String topicId,
    required String ageGroup,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        '/stories/generate',
        data: {'topic_id': topicId, 'age_group': ageGroup},
      );
      return Story.fromJson(res.data!);
    } on DioException catch (e) {
      throw StoryGenerationException.fromStatus(e.response?.statusCode);
    }
  }

  /// POST /stories/{id}/audio — generate (once, then cached) the read-aloud
  /// audio and return an absolute URL the player can stream.
  Future<String> fetchStoryAudio(String storyId) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        '/stories/$storyId/audio',
      );
      final path = res.data!['audio_url'] as String;
      // Backend returns a relative "/media/…" path.
      return path.startsWith('http')
          ? path
          : '${_dio.options.baseUrl}$path';
    } on DioException catch (e) {
      throw StoryAudioException(e.response?.statusCode);
    }
  }

  /// GET /stories — the signed-in parent's saved library.
  Future<List<Story>> listSavedStories() async {
    final res = await _dio.get<List<dynamic>>('/stories');
    return (res.data ?? [])
        .map((e) => Story.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// PUT /stories/{id}/saved — add to / remove from the library.
  Future<Story> setStorySaved(String storyId, {required bool saved}) async {
    final res = await _dio.put<Map<String, dynamic>>(
      '/stories/$storyId/saved',
      data: {'saved': saved},
    );
    return Story.fromJson(res.data!);
  }

  /// GET /me/subscription — status + this week's free-tier usage.
  Future<Subscription> fetchSubscription() async {
    final res = await _dio.get<Map<String, dynamic>>('/me/subscription');
    return Subscription.fromJson(res.data!);
  }

  /// DELETE /me — permanently delete the account and all its data.
  Future<void> deleteAccount() async {
    await _dio.delete<void>('/me');
  }
}

class StoryAudioException implements Exception {
  const StoryAudioException(this.status);
  final int? status;

  String get message => switch (status) {
        502 => 'Het voorlezen lukte niet. Probeer het opnieuw.',
        503 => 'Voorlezen is nu niet beschikbaar.',
        _ => 'Kon de audio niet laden.',
      };
}

enum StoryGenerationFailure {
  moderation,
  unavailable,
  notSignedIn,
  limitReached,
  unknown,
}

class StoryGenerationException implements Exception {
  const StoryGenerationException(this.kind);

  final StoryGenerationFailure kind;

  factory StoryGenerationException.fromStatus(int? status) => switch (status) {
        402 =>
          const StoryGenerationException(StoryGenerationFailure.limitReached),
        422 => const StoryGenerationException(StoryGenerationFailure.moderation),
        502 || 503 =>
          const StoryGenerationException(StoryGenerationFailure.unavailable),
        401 => const StoryGenerationException(
            StoryGenerationFailure.notSignedIn),
        _ => const StoryGenerationException(StoryGenerationFailure.unknown),
      };

  /// Kid-safe Dutch copy for each failure kind.
  String get message => switch (kind) {
        StoryGenerationFailure.moderation =>
          'Dit verhaaltje werd niet goedgekeurd. Probeer een ander onderwerp.',
        StoryGenerationFailure.unavailable =>
          'De verhaaltjesmaker is even niet bereikbaar. Probeer het zo nog eens.',
        StoryGenerationFailure.notSignedIn =>
          'Je bent uitgelogd. Log opnieuw in.',
        StoryGenerationFailure.limitReached =>
          'Je gratis verhaaltjes voor deze week zijn op.',
        StoryGenerationFailure.unknown =>
          'Er ging iets mis. Probeer het opnieuw.',
      };
}

/// Supabase JWT for the signed-in parent, or null. Guarded so the app still
/// runs before `Supabase.initialize` (dev without config).
String? _currentAccessToken() {
  try {
    return Supabase.instance.client.auth.currentSession?.accessToken;
  } catch (_) {
    return null;
  }
}

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient.create());

/// One-shot backend reachability probe, handy on a debug screen.
final backendHealthProvider = FutureProvider<bool>((ref) {
  return ref.watch(apiClientProvider).health();
});
