---
id: f210-02-one-strip-of-steps
milestone: f210-bundle-a-card-s-conversation-with
difficulty: 4
depends_on: []
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/_partials/card_steps.html
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/thread.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_proposal.py
---

### Goal
A card's thread page and its proposal pages show the same strip of steps: Conversation, then each proposal with its state and key points.

### Context
The picture to build: `.softfield/cards/f210-mockup/one-box.html` (Proposed), both card pages. Read D3, D4 and D8 in `.softfield/cards/f210-bundle-a-card-s-conversation-with.md`. Follow `#proposal-tabs` in `factory_dashboard/templates/proposal.html`. Read `#proposals` in `factory_dashboard/templates/thread.html`, and `Proposal` and `_proposals` in `factory_dashboard/thread.py`.
- Add `reading_order` to `factory_dashboard/planning.py` (D8): it takes a list of items and a function giving each one's proposal dict, and returns them sorted ADR, mock-up, plan or replan, merge, seed, anything else last; same kinds keep their order. `_proposals` uses it. f210-01 uses it for the desk.
- `Proposal` also gets its key points' number. The partial takes the thread and the proposals, and marks the current page with `aria-current="page"`, as the tabs do.
- On a thread with proposals, the strip replaces the `#proposals` aside. It sits inside `#conversation`, after the latest messages and before `#merged-on` and the reply form, so it shows while a reply is awaited too. Remove the two `#proposals` redraws in the page's scripts; the conversation's redraw now carries the strip. Change the `#conversation-stamp` so that a proposal's new state redraws it, or F100's "being revised" shows late.
- Keep "Nothing becomes a ticket until you approve it." under the strip on the thread page.
- On a proposal page, the strip replaces `#proposal-tabs` in the same place. F207's f207-02 puts an "In short" plate under the page's header: when it is there, the strip stays above it.
- A thread with no proposals has no strip. It has no buttons of its own.
- Colours: `--hazard` and `--hazard-ink` for the current step, as the tabs do; the top stripe is the hazard stripe, as `.fix` in `factory_dashboard/templates/planning.html` draws one. A `being revised` or `on its way` step has a dashed `--hazard` edge.

### Done when
- a thread whose reply lists a plan then a mock-up: under its latest reply and above the reply box, a strip reads Conversation (current), Mock-up, Plan, each proposal with its state and key points, each linking to its page; there is no aside
- that plan's page: the same strip, in the same order, Plan current, and Conversation links to the thread; no `#proposal-tabs`
- a reply listing a plan, a merge, a mock-up and an ADR: the strip reads Conversation, ADR, Mock-up, Plan, Merge
- at 390 px on a thread page, the strip comes before the reply box; each step is at least 44 px tall and nothing overflows
- the owner's message on the thread: the open proposals' steps say "being revised", dashed, without a reload
- a thread with no proposals has no strip
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 1168547
logs: .softfield/var/runs/20261110-182701/f210-02-one-strip-of-steps
```
