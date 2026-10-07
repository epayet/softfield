---
id: f6-08-proposal-review
milestone: f6-planning-room
depends_on: [f6-06-desk-page]
difficulty: 5
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A proposal's review page lays out its key points in plain words, agreed by default, with Comment… on each, and gives "Send back", "Accept ADR" or "Approve plan".

### Context
Read the mock-up (`docs/milestones/planning-room-mockup/Main.dc.html`, `docs/milestones/planning-room-mockup/Review.dc.html`, `docs/milestones/planning-room-mockup/Phone.dc.html`: read the markup and the data in each script, not pages to open) (`docs/milestones/planning-room-mockup/Review.dc.html`; agreed is the default), D1, D2, D4 and D6 in `docs/milestones/f6-planning-room.md`, `factory_dashboard/planning.py`, `factory_dashboard/requests.py`, and `find_proposal` in `runner/metrics.py` and `draft`, `is_proposed` in `runner/planner.py`.
- **`/planning/<thread>/proposals/<id>`:** the proposal as the thread's latest lead message lists it (`metrics.find_proposal`):
  - tabs per proposal of the card (ADR, mock-up, plan);
  - the key points (`key_points`: `n`, `title`, `text`, `flag`) grouped as the proposal lists them; a ⚑ where `flag` is true;
  - a side panel with what happens next.
- **A mock-up proposal** shows its HTML file in a sandboxed `<iframe>` from `/planning/mockups/<thread>/<path>`: a read-only route serving only files under `docs/milestones/*-mockup/`. Drafts aren't in the working tree: read the file with `planner.draft` (f6-11) from the project's repo (`projects.repo`).
- **The buttons** (D1 gives each request's subject and value):
  - with any comment, "Send back" posts `send_back`, subject `<thread>/<id>`, value JSON `{"text": …, "comments": {"<key point n>": …}}`;
  - with none:
    - an `adr` proposal: "Accept ADR" posts `accept_adr`, subject the thread, value the number from the proposal's path (`docs/adr/23-….md` → `23`);
    - a `plan`, `mockup` or `replan`: "Approve plan" posts `approve_plan`, subject the thread. It approves every draft on the card's branch at once. It stays disabled while the card has an `adr` proposal whose file on main is missing or still Proposed (`planner.is_proposed`);
    - a `seed` (general thread): "Plant it" posts `plant`, subject `general/<id>`.

### Done when
- an ADR proposal's points show grouped, with their flags; a comment turns the primary button into Send back
- Approve plan is disabled while the card's ADR is Proposed, and enabled after
- a seed's button posts `plant` with subject `general/<id>`
- the mock-up route serves a file under a `-mockup/` folder from the card's plan branch, and refuses any other path
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: mypy)
attempts: 3
tokens: 6088581
logs: var/runs/20261007-005149/f6-08-proposal-review
```
