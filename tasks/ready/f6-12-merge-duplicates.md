---
id: f6-12-merge-duplicates
milestone: f6-planning-room
depends_on: [f6-08-proposal-review]
agent: lead
difficulty: 6
files:
  - runner/planner.py
  - runner/prompts.py
  - runner/requests.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_prompts.py
  - tests/runner/test_requests.py
---

### Goal
When the owner plants an idea or writes on a thread that repeats another card or thread, the lead notices and proposes to merge them. Once the owner approves, the duplicate is closed with a pointer and the conversation goes on in one place.

### Context
Read `runner/planner.py` (`PROPOSAL_KINDS`, `parse_reply`, `seed_card`, `next_key`), `PLANNER` and `PLANNER_GENERAL` in `runner/prompts.py`, the `approve_plan` and `plant` handling in `runner/requests.py` (`_plant`, `_seed`), and F6's Decisions D1, D2 and D4 in `docs/milestones/f6-planning-room.md`.
- The owner (2026-10-06): "whenever I plant an idea, or whenever relevant, the lead should detect it, suggest closing one of the duplicates and continue the conversation on only one of them, with my approval".
- **The planner looks:** both prompts tell it to check the cards in `docs/milestones/` (state idea, planning or ready) and the other threads before answering, and, when one repeats another, to say so as a point and propose a merge.
- **The proposal:** a new kind `merge` with `path` the duplicate card's doc and a field `into`, the card it joins (short key). Its key points say what moves where. Decide the exact shape and add it to D2.
- **On approval** (the same `approve_plan` request; `send_back` works as for any proposal): the duplicate's notes are appended to the kept card's doc under "Notes" with where they came from, and the duplicate's doc is removed (`git rm`, in the runner's commit). Its thread gets a lead message pointing to the kept card's thread, and the owner item for it is resolved. One commit, like `_plant`'s.
- A planted idea whose title is already a card is refused today (`card_named`). Keep that: the merge covers ideas that are the same with other words.
- `/planning` shows a merge proposal like the others; its words say "merge F12 into F10". f6-08 built the proposal page.
- Record the shape in F6's D2 and the approval in D4.

### Done when
- `parse_reply` takes a `merge` proposal with `into`, and refuses one without it or with an unknown card
- both prompts ask the planner to look for duplicates among cards and threads, and to propose a merge with the owner's approval
- approving a merge moves the duplicate's notes into the kept card, removes its doc, posts the pointer on its thread and resolves its item, in one commit; nothing changes before approval
- `send_back` on a merge works as on any proposal
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
