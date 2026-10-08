---
id: f50-03-signoff-button
milestone: f50-the-data-safety-review-it-asks
depends_on: [f50-02-thread-signoff-sheet]
difficulty: 2
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A ripe card's page has a Sign off button that asks the runner to sign the card off.

### Context
Read `thread_page` in `factory_dashboard/planning.py` and `factory_dashboard/templates/thread.html`: the Archive button (`#archive`, and `archiving` in `thread_page`) is the worked example, request and pending state alike. `factory_dashboard/requests.py` already accepts the `signoff` kind; the runner applies it as `runner signoff` (subject: the card's full key, no value).
- Show the button inside `#review` (f50-02) only when the card is ripe: in `live_line(...)["field"]["ripe"]`, as `_ripe` reads it.
- An open `signoff` request for the card (done NULL) replaces the button with a pill "Signing off at the runner's next pick", with a dashed `var(--hazard)` border, as Archive's pending pill.
- The answer lands in a status span next to the button, as `#archive-status`; the button removes itself on send (`hx-on::before-request`).
- A signed-off card isn't ripe any more, so the button goes by itself.

### Done when
- a ripe card's page has `#signoff-button` posting `kind` "signoff" with the card's full key as `subject`
- a card that isn't ripe (tickets left, or no sheet) has no button
- with an open signoff request, the page shows the pending pill and no button
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
note: built by the lead in a terminal session (owner, 2026-10-08)
```
