---
id: f51-01-desk-counts-what-waits-on-you
agent: lead
milestone: f51-when-a-plan-depends-on-an
difficulty: 4
depends_on: []
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
The owner's desk shows one item per card's open proposals (ADR, plan, replan, mock-ups, merges), counted only while a part still waits on them; and a thread the owner has answered leaves "Your answers wanted".

### Context
The picture to build: `.factory/cards/f51-mockup/desk-bundles.html` (Proposed). Read `_open_proposals`, `_answers_wanted`, `waiting_for_you`, `DeskItem` and `_adr_waits` in `factory_dashboard/planning.py`, `proposal_state` and `_about` in `runner/planner.py`, and the desk's item in `factory_dashboard/templates/planning.html`. The Planning tab's count, Overview's Needs you and F35's Previous and Next all read `waiting_for_you`, so fixing the desk fixes them.
- The owner (2026-10-08): "i can't do anything about it, so it shouldn't count as something on my desk"; F99 (2026-10-20): "it looks like I have 2 things to look into but one approval approves both".
- D1 (`.factory/cards/f51-when-a-plan-depends-on-an.md`): on a card's thread (not the general one), the open and on-its-way proposals of the latest set are one `DeskItem`:
  - title: the card's key and the plan's (or replan's) title, else the first proposal's;
  - parts: each proposal's short name ("ADR" and its number, "plan", "replan", "mock-up", "merge" and the card it merges), ADR first, each marked still to do or on its way (a new `DeskItem` field, default empty, so other groups are unchanged);
  - words: the key points' total; while the ADR is open (`_adr_waits` and its own state OPEN), add " · accept the ADR first";
  - link: the first part still to do; `on_its_way` only once every part is.
- The general thread's proposals (seeds, merges) stay one item each, as today.
- D4: `_answers_wanted` skips a thread with an open `plan_message` request (`kind = 'plan_message'`, `done IS NULL`, `subject` = the card); `coming()` already lists it.
- Parts on their way use the desk's existing dashed `--hazard` style; nothing new in `factory_dashboard/static/dashboard.css`.

### Done when
- a card with an ADR proposal (Proposed on main), a plan and a merge: one item, its parts in that order, words ending "accept the ADR first", linking to the ADR proposal's page; the Planning tab's count is 1
- the same card with an `accept_adr` request pending: still one counted item, the ADR part on its way, linking to the plan's page
- with an `approve_plan` pending as well: the item is on its way and not counted
- a card with a plan and a mock-up: one item, parts "plan" and "mock-up"; the general thread's two seeds stay two items
- a thread whose last message is the lead's, with an open `plan_message` request: not in "Your answers wanted", in Coming; the count drops by one
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
