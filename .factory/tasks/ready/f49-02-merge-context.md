---
id: f49-02-merge-context
milestone: f49-don-t-ask-me-to-merge
difficulty: 6
depends_on: [f49-01-auto-merge]
agent: lead
files:
  - runner/planner.py
  - runner/requests.py
  - runner/loop.py
  - runner/prompts.py
  - runner/metrics.py
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
  - tests/runner/test_loop.py
---

### Goal
A merge keeps the context of both threads: the lead's summary on the kept card, the duplicate's thread exported, and its history read by the kept thread's next job.

### Context
Read `.factory/cards/f49-don-t-ask-me-to-merge.md` D3 and D4. In `runner/planner.py`: `_proposal`, `merged_card`, `card_notes`, `history` and `export`. In `runner/requests.py`: `_merge`, `_merged` and `_export`. In `runner/loop.py`: `run_planner` (its `earlier`). In `runner/metrics.py`: `find_thread`, `planner_messages`, `add_planner_message`.
- A `merge` takes an optional `summary` (text); `_proposal` refuses one that isn't text. The prompts ask for it.
- `merged_card`'s block: the duplicate's notes verbatim, then "What was said on F44's thread:" and the summary, when there is one.
- `_merge` exports the duplicate's thread to .factory/planning/ under its full key, in the merge's commit, when it has one.
- `_merged` adds the kept thread's lead line, "Merged F44 here: <summary>" (its title when there is no summary), beside the duplicate's pointer line.
- The kept thread's next planner job gets the duplicate's `history` once, under "From F44's thread, merged here:", whether or not it resumes a session; store which merges it has read (a column on `planner_threads`, with its migration).
- **Protected work: test-first.**

### Done when
- merging F48 into F46 with a summary gives F46's doc F48's notes as they were, then the summary under its heading
- .factory/planning/ has F48's file, holding F48's thread, in the same commit; a duplicate with no thread exports nothing
- F46's thread has the line "Merged F48 here: …"
- F46's next planner prompt holds F48's history once, also on a resumed session; the one after doesn't
- a `summary` that isn't text makes the reply's block unread, with the note saying why
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
