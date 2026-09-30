---
id: f1-04-backfill
milestone: f1
depends_on: [f1-03-runner-writes-state]
agent: lead
difficulty: 7
files:
  - runner/backfill.py
  - runner/cli.py
tests:
  - tests/runner/test_backfill.py
  - tests/runner/test_cli.py
---

### Goal
`uv run runner backfill` loads M1–M4 into the metrics database from what's left of their logs, and says what it couldn't recover.

### Context
Read `docs/milestones/f1.md` (D2, D6) and `docs/adr/13-factory-dashboard.md` (the table of sources). Reuse the runner's writers from f1-02/f1-03 and these readers: `runner/local_model.py` (`parse_events`, `stream_facts`), `runner/milestone.py` (`all_footers`, `footer_tokens`), `runner/review.py` (`parse_review`), `runner/usage.py` (`claude_tokens`), and `runner/gitops.py` (trailers, numstat).
- Sources: `var/runs/<run>/` (OpenCode logs, gates files, `claude-*.log`, `review-*.json`, `var/runs/state.json`), task footers in `tasks/*/`, `docs/milestones/*.md`, `docs/reviews/*.md`, and git (`Agent:`/`Task:` trailers, numstat).
- Jobs whose role or agent the logs don't say get `backfill-unknown` (D6). M1–M2 attempts may only exist as footers; record the ticket-level facts and list the gap.
- Idempotent by D2's natural keys. The command prints a table of what it wrote per milestone, then the gaps.
- **Tests build a small fake `var/runs` and repo in `tmp_path`;** they never read the real ones. Test the parsers on real-shaped fixtures (a two-line OpenCode log, a gates file, a review JSON).

### Done when
- a fake M4-shaped run gives its runs, tickets, jobs (tokens, steps, peak context, gates), findings and merges
- running it twice gives identical row counts
- a missing or malformed file is listed as a gap, not an error
- `uv run runner backfill --db <path>` writes to that path (the default comes from the config)
- `uv run runner check-all --task f1-04-backfill` passes
