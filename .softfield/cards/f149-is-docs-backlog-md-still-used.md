# Milestone F149: Retire the backlog file: reviews stop writing it, its items become seeds

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-05. Base: git tag `f149-is-docs-backlog-md-still-used-start`. Report: [`.softfield/reviews/f149-is-docs-backlog-md-still-used.md`](../reviews/f149-is-docs-backlog-md-still-used.md).
> Planted by the owner on 2026-10-16.

## Notes
is docs/backlog.md still used? i thought that one was retired

## What we know (2026-10-27)
- Nothing on the dashboard shows `docs/backlog.md`, but every project's review still writes to it: `REVIEW` in `runner/prompts.py` ("backlog: nits and should-fix points about untouched code go to docs/backlog.md"), the re-review scope in `runner/milestone.py` (`_fix_scope`, "go to the backlog" twice), and `docs/workflow.md` ("Nit → `docs/backlog.md`"). The checkpoint prompts (`CHECKPOINT`, `CHECKPOINT_SHADOW`, `CHECKPOINT_STAND_IN`) use `"route": "backlog"` for a finding with no fix ticket; `runner/review.py` lists it in `ROUTES` and defaults to it.
- Softfield's file: 30 items after the f5-13 pass (2026-10-23), which made bug-05 to bug-47 set-aside bug tickets; its "Coucou" section copies Coucou's own backlog. Travel companion (`/home/manu/projects/epayet/travel-companion/docs/backlog.md`): 17 items from five reviews, 2026-10-20 to 22. Coucou (`/home/manu/projects/epayet/coucou/docs/backlog.md`): 18 items, product on hold.
- F164 (Plant a review's ideas straight from the review) covers ideas from "What next", not the nits and fixes the backlog holds.
- A planner can't write another project's repo, and a plan's drafts in `.softfield/tasks/later/` are queued at approval, so the set-aside bug seeds are written by a lead ticket on main.

## Outcome
No review in any project writes a backlog file again; Softfield's is gone, each of its items a bug seed on the board, a planted card, or dropped with its reason.

## Done when
- `REVIEW`, the re-review scope and the checkpoint prompts never name a backlog; a test fails if `docs/backlog.md` comes back into `runner/prompts.py` or `runner/milestone.py`
- `docs/backlog.md` is gone from Softfield, and the board shows the new bug seeds and cards from D4
- the next review of any project sets aside a bug ticket for a nit worth a fix, and says the others in its report
- Travel companion's and Coucou's files go through their own cards (D5)

## Decisions
- **D1. ADR 35** (`.softfield/adr/35-no-backlog-file.md`): routes `later` (a set-aside bug ticket, `finding:` in its frontmatter) and `report` (said in the review report only) replace `backlog`; `ROUTES` keeps `backlog` readable for old files, and a missing route reads as `report`.
- **D2. Which file owns what.** `runner/prompts.py` (`REVIEW`, the three checkpoint prompts), `runner/milestone.py` (`_fix_scope`), `runner/review.py` (`ROUTES`, the default), `docs/workflow.md` (Milestone review loop, Discoveries, Report), `docs/how-it-works.md`, `runner/instructions/lead.md` ("Left for later"), `runner/instructions/author/owner.md` (the "parked backlog item" line), `.softfield/cards/bugs.md` ("Where bugs come from").
- **D3. A bug seed** is a ticket shaped like `.softfield/tasks/later/bug-43-remove-the-dead-line-page.md`: `milestone: bugs`, `area:`, `finding:`, the next free `bug-<nn>`, no `priority:` (the board's drag places it).
- **D4. Softfield's items**, decided on 2026-10-27:
  - Bug seeds: f90-F2 (two timing tests in `tests/runner/test_loop.py`, lead: protected tests); f151-F2 (`note_merge` unparks the checkpoint on every merge past `checkpoint_every`, lead); f158-F3 (one dashboard test opens every page on the test data and fails on escaped `&lt;ul&gt;`, `&lt;li&gt;` or `&lt;p&gt;`, developer).
  - Planted cards (factory, state idea): f53 ("where the hours went" in `softfield report`: limit waits, failed attempts, stops for the owner, for reviews to quote); f159-F5 (ticket and card pages render their markdown instead of showing backticks and stars). Each goes into an existing card's Notes instead when one covers it.
  - Dropped, each already a ticket or covered: f79-F3 (bug-01), ADR 07's parallel developers (bug-03, the roadmap's parallel-lanes item), f12-F10 (bug-40 changes those tests).
  - Dropped, not worth a run (seconds-wide races never seen, harmless leftovers, a gate turned down for low ceremony; each stays in its review report): f12-F11, f104-F3, f17-F5, f153-F3, f3 (SIGKILL), f4-F4, f3-C310-2, f114-F7, f2 (the two gates).
  - The "Coucou" section and m2-F6: Coucou's own `docs/backlog.md` holds them (D5).
- **D5. The other projects.** Each gets a card on its own board, from the owner's Plant box, whose lead drafts one lead ticket that does what f149-02 does there, its bug seeds set aside (Coucou's product work is on hold: none queued).
- **D6. Who builds.** Both lead: `runner/` and `runner/instructions/` are protected, and f149-02 deletes a file.

## Tickets
- f149-01-reviews-stop-writing-a-backlog (lead)
- f149-02-backlog-items-to-seeds (lead, after 01)

## Done (2026-11-02, terminal session)
**Where each item went:** bug-49 (f90-F2), bug-50 (f151-F2), bug-51 (f158-F3), bug-52 (f73-F3), bug-53 (f73-F4); cards F200 (f53), F201 (f159-F5), F202 (f80-F4, it amends ADR 29 item 7); F143's Notes (f84-F4, waits for f143-05).
**Dropped, each still in its review report:** already tickets: f79-F3 (bug-01), ADR 07's parallel developers (bug-03), f12-F10 (bug-40). Not worth a run, as D4 decided: f12-F11, f104-F3, f17-F5, f153-F3, f3 (SIGKILL), f4-F4, f3-C310-2, f114-F7, f2 (two gates). Added since D4, same reason (never seen, or right today): f68-F7, f84-F3, f32-F1, f21-F3, f15-F6.
**Coucou's section and m2-F6** are in Coucou's own file, which its F1 card retires. Travel Companion's goes through its F10.

## The owner's note on sign-off (2026-11-04)
The owner wants to plant a review's small fixes from the review, not find them on the board. ADR 43 amends D1 and D3: the route `later` becomes a quoted line with F164's Plant buttons. The work is `f164-07-review-fixes-are-quoted-too`, on F164 because it waits for F164's plates, so this card's sign-off doesn't wait for it.

