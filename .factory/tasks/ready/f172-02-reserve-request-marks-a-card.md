---
id: f172-02-reserve-request-marks-a-card
milestone: f172-i-d-like-to-be-able
agent: lead
difficulty: 4
depends_on: [f172-01-marked-cards-pass-the-reserve]
files:
  - runner/requests.py
  - runner/loop.py
tests:
  - tests/runner/test_requests.py
---

### Goal
A `reserve` request whose subject is a card's short key (`f142`, value `on` or `off`) writes or removes `**Reserve:** yes` in that card's header, committed by the runner, and with `on` the card's tickets parked at either reserve (the week's, or the owner's 25% of the 5-hour window) go at the next pick.

### Context
Read D2 and D4 in `.factory/cards/f172-i-d-like-to-be-able.md`. Then in `runner/requests.py`: `_switch` (today's `reserve` request, subjects `week` and `five_hour`), `_card_with` and `_ticket_priority` (how the board's order rewrites a card's header and commits it with `_commit_file`); in `runner/loop.py`: `_week_switched_on` and `_five_hour_switched_on` (what D4 does for every parked ticket) and `reserve_cards` from f172-01.
- `week` and `five_hour` behave exactly as today. Any other subject must be the short key of a card in `.factory/cards/` whose state is ready or building; else the request is refused with a sentence saying why, which the owner sees as today.
- The field goes after `**Area:**` in the header line, as D1 says; `off` removes it with its ` · `. Asking for what is already so changes nothing and commits nothing.
- The commit message reads `F142 may use Claude's reserve, by the owner` (or `may no longer use`).
- With `on`, the parked tickets freed are those in `reserve_cards` for that card, parked with kind `reserve` or `five-hour`; their `reserve` and `five-hour` owner items are resolved.
- `runner/requests.py` is imported by the dashboard (`factory_dashboard/requests.py` takes `RESERVE` from it): the kind's name stays `reserve`.

### Done when
- `reserve f142 on` writes `**Reserve:** yes` in F142's header and commits it; `off` removes it
- `reserve f142 on` on a card already marked commits nothing
- a subject that is no card, or a card that is an idea or done, is refused with a sentence naming the card and why
- after `reserve f142 on`, a F142 ticket parked at the week's reserve, and one parked for the 5-hour share, have `retry` set and their Needs-you items are resolved; a parked ticket of another card is left as it is
- `reserve week on` and `reserve five_hour off` behave as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
