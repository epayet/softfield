---
id: f196-01-old-adr-paths
milestone: f196-f58-is-in-progress-but-has
difficulty: 3
depends_on: []
files:
  - factory_dashboard/planning.py
  - factory_dashboard/proposal.py
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_proposal.py
---

### Goal
An ADR proposal stored with its old `docs/adr/` path offers Accept ADR again when that exact file is on main, and never when only another ADR has its number.

### Context
Read `.softfield/cards/f196-f58-is-in-progress-but-has.md`: "What happens today" and D2.
- `factory_dashboard/planning.py`: `_ADR_NUMBER` reads only `.softfield/adr/<n>-…`. `_adr_waits` uses it for Approve plan's wait.
- `factory_dashboard/proposal.py`: `proposal_review` uses `_ADR_NUMBER` for `adr_number`, which `factory_dashboard/templates/proposal.html` needs to draw Accept ADR.
- Real cases, both with the number 27 in their old paths: F58's proposal names the file 27-the-lead-acts-when-asked.md, which is on main in the ADR folder. F27's names 27-planning-beside-the-line.md, which exists nowhere.
- Follow the tests around `accept-adr` in `tests/factory_dashboard/test_proposal.py`.

### Done when
- a proposal whose path is `docs/adr/<name>.md`, with `.softfield/adr/<name>.md` on main, shows Accept ADR posting its number
- a proposal whose path is `docs/adr/<name>.md`, with another ADR of that number on main and none of that name, shows no Accept ADR; Send back and Reject stay, and `_adr_waits` still says it waits
- a proposal whose path is `.softfield/adr/…` behaves as it does today, its draft on the plan branch included
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2616
gate_failures: []
tokens: 2383769
```
