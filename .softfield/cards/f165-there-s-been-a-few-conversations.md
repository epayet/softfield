# Milestone F165: A point that speaks of a mock-up opens it in one tap

> **State:** ready · **Priority:** 13 · **Area:** factory
> Planted by the owner on 2026-10-21.

## Notes
there's been a few conversations where it says 'on the mockup you can see...' but with no links to the mockup. why is that and how come it can happen

The owner, 2026-10-21, on the first plan: "I don't really want inline links, I just want to make sure the global links work. There's been times where mockups were mentioned but no link anywhere."

### From F141: this seems like a bug: [11:37:41] ▶ [claude-opus] planner… (merged by the lead on 2026-10-27)
this seems like a bug: [11:37:41] ▶ [claude-opus] planner f135#523
[11:37:59] ■ [claude-opus] planner f135#523 done · 0 min · $2.29
[11:37:59]   ↳ [claude-opus] I can't approve it for you: only your Approve on this page queues work. My last reply sent an empty list, and that took the plan's button away. That was my mistake. The plan is listed again below with no changes, so its Approve button is back. I also noted F101 in the card's facts.

What was said on F141's thread:
The owner pasted F135's log, where the lead admitted its empty list had taken the plan's Approve button away. On this thread they only asked to plan the card. The lead found that the bug was f51-03's (an empty list stored as '[]' hid the earlier proposals), which is merged on main. Nothing is still open.

## What we know (2026-10-21)
The "global links" are the thread's "Proposals from this card" list and the tabs on a proposal's review page. Both read only the thread's latest list of proposals. A mock-up has no link anywhere, or a link that shows nothing, in four ways:
- **Drawn, never listed.** The lead drew the file but listed only the plan (F152's first reply, 2026-10-20). Fixed by f152-02-every-mockup-is-listed (ready, priority 5): the runner lists any mock-up the job added or changed that the reply didn't name.
- **Hidden by an empty list.** A reply with no proposals hid F51's mock-up behind "replaced by a newer reply" (2026-10-20). Fixed by f51-03-empty-list-keeps-proposals (ready, priority 14).
- **Forgotten by a newer list.** A mock-up listed on an earlier turn and unchanged since drops out of the list when a later reply lists only the plan. Not seen on softfield's threads yet; f152-02 doesn't cover it, because it only looks at the files that job changed.
- **Listed, but the picture is gone.** Mock-ups listed before ADR 30's move are stored as `docs/milestones/<name>-mockup/…`, a path the review page no longer accepts. So F8, F17, F65, F67, F68 and F94 open their review page with no picture, though each file is on main under `.softfield/cards/`. F54's file was never kept.

## Outcome
Every mock-up the lead has listed for a card shows in the card's list and opens with its picture, or says plainly that its file is gone.

## Done when
- F67's mock-up review page shows the F67 picture again; F54's says its file isn't in the repo any more
- a reply that changes only the plan still leaves the card's mock-up in "Proposals from this card"
- with f152-02 and f51-03 merged, no mock-up a reply drew or listed is missing from the list

## Decisions
- **D1. The review page reads old paths where the files live now.** A stored `docs/milestones/<name>-mockup/<file>` is read as `.softfield/cards/<name>-mockup/<file>`. The stored proposals are left as they are. A mock-up whose file is on neither path says so where the picture would be. Developer ticket f165-01 (`factory_dashboard/`, not protected). Mock-up: `.softfield/cards/f165-mockup/point-links.html`.
- **D2. The runner keeps every mock-up listed.** Building on f152-02: when a reply lists proposals, every mock-up on `plan/<card>` that differs from main and isn't named is added to the list. A reply with no proposals that changed no mock-up leaves the last list standing (f51-03). Lead ticket f165-02 (`runner/` is protected), after f152-02.
- **D3. No links inside points** (owner, 2026-10-21). The first draft's per-point link and the prompt rule are dropped. The two tickets keep their first draft's file names, because a planner job can't rename a file; each ticket's Goal says what it does.

## Tickets
- f165-01-point-opens-its-proposal (developer, D1)
- f165-02-every-mockup-has-its-point (lead, D2)

## Not here
- f31-04-what-to-do-now (F31's set-aside "What to do now") stays set aside.

## How to test
Open F67's thread, then the mock-up in "Proposals from this card": the picture shows. On a card with a plan and a mock-up, comment on the plan only: the lead's next reply lists the plan, and the list still has the mock-up.
