---
id: m4-01-compose-note
milestone: 4
depends_on: []
files:
  - coucou/static/coucou/js/compose.js
  - coucou/locale/fr/LC_MESSAGES/djangojs.po
  - coucou/locale/fr/LC_MESSAGES/djangojs.mo
tests:
  - tests/browser/test_compose.py
---

### Goal
`Compose({spaces, onSend})`: write a note, pick a space, press Send.

### Context
Read `docs/agents/preact.md`, then follow the worked example `coucou/static/coucou/js/name_form.js` and its test `tests/browser/test_name_form.py`. Milestone decisions (`docs/milestones/m4.md`) D3, D6, D7 and D8 apply.
- A note is at most 280 characters, with a live counter ("120 / 280").
- The space picker shows **only when `spaces` has more than one entry**. The choice is remembered in `localStorage` under `coucou-space` (a remembered id that is no longer in `spaces` is ignored; with one space, use it).
- Send calls `onSend` with `{id: crypto.randomUUID(), type: "content.posted", space, created_at: <ISO time now>, payload: {note}}`. **No `note` key when the note is empty**, and no photo yet (m4-02 adds it).
- Nothing to send (empty note, no photo) shows a message and doesn't call `onSend`; so does a note over 280. After a send, the note is cleared.
- French tone: `"Réessayez un peu plus tard"`, never `"Veuillez réessayer"`. Use `vous`, with all the accents.

### Done when
- the picker is absent with one space and present with two; the choice survives a reload
- a note of exactly 280 characters sends; 281 doesn't, and shows the message
- an empty note shows its message; the sent event has no `note` key when the note was blank
- the counter follows the typing
- every string goes through `gettext()` and has its French in `djangojs.po`, compiled to `djangojs.mo`
- `layout_problems(page) == []` at `PHONE`
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
