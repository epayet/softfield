# Milestone F202: While main fails its tests, only the ticket that mends it runs

> **State:** ready · **Priority:** 4 · **Area:** factory
> From docs/backlog.md (f80-review), written by the lead on 2026-11-02.

## Notes
While main fails its `tests`, `waits_for_main` (`runner/loop.py`) holds lead tickets and the developer tickets already waiting (f80-02), but other developer tickets still start, as ADR 29 item 7 says ("Developer tickets go on"). All of them but the mender fail `all-tests` on a branch cut from that main, so each spends a full model run before it waits (no attempt, no game). Each also rewrites `main_red`'s `checks` to `["tests"]`, so a main that also failed a lead ticket's `layout` can be called mended while `layout` still fails (the next lead ticket finds it again). Fix: while `main_red`'s checks include `tests`, hold every ready ticket but the mender, and add to `checks` instead of replacing them. Stays: it amends ADR 29 item 7, so it goes with the next ADR on main-red; two red mains so far.

## Plan (2026-11-11)
Draft [ADR 47](../adr/47-a-red-main-holds-every-ticket-but-the-mender.md) carries the rule change; two lead tickets build it, both in `runner/loop.py` (protected, tests first). Nothing on screen changes but the words of the owner's red-main item, so no mock-up.

## Decisions
- **D1, the hold** (ADR 47 item 1): `_held_by_red_main` holds every ready ticket but `main_red["mender"]` when `main_red["checks"]` holds `MAIN_TESTS`; otherwise it holds as today (the lead's and the ones in `waits_on_main`).
- **D2, checks add up** (item 2): `_main_is_red` with `main_red` already set keeps its `head`, `ticket` and `mender`, and sets `checks` to the old list plus the new names, in order, no repeats.
- **D3, the mender never waits** (item 3): in `_settle_lead_task`'s failed path and before `_waits_for_red_main` in `run_task`, a ticket whose id is `main_red["mender"]` skips the main check and fails as any attempt would.
- **D4, the mender found again** (item 4): `main_red` keeps `said`, the failing checks' output cut to its first 4000 characters, beside its other keys. At each pick, while `mender` is None or names no ready ticket, `_mender` runs again on `said` and the result is saved. A state file without `said` loads, and its mender is left as it is.
- **D5, the words** (item 5): `red_main_text` says "no other ticket runs until main passes" when the checks hold `tests` (else "no other lead ticket"), and ends "nothing would mend it yet" when there's no mender.

## Tickets
- `f202-01-red-main-holds-every-ticket`: D1, D2, D5.
- `f202-02-the-mender-never-waits`: D3, D4.
