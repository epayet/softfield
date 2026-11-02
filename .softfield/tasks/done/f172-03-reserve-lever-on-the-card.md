---
id: f172-03-reserve-lever-on-the-card
milestone: f172-i-d-like-to-be-able
difficulty: 4
depends_on: [f172-02-reserve-request-marks-a-card]
files:
  - factory_dashboard/templates/thread.html
  - factory_dashboard/planning.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/board.py
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/overview.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The owner marks a card "may use Claude's reserve" with a lever on the card's page, sees the mark on the board's planted and growing cards, and sees the marked cards named under Claude's meters on the Overview.

### Context
The picture to build is `.softfield/cards/f172-mockup/card-reserve.html` (Proposed). Read D6 in `.softfield/cards/f172-i-d-like-to-be-able.md`.
- Follow the reserve lever in `factory_dashboard/templates/_partials/allowance.html`: same `.lever` markup and CSS, same `hx-post="/requests"` with `kind: "reserve"`, but the subject is the card's short key (`f142`) and the value `on` or `off`. A lever pulled shows on its way (dashed orange edge, `.on-its-way`) until the runner has applied it; `reserve_switches` in `factory_dashboard/overview.py` shows how an asked request is found.
- Whether a card is marked comes from its doc's header (`**Reserve:** yes`, read by `card` in `runner/milestone.py` as `Card.reserve`). Find where the card's page builds `card_meta` (`factory_dashboard/planning.py`) and where the board builds its cards (`factory_dashboard/board.py`).
- The lever shows only on a card in Planted or Growing (ready or building); the board's plate likewise.
- The Overview's line under Claude's two meters (once, not under each) lists the marked cards, each with its title, as links to their pages; nothing when none is marked.
- The lever's line on the card's page says it uses both reserves, as the mock-up words it.
- The board's plate uses the hazard stripe and the ink only (owner.md, "Factory theme": ornament never looks like a status) and says its meaning in words.

### Done when
- a ready card's page shows the lever, off for an unmarked card and on for a card whose header says `**Reserve:** yes`; an idea or done card shows none
- pulling it posts `reserve` with the card's short key and the other value, and the lever shows on its way until the runner applies it
- a marked card on the board shows the "uses reserve" plate; an unmarked one doesn't
- the Overview names the marked cards once under Claude's meters, and says nothing when none is
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 2059117
logs: .softfield/var/runs/20261022-235747/f172-03-reserve-lever-on-the-card
```
