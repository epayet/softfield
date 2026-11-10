---
id: f211-01-merge-only-what-plan-covers
milestone: f211-a-plan-must-not-get-lost
agent: lead
difficulty: 4
depends_on: []
files:
  - runner/prompts.py
  - runner/planner.py
  - runner/requests.py
  - runner/loop.py
  - runner/instructions/lead.md
tests:
  - tests/runner/test_prompts.py
  - tests/runner/test_requests.py
---

### Goal
Two open discussions merge; a new idea joins a card with an approved plan only when that plan covers it; and a thread the owner closed is neither merged with nor brought up again.

### Context
Read `.softfield/cards/f211-a-plan-must-not-get-lost.md`: "What happened" says why, D1, D2 and D11 are what this ticket builds.
- `runner/prompts.py`: `PLANNER` and `PLANNER_GENERAL` both hold the repeat paragraph, with "Keep the more advanced card (ready over planning over idea), else the older one". That sentence is what sent F176 into F51.
- `tests/runner/test_prompts.py`: `test_both_planner_prompts_look_for_duplicates_and_propose_a_merge` is the test to extend.
- `runner/planner.py`: `prompt` gets every thread as one flat list. `runner/loop.py` calls it, with `metrics.thread_cards`.
- `runner/requests.py`: `auto_merge` applies a reply's merge, and returns why not when the merge must wait for the owner (see its plan-branch check). `BY_YOU` is the reason a thread the owner closed carries, in `archived_why`; `metrics.find_thread` reads it.
- `runner/instructions/lead.md`, section "Planning room": one bullet in its style, dated, pointing at the prompt; the prompt keeps the rule.

### Done when
- both prompts say two open discussions with no approved plan keep the more advanced card, else the older, as today
- both prompts say a card with an approved plan (ready, building or past) keeps a merge only when that plan covers the idea, and that the merge's key points then name the tickets that cover it; otherwise there is no merge, the idea stays its own card, and a point says which card it sits beside
- both prompts name the threads the owner closed apart from the others, and say the lead doesn't merge with them, or bring their plans up or reuse their drafts, unless the owner asks
- `PLANNER` says that on a card whose doc says done the lead draws no plan, replan, ADR or mock-up, and answers with the words ready to plant
- `auto_merge` with either card's thread archived as `BY_YOU` changes nothing and returns why, so the merge waits for the owner; a kept thread archived as `approved` still merges
- `runner/instructions/lead.md` has the bullet
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
