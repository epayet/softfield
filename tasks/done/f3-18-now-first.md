---
id: f3-18-now-first
milestone: f3
depends_on: [f3-17-line-refresh-in-place]
difficulty: 3
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/line.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview opens on what is being worked on now. On desktop and on a phone, Now is at the top, the floor's legend is folded away, and the allowances sit in one compact row under Now.

### Context
Read `factory_dashboard/templates/overview.html`, `factory_dashboard/templates/_partials/line.html`, `factory_dashboard/templates/_partials/running.html` (Now) and the order tests in `tests/factory_dashboard/test_overview.py`.
- **Why (owner, 2026-10-03):**
  - "What I really want to see when I open the page is what's currently being worked on; I currently have to scroll down for that."
  - "When I open the mobile view, the first thing I see is the legend of the factory and what's in the field: not super interesting."
- **The order on `/`, top to bottom:**
  1. Needs you, only when something needs the owner, as today.
  2. Now: the `#live-now` wrapper and its `/live` refresh, unchanged.
  3. The allowance, as one compact row: each agent's window as a short meter with its label and percent. Keep the section id `allowance` and each row's id `allow-<label>-<window>`.
  4. The floor (`#line-live`) and the replay bar.
  5. What clogged the line today.
  6. Last verdict, savings and spend, as today.
- **The legend:** the `.legend` block in `factory_dashboard/templates/_partials/line.html` moves into a closed `<details>` right under the floor, with the summary "How to read the floor". Its four entries stay the same.
- The same order holds under 640 px. Use no CSS `order` tricks: the markup is in this order.

### Done when
- on `/`, `#now` comes before `#allowance`, which comes before `#line-live`; `#needs-you` comes first when present (a test reads the positions in the HTML)
- the legend is inside a `<details>` without `open`, after the floor
- the allowance rows keep their ids, and the allowance tests still pass
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 2931
gate_failures: ['task-tests']
tokens: 893468
```
