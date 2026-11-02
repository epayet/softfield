---
id: f143-05-replan-routes-planning-tickets
agent: lead
milestone: f143-split-test-planning-py-by-page
difficulty: 3
depends_on: [f143-04-coming-own-module]
files:
  - docs/agents/lead.md
  - docs/task-writing.md
  - .softfield/cards/f143-split-test-planning-py-by-page.md
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
After the split, planning-page tickets go to the local developer again when they touch one page: the routing rule says so, and the ready tickets that were the lead's only for F14's rule are re-routed.

### Context
Read D6 in `.softfield/cards/f143-split-test-planning-py-by-page.md`, F14's rule and the entries after it under "Known range" in `docs/agents/lead.md` (F14, F109, F172), and the finding rule that names `tests/factory_dashboard/test_planning.py` in `docs/task-writing.md`.
- **The rule:** rewrite F14's last sentence and F172's last two, and the line in `docs/task-writing.md`, as D6: one of D1's five modules under `factory_dashboard/`, its test file and its template go to the developer; two pages' modules, or a protected path, stay the lead's. Keep the dated stories; change only the rule they end on, with today's date.
- **The re-route:** for each ticket in `.softfield/tasks/ready/` with `agent: lead` whose `files:` and `tests:` now fit D6's developer side, read its card's doc under `.softfield/cards/`. Remove its `agent: lead` line (the developer is the default) only when nothing there or in the ticket makes it the lead's for another reason (protected, test-first, a new pattern, `difficulty` above 4). Leave the ticket in flight alone (`in_flight` in `.softfield/var/runs/state.json`).
- **The replan:** read each ticket the split touched against the moved code (Grep for any `def` named beside a path where it no longer is). Log what you changed and re-routed, one line each, under "Replan (f143-05)" in the card doc.
- This ticket edits no code: its test file is listed only for the standing gates; no test is added.

### Done when
- `docs/agents/lead.md` and `docs/task-writing.md` state D6's rule, and no longer say a ticket adding to `tests/factory_dashboard/test_planning.py` is the lead's for that alone
- every re-routed ticket is listed in the card doc with its reason, and every ticket left with the lead that fits D6 says why in the same list
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
