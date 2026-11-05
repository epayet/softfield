---
id: f207-01-in-short-in-the-prompt
milestone: f207-i-want-a-tl-dr-of
difficulty: 2
depends_on: []
files:
  - runner/prompts.py
  - runner/planner.py
tests:
  - tests/runner/test_prompts.py
  - tests/runner/test_planner.py
agent: lead
---

### Goal
The lead opens every reply and every proposal with a short "In short" for the owner: the reply's text before its block, and a new `tldr` field on each proposal.

### Context
Read D1, D2 and D3 in `.softfield/cards/f207-i-want-a-tl-dr-of.md`. The rule to replace is "at most two short lines on what this reply does" in `_PLANNER_HEAD` (`runner/prompts.py`); the block's example is in `_PLANNER_TAIL`. The check to follow is how `_proposal` in `runner/planner.py` treats a merge's `summary`. `tests/runner/test_prompts.py` asserts the old words and changes with them.

### Done when
- both planner prompts ask for the text before the block as a summary of at most three short sentences, under 300 characters: what the lead found or recommends and what it needs from the owner, naming each `question` point by its number; nothing else outside the block, and none on a reply of one point
- both prompts' block example shows `"tldr"` on a proposal, and say what it holds: one or two short sentences on what approving it does and its main cost or risk; on a mock-up, what the picture shows
- `parse_reply` keeps a proposal's `tldr`; a proposal without one, or with null, reads as before; one that is neither text nor null makes the block unread, with a note naming the proposal
- a proposal listed by the runner for a mock-up nobody listed still reads, with no `tldr`
- the listed `tests:` pass, and fail without the change
