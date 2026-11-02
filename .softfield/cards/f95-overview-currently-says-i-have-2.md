# Milestone F95: overview currently says i have 2 things to sign off, but i…

> **State:** done · **Priority:** 3 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-16. Base: git tag `f95-overview-currently-says-i-have-2-start`. Report: [`.softfield/reviews/f95-overview-currently-says-i-have-2.md`](../reviews/f95-overview-currently-says-i-have-2.md).
> Planted by the owner on 2026-10-10.

## Notes
overview currently says i have 2 things to sign off, but i see only 1 'finish to talk through' on my desk

### From F107: overview page says I have this to sign off but planning… (merged by the lead on 2026-10-13)
overview page says I have this to sign off but planning desk does not: softfield signoff f31-when-i-click-on-approve-plan

### From F115: I may have asked this before but why are there things to… (merged by the lead on 2026-10-13)
I may have asked this before but why are there things to to sign off in overview needs you but nothing on my desk

## Expected outcome
- The Overview never shows more sign-offs waiting than the desk lists: a milestone waiting for sign-off shows once, through the desk's entry in Needs you.
- When the owner asks the planning room about what they see ("it says 2, I see 1"), the lead can look at the same page and the same data, and answers with names, not only with the mechanism.

## Done when
- Needs you on the Overview has no `signoff` rows of its own; the desk's entry counts them.
- The other Needs-you items (an ADR, a blocked ticket, Claude's reserve) show as before.
- A planner job and a review job can run `softfield look sql "…"` and `softfield look page /planning`; neither can change anything.
- To test: plant a question about what is on your desk, and check the lead's reply names the items you see.

## Decisions
- **D1: the desk is the one place a sign-off shows.** Needs you drew sign-offs from two sources: the desk (worked out live: every ticket done, the review's sheet stored, not signed off) and the rows the runner stored at each milestone's verdict (`owner_items`, kind `signoff`). A stored row stays open until the milestone is signed off, even when the milestone got new tickets since or has no review sheet, so the two disagreed. The Overview drops the stored rows, as it already does for the lead's replies (f6-09).
- **D2: the runner keeps storing them.** Notifications still read them, and `runner milestone` still prints its verdict. Nothing changes in `runner/`.
- **D3: planning and review jobs can look** ([ADR 28](../adr/28-lead-jobs-can-look.md), settled with the owner on this thread, 2026-10-10): one read-only command, `softfield look`, for a SELECT on the metrics database or any dashboard page as text. No copy of the database, no fixed list of facts to keep up (any page works, new ones included), nothing added to prompts.
- **D4: information first, looks later.** The text of a page answers "what do I see"; it can't answer "this looks bad". A screenshot form of the same command is the next step when such a question comes (ADR 28, Later); a browser for the job (a browser MCP) is turned down for now: it can press buttons and ties the workflow to one frontier.

## Tickets
- `f95-01-sign-offs-counted-once` (developer): the Overview leaves the stored sign-off rows out of Needs you.
- `f95-02-lead-jobs-can-look` (lead, `runner/` is protected): the `look` command and its place in the planner's and the review's tool list. Waits for ADR 28.
