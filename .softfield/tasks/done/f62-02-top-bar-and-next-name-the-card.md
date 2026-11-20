---
id: f62-02-top-bar-and-next-name-the-card
milestone: f62-claude-opus-review-on-overview-does
difficulty: 3
depends_on: [f62-01-now-names-the-card]
finding: f62-claude-opus-review-on-overview-does-F1
files:
  - factory_dashboard/app.py
  - factory_dashboard/line.py
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The top bar and Next in line name the card a ticketless job works on, as Now already does: the top bar reads "Running: softfield · review F158" instead of "review, job 1353", and a due review in Next in line reads "review F68", the card's title and "the lead reads what it built" instead of "a batch".

### Context
- `job_card` in `factory_dashboard/overview.py` names a ticketless job's card (key, title, line) from its role, its milestone key and the milestone's title (F62 D1, D2). Call it; don't look the card up another way.
- Top bar: `factory_status` in `factory_dashboard/app.py` builds `doing` as `job.ticket or f"{job.role}, job {job.job}"`. With no ticket and a card (`job.job_card`), `doing` is `f"{job.role} {key}"`; otherwise as today. `pausing` follows `doing`, so "Pausing after review F158" comes with it.
- Next in line: the due-review rows (`"kind": "batch"`, `"title": f"review …"`) come from the function at the end of the review section of `factory_dashboard/line.py`, and `factory_dashboard/templates/_partials/queue.html` draws them with "· a batch". Add the card's title to each row (read `milestones.title` in the same query) and draw "review F68 · <title> · the lead reads what it built"; no "a batch". The key links to `/planning/<lower-case key>` with the row's `?project=`, as the planned-card rows in the same template do.
- A due checkpoint row, if any, keeps its own wording; only `role == "review"` changes.
- The tests to copy are the f62-01 ones at the end of `tests/factory_dashboard/test_overview.py` (a ticketless job built with `runner.metrics`); use a full card key like `f68-the-factory-is-softfield` in fixtures, as the live database has.

### Done when
- a running review on `f158-milestones-don-t-show-me-their`: the top bar says "Running: softfield · review F158" (and "Pausing after review F158" when a pause is asked)
- a running job with a ticket keeps "Running: … · <ticket>"; a ticketless job with no card keeps "<role>, job <n>"
- a due review on `f68-…` with a title: Next in line shows "review F68" linked to `/planning/f68`, its title and "the lead reads what it built", and not "a batch"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 11840
gate_failures: ['mypy', 'task-tests']
tokens: 11288833
```
