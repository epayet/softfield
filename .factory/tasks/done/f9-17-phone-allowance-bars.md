---
id: f9-17-phone-allowance-bars
milestone: f9-line-polish
depends_on: []
difficulty: 3
priority: 2
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On a phone, the allowance panel shows the same bars as on a desktop again: one line per window, coloured green, yellow or red. The dials go.

### Context
Read the `#allowance` section of `factory_dashboard/templates/overview.html` (each row has a `.dial` svg and a `.meter` bar), its rules in `factory_dashboard/static/dashboard.css` (the "Mobile: allowance dials in one row (f3-25)" block, `.meter`, `.swatch`), and in `tests/factory_dashboard/test_overview.py` `test_allowance_dials_share_one_row_at_phone`, `test_allowance_bars_drawn_at_desktop` and `test_dial_fill_class_follows_bar_rule`.
- The owner (2026-10-06): "on mobile I prefer the lines as before, with green to red". This replaces f3-25's dials. The old f9-17 (fixing the dials' colours) is dropped with them.
- The bar's colour rule stays as it is: green under the mark, yellow past the mark, red above 95%.
- The "How to read the allowance" legend speaks of the ring's tick. It should describe the bar's mark instead.
- f9-16 removes the Ollama row and f8-06 adds switches to this panel. Leave both alone.

### Done when
- at 390 px each window is one row with its name, its bar and its reset text, and no `.dial` is in the page
- at 390 px a window under its mark, one past it and one above 95% have three different bar colours, each the same as that window's bar at 1440 px
- the legend names the bar's mark, not a ring
- the dial tests are replaced by these. The layout check passes at 390 px.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: protected-paths)
attempts: 3
tokens: 3998609
logs: var/runs/20261008-204153/f9-17-phone-allowance-bars
```

```yaml
# --- runner ---
result: done
agent: lead
note: the developer's attempt 3, merged by the lead in a terminal session (owner, 2026-10-08). Its gates had failed only on protected-paths: the lead's own commits had landed on its branch by mistake (lead.md, "Your own work").
```
