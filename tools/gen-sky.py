#!/usr/bin/env python3
"""Regenerate the .sky__layer inline gradients across the site.

Icy-blue/white starfield. Seeded so a re-run produces the same sky and the
diff stays stable.

Performance note: the glow is baked into each gradient's colour stops — a
bright core, a mid halo, then falloff — rather than applied with
filter: drop-shadow(). The filter version cost a full offscreen blur pass
per layer per frame, and these layers animate continuously, which made the
page crawl. Keep it that way: no `filter` on a layer that animates.
"""
import glob
import random
import re

# name, count, radius px, core rgb, halo rgb, alpha range, animation
LAYERS = [
    (
        "fine", 118, 3.2, (226, 244, 255), (150, 214, 255), (0.34, 0.66),
        "off2Twinkle 7s ease-in-out infinite, off2Float 46s ease-in-out infinite",
    ),
    (
        "mid", 44, 5.5, (236, 249, 255), (126, 200, 245), (0.50, 0.88),
        "off2Twinkle 5.2s ease-in-out infinite reverse, off2Float 34s ease-in-out infinite",
    ),
    (
        "bright", 26, 10, (255, 255, 255), (126, 200, 245), (0.70, 1.0),
        "off2Twinkle 3.6s ease-in-out infinite, off2Float 26s ease-in-out infinite",
    ),
    (
        "bokeh", 10, 16, (198, 232, 255), (140, 205, 250), (0.16, 0.32),
        "off2Float 20s ease-in-out infinite",
    ),
]


def build_layer(rng, count, radius, core, halo, arange, animation):
    cr, cg, cb = core
    hr, hg, hb = halo
    stops = []
    for _ in range(count):
        x, y = rng.uniform(0, 100), rng.uniform(0, 100)
        a = rng.uniform(*arange)
        # Core -> halo -> transparent. The tight first stop keeps the star a
        # point; the wide tail is the glow.
        stops.append(
            "radial-gradient(circle %gpx at %.2f%% %.2f%%, "
            "rgba(%d,%d,%d,%.2f) 0%%, "
            "rgba(%d,%d,%d,%.2f) 18%%, "
            "rgba(%d,%d,%d,%.2f) 42%%, "
            "rgba(%d,%d,%d,0) 100%%)"
            % (radius, x, y,
               cr, cg, cb, a,
               cr, cg, cb, a * 0.55,
               hr, hg, hb, a * 0.22,
               hr, hg, hb)
        )
    style = "animation: %s; background-image: %s;" % (animation, ", ".join(stops))
    return '    <div class="sky__layer" style="%s"></div>' % style


def main():
    pattern = re.compile(r'^\s*<div class="sky__layer".*?</div>\s*$', re.M)
    for path in sorted(glob.glob("*.html")):
        src = open(path, encoding="utf-8").read()
        if '<div class="sky__layer"' not in src:
            continue
        rng = random.Random(hash(path) & 0xFFFF)
        blocks = [build_layer(rng, *cfg[1:]) for cfg in LAYERS]
        if len(pattern.findall(src)) != len(LAYERS):
            print("  %-16s SKIP — layer count mismatch" % path)
            continue
        i = 0

        def sub(_m):
            nonlocal i
            block = blocks[i]
            i += 1
            return block

        src = pattern.sub(sub, src)
        open(path, "w", encoding="utf-8").write(src)
        print("  %-16s %d stars, no filters" % (path, sum(c[1] for c in LAYERS)))


if __name__ == "__main__":
    main()
