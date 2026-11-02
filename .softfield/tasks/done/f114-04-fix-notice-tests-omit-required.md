---
id: f114-04-fix-notice-tests-omit-required
milestone: f114-i-want-to-be-notified-only
difficulty: 4
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f69-i-want-a-button-to-switch-C1035-4
tests_only: true
---

### Goal
Fix a checkpoint finding on f114-01-notices-say-what-and-where's tests: Notice tests omit required cases and do not verify the notice ID set

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f114-01-notices-say-what-and-where.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1035-4, should-fix: in `tests/factory_dashboard/test_overview.py`, line 2988.

### Finding
f69-i-want-a-button-to-switch-C1035-4: Notice tests omit required cases and do not verify the notice ID set
> The no-proposal test never creates the one-proposal case it names; there is also no test for a card without a title falling back to its key or for `short_key` converting a full milestone key. `test_data_notices_has_the_ids` only checks that returned links contain `?project=coucou`; it does not check that the notice keys exactly match the open items. Add assertions for those specified outputs and the exact expected notice IDs.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3414
gate_failures: []
tokens: 713339
```
