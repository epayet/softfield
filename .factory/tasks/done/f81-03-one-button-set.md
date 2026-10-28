---
id: f81-03-one-button-set
milestone: f81-assess-the-current-ui-state-of
agent: developer
difficulty: 3
depends_on: [f81-01-plate-panels]
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/projects.html
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_app.py
---

### Goal
Every button on the factory's pages is one of two: Go, a hazard-yellow plate with a cut corner, or Plain, outlined; the Planning room's buttons stop carrying their own inline styles.

### Context
Build the buttons of the Proposed side of `.factory/cards/f81-mockup/theme-pass.html` (`.btn`, `.btn.go`, `.btn.plain`); card doc `.factory/cards/f81-assess-the-current-ui-state-of.md` D5.
- Add `.btn`, `.btn.go` and `.btn.plain` to `factory_dashboard/static/dashboard.css`; the cut corner is `clip-path: var(--notch)` (the token f81-01 added). At least 44 px high. Add `.btn.go:disabled` (muted, transparent, dashed rule border) for the Approve plan button that waits on an ADR.
- The buttons to change, all with an inline `style=` today (some span 2–3 lines, the `style=` on the last):
  - `planning.html`: `#plant-only` (go), `#plant-ask` (plain), `save-…` (go), `cancel-…` (plain), the `again-…` link and the `again-…` button (go), `dismiss-…` (plain), `try-again-…` (go), `set-aside-…` (plain).
  - `thread.html`: Sign off (go), `edit-…` (go), `save-…` (go), `cancel-…` (plain), Send (go), Remove (go), Archive/Unarchive (plain).
  - `proposal.html`: `.change-btn` Comment… (plain; keep its class too), and `#send-back`, `#accept-adr`, `#approve-plan`, `#approve-merge`, `#plant` (go), which share the `{% set button = … %}` string: drop that string. `#reject-button` is plain. These sit full width in `.action-buttons`: give that width in the CSS, not inline.
  - Plain `<a>` links (cards, merged-into, the back link) are not buttons: leave them.
- Keep each button's id, `hx-*`, `onclick`, `hidden`, `disabled` and words.
- The existing go-buttons become `.btn.go` too: `.aside .go` (`ticket.html`), `.order-bar .go` (`board.html`; `factory_dashboard/static/board.js` reads only its id or class `go`: keep `go`), `.projects-page .send-order` (`projects.html`; its script reads `.send-order`: keep that class).
- No existing test reads a button's inline style: the new tests are your own. Put them at the end of the files, don't read the whole files:
  - `tests/factory_dashboard/test_app.py`: after the "plate panels (f81-01)" section, a "one button set (f81-03)" section that reads `dashboard.css` the same way (`.btn.go` has `clip-path: var(--notch)`, `.btn` a 44 px min-height).
  - `tests/factory_dashboard/test_planning.py`: render `/planning` with the `planning` and `serve` fixtures (as `test_each_group_shows_its_items_in_order` does) and check `#plant-only` carries `btn go`, `#plant-ask` `btn plain`, and no `<button` tag in the page has `style=`.

### Done when
- no `<button>` in the three planning templates has a `style=`
- the go-buttons on the ticket, board and projects pages have the cut corner
- every button keeps its id, request and words
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 7011
gate_failures: ['stopped', 'stopped']
tokens: 5276416
```
