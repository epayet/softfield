---
id: f122-04-replan
milestone: f122-new-project-from-the-projects-page
agent: lead
difficulty: 3
depends_on: [f122-03-adr-00-adds-the-project]
files:
  - .softfield/cards/f122-new-project-from-the-projects-page.md
  - .softfield/tasks/ready/f122-05-start-a-project-on-the-page.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
Check F122's Decisions and its waiting developer ticket against what f122-01 to f122-03 built, fix them, and log what changed (ADR 16 item 7).

### Context
Read `.softfield/cards/f122-new-project-from-the-projects-page.md` (Decisions, Tickets), the merged diffs of f122-01, f122-02 and f122-03 (`git log --grep f122-0`), and `.softfield/tasks/ready/f122-05-start-a-project-on-the-page.md`.
- What f122-05 needs to be true: the `new_project` request's kind and value shape, the plate's state for a waiting request and for a setting-up project (which owner items and proposals count as "for you"), the thread key and address of M1's page, and the root `projects_root` gives.
- Write any difference under a `## Replan` section in the card doc, and fix f122-05's Context to match. Change no code.

### Done when
- the card doc has a `## Replan` section listing each difference found, or saying none was
- f122-05's Context names only functions and paths that exist on main, and passes `softfield check-tickets`
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
