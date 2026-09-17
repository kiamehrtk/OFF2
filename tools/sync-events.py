#!/usr/bin/env python3
"""Pull upcoming Harbour events from Tixr and regenerate the site's listings.

Rewrites only the regions between the AUTO:harbour-events markers in
events.html and index.html, so hand-written content (Tradex, copy, layout)
is never touched. Posters are downloaded, resized to 900px wide and saved
under images/events/.

Run:  python3 tools/sync-events.py          (writes)
      python3 tools/sync-events.py --check  (reports, changes nothing)
"""
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tixr

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
IMG_DIR = os.path.join(ROOT, "images", "events")
START = "<!-- AUTO:harbour-events start"
END = "<!-- AUTO:harbour-events end -->"
RAIL_LIMIT = 6           # homepage rail; the events page shows everything
VENUE = "Harbour Event Centre"


def upcoming_music(events):
    """PUBLISHED music events that have not happened yet, soonest first.

    status matters: ~10% of the feed is UNPUBLISHED drafts, which are
    unannounced shows and must never reach the public site.
    """
    now = int(time.time() * 1000)
    keep = [e for e in events
            if e.get("start_date", 0) > now
            and e.get("status") == "PUBLISHED"
            and e.get("category") == "Music Event"]
    keep.sort(key=lambda e: e["start_date"])
    return keep


def poster(event):
    """Download and downsize the flyer. Returns a site-relative path."""
    url = event.get("flyer_url")
    if not url:
        return None
    os.makedirs(IMG_DIR, exist_ok=True)
    name = "tixr-%s.jpg" % event["id"]
    dest = os.path.join(IMG_DIR, name)
    rel = "images/events/" + name
    if os.path.exists(dest):
        return rel
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            data = r.read()
        open(dest, "wb").write(data)
        # Same recipe as the rest of the site's imagery — full-size flyers
        # are ~1200-2000px and would undo the performance work.
        subprocess.run(["sips", "--resampleWidth", "900", "-s", "format", "jpeg",
                        "-s", "formatOptions", "78", dest, "--out", dest],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return rel
    except Exception as exc:
        print("  ! poster failed for %s: %s" % (event["id"], exc))
        return None


def normalise(event):
    t = time.localtime(event["start_date"] / 1000)
    age = event.get("age_restriction")
    return {
        "id": event["id"],
        "name": event["name"].strip(),
        "date": time.strftime("%a %d %b", t),
        "doors": time.strftime("Doors %H:%M", t),
        "age": ("%d+" % age) if age else "All ages",
        "link": event.get("short_url") or event.get("url"),
        "image": poster(event),
        "startsAt": event["start_date"],
    }


def card(ev, rail):
    """Mirror the existing hand-written card markup exactly."""
    e = lambda s: html.escape(s, quote=True)
    media = ('<div class="img-slot is-filled"><img src="%s" alt="%s — %s, %s" loading="lazy"></div>'
             % (e(ev["image"]), e(ev["name"]), e(VENUE), e(ev["date"]))) if ev["image"] else \
            ('<div class="img-slot"><span>%s</span></div>' % e(ev["name"]))
    venue_line = "" if rail else '\n              <div class="card__venue">%s</div>' % e(VENUE)
    inner = (
        '<a href="%s" class="card" target="_blank" rel="noopener noreferrer">\n'
        '            <div class="card__media">%s</div>\n'
        '            <div class="card__body">\n'
        '              <div class="card__date">%s</div>\n'
        '              <div class="card__name">%s</div>%s\n'
        '              <div class="card__row"><span>%s</span><span>%s</span></div>\n'
        '              <div class="card__tickets">Tickets →</div>\n'
        '            </div>\n'
        '          </a>'
        % (e(ev["link"]), media, e(ev["date"]), e(ev["name"]), venue_line,
           e(ev["age"]), e(ev["doors"]))
    )
    if rail:
        return "\n        " + inner
    return ('\n        <div class="event-item" data-filter-key="harbour" data-reveal>\n          '
            + inner + "\n        </div>")


def splice(path, markup):
    p = os.path.join(ROOT, path)
    s = open(p, encoding="utf-8").read()
    i, j = s.index(START), s.index(END)
    head = s[:s.index("-->", i) + 3]
    out = s[:i] + head[i:] + markup + "\n        " + s[j:]
    open(p, "w", encoding="utf-8").write(out)


def main():
    check = "--check" in sys.argv
    gid, cpk, secret = tixr.credentials("HARBOUR")
    events = upcoming_music(tixr.fetch_events(gid, cpk, secret))

    # Never blank the listings because of a bad response.
    if not events:
        raise SystemExit("ERROR: Tixr returned no upcoming music events. "
                         "Refusing to write empty listings; site left as-is.")

    print("%d upcoming music events at Harbour" % len(events))
    for e in events[:RAIL_LIMIT]:
        print("  %-15s %s" % (time.strftime("%a %d %b", time.localtime(e["start_date"] / 1000)),
                              e["name"][:50]))
    if len(events) > RAIL_LIMIT:
        print("  … and %d more" % (len(events) - RAIL_LIMIT))
    if check:
        print("\n--check: nothing written.")
        return

    rows = [normalise(e) for e in events]
    splice("events.html", "".join(card(r, rail=False) for r in rows))
    splice("index.html", "".join(card(r, rail=True) for r in rows[:RAIL_LIMIT]))

    snapshot = os.path.join(ROOT, "content", "events-harbour.json")
    json.dump({"venue": VENUE, "source": "Tixr group %s" % gid,
               "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "events": rows}, open(snapshot, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    open(snapshot, "a", encoding="utf-8").write("\n")
    print("\nWrote events.html, index.html, content/events-harbour.json")


if __name__ == "__main__":
    main()
