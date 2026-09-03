"""Generate the app icon + splash logo. Run: python3 tool/make_icon.py"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets" / "branding"
OUT.mkdir(parents=True, exist_ok=True)

INDIGO_TOP = (74, 61, 122)
INDIGO_BOTTOM = (43, 35, 74)
MOON = (255, 217, 142)
STAR = (255, 180, 162)


def _bg(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        t = y / size
        row = tuple(
            int(INDIGO_TOP[i] + (INDIGO_BOTTOM[i] - INDIGO_TOP[i]) * t)
            for i in range(3)
        )
        for x in range(size):
            px[x, y] = row
    return img.convert("RGBA")


def _crescent_layer(size: int, cx: int, cy: int, radius: int) -> Image.Image:
    """A clean crescent as its own RGBA layer (full circle minus an offset one)."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    disc = Image.new("L", (size, size), 0)
    ImageDraw.Draw(disc).ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius], fill=255
    )
    bite = Image.new("L", (size, size), 0)
    off = int(radius * 0.52)
    lift = int(radius * 0.12)
    ImageDraw.Draw(bite).ellipse(
        [cx - radius + off, cy - radius - lift,
         cx + radius + off, cy + radius - lift],
        fill=255,
    )
    mask = Image.eval(disc, lambda a: a)  # copy
    mask.paste(0, (0, 0), bite)  # subtract the bite
    solid = Image.new("RGBA", (size, size), MOON + (255,))
    layer.paste(solid, (0, 0), mask)
    return layer


def _stars(draw: ImageDraw.ImageDraw, size: int, pts) -> None:
    for fx, fy, fr in pts:
        cx, cy, r = int(fx * size), int(fy * size), int(fr * size)
        poly = []
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.42
            poly.append((cx + rad * math.cos(ang), cy - rad * math.sin(ang)))
        draw.polygon(poly, fill=STAR)


def icon(size: int) -> Image.Image:
    img = _bg(size)
    img.alpha_composite(_crescent_layer(size, int(size * 0.52), int(size * 0.5),
                                        int(size * 0.27)))
    _stars(ImageDraw.Draw(img), size,
           [(0.72, 0.26, 0.05), (0.80, 0.60, 0.038), (0.34, 0.74, 0.045)])
    return img


def main() -> None:
    icon(1024).convert("RGB").save(OUT / "icon.png")

    fg = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    fg.alpha_composite(_crescent_layer(1024, 512, 500, 200))
    fg.save(OUT / "icon_foreground.png")

    splash = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    splash.alpha_composite(_crescent_layer(512, 256, 250, 150))
    splash.save(OUT / "splash_logo.png")
    print("wrote", *(sorted(p.name for p in OUT.iterdir())))


if __name__ == "__main__":
    main()
