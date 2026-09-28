---
id: m3-07-render-moment
milestone: 3
depends_on: [m3-01-display-page]
files:
  - coucou/static/coucou/js/render.js
tests:
  - tests/browser/test_render.py
max_diff: 80
---

### Goal
`render.js` draws a display's snapshot on its page, shows the offline line, and floats reactions.

### Context
`coucou/static/coucou/js/render.js` has three stubs that throw. Their comments say what each one does:

```js
export function render(root, snapshot, { onReact, enterMs = 600 }) {}
export function setOffline(root, offline) {}
export function floatReaction(root, emoji, { durationMs = 2500 } = {}) {}
```

`root` is `<main id="display">` from `coucou/templates/coucou/display.html`. Inside it:
- three `<section data-state="loading|empty|moment">`
- `#moment-photo` (an `<img>`), `#moment-note` (a `<p>`) and `#reactions` (a `<div>`), all inside the `moment` section
- `#offline` and `#floats`

`snapshot` is `{ moment: {id, note, photo, at} | null, reactions: [...], reaction_set: ["❤️", …] }`. `photo` is a URL or `null`, and `note` may be `""`.

What `tests/browser/test_render.py` expects:
- **Sections:** exactly one section is visible: `moment` if there is a moment, else `empty`.
- **Photo and note:** the photo is shown with `src` only when `photo` is set. The note is shown only when it isn't empty.
- **Buttons:** `#reactions` holds one `<button type="button">` per emoji, rebuilt on every render. A click calls `onReact(emoji, moment.id)`.
- **A new moment:** when the moment id differs from the last one drawn (remember it in `root.dataset.moment`), add the class `entering` to the `moment` section and remove it after `enterMs`.
- **`setOffline`:** sets `#offline.hidden`.
- **`floatReaction`:** appends `<span class="float">emoji</span>` to `#floats` and removes it after `durationMs`.

### Pattern to follow
The `show()` function in `coucou/static/coucou/js/pairing.js`

### Steps
1. Implement the three functions in `coucou/static/coucou/js/render.js` until every test in `tests/browser/test_render.py` passes. Use `hidden`, `classList`, `replaceChildren` and `document.createElement`. No framework, no imports.
2. **Put the note in with `textContent`, never `innerHTML`: notes are written by people and must never run as code.**

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
