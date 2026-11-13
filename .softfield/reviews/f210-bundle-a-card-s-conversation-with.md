# F210 review: one box per card on the desk, and one reading path through its proposals

- **Status:** done, signed off by the owner on 2026-11-13.

## Sign-off sheet

### 1. What changed
- **One box per card on the desk.** "Proposals to review" is gone. In "Your answers wanted", a card's conversation and its open proposals are one box, counted once. The box links to the conversation, and each proposal is a small link of its own inside the box, with its key points. The ADR always comes first, then the mock-up, then the plan, whatever order the lead listed them in. A proposal already sent on its way is dashed, and the box stays counted until every proposal is. When your message waits for the lead, the whole box is dashed and not counted. A card ripe for sign-off keeps its proposals in its To sign off row.
- **Next walks a card before moving on.** From a card's conversation, Next names the step: "Next: mock-up", then "Next: plan", then just "Next" to the next card. Previous names it too ("‹ Mock-up"). "3 of 6 waiting for you" counts cards, so the number stays the same inside a card.
- **"This card's steps" on every page of a card.** One strip reads Conversation → ADR → Mock-up → Plan, each step with its state and key points. On the conversation it sits under the lead's latest reply, above Send, on a phone too, and replaces the old side panel. On a proposal's page it replaces the tabs.
- **A comment you typed waits.** Comments typed on a conversation's points or a proposal's points stay in that browser tab while you visit the card's other steps. They come back in their open boxes, and the strip says "1 comment not sent" in orange on the step that holds them. Sending clears them. A failed send keeps them. If the lead replies again, comments typed under the old reply are dropped.
- **Approve plan wakes up.** A plan page left open while its ADR waits now enables Approve plan and Approve first by itself, within about 5 seconds of you pressing Accept ADR, and says "ADR N's acceptance is on its way". The review fixed this part before you saw it: as merged, the page's poll removed both buttons instead of enabling them.
- The old "What to do now" ticket (f31-04) is deleted, as the card decided (D6).

The pictures show F133's box with its plan link, and F210's own thread with the strip under the reply. Matches the mock-up, with one small difference: the mock-up put the card's key (F71) before the box's title, and the desk shows the title only, as its other rows do. On after-phone-2 the reply box sits mid-page: it's the phone's sticky Send bar, caught where the full-page picture was taken, not a layout bug.

### 2. How to test it yourself
1. On your phone, open Planning. Each card the lead answered is one box under "Your answers wanted", with its proposals as small links inside it. The tab's number counts each box once.
2. Tap a box that has a mock-up and a plan. Under the lead's reply, above Send, "This card's steps" reads Conversation, Mock-up, Plan. At the top, Next says "Next: mock-up".
3. Open a point's "Comment…" and type a few words. Tap Mock-up in the strip. The strip's Conversation step says "1 comment not sent" in orange. Tap Conversation: your words are back in their open box.
4. Press Next twice more. It goes to the plan ("Next: plan"), then to the next card ("Next"). The "N of M" number stays the same until you leave the card.
5. On a card with an ADR and a plan: open the plan page (Approve plan is greyed out), then press Accept ADR on the ADR's page in another tab. Within about 5 seconds the plan page enables Approve plan by itself and says the acceptance is on its way.
6. Send your comments on a conversation, then reload: nothing comes back.

### 3. Left for later
- Nothing set aside as a ticket. Three nits are noted below (F4 to F6), each too small for a run.

### 4. Decisions waiting for you
- None.

### 5. How the work went
- 2026-11-10 ([session](../sessions/2026-11-10-1827.md)): f210-02 (the strip). The local model failed it three times (3 × 20 min, one lead direction between), then Claude finished it in 27 min.
- 2026-11-11 ([session](../sessions/2026-11-11-0833.md)): f210-03 (typed comments). The local model merged it on attempt 1 in 28 min, but it added only a script, with no test and no markup for it to act on. The checkpoint on 2026-11-12 caught it and wrote f210-05.
- 2026-11-12 ([session](../sessions/2026-11-12-0628.md)): f210-05, the repair. The local model failed it three times (two 80-min timeouts, a 37-min failure, one direction), then Claude finished it in 16 min. f210-01 (the desk box and Next) was the lead's: 33 min of Claude.
- 2026-11-13 ([session](../sessions/2026-11-13-0046.md)): f210-04 (Approve plan wakes up). The local model merged it on attempt 2 after 43 min, but its poll removed the buttons it was meant to enable, and its tests couldn't fail. Fixed in this review.
- Lessons:
  - **A live-update test must change the data after the page is open.** f210-04's test added the request before loading the page, so it tested the first draw, which f51-02 already built. That is how a broken poll passed every gate. The new test opens the page, then accepts the ADR, and it failed on the merged code.
  - **A script with no test is dead weight.** f210-03 passed its gates because nothing ran its code. The checkpoint's repair ticket (05) named every gap as a fact, which is what let Claude finish it quickly.
  - **Two of the four local tickets went to Claude after 3 attempts each,** about 4.6 hours of local time in failures and timeouts. Both were browser-script work (htmx swaps, sessionStorage), the area where Qwen does worst here.

### 6. What next
- **Product:** product work is on hold; nothing proposed.
- **Factory:**
  - When a ticket's Done when says "without a reload" or "within the poll", the planner should write the browser test's shape into the ticket: open the page first, then change the data. The local model then can't satisfy it with a first-draw test.
  - Route browser-script tickets (htmx swaps, storage, polling) above difficulty 3 to the lead from the start. On F210 both went to Claude anyway, after about 4 hours of local attempts.

### 7. What clogged the factory line
- **About 4.6 hours of local attempts that didn't merge** (from `jobs`): f210-02's three 20-min failures (2026-11-10 18:43–23:01), f210-05's two timeouts and one failure (2026-11-12 06:28–09:45, 196 min), f210-04's first 20-min failure. Fix: send browser-script tickets to the lead from the start (above).
- **About 18 hours with dead code on main:** f210-03 merged on 2026-11-11 at 09:03, and the checkpoint that caught it ran on 2026-11-12 at 03:38, after a day of other milestones' reviews. Fix: a ticket whose Done when names browser behaviour lists a browser test in `tests:` (the planner's job), so the gates catch it instead.
- **Tickets waiting on one another:** f210-01 waited for f75-01 and f108-01 from other cards, and f210-04 waited for f224-02 and f210-05. The milestone spanned 2026-11-10 to 2026-11-13. The line wasn't idle: other cards ran in the gaps. No waits for limits and no stops for the owner.

## What was built
- **f210-02 one-strip-of-steps** (`ed2138279`, Claude after 3 local failures): `reading_order` in `planning.py` (D8); `_partials/card_steps.html`; `Proposal.points` and `.step`; the strip replaces `#proposals` on the thread and `#proposal-tabs` on the review page. The conversation's stamp now changes with a proposal's state, so F100's "being revised" redraws.
- **f210-03 typed-comments-wait** (`3f4edd859`, local): a sessionStorage block in `deck.js` that nothing called and nothing tested (the checkpoint's finding).
- **f210-05 typed-comments-wait-for-real** (`4fe049f0f`, Claude after 3 local failures): rewrote that block. One stored shape `{latest, comments}` per path; counts redrawn from storage; `sentComments()` called only on a successful send; `data-latest` on `#conversation-stamp`; the proposal page reopens its boxes and runs `update()` on `comments-restored`. Three browser tests per page.
- **f210-01 one-box-per-card** (`fd560373b`, lead): `_listed`, `_general_items` and `_with_proposals` in `planning.py`; `Part` in `coming.py`; `.desk-box` in `dashboard.css`; `desk_trail` walks boxes and their parts and names the steps; "Proposals to review" leaves `desk()`; f31-04 deleted.
- **f210-04 approve-plan-wakes-up** (`2fe51b511`, local, attempt 2), fixed by this review (F1 to F3).

## Findings and resolutions
| id | severity | route | what | resolution |
|---|---|---|---|---|
| F1 | blocking | claude | f210-04's poll selected `#polling-fold`, which the server stops drawing once the ADR's acceptance is on its way, so the swap removed Approve plan and Approve first | Fixed: `#approval` is always drawn (`display: contents`, so the phone row keeps laying out its buttons) and carries the poll only while the ADR waits. The redrawn box has no poll, so it stops |
| F2 | should-fix | claude | f210-04's three tests couldn't fail: the request was added before the page opened, the comment test listed no ADR, and the third only checked that the wrapper was visible | Replaced: `test_the_plans_approval_polls_only_while_the_adr_waits`; `test_approve_plan_wakes_up_once_accept_adr_is_pressed` (opens the page, then accepts; failed on the merged code); `test_a_comment_typed_keeps_approve_hidden_across_the_approval_redraw` |
| F3 | should-fix | claude | The poll closed an open Approve first fold every 5 s; `update()` never ran after a swap; the `pageshow` handler sat on `document`, where it never fires, and didn't ask the page again | Fixed: the fold's state is kept across the swap, `update()` runs on `htmx:load` of the new box, and a page shown from the back-forward cache while the ADR waited asks once more |
| F4 | nit | report | "Nothing becomes a ticket until you approve it." sits flush left under the strip, against the reply box's corner tick (after-wide-2) | Noted only |
| F5 | nit | report | The mock-up's box led with the card key (F71). The built box shows the title only, like the other desk rows | Noted only: no Done when line asked for it |
| F6 | nit | report | `_with_proposals` puts a card with no conversation row whose proposals are all on their way before the dashed answers, not among them | Noted only: rare, and the box is still dashed and not counted |

Checkpoint finding `f209-…-C2118-1` (typed-comments feature is dead code, untested): **confirmed**. f210-05 was written for it and fixed it. The checkpoint missed nothing of mine: f210-04 merged after it ran.

Score: **7/10.** The desk box, the strip, Next and the typed comments are solid and well tested (01, 02 and 05 by Claude). Both of the local model's merges needed rescuing: 03 did nothing, and 04 broke the page it was meant to fix.

## Tests read
- `test_planning.py`: the F210 block covers every Done when line of 01: reading order, no-proposal box, dashed when waiting for the lead, one part on its way, Overview equals the Planning tab, the ripe row (D9), no inline styles. Existing desk tests were moved from the "proposals" group to `_box` with exact words, not loosened.
- `test_proposal.py`, `test_coming.py`: their edits follow the box (`_box`, `_counted` per card) and keep exact assertions. f210-04's tests were replaced (F2).
- `test_thread.py`: the strip's order, the 390-px placement, "being revised" without a reload, no strip without proposals, and f210-05's three browser tests (waits across steps and doesn't grow on redraws, an older reply's comment dropped, failed send keeps it).

No French: this is factory work only.

## Workflow observations
- The checkpoint earned its cost here: its repair ticket listed six concrete facts about what didn't work. That turned an unworkable script into a 16-min Claude fix.
- The gates trust "the listed tests fail without the change", but the runner doesn't check it. f210-04's tests passed with or without most of the change. Running a ticket's new tests against the base commit would have caught it.
- The planner sized 02 to 05 for the local model because they "follow `#proposal-tabs` and `#live-desk`". Following a pattern in a template held for 02's markup, but not for scripts that keep state across htmx swaps.

<!-- runner report -->
<!-- /runner report -->
