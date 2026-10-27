---
id: f100-01-proposals-being-revised
agent: lead
milestone: f100-if-i-replied-to-a-conversation
difficulty: 3
depends_on: [f74-01-one-box-per-conversation]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
While the owner's message on a thread waits for the lead, the thread's open proposals show dashed orange, "being revised", on the desk, the thread page and the proposal page, and no longer count as waiting for the owner.

### Context
Read `.factory/cards/f100-if-i-replied-to-a-conversation.md` (Why it happens, D1–D6) and the mock-up `.factory/cards/f100-mockup/being-revised.html` (Proposed is the picture to build). Then, in `factory_dashboard/planning.py`: `_answers_wanted` (f74-01 put the "waiting for the lead" rule there), `_open_proposals`, `_proposals`, `_standing`, `_next_reply`, `_held`, `waiting_for_you`; and the proposal rows in `factory_dashboard/templates/planning.html`, `#proposals` and the reply form's `htmx:afterRequest` in `factory_dashboard/templates/thread.html`, `#actions` in `factory_dashboard/templates/proposal.html`.
- D1: lift f74-01's rule into `_waiting_for_lead(conn, project_id) -> set[str]` (the thread cards); `_answers_wanted` uses it unchanged in behaviour.
- `_open_proposals`: a proposal whose state is open and whose thread is in that set is `on_its_way=True`, words `f"being revised · {next_reply}"`. One already on its way keeps `_NEXT_PICK`. `desk()` passes what `_open_proposals` now needs.
- `_proposals` (the thread aside): such a proposal's state reads `being revised`; the aside draws it with a dashed `--hazard` edge and that word in `--hazard`, keeping its kind's top border, and the foot line reads as in the mock-up.
- `_standing` / the proposal page: a dashed line above the buttons, words from D3; the buttons stay.
- thread.html: after a successful Send, redraw `#proposals` as `#conversation` is redrawn.
- Use the existing `--hazard` token; no new colour.

### Done when
- a thread with two open proposals and an open `plan_message` request naming it: both proposals are dashed items (`on-its-way-item`) in the `proposals` group, "being revised · …", and not in `waiting_for_you`
- the same with the request done, the owner's message stored and an open planner job about the thread: still dashed
- after a lead reply with no proposals is stored: both are solid and in `waiting_for_you` again
- a proposal with an Approve on its way, on a thread with a message on its way: still "on its way · the runner applies it at its next pick"
- the thread page lists them as "being revised", dashed; the proposal page shows "Being revised" above Approve and Reject, and both buttons are there
- a message cancelled before the pick (F14) leaves the proposals solid
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
