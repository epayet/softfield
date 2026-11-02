---
id: f172-07-fast-lane-in-the-card
milestone: f172-i-d-like-to-be-able
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/milestone.py
  - runner/requests.py
  - runner/owner.py
  - runner/loop.py
tests:
  - tests/runner/test_milestone.py
  - tests/runner/test_requests.py
  - tests/runner/test_owner.py
---

### Goal
A card in the fast lane says `**Fast lane:** yes` in its header, and the runner's words about it say "fast lane": the commit, the refusal and the sign-off's clean-up. A card still saying `**Reserve:** yes` counts as in the lane.

### Context
Read ADR 35 item 1 in `.softfield/adr/35-a-marked-card-goes-first.md` (it must be Accepted) and D10 in `.softfield/cards/f172-i-d-like-to-be-able.md`. Then `CARD_RESERVE_RE` and `card` in `runner/milestone.py`, the "reserve on a card" section of `runner/requests.py` (`_MARK`, the header regex, the request's commit message and refusals), `_CARD_RESERVE` in `runner/owner.py` (the sign-off drops the mark), and the docstrings of `reserve_cards` and `_uses_reserve` in `runner/loop.py`.
- Only the words change. `Card.reserve`, `reserve_cards`, the request's kind `reserve` and its subjects stay, so the dashboard keeps working until f172-05 changes its words.
- `card` reads `**Fast lane:** yes` and the old `**Reserve:** yes` alike; the request writes only the new form, and taking a card out of the lane, or signing it off, removes either form.
- Commit messages: "F142 in the fast lane, by the owner" and "F142 out of the fast lane, by the owner". A refusal for an idea or done card: "F142 is done: only a planted card goes in the fast lane" (with its state).
- Rewrite every card doc in `.softfield/cards/` whose header says `**Reserve:** yes` to `**Fast lane:** yes` in this change. On 2026-10-27 main had F142 and F173 marked; check what is there when you start.

### Done when
- `milestone.card` reads `**Fast lane:** yes` and `**Reserve:** yes` both as `reserve=True`
- `reserve f142 on` writes `**Fast lane:** yes` and commits "F142 in the fast lane, by the owner"; `off` removes either form
- a sign-off removes either form from the header
- no card doc in `.softfield/cards/` says `**Reserve:**` after this change
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
