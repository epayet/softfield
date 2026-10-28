---
id: f68-08-a-fix-of-a-fix-goes-to-the-lead
milestone: f68-i-want-the-factory-to-be
difficulty: 3
agent: lead
depends_on: []
files:
  - runner/tasks.py
  - runner/loop.py
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_loop.py
finding: f68-i-want-the-factory-to-be-F6
---

### Goal
A checkpoint's fix ticket on a ticket that was itself a fix ticket goes to the lead, never to a developer: a third developer ticket on the same tests is caught by a check, not by a line in `docs/agents/lead.md`.

### Context
Read `fix_ticket` in `runner/loop.py` (the stand-in checkpoints' fix tickets), `preflight` in `runner/tasks.py` and its messages above it (`TESTS_ONLY`, `FEATURE_PRIORITY`), and the F114 line in `docs/agents/lead.md` §Known range ("a finding on tests that a fix ticket of the same card already rewrote is the lead's to fix").
- F68 had five developer fix tickets in a row on one regression test (f68-03 to f68-07, 2026-10-17 to 2026-10-23, about 4 hours of developer time), each closing the last checkpoint's finding and drawing the next. F114 had eight the week before. The F114 rule was written on 2026-10-23 and f68-07 was still filed that day, by a Claude checkpoint: a rule only in `docs/agents/lead.md` doesn't reach the checkpoint.
- The ticket at fault is in `.factory/tasks/done/`, and a fix ticket's Context names it ("on the merge of `.factory/tasks/done/<id>.md`"); a fix ticket carries `finding:` in its frontmatter.
- Two places: `fix_ticket` writes `agent: lead` when the ticket at fault has `finding:` set; and `preflight` reports a problem for a developer ticket with `finding:` whose ticket at fault (named in its Context) has `finding:` too, so a Claude checkpoint's own ticket is caught as well and goes to the lead before any attempt.

### Done when
- a stand-in checkpoint's fix ticket on a done ticket with `finding:` is written with `agent: lead`; one on a done ticket without `finding:` stays a developer ticket
- `preflight` reports "a fix of a fix: the lead does it" for a developer ticket with `finding:` whose Context names a done ticket with `finding:`; the same ticket with `agent: lead`, or naming a done ticket without `finding:`, reports nothing new
- the F114 line in `docs/agents/lead.md` says the check now holds it
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
