---
id: f210-01-one-box-per-card
agent: lead
milestone: f210-bundle-a-card-s-conversation-with
difficulty: 5
depends_on: [f75-01-archiving-on-approval, f108-01-desk-says-when, f210-02-one-strip-of-steps]
commands: [rm .softfield/tasks/later/f31-04-what-to-do-now.md]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/coming.py
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/_partials/desk_trail.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_coming.py
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_app.py
---

### Goal
On the owner's desk, each card's conversation and its open proposals are one box in "Your answers wanted", counted once, and Next walks a card's conversation and proposals before going to the next card.

### Context
The picture to build: `.softfield/cards/f210-mockup/one-box.html` (Proposed), the desk and the trail. Read D1, D2, D6, D8 and D9 in `.softfield/cards/f210-bundle-a-card-s-conversation-with.md`, then `desk`, `_answers_wanted`, `_open_proposals`, `_bundle`, `waiting_for_you` and `desk_trail` in `factory_dashboard/planning.py`, `DeskItem` and `_acted_on` in `factory_dashboard/coming.py`, and the desk in `factory_dashboard/templates/planning.html`.
- This regroups what is built: keep every rule of the items it joins (F74's dashed box and its place in line, F75's "archiving", F100's "being revised", F84's Writing now, F108's sign-off time). F108's "proposed N ago" goes from the box, whose words already say when the lead replied.
- `DeskItem.parts` needs each part's link and key points, beside its name and on-its-way mark. `_bundle` can stay the place that works them out.
- `_bundle` sorts its parts with `reading_order` (f210-02, D8) instead of "ADR first", and the box and Next follow that order. The title's rule stays: the plan's, else the first proposal's.
- A box's `<a>` can't hold its proposals' links: they sit beside it, in one element that draws the box. Keep `on-its-way-item` on the box's own link, which tests read.
- The desk is drawn from classes (f81-04: `.desk-item`, `.desk-title`, `.desk-words`, `.parts`, `.part`), with no inline styles. The box follows them; its new rules (the box, its corner ticks in `--ink-2`, the proposal links) go beside `.desk-item` in `factory_dashboard/static/dashboard.css`, and nothing goes inline.
- D9: build the box from whichever group holds the card's conversation link. If F65's f65-06 is on main by then, a ripe card's conversation is in its To sign off row, and that row takes the proposals; if it isn't, every conversation is in Your answers wanted.
- `_open_proposals` stays for the Overview's notices (`factory_dashboard/overview.py`). The groups left keep their markup; "Proposals to review" leaves `desk()` and the tests that name it.
- Delete f31-04's ticket, what-to-do-now, from `.softfield/tasks/later/` (D6; the `rm` in `commands:`).

### Done when
- a thread with a lead reply, listing a plan, a mock-up and an open ADR in that order: one box, linking to the thread, with three proposal links reading ADR, mock-up, plan, each with its key points, and "accept the ADR first"; the desk's number counts it once
- a thread with a lead reply and no proposals: a box with no proposal links
- the owner's message on that thread waiting for the lead: the box is dashed and not counted, its proposal links still there
- one of a box's two proposals on its way: that link is dashed, the box solid and counted; both on their way: the box is dashed and not counted
- `/planning` has no "Proposals to review"; the Overview's "thing(s) wait for you" number equals the Planning tab's
- from a thread listing a plan then a mock-up: Next is the mock-up ("Next: mock-up"), then the plan ("Next: plan"), then the next box's link ("Next"); on the plan, Previous says "Mock-up"; each says the same "N of M waiting for you", M counting boxes
- the first card's thread has no Previous, the last box's last proposal no Next; a proposal page already settled keeps today's behaviour: Next is the first item left
- a ripe card whose conversation is in To sign off (f65-06's row): its proposals are links in that row, and no other row names the card
- the desk's template has no `style=` attribute but the ones main already has (the meters' width and mark, the group's colour)
- `.softfield/tasks/later/f31-04-what-to-do-now.md` is gone
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
