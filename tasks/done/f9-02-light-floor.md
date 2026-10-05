---
id: f9-02-light-floor
milestone: f9-line-polish
depends_on: []
difficulty: 2
files:
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
In light mode, the planted rows' words and the floor's yellow progress bars read clearly.

### Context
Read the light-mode tokens and the `.floor` rules in `factory_dashboard/static/dashboard.css` (`.floor .bar-bg` on `--grid`, `.floor .bar-fill` in `--warn`, `.floor text.dim` in `--muted`, `.floor .soil`), and `rows` in `factory_dashboard/static/factory.js`.
- The owner (2026-10-04): "yellow on grey is a bit meh on light mode"; "the planted rows are not super readable on light mode". In light mode the bars are hazard yellow `#f2b10a` on `--grid` `#dcdfd9`, and the rows' small words sit in `--muted` on the soil pattern.
- Change light mode only: the bars' fill gets a darker yellow or an outline, and the rows' words a stronger ink, so each passes 3:1 against what is behind it. Dark mode stays as it is.

### Done when
- a browser test in light mode: a planted row's bar fill and its words each differ from what's behind them by a contrast ratio of at least 3 (computed from the elements' computed colours)
- the same test in dark mode still passes with today's colours
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 2896
gate_failures: []
tokens: 3831491
```
