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
from datetime import datetime
from zoneinfo import ZoneInfo
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

# A Tixr group is a sales channel, not a venue: the OFF2 Live group sells
# Harbour shows too (Emo Orchestra, 5 Dec). So pull every group that can
# contain a Harbour date and bucket by the event's own venue name.
# HALO is deliberately absent — it reports itself as a separate venue and
# is not listed on this site.
SOURCE_GROUPS = ["HARBOUR", "LIVE", "HALO"]

# Harbour is one building with several rooms. Tixr names the main room and
# Blueprint after the venue, but Halo only as "Halo", so matching on the word
# "harbour" alone silently dropped every Halo date. Rooms are listed together
# under the Harbour filter and labelled individually on the card.
VENUE = "Harbour Event Centre"
ROOM_VENUES = {"halo": "Halo"}   # venue names that are Harbour rooms


def is_harbour(event):
    name = ((event.get("venue") or {}).get("name") or "").strip().lower()
    return "harbour" in name or name in ROOM_VENUES


def venue_label(event):
    """'Harbour Event Centre', or '… · Blueprint' / '… · Halo' for a room."""
    raw = ((event.get("venue") or {}).get("name") or "").strip()
    room = ROOM_VENUES.get(raw.lower())
    if not room:
        bracket = re.search(r"\(([^)]+)\)", raw)
        room = bracket.group(1).strip() if bracket else None
    return "%s · %s" % (VENUE, room) if room else VENUE


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


# Tixr timestamps are epoch ms, so they carry no timezone. Formatting them
# with the machine's local clock gave the right answer on a Vancouver laptop
# and the wrong one on the UTC CI runner, where a 22:00 show rolled over into
# 05:00 the next day. Always format in the venue's own timezone, which Tixr
# supplies per event.
DEFAULT_TZ = "America/Vancouver"


def local_time(event):
    name = (event.get("venue") or {}).get("timezone") or DEFAULT_TZ
    try:
        tz = ZoneInfo(name)
    except Exception:
        tz = ZoneInfo(DEFAULT_TZ)
    return datetime.fromtimestamp(event["start_date"] / 1000, tz)


def normalise(event):
    t = local_time(event)
    age = event.get("age_restriction")
    return {
        "id": event["id"],
        "name": event["name"].strip(),
        "date": t.strftime("%a %d %b"),
        "doors": t.strftime("Doors %H:%M"),
        "age": ("%d+" % age) if age else "All ages",
        "venue": venue_label(event),
        "link": event.get("short_url") or event.get("url"),
        "image": poster(event),
        "startsAt": event["start_date"],
    }


def card(ev, rail):
    """Mirror the existing hand-written card markup exactly."""
    e = lambda s: html.escape(s, quote=True)
    media = ('<div class="img-slot is-filled"><img src="%s" alt="%s — %s, %s" loading="lazy"></div>'
             % (e(ev["image"]), e(ev["name"]), e(ev["venue"]), e(ev["date"]))) if ev["image"] else \
            ('<div class="img-slot"><span>%s</span></div>' % e(ev["name"]))
    venue_line = "" if rail else '\n              <div class="card__venue">%s</div>' % e(ev["venue"])
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
    raw, seen = [], set()
    for group in SOURCE_GROUPS:
        gid, cpk, secret = tixr.credentials(group)
        for event in tixr.fetch_events(gid, cpk, secret):
            if not is_harbour(event):
                continue          # e.g. a Tradex date sold by this group
            if event["id"] in seen:
                continue          # same show listed under two groups
            seen.add(event["id"])
            raw.append(event)
    events = upcoming_music(raw)

    # Never blank the listings because of a bad response.
    if not events:
        raise SystemExit("ERROR: Tixr returned no upcoming music events. "
                         "Refusing to write empty listings; site left as-is.")

    print("%d upcoming music events at Harbour (groups: %s)"
          % (len(events), ", ".join(SOURCE_GROUPS)))
    for e in events[:RAIL_LIMIT]:
        print("  %-15s %s" % (local_time(e).strftime("%a %d %b"), e["name"][:50]))
    if len(events) > RAIL_LIMIT:
        print("  … and %d more" % (len(events) - RAIL_LIMIT))
    if check:
        print("\n--check: nothing written.")
        return

    rows = [normalise(e) for e in events]
    splice("events.html", "".join(card(r, rail=False) for r in rows))
    splice("index.html", "".join(card(r, rail=True) for r in rows[:RAIL_LIMIT]))

    snapshot = os.path.join(ROOT, "content", "events-harbour.json")
    json.dump({"venue": VENUE, "source": "Tixr groups " + ", ".join(SOURCE_GROUPS),
               "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "events": rows}, open(snapshot, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    open(snapshot, "a", encoding="utf-8").write("\n")
    print("\nWrote events.html, index.html, content/events-harbour.json")


if __name__ == "__main__":
    main()
