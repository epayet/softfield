---
id: f210-04-approve-plan-wakes-up
milestone: f210-bundle-a-card-s-conversation-with
difficulty: 2
depends_on: [f224-02-approve-first-on-the-pages, f210-05-typed-comments-wait-for-real]
files:
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_proposal.py
---

### Goal
A plan's review page that shows Approve plan greyed out, waiting for the card's ADR, enables it by itself once Accept ADR has been pressed, without a reload.

### Context
Read the `#primary` block and the page's script in `factory_dashboard/templates/proposal.html` (`adr_waits`, `adr_on_its_way`), `proposal_review` in `factory_dashboard/proposal.py`, and `test_an_open_accept_adr_enables_approve_plan_and_says_so` in `tests/factory_dashboard/test_proposal.py` as the example to follow. The desk's live poll in `factory_dashboard/templates/planning.html` (`#live-desk`, `every 5s [window.liveIdle()]`) is the pattern.
- The owner (2026-10-29): "Approved plan is still grey even though adr acceptance is on the way." A fresh load already enables it (f51-02), but a plan page opened before the ADR was accepted, then come back to with Back or from another tab, never asks again. On F162 the plan was approved 20 minutes after its ADR.
- Only while `adr_waits` is true, `#primary` polls its own page every 5 s (`hx-get` the page's address with its query, `hx-select="#primary"`, `hx-swap="outerHTML"`, `hx-trigger="every 5s [window.liveIdle()]"`). Once the button is enabled the new `#primary` has no poll, so it stops.
- F224's f224-02 put `details#approve-first` beside `#primary`, its button disabled while the ADR waits, and hidden with `#primary` while a comment is written. It wakes up with `#primary`: redraw both from the same response (wrap the two, or swap the fold out of band), and keep the fold's open or closed state.
- Also redraw them when the browser shows the page from its back-forward cache (`pageshow` with `event.persisted`).
- **The trap:** the page's script keeps `primary` in a variable and sets `hidden` on it (and on the fold) while comments are typed. After a swap that variable is a dead node. Look them up inside `update()`, and run `update()` after the swap, or Approve comes back beside Send back.

### Done when
- a plan page with the ADR still Proposed and no Accept ADR: `#primary` carries the 5 s poll; with an Accept ADR open, or the ADR Accepted, it doesn't
- the browser test: open the plan page (Approve plan disabled), add an open `accept_adr` for the card, and within the poll Approve plan and Approve first's button are both enabled and the page says "ADR N's acceptance is on its way: the runner applies it first."
- the browser test: with a comment typed on the waiting plan page, after the poll Send back still shows and Approve plan and the Approve first fold stay hidden
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
