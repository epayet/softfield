---
id: f4-25-fix-cached-tokens-are-hidden
milestone: f4-always-on
difficulty: 2
depends_on: []
files:
- coucou/factory_dashboard/templates/_partials/running.html
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C231-1
---

### Goal
Fix a checkpoint finding on f4-06-running-tokens: Cached tokens are hidden when uncached input is NULL

### Context
A should-fix finding (f4-always-on-C231-1) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-06-running-tokens.md`: in `coucou/factory_dashboard/templates/_partials/running.html`, line 23. What it found is under Finding.

### Finding
> The fallback checks only whether tokens_in is present. If tokens_in is NULL but tokens_cached has a value, the page says “no tokens reported yet” instead of showing the cached count. The ticket specifies that NULL counts as zero and the fallback applies only when both counts are NULL.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
