---
id: f216-02-findings-costs-and-markdown
milestone: f216-let-s-redesign-the-milestone-review
difficulty: 4
depends_on: [f164-03-idea-plates-with-plant]
files:
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The card's page has what its redesign needs: the card's findings with what happened to each, its dollars by job role, and a `_to_html` that renders numbered lists, nested bullets, inline code and links.

### Context
Read `.softfield/cards/f216-let-s-redesign-the-milestone-review.md` (D10, D11, D12). Nothing in a template changes here: f216-03 draws them.
- `MilestoneDetail` and `get_milestone_detail` in `factory_dashboard/milestones.py` gain two fields, filled by two small functions beside it:
  - `caught: list[CaughtRow]`, with `severity`, `summary` and `outcome`, the words D11 gives. Severity order is blocking, should-fix, nit, then key.
  - `spend: list[SpendRow]`, with `label`, `usd` and `share` (0 to 1 of the largest row). One row per role with dollars, largest first. Labels: review "The review", escalation "The lead finishing a developer's ticket", planner "Planning", lead-ticket "The lead's tickets", direction "Directions for developers", checkpoint "Checkpoints"; any other role keeps its name. A developer role with jobs and no dollars is "Developers, on your GPU" at $0.
- `_to_html` in the same file, per D12. It escapes first, as it does now. F164's handling of quoted lines stays as it is.
- The tests in `tests/factory_dashboard/test_milestones.py` show how a milestone's rows are set up.

### Done when
- a card's `caught` lists its findings with "fixed", "left", "ticket" or "for you" as D11 says, blocking first
- a card's `spend` gives its dollars by role with D10's plain labels, largest first, and its `share` values are to scale
- `_to_html` renders `1. x` lines as `<ol>`, an indented `- x` under a bullet as a nested `<ul>`, `**x**` in a paragraph as `<strong>`, `` `x` `` as `<code>`
- `[text](https://x)` becomes a link, `[text](../sessions/x.md)` becomes the text alone, and `[text](javascript:x)` becomes the text alone
- `<script>` in the sheet's text still comes out escaped, inside `code` too
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
