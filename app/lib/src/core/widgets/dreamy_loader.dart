import 'dart:math' as math;

import 'package:flutter/material.dart';

/// A calm, wordless loading animation for the story-generation wait: a moon
/// that gently breathes while a few stars twinkle around it. No harsh spinner.
class DreamyLoader extends StatefulWidget {
  const DreamyLoader({super.key, this.message, this.hint});

  final String? message;
  final String? hint;

  @override
  State<DreamyLoader> createState() => _DreamyLoaderState();
}

class _DreamyLoaderState extends State<DreamyLoader>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(seconds: 4))
        ..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 140,
            height: 140,
            child: AnimatedBuilder(
              animation: _c,
              builder: (context, _) {
                final t = _c.value;
                final breathe = 1 + 0.06 * math.sin(t * 2 * math.pi);
                return Stack(
                  alignment: Alignment.center,
                  children: [
                    _Twinkle(phase: t, offset: const Offset(-46, -34), size: 14),
                    _Twinkle(phase: t + 0.33, offset: const Offset(48, -18), size: 10),
                    _Twinkle(phase: t + 0.66, offset: const Offset(30, 44), size: 12),
                    Transform.scale(
                      scale: breathe,
                      child: Icon(Icons.nightlight_round,
                          size: 84, color: theme.colorScheme.tertiary),
                    ),
                  ],
                );
              },
            ),
          ),
          const SizedBox(height: 20),
          Text(widget.message ?? 'Even geduld…',
              style: theme.textTheme.titleMedium),
          if (widget.hint != null) ...[
            const SizedBox(height: 4),
            Text(widget.hint!, style: theme.textTheme.bodyMedium),
          ],
        ],
      ),
    );
  }
}

class _Twinkle extends StatelessWidget {
  const _Twinkle({
    required this.phase,
    required this.offset,
    required this.size,
  });

  final double phase;
  final Offset offset;
  final double size;

  @override
  Widget build(BuildContext context) {
    final p = phase % 1.0;
    final opacity = (0.3 + 0.7 * (0.5 + 0.5 * math.sin(p * 2 * math.pi)))
        .clamp(0.0, 1.0);
    return Transform.translate(
      offset: offset,
      child: Opacity(
        opacity: opacity,
        child: Icon(Icons.star_rounded,
            size: size, color: Theme.of(context).colorScheme.secondary),
      ),
    );
  }
}
