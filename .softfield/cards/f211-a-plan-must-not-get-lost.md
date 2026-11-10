# Milestone F211: Open plans survive a card's closing, and new ideas don't join a planned card

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-03.

## Notes
A plan must not get lost when its card closes. Don't merge a new idea into a card whose plan is already approved unless that plan covers it; give it its own card. Sign-off and Archive must say when a plan is still open on the card, and let me keep it as a new card.

### From F223: I've signed off f149 but I don't remember if I asked it to… (merged by the lead on 2026-11-05)
I've signed off f149 but I don't remember if I asked it to do some more work. Clarify what happens in this situation

What was said on F223's thread:
Asked: the owner signed off F149, Retire the backlog file, did not remember whether they had asked it for more work, and wants to know what happens in that situation.
Answered for F149: they asked on 2026-11-04. ADR 43 was accepted and its plan approved that day, and the sign-off was on 2026-11-05 with no message waiting. The work is f164-07-review-fixes-are-quoted-too, ready on F164, not started, and waiting for f164-01 and f164-03.
Still to answer, from the code: `owner.signoff` refuses only when the card's own tickets are ready or stopped. Tickets on another card carry on untouched. A message still waiting doesn't stop a sign-off, and the lead still answers on the thread while the card stays done. An open plan doesn't stop one either. Approving a plan after sign-off sets the card back to ready, its tickets run, and `due_reviews` skips a signed-off card, so that work gets no review.
Still open, the gap for F211's plan: an approved plan whose ticket sits on another card fires neither F211 warning. The only trace is the 'queued f164-07' line on the thread. Suggested fix: one line by Sign off and on the done card's page naming that ticket, its card and whether it has run, added to f211-03 and its mock-up.

## Expected outcome
A plan can't quietly end with its card, and a thread the owner closed stays closed. Two open discussions that repeat each other merge; an idea joins a card already planned only when that plan covers it, and never joins a thread the owner closed. Sign off says when a plan is still open and offers to keep it as a new card. Archive stays one press meaning "I don't want this": it only names what it closes.

## What happened (from the code and the database, 2026-11-04)
- **F51, one box per card:** F176's note was merged into F51 on 2026-10-27, after F51's plan was approved, because the merge rule keeps "the more advanced card". The owner signed F51 off on 10-29 at 00:51 with a message still waiting for the lead. The lead's replan for F176 arrived at 00:54, on a card already done. Archived at 09:47. The owner planted it again as F210.
- **F82, Text boxes grow:** the lead added f82-02 on 10-28. The owner signed off on 10-29 at 01:02, and nothing on the button mentioned the open plan. Archived at 09:47. The owner planted it again as F213.
- **F195, the context window:** archived on 11-02 with its plan open. The card is still an idea, so nothing is gone. The owner planted the plan again as F212.
- **F212 into F195 (2026-11-04):** the lead merged F212 into F195, whose thread the owner had closed on 11-02. The note reopened that thread and cost a reply, and the owner closed it again at 08:04. The lead's list of threads doesn't say which are closed, so it couldn't have known.
- **F218 into F209 (2026-11-04):** F209's plan was already approved, and its D2 already covers F218's note (a developer's card stays blue in the developer's view). This is the exception worth keeping.
- **F149, Retire the backlog file (signed off 2026-11-05):** the owner asked for more work on 11-04, accepted ADR 43 and approved its plan, whose one ticket, f164-07, sits on F164 because it waits for F164's plates. At sign-off the next morning nothing said so, and the owner couldn't remember whether more work had been asked for (F223). No open plan and no waiting message: D3's plate would stay silent too.
- **What closing means (the owner, 2026-11-04):** "If I close a planning thread it is usually because I don't want the plan to be done."
- **Today:** Sign off and the thread's Archive say nothing about an open plan. Such a thread goes to "Set aside" on Planning, but on a done card there is no way forward: `_approve_plan` would run `planner.ready_card` and set a done card back to ready. No plan has ever been approved on a signed-off card, so refusing that breaks nothing.

## Done when
- Two open discussions that repeat each other merge as today.
- A new idea whose subject a planned card's tickets don't cover stays its own card; a merge into a planned card names in its key points the tickets that already cover the idea.
- A merge with a thread the owner closed isn't applied on its own: the lead's prompt says which threads are closed, and the runner holds such a merge for the owner.
- `/planning/<key>` of a ripe card with an open plan: a plate above Sign off names the plan, with "Keep it as a new card" beside Sign off. A message still waiting for the lead is said too.
- The same plate on the card's milestone page.
- A card with an approved ticket on another card, not yet done: its review says so in one line by Sign off, on the thread page and the milestone page, naming the ticket and that card. On the thread page the line stays after sign-off until the ticket is done.
- An open thread with an open plan: Archive looks and works as today, with one line naming the plan it closes. On a done card a plain "Keep it as a new card" sits beside it; on any other card there is no Keep.
- A thread already archived shows none of this.
- A press on Keep shows at once, dashed orange, "Keeping as a new card at the runner's next pick". At the pick: a new idea card holds the plan's title, its key points and where its drafts are, the lead is queued on it, the old thread says where the plan went and links there, the old proposals read "Kept as a new card".
- A done card's proposal page has "Keep it as a new card" in place of Approve plan, and the runner refuses an approval on a done card, saying why.
- To test: on a ripe card with an open plan press Keep, then Sign off. The new card appears on the desk with the lead's reply queued, its plan comes for approval, and the old card signs off with nothing left open.

## Decisions
- **D1 Merging into a planned card (the planner's brief, `PLANNER` and `PLANNER_GENERAL`):** "Keep the more advanced card" holds only when that card has no approved plan yet, or its plan already covers the idea. A card has an approved plan once it is ready, building or past. To merge into one, the merge's key points name the tickets that cover the idea. If none does, no merge: the idea stays its own card, and a point says which card it sits beside. Two open discussions, with no approved plan on either, merge as they do today (the owner, 2026-11-04). The runner doesn't check "covers", because it can't tell what a plan covers; the Sign off plate is the net when the lead gets it wrong.
- **D2 No drafts on a done card (the same brief):** on a card whose doc says done, the lead draws no plan, replan, ADR or mock-up. A request for new work there is answered with the words ready to plant, as a planted idea of its own. Named in `runner/instructions/lead.md` under "Planning room".
- **D11 A thread the owner closed stays closed:** the lead doesn't merge with it, doesn't bring its plan up again and doesn't reuse its drafts unless the owner asks. `planner.prompt` takes the threads the owner closed (`archived_why` is `BY_YOU`) and names them apart, because today the lead gets one flat list. An idea repeating a closed thread stays its own card, and a point says the owner closed that one. `auto_merge` holds a merge when either thread is closed that way: it returns why, and the merge waits for the owner. This part the runner can check, so it does. A thread archived as `approved` isn't closed in this sense: D1's "covers" still applies to it.
- **D12 Work approved here that sits on another card (F223):** a plan on one card can queue a ticket of another, as F149's did. The list comes from what is already stored: each worked `approve_plan` request of the thread has the tickets it queued in its `result`, and those named for another card and not yet done are the line. No new column. It reads "Also asked for here, still to come: <ticket>, on <card and title>. Signing off doesn't touch it." It's information, not a warning: no plate, no button, no status colour, and Sign off stays yellow. Signing off has no effect on that ticket. One function, `work_elsewhere` in `factory_dashboard/planning.py`.
- **D3 "A plan is still open" is one rule:** the latest proposal list of the card's thread (`_latest`) has an `adr`, `mockup`, `plan` or `replan` (`planner.DRAFTED`) whose state is open or on its way. One function, `open_plan` in `factory_dashboard/planning.py`, for every page. A seed or a merge doesn't count: only drafts wait on a branch.
- **D4 Sign off warns, Archive only names (revised 2026-11-04):**
  - Sign off isn't a no: the owner is signing the work, not the plan. So a ripe card gets the plate and the yellow Keep (D7).
  - Archive is a no. The button stays "Archive", plain, one press. One line beside it reads "Also closes the open plan: <title>. It won't be built unless you reply here."
  - On a done card a plain Keep sits beside it, for the F51 and F82 kind of plan, closed without being seen. On any other card the plan stays where it is, so there is no Keep.
  - A thread already archived shows nothing: it was answered.
- **D5 Keep plants, the lead drafts again; nothing moves between branches.** A new request kind, `keep_plan` (subject: the thread), goes through `_plant` as "Plant and ask the lead" does:
  - Area: the old card's, so a product card's plan stays a product card. Since F171, a plant without an area takes the project's area (`planner.project_area`), and that could differ.
  - Title: the plan proposal's title, else the first draft's, without its leading "F51: " or "F51, ".
  - Notes: "Kept from F51, <its title>, whose plan was still open when it closed.", the proposals' key points as `planner.seed_words` writes them, then "Drafts are on plan/f51: check them against main before reusing them." These are the notes the owner wrote by hand on F210, F212 and F213.
  - Why not move the files: tickets carry the card's key in their name and their `depends_on`, and old branches lag main. plan/f51 and plan/f82 start before `.factory` became `.softfield`, so their diff against main runs to about 70 KB. Each kept plan costs one lead reply.
  - The old branch stays, as it does today.
- **D6 What Keep leaves behind:** the drafts' state becomes `kept` (`planner.KEPT`, "Kept as a new card"), settled like approved or rejected. The old thread gets a lead line, "Kept as F215: /planning/f215". If every proposal of the list is settled and the thread isn't archived, it archives with the reason `approved`; a thread under Set aside moves to Archived. Keep does not sign off: that stays the owner's own press, and the two can go in either order.
- **D7 Sign off is not blocked.** The plate says it, Keep becomes the yellow button and Sign off turns plain, but one press still signs off. If the plan is left open, the card goes on showing it on the desk, and Keep is there on the thread and on the proposal page.
- **D8 A done card's plan can't be approved:** `_approve_plan` refuses first, before `loop.catch_up_plan` and F139's clash check, and also refuses F224's Approve first. On that page the clash line ("Refresh against main") and Approve first give way to Keep. Then it refuses before merging when the branch has drafts and the card's doc on main is done, with "F51 is signed off: keep its plan as a new card". A merge-only approval still works. The proposal page shows Keep in place of Approve plan; Send back and Reject stay.
- **D9 The proposal page's and the board's Set aside stay as they are:** the owner presses them with the plan in front of them, or on a card that stays, and the page already says "with its drafts kept". Archive deletes nothing either: Reject is what removes drafts. The Set aside list on Planning stays too, though a thread's Archive also lands there.
- **D10 The picture:** `.softfield/cards/f211-mockup/open-plan.html`. The plate is `.panel.needs`, which already exists: no new token.

## Before and after
- `/planning/f82`
- `/milestones/f82-the-plant-idea-text-box-is`
- `/planning/f82/proposals/plan-f82-stuck`
- `/planning/f140`
- `/planning/f149`

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | merge-only-what-plan-covers | lead | 4 | | D1, D2, D11: the planner's brief, the closed threads in its prompt, the hold in `auto_merge`, and `lead.md` |
| 02 | keep-plan-as-new-card | lead | 6 | | D3 (the state), D5, D6, D8: the runner's side |
| 03 | open-plan-on-thread-page | developer | 5 | 02 | D3, D4, D7: the plate on the thread and milestone pages |
| 04 | keep-on-proposal-page | developer | 2 | 03 | D8's button |
| 05 | work-on-another-card | developer | 3 | 03 | D12: the line by Sign off |

## Later
- Delete a kept plan's old branch once the new card's plan is approved.
- A thread's Archive listed under Archived rather than Set aside, if closed threads clutter that list.
- "Remove seed" on an idea card with an open plan says its notes go, and not the plan.
