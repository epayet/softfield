# ADR 10: A gallery view on the display

- **Status:** Proposed
- **Date:** 2026-09-29
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

ADR 09 lets a display step back through its space's history one moment at a time (‹ ›, swiping), with a pill back to the latest. Testing M3, the owner asked for a gallery: a way to see many past moments at once and jump to one. The owner wants it as a separate feature, not part of M3 (2026-09-29).

What exists already:
- `GET /api/display/moments?before=&limit=` pages through the history, newest first, each moment with its reactions (ADR 09).
- `GET /api/media/<event id>` serves a photo's display copy (long edge ≤ 3072 px, about 1 MB), only to devices that can read that event.
- The service worker keeps the 10 most recently used display copies for offline use.

Display copies are too heavy for a grid: 20 tiles would mean 20 MB on an old Android tablet.

## Decisions

### 1. Opening and closing

- A small grid button (▦), a quiet pill next to the cog at the top right, opens the gallery full screen, over the moment.
- A close button (×) closes it. It also closes by itself after **2 minutes** without a touch, when the screen returns to the latest moment (ADR 09).
- A new moment arriving while the gallery is open shows at the top of the grid; the screen doesn't jump.

### 2. The grid

- Tiles in a responsive grid, newest first, about 3 columns on a phone and 5–6 on a tablet in landscape.
- **A photo moment:** its thumbnail, cropped to a square (`object-fit: cover`).
- **A note-only moment:** a tile with the first lines of the note.
- Each tile has a small label with its day (`momentWhen`, ADR 09) and, when there is one, the author.
- The moment currently on screen is highlighted.
- Scrolling near the end loads the next page (`/api/display/moments?before=…`), until `more` is false.
- **Tapping a tile** closes the gallery and shows that moment. The arrows and the "Latest ›" pill then work from there.

### 3. Thumbnails

- `GET /api/media/<event id>?size=thumb` serves a **480 px, q80** JPEG, with the same access check as the photo (`readable_events`). Anything else is the same 404, and an unknown `size` is a 400.
- The thumbnail is made from the display copy the first time it's asked for, and kept under `.thumbs/` at the photo's relative path (`coucou/media_paths.py`). Existing photos need no migration.
- It's a fresh re-encode like every stored file (no metadata; an ICC profile only for sRGB/P3).
- **Offline:** the service worker keeps thumbnails in **their own cache** (the most recent 60), so browsing the gallery never pushes the last 10 display copies out. The first page of history is already cached (ADR 09).

### 4. Text

- "Gallery" / "Galerie" (the grid button's label), "Close" / "Fermer" (already there), and the page's usual "Loading…"-style line if a page is slow to come. French with the usual tone.

## How it gets built

- **Claude (protected):**
  - thumbnails in `coucou/media.py`, `coucou/media_paths.py`, `coucou/views/media.py`, with isolation tests
  - the service worker's thumbnail cache
  - `display.js`: open and close, paging, picking a tile, the idle close
- **Local model (UI, browser tests written first):**
  - `render.js`: `renderGallery(root, moments, { currentId, now, language, onPick })`
  - `display.html`: the gallery's elements and text, with the French
  - `display.css`: the grid, tiles and highlight
- A milestone of its own, or the first items of M4: the owner decides when.

## Consequences

- The display gets one more control, a quiet ▦ next to the cog.
- More files per photo: a thumbnail of about 30–60 KB, made on first view.
- The sender app's history (M5 and later) can reuse the same thumbnails and the grid's shape.
