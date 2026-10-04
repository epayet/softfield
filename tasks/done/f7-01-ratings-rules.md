---
id: f7-01-ratings-rules
milestone: f7-factory-fixes
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/ratings.py
  - runner/loop.py
  - runner/bench.py
tests:
  - tests/runner/test_ratings.py
  - tests/runner/test_loop.py
---

### Goal
Ratings follow [ADR 24](../../docs/adr/24-ratings-that-hold.md): one finding penalty per ticket, bench replays count as games, and an agent with fewer than 3 games routes at the floor.

### Context
Read `docs/adr/24-ratings-that-hold.md`, D1–D3 in `docs/milestones/f7-factory-fixes.md`, `runner/ratings.py` (`judged_games`, `ticket_games`, `rate`), and in `runner/loop.py` `rate_verdicts`, `rate_ticket`, `standing` and `current_ratings`. Test-first.
- Today `judged_games` adds a `FINDING` game per confirmed or missed finding: F3's and F4's reviews took Qwen from 3.2 to 1.0 in one evening (`rating_changes`, 2026-10-04 18:57).
- `rate_verdicts` skips findings already rated by their key; keep that, and add the ticket-level guard (one penalty per ticket, whatever later verdicts come).
- Bench jobs (`runner/bench.py`, role `bench`) carry their ticket and agent, and today move no rating.
- The floor applies where routing reads ratings, not to the stored rating: the Agents page keeps showing the estimate with "not rated yet".

### Done when
- a ticket merged first time with four confirmed findings moves its author by one −0.25 × K step in total, and a ticket not merged with findings moves it by none
- a bench replay that passed first time is a game for its agent; the same agent's real game on that ticket is still played once
- an agent with 2 rated games routes as 1; with 3, as its rating
- `uv run runner check-all --task f7-01-ratings-rules` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
