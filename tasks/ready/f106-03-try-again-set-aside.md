---
id: f106-03-try-again-set-aside
milestone: f106-where-do-blocked-tickets-go-for
difficulty: 5
depends_on: [f106-01-blocked-reaches-the-owner, f106-02-blocked-on-the-desk]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
Each blocked ticket on the desk has two buttons, "Try again" and "Set aside", and shows as on its way as soon as one is pressed.

### Context
Read lines 79–114 of `factory_dashboard/templates/planning.html` (the desk's groups; the "refused" branch and its Dismiss button are the example to follow), and `_acted_on` and `waiting_for_you` in `factory_dashboard/planning.py`. Tests to follow in `tests/factory_dashboard/test_planning.py`: `test_a_dismissed_or_dismissing_request_leaves_the_desk` and `test_a_sign_off_on_its_way_shows_on_the_desk`.
- D3 (`docs/milestones/f106-where-do-blocked-tickets-go-for.md`): in the group whose key is "blocked", an item keeps its link to the ticket's page and gets two buttons under it. "Try again" posts a request of kind "queue", "Set aside" one of kind "set_aside"; the subject of both is the ticket's id (the item's title). They post to "/requests" the way Dismiss does.
- On its way: an item whose ticket has an open request (`owner_requests`, `done IS NULL`) of kind "queue" or "set_aside" with that subject has `on_its_way` true, its words "Trying again at the runner's next pick" or "Set aside at the runner's next pick", and no buttons. `_acted_on` does this for archive, sign-off and remove seed: extend it, and pass the blocked items through it in `desk`.
- Pressing a button marks the item on its way at once, before the answer comes, as the proposal page's buttons do with "hx-on::before-request".
- **Buttons are at least 44px high, as the others on this page, and the page must still pass its layout test at phone size.**

### Done when
- a blocked ticket on `/planning` has a "Try again" and a "Set aside" button; clicking each (as a person would) writes one request with its kind and that ticket's id as subject, asserted for the second of two tickets so no button carries another's id
- with an open "queue" request for the ticket: its item is dashed, says "Trying again at the runner's next pick", has no button, and no longer counts in the desk heading; with "set_aside", the same with its own words
- the other blocked ticket keeps its buttons
- the desk page still lays out at phone and display sizes with a blocked ticket on it
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
