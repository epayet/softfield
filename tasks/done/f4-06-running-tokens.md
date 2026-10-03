---
id: f4-06-running-tokens
milestone: f4-always-on
depends_on: [f4-04-running-goal]
difficulty: 2
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/running.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Running now says how much a live job has read, cached input included, and counts "turns" instead of "steps".

### Context
Read `factory_dashboard/overview.py` (`Running`, `running_jobs`), the "Live" line of `factory_dashboard/templates/_partials/running.html` and its tests in `tests/factory_dashboard/test_overview.py`.
- Facts: the line reads `{{ job.tokens_in | tokens }} tokens in · {{ job.steps or 0 }} steps`. For Claude jobs `jobs.tokens_in` is only the uncached input: f2-04's attempt showed "36 tokens in · 18 steps" while it had read 970k cached tokens (`jobs.tokens_cached`). For OpenCode jobs `tokens_cached` is NULL and `tokens_in` is the whole input. A step is one model turn.
- The new line: "read N tokens · M turns", where N is `tokens_in` plus `tokens_cached` (NULL counts as 0), formatted with the same `tokens` filter. With both NULL, keep "no tokens reported yet".

### Done when
- a Claude job with 36 tokens in and 970,000 cached reads "read 970k tokens · 18 turns" (or the `tokens` filter's form of 970,036)
- an OpenCode job with no cached count reads its `tokens_in`
- a job with neither reads "no tokens reported yet"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 684
gate_failures: []
tokens: 51139
```
