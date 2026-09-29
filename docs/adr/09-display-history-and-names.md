# ADR 09: The display shows history, names and a language switch

- **Status:** Proposed
- **Date:** 2026-09-29
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

Testing M3, the owner asked for four things on the display. The owner has already chosen the options in items 2–4 (2026-09-29):

1. arrows to see previous posts
2. who a post comes from
3. who reacted
4. a way to change the language on the display itself, e.g. from "Nothing here yet"

Today the display shows only the current moment and its reaction buttons, with "nothing else to tap" (M3 outcome). A display's language is set in admin, and since `107d779` a change there reaches an open screen within about 2 s. The brief puts "in-app history and timeline" on the roadmap, not in the MVP.

The data is already there:
- Every moment is kept, and history is ordered by `effective_at` (ADR 00).
- Each reaction carries `by`: the display's label, or the person's chosen name (ADR 05).
- Content events have an `author` column, which the M4 sender app will fill in.

## Decisions

### 1. ⚑ Arrows through the space's whole history

Amends M3's "nothing else to tap" and brings part of the roadmap's history into M3.

- **Controls:** ‹ and › at the screen edges, and swiping on touch screens. › is hidden on the latest moment, and ‹ on the oldest.
- **Back to the latest:** the screen returns to the latest moment after **2 minutes** without a touch, and at once when a new moment arrives. A screen on the wall is never left on an old post.
- **Reacting to an older moment:** tapping an emoji there reacts to *that* moment. `POST /api/events` already allows it (the target must be in the same space).
- **API:** `GET /api/display/moments?before=<event id>&limit=10`, for displays only and scoped like the snapshot. It returns moments newest first, each with its reactions, ordered as ADR 00's "current content" rule orders them.
- **Offline:** the service worker keeps the photos of the **last 10 moments**, instead of only the current one. Older photos need the server, and show the note and a quiet placeholder while it's off.

### 2. The author on each moment

- **Format:** a quiet line under the note, "from Manu · 9:30" / "de Manu · 9:30". The time uses `Intl.DateTimeFormat` in the screen's language. It shows the date too when the moment isn't from today.
- **Which name:** the author's chosen name (`User.shown_name`, ADR 05). A moment with no author, such as one posted by `post_moment` without `--as`, shows the time only.
- **Where it comes from:** `moment_json` gains `by`, so the snapshot, the stream and the history all carry it.
- **Testing before M4:** `post_moment` gains `--as <username>`, which must be a member of the space's vault.

### 3. Who reacted: the float plus a summary line

- **The float:** the floating emoji carries the name, e.g. "❤️ Maman".
- **The summary:** a quiet line under the moment lists its recent reactions, newest first, as "❤️ Maman · 😂 Kitchen · ❤️ Léa". It's capped to what fits on one line (at most `RECENT_REACTIONS`). Nothing in it is tappable.
- **What it's built from:** the snapshot's and the history's `reactions`, plus the live ones.

**Not chosen:** counts with names shown on tap (a second tap target next to the reaction buttons, easy to mis-tap); names only on the float (anyone who wasn't looking never finds out).

### 4. ⚑ A language switch on the display's empty screen

Amends ADR 00 A5 ("after pairing, nothing changes").

- **Where:** the "Nothing here yet" screen shows **English | Français**, as the pairing screen does. It isn't shown over a moment: there, a mis-tap would switch Mum's screen, and admin remains the way to change it (applied live since `107d779`).
- **How:** `PATCH /api/me {language}`. A display may change only its own `Device.language`, to one of `LANGUAGES`. A personal device gets 403 for now; its language setting comes with M4's settings screen. The page then reloads.
- **Checks:** the usual `Origin` + `X-Coucou` ones. Isolation tests: a display can't change another device, and can't set an unknown language.

**Open for the owner:** should the switch also sit behind a long press on the moment screen? Recommendation: no, keep admin for that, to protect Mum's screen.

## How it gets built (inside M3, before sign-off)

- **Claude (protected):**
  - the history endpoint
  - `PATCH /api/me {language}` for displays
  - `moment_json`'s `by`
  - the service worker's 10-photo cache
  - `display.js` state: the position in history and the return to the latest
  - `post_moment --as`
- **Local model (UI, with browser tests written first):**
  - `render.js`: the arrows, the author line and the summary line; the float gets its name
  - `display.html`: the language switch and the new text
  - `display.css`: arrows, author line, summary line
  - the French

## Consequences

- The display is no longer "nothing else to tap": arrows and, on the empty screen only, a language switch. The reaction buttons stay the main thing.
- The history view on the roadmap starts here, on displays. The sender app's history (M5) can reuse the endpoint's shape.
- More photos are cached on the device: 10 display copies, about 5–10 MB.
- M3's outcome and "done when" in `docs/milestones/m3.md` gain these four items.
