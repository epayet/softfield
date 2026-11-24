---
id: f97-02-card-steps-styles-stay-in-the-strip
milestone: f97-given-that-the-planning-board-has
difficulty: 2
files:
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On a phone, the Overview no longer scrolls sideways: the card steps strip's styles apply to that strip only, and no longer to the Overview's other lists, such as While you were away and Needs you.

### Context
Read `.softfield/cards/f97-given-that-the-planning-board-has.md` (D6).
- F210's strip (`factory_dashboard/templates/_partials/card_steps.html`, `<nav id="card-steps" class="steps">`) is styled in `factory_dashboard/static/dashboard.css` by bare `.steps …` rules (the block under "F210 D3: a card's steps": `.steps`, `.steps::before`, `.steps h3`, `.steps ol`, `.steps li { display: contents; }`, `.steps a`, `.steps a small`, `.steps a.waits`, `.steps a small.not-sent`).
- Every `ul.steps` list matches those rules too. That covers While you were away (`factory_dashboard/templates/_partials/away.html`), Needs you (`factory_dashboard/templates/_partials/needs_you.html`), the Projects page and the ticket and job pages. Each row loses its grid, and each link becomes a 44 px tall, unwrapped, uppercase plate. A ticket's name, such as `f262-02-archive-on-the-projects-page`, is then wider than a 390 px screen.
- Scope that block to `#card-steps` only (for example `#card-steps`, `#card-steps ol`, `#card-steps li`, `#card-steps a`). Leave the strip's look on a thread and on a proposal's page unchanged. The older `.steps` rules near `.steps li { display: grid; … }` stay as they are.
- Phone layout checks: `layout_problems`, `PHONE` in `tests/layout.py`. The Overview's tests set the viewport as `test_allowance_bars_one_row_per_window_at_phone` does.

### Done when
- at 390 px, the Overview with While you were away listing a merged ticket named `f262-02-archive-on-the-projects-page`, and Needs you holding a desk and a `reserve` item, has no `layout_problems`, and the page's `scrollWidth` is at most 390
- in While you were away, a ticket's link is an ordinary inline link (not 44 px tall, not uppercase), and each row has its line under it again
- the card steps strip on a thread and on a proposal's page looks as before: `tests/factory_dashboard/test_thread.py` and `tests/factory_dashboard/test_proposal.py` pass unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 7430
gate_failures: ['task-tests', 'stopped']
tokens: 5132038
```
