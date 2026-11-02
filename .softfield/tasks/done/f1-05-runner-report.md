---
id: f1-05-runner-report
milestone: f1
depends_on: [f1-04-backfill]
agent: lead
difficulty: 6
files:
  - factory_dashboard/__init__.py
  - factory_dashboard/queries.py
  - tests/factory_dashboard/conftest.py
  - runner/cli.py
  - runner/gates.py
  - runner/checks.py
  - pyproject.toml
  - docs/agents/lead.md
  - runner/prompts.py
  - workflow/protected-paths.txt
tests:
  - tests/factory_dashboard/test_queries.py
  - tests/runner/test_report.py
  - tests/runner/test_gates.py
---

### Goal
`factory_dashboard/queries.py` holds the numbers a milestone review needs, and `uv run runner report <key>` writes them into the review.

### Context
Read `docs/milestones/f1.md` (D1, D2, D7, D8) and `docs/adr/14-developers-and-agents.md` item 16. Test-first against a fixture database that `tests/factory_dashboard/conftest.py` writes with `runner/metrics.py`; the pages reuse that fixture.
- **Plumbing:** the `factory_dashboard` package (in hatch's `packages` in `pyproject.toml`); `tests/factory_dashboard` ↔ `factory_dashboard` in the layout gate (`runner/gates.py`) and in `check-all`'s `TEST_DIRS` (`runner/checks.py`); `tests/runner/test_report.py` added to `workflow/protected-paths.txt`.
- **`factory_dashboard/queries.py`:** plain functions over a read-only connection that return data, not text: per milestone, tickets merged, first-attempt pass rate, attempts, escalations, directions, checkpoints, review rounds, findings by severity, local and Claude tokens and dollars, and D7's savings (doing it itself vs supporting, net), overall and per agent; trends across milestones.
- **`runner report <key>`** renders them as Markdown between `<!-- runner report -->` and `<!-- /runner report -->` in `docs/reviews/<key>.md`, replacing what's between the markers (a frozen snapshot: the database isn't in git).
- **lead.md:** "Sign-off sheet" gains "6. What next" (product and factory suggestions), and it and "Reporting" say the numbers come from `runner report`; the REVIEW prompt in `runner/prompts.py` asks for "What next" too.
- The dashboard's pages (f1-06 on) will reuse these functions, so name them for what they return (`milestone_results`, `savings`, `trends`).

### Done when
- on a fixture of 3 tickets (one first-attempt pass, one escalated then merged, one lead ticket), the results give the pass rate, attempts, escalations and dollars you'd count by hand
- savings follow D7: seed rate from M4's L0–L3 when no lead ticket of that difficulty exists
- `runner report f1` replaces only the text between the markers, and adds them at the end when missing
- a test file in `tests/factory_dashboard/` with no matching module fails the layout gate
- `uv run runner check-all --task f1-05-runner-report` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
