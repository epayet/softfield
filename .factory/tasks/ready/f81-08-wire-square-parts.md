---
id: f81-08-wire-square-parts
milestone: f81-assess-the-current-ui-state-of
agent: developer
difficulty: 3
depends_on: [f81-03-one-button-set]
finding: f81-checkpoint-2
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/agents.html
tests:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
What f81-02 and f81-03 left unfinished on screen is finished: the idle crate shows in an empty panel, the meter's quarter ticks sit under a meter without touching the agents page's gauge, and the buttons all come from `.btn`.

### Context
Findings from the checkpoint after f81-02 and f81-03 (their tests read the CSS text, not a rendered page):
- `factory_dashboard/templates/_partials/idle_crate.svg` is included from no template, and no template or Python file prints `class="empty"` today, so `.empty svg` styles nothing. Find the panels that print an empty-state sentence (search the templates for the "nothing" / "no … yet" lines) and give them `<div class="empty">{% include "_partials/idle_crate.svg" %}<span>…words unchanged…</span></div>`.
- The new `.gauge` rule (`dashboard.css` near `.meter`) has the same name as the agents page's `.gauge` (near `.gauge .fill`, used in `agents.html`): its `background-image` quarter ticks and `margin-top` now apply to the agents gauges too. Rename the new one (for example `.meter-ticks`), make it a sibling after each `.meter` in `planning.html`, `board.html` and `factory_dashboard/templates/_partials/allowance.html`, and leave `.gauge` as it was before f81-02.
- `planning.html` still has the "Try again" `<a id="again-…">` with an inline hazard style; give it `class="btn go"` and drop the inline style. `proposal.html`'s Approve plan prints `{% if adr_waits %}Approve plan{% else %}Approve plan{% endif %}`: make it the plain word. The order bar's Cancel button in `board.html` has no `.btn plain`.
- `.order-bar .go`, `.aside .go` and `.projects-page .send-order` in `dashboard.css` still style the buttons that now also carry `.btn`: drop the part they repeat, so one rule decides each button.
- The new tests assert the CSS text (`"25%" in gauge_block`) or a class on the HTML; add a test that loads `/planning` and `/agents` and checks the rendered page: a `.meter` is followed by the ticks element, an empty panel contains `<svg`, the agents page's `.gauge` has no tick rule.

### Done when
- a page with an empty panel shows the idle crate beside the same words
- the agents page's gauges look as before f81-02; a meter has quarter ticks under it
- every `<button>` and button-like link on the Planning room and review pages is `.btn go` or `.btn plain`, with no inline style
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
