# Milestone F202: While main fails its tests, only the ticket that mends it runs

> **State:** idea · **Priority:** 100 · **Area:** factory
> From docs/backlog.md (f80-review), written by the lead on 2026-11-02.

## Notes
While main fails its `tests`, `waits_for_main` (`runner/loop.py`) holds lead tickets and the developer tickets already waiting (f80-02), but other developer tickets still start, as ADR 29 item 7 says ("Developer tickets go on"). All of them but the mender fail `all-tests` on a branch cut from that main, so each spends a full model run before it waits (no attempt, no game). Each also rewrites `main_red`'s `checks` to `["tests"]`, so a main that also failed a lead ticket's `layout` can be called mended while `layout` still fails (the next lead ticket finds it again). Fix: while `main_red`'s checks include `tests`, hold every ready ticket but the mender, and add to `checks` instead of replacing them. Stays: it amends ADR 29 item 7, so it goes with the next ADR on main-red; two red mains so far.
