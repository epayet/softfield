# Milestone F152: A done card says where its review is, and set aside says it won't run

> **State:** ready · **Priority:** 9 · **Area:** factory
> Planted by the owner on 2026-10-20.

## Notes
When a ticket is on the board growing and all tickets are done but it's still there. Does they mean it's waiting for a review round? If soit should state as much as it's not clear what's supposed to happen next. When it says 1 tickets has been set aside, do I need to do anything?

## What we know (2026-10-20)
- A card goes Ripe once every ticket is done **and** its review's sheet is stored (`_milestone_stage`, `factory_dashboard/board.py`); until then it stays Growing with no word on why. Today that is F19, F28 and F88.
- F88's review ran 07:21–07:40 (job 1066) and wrote `.factory/reviews/f88-add-to-lead-memory-that-new.md`; the runner stores its sheet at its next pick (`sync_cards`), and F88 turns Ripe then.
- F19's and F28's reviews stopped at once on 15 Oct, "end-to-end tests fail on staging": no `tests/e2e` since the split. F135 (ticket f135-01-no-e2e-no-stop, ready) makes them due again; their review-stop items are on the Overview's Needs you meanwhile.
- A set-aside ticket (`.factory/tasks/later/`) never runs and counts for no stage: F5's f5-10 was replaced by the reserve switch and is kept for the record. The owner has nothing to do with one.

## Outcome
A growing card whose tickets are all done says which step its review is at, so the owner knows whether to wait or act; a set-aside count says it won't run.

## Done when
- on the board and on the card's page, F19 reads "review stopped: end-to-end tests fail on staging · shown under Needs you" while its stop stands, and "review next" once it is due
- a card whose review job runs says "review running" and who runs it
- "1 set aside, won't run" on F5's card and page

## Decisions
- **D1. No new stage.** Ripe keeps meaning "needs your sign-off"; the review's step is a line on the Growing card, as the mock-up draws it (`.factory/cards/f152-mockup/review-note.html`).
- **D2. The review's step**, on a growing milestone card whose counted tickets are all done and whose sheet isn't stored, the first that holds:
  - a live job with role `review` on the milestone (`running_jobs`): "Review running", "{agent} reads the work · then it's yours to sign off";
  - an `owner_items` row of kind `review-stop` on the milestone, not resolved: "Review stopped", "{its text} · shown under Needs you";
  - otherwise: "Review next", "Claude reviews it before the next ticket · then it's yours to sign off".
- **D3. Set aside reads "N set aside, won't run"** on the board card and the card page.
- **D4. Developer ticket.** `factory_dashboard/` is not protected and `_card_note` is the example.
- **D5. A drawn mock-up is always listed** (2026-10-20: the first reply drew one and listed only the plan, so the owner couldn't see it). After a planner job, the runner adds a `mockup` proposal for every mock-up file the job added or changed that the reply didn't name. Lead ticket: `runner/` is protected.

## Tickets
- f152-01-review-step-on-the-card (developer)
- f152-02-every-mockup-is-listed (lead)
