---
id: f1-28-bench-page
milestone: f1
depends_on: [f1-27-bench]
difficulty: 3
files:
  - factory_dashboard/bench.py
  - factory_dashboard/templates/bench.html
  - factory_dashboard/app.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_bench.py
---

### Goal
`/bench` shows each replayed ticket against each agent that tried it.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`. `write_fixture`'s numbers are pinned by `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py`: put the rows your page needs in a function of your own (as `write_live` is), not among f1's or m4's tickets and jobs.
- Bench jobs have role `bench`. A grid: a row per ticket (with its difficulty, linking to `/tickets/{id}`), a column per agent; each cell shows the result (passed at attempt N, "would escalate", or refused), minutes and tokens, and links to the last bench job.
- With no bench jobs, an empty state explains the command: `uv run runner bench <ticket…> --agents <id…>`.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- two tickets benched by two agents give a 2×2 grid with each result
- a pair never benched shows an empty cell
- with no bench jobs, the empty state shows the command
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 297
gate_failures: []
tokens: 8930
```
