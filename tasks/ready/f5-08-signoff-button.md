---
id: f5-08-signoff-button
milestone: f5-board
depends_on: [f5-07-replan]
difficulty: 3
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A milestone's page shows the same "Sign off" button as its planning page, when the milestone is ripe.

### Context
Read `factory_dashboard/milestones.py` (the `/milestones/{key}` route), `factory_dashboard/templates/milestone.html`, the `#review` section of `factory_dashboard/templates/thread.html` (the button as built, F50 D2 and D3), `_review` in `factory_dashboard/planning.py` (what decides it), `test_a_ripe_cards_page_shows_its_sheet_and_signs_off` and the three tests after it in `tests/factory_dashboard/test_planning.py`, and `tests/factory_dashboard/test_milestones.py`.
- **The button exists already** on a ripe card's planning page (`/planning/<short key>`). This ticket puts the same one on `/milestones/<key>`, with the same rule and the same three states. It doesn't change the planning page.
- **Ripe** (F50 D1): every ticket done, the review's sheet stored (`milestones.signoff`), and not signed off. `_review` reads it from `live_line(conn, project, now)["field"]["ripe"]`, whose `key` is the milestone's full key (`f5-board`).
- **The three states,** as `_review` returns them:
  - `ripe` and nothing asked: the button, posting a `signoff` request whose subject is the full key;
  - `signing_off` (a `signoff` request not done yet): "Signing off at the runner's next pick", and no button;
  - `refused` (a done request on a card still ripe): the runner's words under the button.
- After the click the button goes at once and "Signing off at the runner's next pick" shows in its place, with a dashed orange edge (the owner, 2026-10-07: what they asked for shows the moment it is made).
- `factory_dashboard/planning.py` imports `_to_html` from `factory_dashboard/milestones.py` at the top, so `factory_dashboard/milestones.py` imports from `factory_dashboard/planning.py` or `factory_dashboard/line.py` inside a function, never at the top.
- Put your fixture rows in your own function in `tests/factory_dashboard/conftest.py` (Edit it, anchored on its last lines).

### Done when
- a ripe milestone's page has the button, and the request it posts (its `hx-vals`, parsed as JSON) is `signoff` with the milestone's full key as subject
- a milestone with a ready ticket, one whose review isn't written, and one already signed off each show no button
- with a `signoff` request not done yet, the page says "Signing off at the runner's next pick" and shows no button
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
