# OFF2 Entertainment — Website

Coded from the OFF2 Homepage design (Claude Design project `68d6471e-054c-4a69-a351-e9673f7dbd2b`).
Static HTML/CSS/JS, no build step — open `index.html` or serve the folder.

## What's here

```
index.html              Homepage — everything from the design (nav, hero carousel,
                         starfield/meteor background, festivals, events, gallery,
                         about, newsletter, footer)
festivals.html           Festivals index — one entry per festival (Insomnia,
                         Doomsnight, Soul Rise, Null Horizon) with its own poster,
                         date, tagline and a subtle per-festival accent color
                         (--mood on each .festival-entry). Each entry links out to
                         coming-soon.html?title=<name> — the individual festival
                         page (e.g. /festivals/insomnia) is a separate template
                         not built yet.
events.html              Events index — every event across both venues, with a
                         venue-filter (All / Harbour Event Centre / Tradex) that
                         fades cards in/out via data-venue attributes. No real
                         Tradex events exist yet, so that filter shows an honest
                         empty state (data-venue-empty) instead of invented shows.
venues.html              Venues page — one stacked section per owned venue
                         (Harbour Event Centre, Tradex), each with a 4-up image
                         strip, description, address + map link, and a "Book this
                         venue" CTA. Gallery images are still placeholders; no
                         capacity/spec numbers by request.
gallery.html             Gallery page — photos from past shows in a mixed-size
                         grid, filterable by album (Lost in Dreams / Insomnia /
                         Doomsnight / Soul Rise / Harbour Nights), with a
                         click-to-enlarge lightbox (Esc or click-out to close).
                         The 6 Lost in Dreams tiles are real photography; the
                         other albums are still placeholders.
careers.html             Careers page — headline, a 3-up culture block, and the
                         open-positions section. There are no real openings, so it
                         renders the "no open roles / send us your resume" block
                         rather than invented listings; the .job-row markup for a
                         live roster is documented in an HTML comment in the file.
coming-soon.html         Stand-in for pages not built yet (Press, booking enquiry
                         flow, individual festival/event pages, full Gallery
                         page) — linked with a ?title= so it doesn't 404
css/style.css            All styling. Every design token (colors, fonts, spacing)
                         is a CSS custom property at the top of the file.
js/main.js               Hero carousel autoplay/dots/arrows, scroll-reveal
                         animation, mobile nav toggle, generic filter groups
                         (events.html venues + gallery.html albums), gallery
                         lightbox, newsletter form stub
content/site-content.json  Documents the CMS content shape (see below) — not
                         wired in yet, just the target schema
```

## Running it locally

No build step needed. Either open `index.html` directly, or serve it so relative
paths behave the same as production:

```bash
npx serve .
```

## Images

Real photos were pulled from [github.com/kiamehrtk/OFF2](https://github.com/kiamehrtk/OFF2)
and are filled in for:

- **Hero carousel** (2 slides by request — Insomnia and Sofi Tukker slides were
  removed): Doomsnight, Soul Rise (`images/hero-*.jpg`)
- **Festivals grid** (still shows all 4 festivals): Insomnia, Doomsnight, Soul Rise
  (`images/festival-*.jpg`)
- **Events rail** (all 5, real upcoming Harbour shows, ordered chronologically):
  Mike Williams (Fri 14 Aug), KREAM & Adam Sellouk / Liquid:Lab (Sat 15 Aug),
  DJ Diesel aka Shaquille O'Neal (Fri 21 Aug), Kevin De Vries / Soulrise Afterparty
  (Sat 29 Aug), Vikkstar (Sat 05 Sep) — `images/event-*.jpg`. Dates/lineups/doors
  times were read directly off each poster; the original 5 (Sofi Tukker, Kess
  Vault, Low Ceiling, Zero Hour NYE, Signal Test 01) were placeholders and have
  been replaced.

The source repo had one banner/poster pair per festival — a 16:9 banner and a
portrait poster. All six images were downsized for the web (banners → max 2400px
wide, posters → max 1600px wide) since the originals ran up to 25MB.

The hero uses **both** images per slide: the 16:9 banner on desktop/tablet, and
below 720px width it swaps to the portrait poster instead (via a `<picture><source
media="(max-width: 720px)">` in each `.hero__media` in `index.html`) — a banner
crops away too much of the artwork at phone widths, the poster doesn't.

- **Gallery** (`gallery.html`): 6 photos from **Lost in Dreams**
  (`images/gallery-*.jpg`) — downsized from ~5400px/8-13MB originals to 1600px
  wide (~1.7MB total), which stays sharp in the lightbox (capped at 1100px).
  Captions describe what's visible in each frame; the event name came from you,
  since nothing readable in the photos identifies the show.

Still **placeholders** — no source photo exists yet, to be provided later:

- Festival card 4, **Null Horizon**
- The homepage's 4 **gallery** teaser tiles
- The 12 non-Lost-in-Dreams **gallery page** tiles (Insomnia, Doomsnight,
  Soul Rise, Harbour Nights)
- Both **venues** galleries (4 images each)
- The **about** section's venue/crew photo

To fill one of the remaining slots: drop the real image file into `images/`,
then in `index.html` replace that slot's `<div class="img-slot">...</div>`
contents with `<img src="images/whatever.jpg" alt="...">` and add the
`is-filled` class to the `.img-slot` div — see the six now-filled slots in
`index.html` for the exact pattern, and the comment above `.img-slot` in
`css/style.css` for how the CSS hides the placeholder chrome once filled.

## CMS — next step, not done yet

Per your call, this pass just ships the working site; no CMS is wired in. When
you're ready to add one:

- Every editable piece of text/image in `index.html` has a `data-cms="section.field"`
  attribute (e.g. `data-cms="hero.slides[0].title"`), and `content/site-content.json`
  mirrors that same structure. Together they're the map for wiring in a CMS
  without re-deriving what's editable from scratch.
- Recommended path: **Next.js + Decap CMS** — free, git-based (no database or
  backend to host), gives non-technical editors a login + visual form at `/admin`.
  Content edits commit to the repo and redeploy automatically on Vercel/Netlify.
  Alternative if you want a more full-featured editor UI: **Sanity** (hosted,
  has a proper media library and roles, but is an external service to manage).
- The migration is mostly: move each `data-cms` element's static value into a
  template call reading the matching `site-content.json` key (or the chosen
  CMS's equivalent), then point image slots at the CMS's media URLs.

## Notes on what changed from the design file

The design was authored in Claude Design's `.dc.html` format, which depends on
a proprietary runtime (`support.js` / `dc-runtime`) and a custom `<image-slot>`
web component that only works inside that tool's editor (drag-drop persistence
goes through a backend the design tool controls). Those aren't usable outside
the design tool, so:

- All inline `style="..."` + the non-standard `style-hover="..."` attributes
  were converted into real CSS classes with `:hover`/`:focus` rules in
  `css/style.css`.
- The hero carousel and scroll-reveal `<script data-dc-script>` logic were
  ported to plain vanilla JS in `js/main.js` (same timings/behavior — 6s
  autoplay, pause on hover, `IntersectionObserver`-based reveal).
- `<image-slot>` was replaced with the `.img-slot` placeholder component
  described above.
- Nav links to other pages in the design project (Festivals, Events, Venues,
  Gallery, About, Careers) point to on-page anchors where the homepage already
  has that section, and to `coming-soon.html` where it doesn't — only the
  homepage was in scope for this pass.
- Basic mobile responsiveness (hamburger nav, stacked grids) was added; the
  source design only specified a desktop layout.
