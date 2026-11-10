---
id: f65-06-comment-dashes-sign-off
milestone: f65-what-happens-if-i-comment-on
difficulty: 3
depends_on: []
files:
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A card waiting for sign-off is one row on the desk, in To sign off: dashed and "being revised" while the owner's comment waits for the lead, and saying when the lead replied once it has.

### Context
Read D8 in `.softfield/cards/f65-what-happens-if-i-comment-on.md` and the picture to build, `.softfield/cards/f65-mockup/comment-dashes.html` (Proposed). Then `desk`, `_ripe`, `_answers_wanted`, `_revising` and `_replies` in `factory_dashboard/planning.py`, `_acted_on` and `DeskItem` in `factory_dashboard/coming.py`, the desk rows in `factory_dashboard/templates/planning.html` (they already draw a dashed row, its Writing now and its place in line, in any group), and `_revising` and `test_proposals_wait_for_the_lead_while_the_owners_message_does` in `tests/factory_dashboard/test_planning.py`, the example to follow.
- Do it in `desk`, before `_acted_on`: for each `_ripe` item, look in the `_answers_wanted` items for the same `link`. No such item: the row is as today. Found: that answers item leaves its group, and the ripe row takes over from it.
- The answers item is on its way (the lead owes a reply): the ripe row gets `on_its_way=True`, its `place`, and the words `_revising` gives for the card.
- The answers item isn't (the lead has replied): the ripe row stays solid, with the words "<the answers item's words> · reviewed, waits for your sign-off".
- `_acted_on` runs after, so a Sign off on its way still wins the row's words.
- No new CSS and no template change.

### Done when
- a ripe card with a waiting `plan_message`, and with the message stored and a planner job open: one row, in To sign off, dashed, "being revised · …", not counted in the group's number or the desk's
- the reply being written: that row shows Writing now
- the lead has replied: one solid row in To sign off, "the lead replied … ago · reviewed, waits for your sign-off", counted once
- a ripe card with no thread waiting or replied: "reviewed · waits for your sign-off", as today
- a card not ripe keeps its row in Your answers wanted
- a Sign off on its way on a row being revised says "signing off at the runner's next pick"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
