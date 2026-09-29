# ADR 09: The display shows history, names and a language switch

- **Status:** Proposed
- **Date:** 2026-09-29
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

Testing M3, the owner asked for four things on the display. The owner has already chosen the options in items 2–4 (2026-09-29):

1. arrows to see previous posts
2. who a post comes from
3. who reacted
4. a way to change the language on the display itself (a small cog in a corner, chosen 2026-09-29)

Today the display shows only the current moment and its reaction buttons, with "nothing else to tap" (M3 outcome). A display's language is set in admin, and since `107d779` a change there reaches an open screen within about 2 s. The brief puts "in-app history and timeline" on the roadmap, not in the MVP.

The data is already there:
- Every moment is kept, and history is ordered by `effective_at` (ADR 00).
- Each reaction carries `by`: the display's label, or the person's chosen name (ADR 05).
- Content events have an `author` column, which the M4 sender app will fill in.

## Decisions

### 1. ⚑ Arrows through the space's whole history

Amends M3's "nothing else to tap" and brings part of the roadmap's history into M3.

- **Controls:** ‹ and › at the screen edges, and swiping on touch screens. › is hidden on the latest moment, and ‹ on the oldest.
- **Back to the latest:** the screen returns to the latest moment after **2 minutes** without a touch, so a screen on the wall is never left on an old post. When a new moment arrives:
  - on the latest moment, or idle: it shows at once;
  - while someone is browsing (touched in the last 2 minutes): a small "New ›" hint appears, and the screen jumps when tapped or when it goes idle. (Open: the owner may prefer an immediate jump.)
- **Labels:** the arrows are buttons with translated labels ("Previous moment" / "Moment précédent", "Next moment" / "Moment suivant"). They sit at the side edges, vertically centred, away from the reaction buttons.
- **Reacting to an older moment:** tapping an emoji there reacts to *that* moment. `POST /api/events` already allows it (the target must be in the same space).
- **API:** `GET /api/display/moments?before=<event id>&limit=10`, for displays only and scoped like the snapshot. It returns moments newest first, each with its reactions.
  - **Order:** by (`effective_at`, `received_at`, id), the order of ADR 00's "current content" rule, and pages by that key. A moment that arrives late (M4's offline outbox) then lands in its place, never skipped or shown twice.
  - A `before` id from another space gets the same answer as an unknown one (404).
- **Offline:** the service worker keeps the photos of the **last 10 moments**, instead of only the current one. After each snapshot, the display fetches those photos in the background, so they're there before anyone browses; displays are on Wi-Fi. Older photos need the server, and show the note and a quiet placeholder while it's off.
- **Reactions to older moments:** a reaction to any moment still floats, with its name. If a screen is showing that moment, its summary line updates.

### 2. The author on each moment

- **Format:** a quiet line under the note, "from Manu · 9:30" / "de Manu · 9h30". The time uses `Intl` in the screen's language, and older moments say when in a warm, relative way ("yesterday at 9:30" / "hier à 9h30", then the weekday, then the date).
- **Which name:** the author's chosen name (`User.shown_name`, ADR 05). A moment with no author, such as one posted by `post_moment` without `--as`, shows the time only.
- **Where it comes from:** `moment_json` gains `by`, so the snapshot, the stream and the history all carry it.
- **Testing before M4:** `post_moment` gains `--as <username>`, which must be a member of the space's vault.

### 3. Who reacted: the float plus a summary line

- **The float:** the floating emoji carries the name, e.g. "❤️ Maman".
- **The summary:** a quiet line under the moment lists its recent reactions, newest first, as "❤️ Maman · 😂 Kitchen · ❤️ Léa". One entry per person and emoji: Maman tapping ❤️ three times shows once. It's capped to what fits on one line (at most `RECENT_REACTIONS`). Nothing in it is tappable.
- **What it's built from:** the snapshot's and the history's `reactions`, plus the live ones.

**Not chosen:** counts with names shown on tap (a second tap target next to the reaction buttons, easy to mis-tap); names only on the float (anyone who wasn't looking never finds out).

### 4. ⚑ A small cog on the display for its language

Amends ADR 00 A5 ("after pairing, nothing changes").

- **Where:** a small, quiet ⚙ in a corner of the display, on every screen (moment, empty, loading). It sits away from the reaction buttons and the arrows.
- **What it does:** a tap opens a small panel with **English | Français**, each named in its own language, and a close button. Nothing changes until a language is chosen, so a stray tap on the cog is harmless. The panel closes by itself after 20 seconds.
- **How:** `PATCH /api/me {language}`, then the page reloads in the new language. A display may change only its own `Device.language`, to one of `LANGUAGES`. Personal devices get 403 for now; their language setting comes with M4's settings screen. Admin still works, and applies live (`107d779`).
- **Checks:** the usual `Origin` + `X-Coucou` ones. Isolation tests: a display can't change another device, and can't set an unknown language.

**Not chosen:** a switch only on "Nothing here yet" (that screen disappears for good after the first moment); a long press (hidden); admin only (the owner wants to switch it standing at the screen).

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
  - `display.html`: the cog, its panel, and the new text
  - `display.css`: arrows, author line, summary line, the cog and its panel
  - the French

## Open for the owner

- The "New ›" hint while browsing (item 1), or an immediate jump to a new moment.
- Timing: all four items before M3's sign-off (the owner's choice so far), or items 2–4 now and the history arrows (the largest) right after the M3 device check.

## Consequences

- The display is no longer "nothing else to tap": it gains arrows and a small cog. The reaction buttons stay the main thing.
- The history view on the roadmap starts here, on displays. The sender app's history (M5) can reuse the endpoint's shape.
- More photos are cached and prefetched on the device: 10 display copies, about 5–10 MB.
- M3's outcome and "done when" in `docs/milestones/m3.md` gain these four items.
