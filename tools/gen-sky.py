#!/usr/bin/env python3
"""Regenerate the .sky__layer inline gradients across the site.

Denser field, icy-blue/white palette, stronger glow. Seeded so a re-run
produces the same sky and the diff stays stable.
"""
import glob
import random
import re

# name, count, size px, rgb, alpha range, animation, filter
LAYERS = [
    (
        "fine", 118, 1.1, (214, 238, 255), (0.30, 0.62),
        "off2Twinkle 7s ease-in-out infinite, off2Float 46s ease-in-out infinite",
        "drop-shadow(0 0 3px rgba(170,220,255,0.55))",
    ),
    (
        "mid", 44, 1.9, (140, 212, 255), (0.45, 0.85),
        "off2Twinkle 5.2s ease-in-out infinite reverse, off2Float 34s ease-in-out infinite",
        "blur(0.3px) drop-shadow(0 0 7px rgba(126,200,245,0.9))",
    ),
    (
        "bright", 26, 3.4, (255, 255, 255), (0.62, 1.0),
        "off2Twinkle 3.6s ease-in-out infinite, off2Float 26s ease-in-out infinite",
        "blur(0.6px) drop-shadow(0 0 12px rgba(255,255,255,0.95)) "
        "drop-shadow(0 0 30px rgba(126,200,245,0.8))",
    ),
    (
        "bokeh", 10, 7, (176, 224, 255), (0.28, 0.55),
        "off2Float 20s ease-in-out infinite",
        "blur(4px)",
    ),
]


def build_layer(rng, count, size, rgb, arange, animation, filt):
    r, g, b = rgb
    stops = []
    for _ in range(count):
        x, y = rng.uniform(0, 100), rng.uniform(0, 100)
        a = rng.uniform(*arange)
        stops.append(
            "radial-gradient(circle %gpx at %.2f%% %.2f%%, "
            "rgba(%d,%d,%d,%.2f) 0%%, rgba(%d,%d,%d,0) 100%%)"
            % (size, x, y, r, g, b, a, r, g, b)
        )
    style = "animation: %s;" % animation
    if filt:
        style += " filter: %s;" % filt
    style += " background-image: %s;" % ", ".join(stops)
    return '    <div class="sky__layer" style="%s"></div>' % style


def main():
    pattern = re.compile(r'^\s*<div class="sky__layer".*?</div>\s*$', re.M)
    for path in sorted(glob.glob("*.html")):
        src = open(path, encoding="utf-8").read()
        if '<div class="sky__layer"' not in src:
            continue
        # Seeded per file so every page gets its own sky, reproducibly.
        rng = random.Random(hash(path) & 0xFFFF)
        blocks = [build_layer(rng, *cfg[1:]) for cfg in LAYERS]
        found = pattern.findall(src)
        if len(found) != len(LAYERS):
            print("  %-16s SKIP — found %d layers, expected %d"
                  % (path, len(found), len(LAYERS)))
            continue
        out, i = [], 0

        def sub(_m):
            nonlocal i
            block = blocks[i]
            i += 1
            return block

        src = pattern.sub(sub, src)
        open(path, "w", encoding="utf-8").write(src)
        total = sum(cfg[1] for cfg in LAYERS)
        print("  %-16s %d layers, %d stars" % (path, len(LAYERS), total))


if __name__ == "__main__":
    main()
