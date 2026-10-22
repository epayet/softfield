# Milestone F172: Mark a card to use Claude's reserve, so only its tickets run past the mark

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-22.

## Notes
I'd like to be able to use the reserve at the ticket level, so that high priority tickets get done even on reserve. i currently set the reserve on because there are some tickets i really want, but i'm keeping an eye on when to turn it off again once the tickets i want are on, so this would solve that problem for me and i won't have to keep an extra eye on it

## Plan (lead, 2026-10-22)
- **Today:** past the week's mark (70%), every lead ticket parks (`at_reserve`, `runner/loop.py`) until the owner turns on "Let the factory use the week's reserve", which lets every lead ticket through for 24 hours. On 2026-10-22 both switches were on until Fri 09:35 with the week at 67%.
- **Proposed ([ADR 34](../adr/34-a-card-may-use-the-reserve.md)):** a card can be marked "may use Claude's reserve" from its page. Its lead tickets, and the lead tickets they wait for, run past both marks (the week's reserve and the owner's 25% of the 5-hour window, owner 2026-10-22); the rest still park. The mark ends with the card's work.
- Tickets: `f172-01-marked-cards-pass-the-reserve` (lead, runner: the mark read and honoured), `f172-02-reserve-request-marks-a-card` (lead, runner: the request writes the mark), `f172-03-reserve-lever-on-the-card` (developer, dashboard: the lever, the board's mark, the Overview's list). 02 waits for 01, 03 for 02.
- Mock-up: `.factory/cards/f172-mockup/card-reserve.html`.

## Decisions
- **D1: the mark lives in the card's header,** `**Reserve:** yes` after its Area, and nowhere else. `milestone.card` reads it into `Card.reserve` (False when missing). Only the runner writes it.
- **D2: the request is `reserve` with a card's short key as subject** (`f142`, value `on` / `off`), beside `week` and `five_hour`. `runner/requests.py` tells them apart; `factory_dashboard/requests.py` doesn't change.
- **D3: who passes:** `loop.reserve_cards(repo, ready) -> set[str]`: the ids of the ready lead tickets of marked cards, plus every ready ticket they wait for through `depends_on`, transitively and across cards. Neither `at_reserve` nor `at_five_hour` parks a ticket in that set, and `_waits_for_the_owner` (the order in `_next_task`) treats it as free (owner, 2026-10-22: both reserves). A real limit (a window at 100%, a refusal resting it) still holds it.
- **D4: marking frees what is parked:** the request applied, the card's tickets parked with kind `reserve` or `five-hour` (and those they wait for) get `RETRY`, and their `reserve` and `five-hour` owner items are resolved, as `_week_switched_on` and `_five_hour_switched_on` do for all.
- **D5: the mark ends at sign-off:** the sign-off's rewrite of the card doc drops the `**Reserve:**` field. Until then a card with no ready ticket lets nothing run.
- **D6: what the page shows:** the card's page has a lever like the allowance panel's (`.lever`, `factory_dashboard/templates/_partials/allowance.html`), only while the card has ready tickets; the board's planted and growing cards show a small "uses reserve" plate; the Overview names the marked cards once, under Claude's two meters. A lever pulled shows on its way (dashed orange edge) until the runner applies it.
