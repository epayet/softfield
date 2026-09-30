---
id: f1-24-ratings
milestone: f1
depends_on: [f1-17-difficulty, f1-23-findings-json]
agent: lead
difficulty: 6
files:
  - runner/ratings.py
  - runner/loop.py
  - runner/milestone.py
  - runner/cli.py
tests:
  - tests/runner/test_ratings.py
---

### Goal
`runner/ratings.py` rates each agent's coding and reviewing from 1 to 10, as plain functions, and the runner records every change.

### Context
Read `docs/adr/14-developers-and-agents.md` items 6–7 and 11. Test-first with table tests; the module does no IO (the caller passes ratings, results and history, and writes `rating_changes`).
- **Coding, Elo-style:** a ticket is a game against its difficulty (the corrected one when set). Results: 1 merged at the first attempt, 0.5 merged later, 0 escalated or blocked, −0.25 per finding the final review confirms on its code. The expected result is 0.5 at rating = difficulty and rises smoothly with the gap (a logistic; choose its scale so a 2-point gap expects about 0.75, and write it down). The change is (result − expected) × K, with a larger K for an agent's first 5 tickets. Ratings stay within 1–10.
- A ticket that passed through several agents: the attempt that merged gets the result; earlier failed attempts count as 0 for their agents.
- **Reviewing:** confirmed ÷ (confirmed + rejected + missed) over the reviewer's judged findings, scaled to 1–10; unrated until it has any.
- **Starting ratings** come from `[agents.*] rating`. `runner ratings --replay` seeds the local Qwen from M1–M4 in the database (by merge order), writing `rating_changes`.
- Wiring: after a ticket's outcome and after the review's verdicts, the runner writes the changes. Claude is rated too; routing ignores it (item 11).

### Done when
- table tests cover: an expected result (small change), beating a hard ticket (large rise), failing an easy one (large drop), a confirmed finding, the provisional K, and the 1–10 bounds
- a two-agent ticket gives the merger its result and the earlier developer a loss
- reviewing is 7 for 7 confirmed of 10 judged findings (scaled as you document)
- `runner ratings --replay` twice gives the same ratings
- `uv run runner check-all --task f1-24-ratings` passes
