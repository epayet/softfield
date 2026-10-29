---
id: f163-01-second-request-in-briefs
milestone: f163-give-developers-a-browser-level-check
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/prompts.py
  - docs/task-writing.md
tests:
  - tests/runner/test_prompts.py
---

### Goal
The checkpoint and the lead's tickets ask about the second request to an htmx part, not only the first.

### Context
Read `.factory/cards/f163-give-developers-a-browser-level-check.md` ("What we know" and D5), then `CHECKPOINT` in `runner/prompts.py` and the htmx line under "Before committing a spec" in `docs/task-writing.md` (it starts "Before a ticket swaps an element away"), which the new line sits beside.
- The checkpoint's new line, after "does the screen show what the ticket asks": for each `hx-target`/`hx-swap` a diff adds, read what its view answers. With `outerHTML` the answer's outer element carries the target's id, and the part gets the same context as when the page draws it. Look for a test that makes the request twice (undo two chips, retry then reply); a part with none is a finding.
- The ticket-writing line: a ticket that adds or changes a request htmx swaps names the second request in its Done when (the second Undo, a reply after Try again), and, in a project with a browser test for its parts, asks for one that does it. Travel companion's reviews (M1, F1, F3, F4, F6) are the evidence: one clause, not the list.
- `CHECKPOINT_SHADOW` and `CHECKPOINT_STAND_IN` stay as they are.

### Done when
- `prompts.CHECKPOINT` holds the second-request line once, and the other checkpoint prompts are unchanged
- `docs/task-writing.md` holds the new line beside the "swaps an element away" one
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
