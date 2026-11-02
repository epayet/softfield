---
id: f1-23-findings-json
milestone: f1
depends_on: [f1-20-agents-config, f1-41-scores-and-project-crumb-fix]
agent: lead
difficulty: 6
files:
  - runner/prompts.py
  - runner/review.py
  - runner/loop.py
  - runner/milestone.py
  - runner/owner.py
  - runner/cli.py
tests:
  - tests/runner/test_review.py
  - tests/runner/test_loop.py
  - tests/runner/test_owner.py
---

### Goal
Checkpoints and reviews report findings as JSON, directions and escalations leave a process note, and the final review judges the checkpoint findings and scores the milestone.

### Context
Read `docs/adr/14-developers-and-agents.md` items 13–14 and `runner/review.py`. Test-first.
- **Checkpoint:** besides its note, it writes `checkpoint-<n>.json`: `{"findings": [{severity, file, line, summary, detail, route, ticket}]}`; the runner stores them as findings on the checkpoint job.
- **Review:** the review JSON gains `file`, `line`, `detail` and `ticket` per finding; the last round adds `"checkpoint_verdicts": {"<finding key>": "confirmed" | "rejected" | "missed"}` and `"score": 1-10`, stored in `findings.verdict` and `milestones.review_score`. A missed finding is one the review found that a checkpoint should have caught.
- **Process notes:** directions and escalations write `{logs}/note.md` (2–4 lines: did the developer follow the ticket, run its checks, go round in circles), stored in `jobs.note`. Descriptive, never scored.
- **`runner signoff <key> --score N`** (1–10, optional) stores `milestones.owner_score`.
- Old review JSON without the new keys still parses.

### Done when
- a checkpoint's JSON becomes finding rows on its job; a malformed one is noted, not fatal
- the final round's verdicts and score land on the findings and the milestone
- a direction's note lands on its job
- `signoff f1 --score 7` stores 7; `--score 11` is refused; no `--score` leaves it empty
- `uv run runner check-all --task f1-23-findings-json` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
