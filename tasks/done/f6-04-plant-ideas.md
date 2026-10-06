---
id: f6-04-plant-ideas
milestone: f6-planning-room
depends_on: [f6-01-planner-threads]
agent: lead
difficulty: 4
files:
  - runner/planner.py
  - runner/requests.py
tests:
  - tests/runner/test_planner.py
---

### Goal
"Plant it" turns the owner's title and thoughts into a seed card at the runner's next pick, without Claude; the general thread can plant one too.

### Context
Read `docs/adr/20-planning-room.md` item 8, D5 in `docs/milestones/f6-planning-room.md`, `runner/milestone.py` (`card`, F5) and `runner/requests.py`. Test-first.
- **A request `plant`:** title, thoughts, and area if given.
  - The runner writes `docs/milestones/<key>.md`: the next free key in the area's series, a slug from the title, and **State:** idea with **Priority:** 100. The owner's words go under "Notes", and the runner commits it.
  - No Claude and no window: it runs even at a limit.
- A planner reply in the general thread may propose a seed (a proposal of kind `seed`). Approving it plants it the same way.

### Done when
- a `plant` request makes `docs/milestones/f7-<slug>.md` (if F6 is the highest factory key) with the owner's words, and the board sees an idea card
- it works while Claude is parked at a limit
- `uv run runner check-all --task f6-04-plant-ideas` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
