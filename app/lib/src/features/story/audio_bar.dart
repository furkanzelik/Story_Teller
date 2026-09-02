import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';

import 'audio_controller.dart';

/// Play/pause + progress bar for the read-aloud audio. Loads automatically
/// when the story text is on screen; stays quiet (small hint + retry) if the
/// audio can't be produced so it never blocks reading the story.
class AudioBar extends ConsumerWidget {
  const AudioBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final audio = ref.watch(audioControllerProvider);

    return audio.when(
      loading: () => const _Shell(
        child: Row(
          children: [
            SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2.5),
            ),
            SizedBox(width: 12),
            Text('Voorlezen wordt klaargemaakt…'),
          ],
        ),
      ),
      error: (_, _) => _Shell(
        child: Row(
          children: [
            Icon(Icons.volume_off_rounded, color: theme.colorScheme.outline),
            const SizedBox(width: 12),
            const Expanded(child: Text('Voorlezen lukte niet.')),
            TextButton(
              onPressed: () =>
                  ref.read(audioControllerProvider.notifier).retry(),
              child: const Text('Probeer opnieuw'),
            ),
          ],
        ),
      ),
      data: (player) => _Shell(child: _Player(player: player)),
    );
  }
}

class _Shell extends StatelessWidget {
  const _Shell({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(20),
      ),
      child: child,
    );
  }
}

class _Player extends StatelessWidget {
  const _Player({required this.player});
  final AudioPlayer player;

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<PlayerState>(
      stream: player.playerStateStream,
      builder: (context, snap) {
        final state = snap.data;
        final playing = state?.playing ?? false;
        final completed = state?.processingState == ProcessingState.completed;

        return Row(
          children: [
            IconButton.filled(
              iconSize: 28,
              onPressed: () async {
                if (completed) {
                  await player.seek(Duration.zero);
                  await player.play();
                } else if (playing) {
                  await player.pause();
                } else {
                  await player.play();
                }
              },
              icon: Icon(
                completed
                    ? Icons.replay_rounded
                    : playing
                        ? Icons.pause_rounded
                        : Icons.play_arrow_rounded,
              ),
            ),
            Expanded(child: _Progress(player: player)),
          ],
        );
      },
    );
  }
}

class _Progress extends StatelessWidget {
  const _Progress({required this.player});
  final AudioPlayer player;

  static String _fmt(Duration d) {
    final m = d.inMinutes.remainder(60).toString();
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<Duration>(
      stream: player.positionStream,
      builder: (context, snap) {
        final pos = snap.data ?? Duration.zero;
        final total = player.duration ?? Duration.zero;
        final max = total.inMilliseconds.toDouble();
        final value = pos.inMilliseconds.clamp(0, total.inMilliseconds).toDouble();

        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SliderTheme(
              data: SliderTheme.of(context).copyWith(
                trackHeight: 3,
                thumbShape:
                    const RoundSliderThumbShape(enabledThumbRadius: 7),
              ),
              child: Slider(
                value: max > 0 ? value : 0,
                max: max > 0 ? max : 1,
                onChanged: max > 0
                    ? (v) => player.seek(Duration(milliseconds: v.round()))
                    : null,
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(_fmt(pos), style: Theme.of(context).textTheme.bodySmall),
                  Text(_fmt(total),
                      style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
