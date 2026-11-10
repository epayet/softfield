---
id: f209-01-card-at-work
milestone: f209-i-want-the-ticket-currently-being
difficulty: 4
depends_on: []
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
The card with a live job stands out on the board: a thick frame, a filled "Working now" head and a wash, in the colour of who works.

### Context
Read D1 and D2 in `.softfield/cards/f209-i-want-the-ticket-currently-being.md`. The picture to build is Proposed in `.softfield/cards/f209-mockup/working-now.html`: copy its `.at-work` rules and the card's markup; its plate is the next ticket.

`Card.running` in `factory_dashboard/board.py` becomes `Card.at_work`, and the template's `.card-now` line goes. `Work` is filled from `running_jobs` in `factory_dashboard/overview.py`, as now, but for every live job. The role rule is in `factory_status`, in `factory_dashboard/app.py`. A job with `waiting_clock` keeps the frame and says "Waits for Claude until HH:MM", with no fill, glow or lamp.

On a card, only `factory_dashboard/templates/board.html` reads `running`. Add the two swatches to the board's legend, in the mock-up's words.

In the developer's view, an at-work slot keeps its frame and full strength, whatever the card holds for developers. Watch the specificity: the fading rules in `factory_dashboard/static/dashboard.css` start `.dev-view .slot.dev-waits` and `.dev-view .slot.dev-none`, so they beat a plain `.slot.at-work`. The card's words (`dev_tag`) don't change here. The picture is "In the developer's view" in the mock-up.

### Done when
- a ticket's live job lights its card, in Planted, on a bug's card too; orange for the lead, blue for a developer
- a live review job and a live planner job light the card their `milestone` names, the planner's on a Sprouting or Seed card too
- a job whose run has stopped beating lights nothing
- a job waiting for Claude's limit shows its words and has no lit look
- a lit card stays at its place in the column, and keeps its growing tag
- in the developer's view, a card with a developer at work has the blue frame and head at full strength (computed `opacity` 1, in a browser test as in `tests/factory_dashboard/test_line.py`), on `dev-can`, `dev-waits` and `dev-none` slots alike
- in the developer's view, a card with the lead at work keeps its orange frame at full strength too
- the listed `tests:` pass, and fail without the change

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 490923
logs: .softfield/var/runs/20261106-011143/f209-01-card-at-work
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
