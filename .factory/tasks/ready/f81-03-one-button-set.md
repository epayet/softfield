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
- Add `.btn`, `.btn.go` and `.btn.plain` to `factory_dashboard/static/dashboard.css`; the cut corner is `clip-path: var(--notch)` (the token f81-01 added). At least 44 px high.
- In `factory_dashboard/templates/planning.html`, `thread.html` and `proposal.html`, every `<button>` and button-like `<a>` with an inline `style=` becomes `class="btn go"` (the hazard-filled ones) or `class="btn plain"` (the outlined ones), keeping its id, `hx-*`, `onclick` and words.
- The existing go-buttons become `.btn.go` too: `.aside .go` (`ticket.html`), `.order-bar .go` (`board.html`; `factory_dashboard/static/board.js` reads only its id or class `go`: keep `go`), `.projects-page .send-order` (`projects.html`).
- Tests in `tests/factory_dashboard/test_planning.py` that read a button's inline style read its class instead.

### Done when
- no `<button>` in the three planning templates has a `style=`
- the go-buttons on the ticket, board and projects pages have the cut corner
- every button keeps its id, request and words
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
