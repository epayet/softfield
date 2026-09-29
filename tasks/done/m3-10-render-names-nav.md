---
id: m3-10-render-names-nav
milestone: 3
depends_on: []
files:
  - coucou/static/coucou/js/render.js
tests:
  - tests/browser/test_render.py
max_diff: 120
---

### Goal
`render.js` shows who posted a moment and when, who reacted, names on the floating emoji, and the arrows, "New" hint and settings panel (ADR 09).

### Context
`coucou/static/coucou/js/render.js` draws the display page (`coucou/templates/coucou/display.html`). It has four stubs at the end that throw; read their comments. It never touches the network and has no text of its own.

A moment is now `{id, note, photo, at, by}`: `by` is the author's name, or `""`. A reaction is `{id, emoji, by, at, target}`, and `snapshot.reactions` is newest first.

The page elements you fill (all exist already):
- `#moment-byline` > `#moment-author`, `#moment-sep` (" · "), `#moment-when`
- `#reaction-summary`
- `#nav-older`, `#nav-newer`, `#new-hint`, `#settings`, `#settings-open` (its `aria-expanded`)

`momentWhen(at, now, language)`, with `TIME = { hour: "numeric", minute: "2-digit" }`:
- same calendar day as `now` → `new Intl.DateTimeFormat(language, TIME)`
- the day before → `new Intl.RelativeTimeFormat(language, { numeric: "auto" }).format(-1, "day")`, a space, then that time ("yesterday 9:30 AM", "hier 09:30")
- 2 to 6 days before → `Intl.DateTimeFormat` with `{ weekday: "long", ...TIME }`
- older → `{ day: "numeric", month: "long" }`, plus `year: "numeric"` when the year differs from `now`'s

### Pattern to follow
The existing `render()` and `floatReaction()` in the same file.

### Steps
1. Write the four stubs as their comments say. `reactionSummary` keeps the first `{emoji, by}` of each `by` + `emoji` pair.
2. `render(root, snapshot, { onReact, enterMs = 600, now = new Date(), language = document.documentElement.lang })`: `now` may be a Date or an ISO string, so use `new Date(now)`. With a moment, show `#moment-byline`: `#moment-author` = `moment.by`, and hide `#moment-author` and `#moment-sep` when `by` is empty; `#moment-when` = `momentWhen(moment.at, new Date(now), language)`. `#reaction-summary` = `reactionSummary(snapshot.reactions ?? [])` as `"❤️ Maman · 😂 Kitchen"` (each entry `` `${emoji} ${by}`.trim() ``, joined by `" · "`), hidden when empty.
3. `floatReaction(root, emoji, { by = "", durationMs = 2500 } = {})`: inside `.float`, a `<span class="float-emoji">` with the emoji, then a `<span class="float-by">` with the name only when `by` isn't empty.
4. `setNavigation` sets `hidden` on `#nav-older` (`!older`), `#nav-newer` (`!newer`), `#new-hint` (`!fresh`). `setSettings` sets `#settings` hidden to `!open` and `#settings-open`'s `aria-expanded` to `String(open)`.
5. **Names and notes are other people's text: set them with `textContent`, never `innerHTML`.**

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 235
gate_failures: []
tokens: 232749
```
