---
id: f41-01-points-carry-all
milestone: f41-i-find-that-on-conversations-there
difficulty: 2
depends_on: []
agent: lead
files:
- runner/prompts.py
- tests/runner/test_planner.py
tests:
- tests/runner/test_planner.py
---

### Goal
The planner's prompt asks for everything in the `json` block's points, and for at most two short lines of free text.

### Context
Read `_PLANNER_HEAD` and `_PLANNER_TAIL` in `runner/prompts.py`, and `prompt` in `runner/planner.py`.
- Today the head asks for "numbered points" in the reply and the tail asks for them again in the `json` block, so the lead writes them twice and the two drift (f41, "Why the text and the boxes differ").
- The pause suggestion in `PLANNER` ("say so in a point") already fits; keep it.
- Worked example for the tests: `test_a_cards_prompt_says_what_a_replan_may_change_and_when_to_suggest_a_pause` in `tests/runner/test_planner.py`.

### Done when
- the prompt, for a card and for the general thread, says the text before the `json` block is at most two short lines, or nothing, and that every answer, risk, question and ask is a point in the block
- the prompt says no point reports that nothing was found (no repeat, no conflict); the repeat check still asks for a point and a `merge` when there is one
- the "numbered points" line no longer asks for the points in the prose
- the listed `tests:` pass, and fail without the change
- all gates pass
