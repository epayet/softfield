---
id: f171-03-fix-tickets-named-by-their-ticket
milestone: f171-there-are-dupliacted-tickets-on-the
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A stand-in checkpoint's fix ticket is named after the ticket it fixes, not after the first four words of the finding's sentence.

### Context
Read D4 in `.factory/cards/f171-there-are-dupliacted-tickets-on-the.md`, then `fix_ticket` in `runner/loop.py` (the `words = …` line builds today's name) and the fix-ticket tests in `tests/runner/test_loop.py` (around `test_a_fix_ticket_belongs_to_the_milestone_at_fault`).
- Today's names stop mid-phrase: `f1-14-fix-the-been-test-does`, `f114-09-fix-notification-tests-do-not`.
- The new id: `<prefix>-<nn>-fix-<slug>`, where the slug is the ticket at fault's id after its `<short key>-<nn>-`, a leading `fix-` dropped, at most four words; `-tests` is added when the fix is `tests_only`. The number is found as today.
- Tickets already written keep their ids.

### Done when
- a code fix on `f3-02-agent-notes` is named `<prefix>-<nn>-fix-agent-notes`
- a test fix on `f1-11-fix-restamp-been-and-undo` is named `<prefix>-<nn>-fix-restamp-been-and-undo-tests`
- a ticket at fault with a long slug gives at most four of its words
- the finding's sentence still opens the ticket's Goal, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
