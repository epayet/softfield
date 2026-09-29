---
id: m4-04-delivery-list
milestone: 4
depends_on: []
files:
  - coucou/static/coucou/js/delivery.js
  - coucou/locale/fr/LC_MESSAGES/djangojs.po
  - coucou/locale/fr/LC_MESSAGES/djangojs.mo
tests:
  - tests/browser/test_delivery.py
---

### Goal
`Delivery({items, onRetry, onDiscard})`: shows each moment's delivery state.

### Context
Read `docs/agents/preact.md` and follow `coucou/static/coucou/js/name_form.js` with `tests/browser/test_name_form.py`. Decisions D5 and D6 in `docs/milestones/m4.md`. Each item is `{id, note, thumb, status, code, at}`, with `status` one of `waiting`, `sending`, `sent`, `refused`; `thumb` is a data URL or absent; `note` may be absent; `at` is an ISO time.
- Show the thumbnail and the note (a moment may have only one of them) and a status line: waiting ("Waiting for a connection"), sending, sent ✓, "Couldn't send".
- A `refused` item also shows a line for its `code`: `note_too_long`, `empty_moment`, `photo_format`, `photo_unreadable`, `photo_too_large`, `space_not_found`, `too_large`. **Any other code** (or none) shows a generic "couldn't send" line.
- A refused item has "Try again" (calls `onRetry(id)`) and "Remove" (calls `onDiscard(id)`). Other items have neither button.
- Order is the order given. No items: render nothing.
- Warm French with `vous`: "Réessayez un peu plus tard", never "Veuillez réessayer"; all accents.

### Done when
- one test per status shows the right line and the right buttons
- each of the seven codes shows its own line, and an unknown code shows the generic one
- Try again and Remove call the right callback with the item's id
- an item with only a photo, and one with only a note, both render
- an empty list renders nothing
- strings go through `gettext()`, with French compiled into `djangojs.mo`
- `layout_problems(page) == []` at `PHONE` with a photo item, a long (280-character) note and a refused item
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
