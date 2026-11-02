---
id: f146-01-developer-line
milestone: f146-some-kind-of-view-or-toggle
agent: lead
difficulty: 4
depends_on: []
files:
  - factory_dashboard/board.py
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
`factory_dashboard/board.py` can tell, for each planted card, what it holds for the developers: whether they can work on it now, whether its developer work waits for the lead (and for which lead tickets), or whether it is lead only, and how much developer work the board holds in all.

### Context
Read `.softfield/cards/f146-some-kind-of-view-or-toggle.md` (D1–D4, D6, and "Where it stands" for real values).
- `factory_dashboard/board.py`: `_cards` reads the `tickets` rows (`kind`, `files`, `depends_on`, `state`) and builds each `Card`; `board()` places and filters them; `_repo` (from `factory_dashboard/planning.py`) gives the checkout, or None.
- The runner's rules to reuse, not copy: `runner.router.lead_only`, `runner.config.read_protected`, `runner.loop.ticket_minutes` (`factory_dashboard/overview.py` already imports `runner.loop`).
- `board(..., developers=False)` must build the same cards, places and `line` as today: only `Card.developers` and `Board.developers` are new. The page doesn't change in this ticket: f146-02 draws it.

### Done when
- with `developers=True`, each planted card carries D4's `DevWork`, and every card of another stage has look `none`
- a ready ticket with files under a protected path counts as the lead's even without `agent: lead`; with no checkout, `kind` alone decides
- a developer ticket waiting on another developer ticket that can run counts as "after"; one waiting on a lead ticket makes its card `waits`, with that lead ticket in `waits_for`, even through another developer ticket
- a card with both a developer ticket that can run and one that waits is `can`
- `then` names the first lead ticket left on a `can` card, or says `review` when none is left
- `Board.developers` counts the `can` cards and their tickets, with minutes from the median of `ticket_minutes`, None with no merged ticket
- with `developers=False`, the board is the same as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
