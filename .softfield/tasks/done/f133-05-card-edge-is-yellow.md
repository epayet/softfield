---
id: f133-05-card-edge-is-yellow
milestone: f133-each-project-has-its-own-series
difficulty: 2
depends_on: []
files:
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
finding: f133-03-F1
---

### Goal
A card on the board has the yellow edge that f133-03 promised, not a grey one.

### Context
f133-03 removed `.card.factory` and `.card.product`, which were the only rules setting `--c` on `.card`. In `factory_dashboard/static/dashboard.css` the `.card` rule and the overrides after it (`#field .card.started`, `#stage-ripe .card`, and the others near them) still read `var(--c, var(--muted))`, so every card's left edge is now the muted grey. `#card-head` already falls back to `var(--factory)`. The dashboard's `.idea.factory` / `.idea.product` rules are not part of this ticket.
Add a test that reads `factory_dashboard/static/dashboard.css` and checks that no `.card` border rule falls back to `--muted`.

### Done when
- every board card's left edge falls back to `var(--factory)`, including started, ripe and at-work cards
- a bug card's striped edge is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1630
gate_failures: []
tokens: 2031402
```
