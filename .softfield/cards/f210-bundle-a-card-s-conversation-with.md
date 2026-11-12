# Milestone F210: One box per card on the desk, and one reading path through its proposals

> **State:** ready · **Priority:** 1 · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-11-03.

## Notes
Bundle a card's conversation with its proposals in one box on the desk, so I read the latest discussion and then the ADR and plan without jumping between pages. Started as F176, merged into F51 and lost when F51 closed. Drafts are on plan/f51: f51-05-one-box-per-card, f51-06-approve-plan-wakes-up and the mock-up desk-cards.html. Check them against main before reusing them.

### From F214: Decide f31-04, "What to do now" (open proposals with their… (merged by the lead on 2026-11-04)
Decide f31-04, "What to do now" (open proposals with their buttons under the lead's latest reply), together with the F176 bundling card: build it as part of that or delete it.

## Outcome
Each card with something for the owner is one box on the desk, its proposals inside it. Inside a card, the conversation and its proposals are one row of steps, and Next walks through them, then goes to the next card. Picture: [`f210-mockup/one-box.html`](f210-mockup/one-box.html).

## What the code does today (read 2026-11-03)
- The desk on 2026-11-03: 31 items, of which 11 conversations and 11 proposals, and they are the same 11 cards.
- Next doesn't follow the reading order: `desk_trail` walks the desk's links in order, so F207's conversation is 14 of 30 and its plan 25 of 30.
- On a phone, the thread's `#proposals` aside comes last, under Archive.
- A comment typed on a point is lost when the page is left, which steps make more likely.

## Checked against main (2026-11-09)
- The desk again: 11 items, of which 5 conversations and 5 proposals, the same 5 cards (F71, F211, F191, F133, F65). The mock-up now draws this desk, and F211's card for the reading path.
- f81-04 redrew the Planning room from `dashboard.css` classes (`.desk-item`, `.desk-title`, `.desk-words`, `.parts`, `.group-head`), with no inline styles. The box follows those classes.
- f75-01 and f108-01 are still ready, so 01 still waits for them. f31-04 is still in `.softfield/tasks/later/`. No f210 ticket number is taken.
- Three other cards' tickets touch the same places; none is done, so nothing is dropped:
  - F65, Review rounds until you sign off: its replan's f65-06 (not yet approved) moves a ripe card's conversation into its To sign off row. 01 builds the box where the card's conversation is, whichever group, so the two agree.
  - F207, Every lead reply opens with In short: f207-02 puts a plate under the review page's header. The strip takes the tabs' place, above that plate.
  - F224, Approve first: f224-02 adds an Approve first fold beside `#primary`, disabled while the ADR waits. 04 now redraws both, and waits for f224-02.

## What changed from F51's drafts (plan/f51)
- f51-05's desk is kept, but it never touched the reading path, the part the owner asked for, and "the thread page doesn't change" is dropped.
- Its `desk_trail` would have broken: with the proposals gone from the desk, a proposal page is in no link, so it says Next is the first item.
- "Boxes with proposals first" goes: F185 D3, newer than the draft, wants the newest answer first.
- Its six dependencies shrink to two: f75-01 and f108-01. The others are on main.
- f51-06's swap would have drawn Approve back beside Send back while comments are typed: the page's script keeps the old `#primary`.

## Decisions
- **D1 One box per card.** `desk()` drops "Proposals to review"; "Your answers wanted" holds one item per card, built from its conversation item and its `_bundle` item. It keeps its place, right after To sign off (F185). Only this group changes.
  - The box links to the thread page; the words are the conversation's (or its dashed words), then the proposals' key points total, then "accept the ADR first" when `_bundle` says so.
  - Its proposals are links of their own inside the box (at least 32 px tall; the box's own link at least 44 px), in reading order (D8), each with its own key points, dashed when on its way.
  - Dashed and not counted when the conversation item is on its way, or every part is. A proposal alone on its way is dashed; the box stays counted.
  - Order: as F185 D3 and F84 D4 have it: answered newest first, then the dashed ones. A card with proposals and no conversation item comes after the answered ones, newest first.
  - The general thread's seeds and merges stay one item each in this group: each takes its own press (F51 D1). The general thread has no message today.
  - `_open_proposals` stays: the Overview's notices read it.
- **D2 Next walks the card.** `desk_trail` steps through each waiting item's link and its open parts' links, in desk order. "N of M waiting for you" counts boxes, so a proposal page shows its box's number. A step inside the card names where it goes ("Next: mock-up", "‹ Mock-up"); a step to another card says only "Next" or "Previous".
- **D3 One strip of steps.** A partial draws "This card's steps": Conversation, then each proposal of `_proposals` with its state and key points. It replaces the review's `#proposal-tabs` in the same place, and on the thread it replaces the `#proposals` aside and sits under the latest exchange, above the reply box. No buttons in it.
- **D4 Buttons stay on the review page.** Approving needs the ADR-first rule, the comments to Send back and the plan's changes, all on that page. A second set of buttons would have to repeat them.
- **D5 A typed comment waits.** Comments typed on either page stay in that browser tab (`sessionStorage`, per page), come back on return, and go once sent. The strip says "2 comments not sent" on the step that holds them.
- **D6 f31-04 goes.** Its proposals under the reply are D3, without buttons (D4). Its points drawn by outcome are dropped: every point already has its action line, and F67, Key points by kind, does this for proposals. Its links on `F22` are built (F37). f210-01 deletes the ticket.
- **D7 Approve plan wakes up.** f51-06's fix: while the plan waits for an ADR, `#primary` and F224's Approve first fold poll their page, without losing comments being typed.
- **D8 One reading order (the owner, 2026-11-04: "conversation for context, then mock up to see result, then verify the plan").** Every card's proposals read in the same order, whatever order the lead listed them: ADR, mock-up, plan or replan, merge, seed; same kinds stay as listed. One function, `reading_order` in `factory_dashboard/planning.py`, gives it to the desk's box, the strip and Next. The ADR stays first: it is settled first, and the plan is built on it. Today's lists vary: F207's has the plan first, F197's the mock-up.
- **D9 The box goes where the conversation is (2026-11-09).** A card's proposals join the row that holds its conversation. Today that is always Your answers wanted; once F65's f65-06 moves a ripe card's conversation into To sign off, that row takes its proposals, so a card stays one row.
- **Left out:** a blocked ticket with the lead's fix stays in Blocked tickets beside its box: its page and presses differ.

## Before and after
- `/planning`
- `/planning/f210`

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | one-box-per-card | L | 5 | f75-01, f108-01, 02 | D1, D2, D6, D8 on the desk, D9 |
| 02 | one-strip-of-steps | D | 4 | – | D3, D4, D8's function |
| 03 | typed-comments-wait | D | 3 | 02 | D5 |
| 04 | approve-plan-wakes-up | D | 2 | f224-02 | D7 |

01 changes every desk count and its many tests, so it's the lead's. 02 to 04 are in templates and a script and follow `#proposal-tabs` and `#live-desk`. 02 and 03 stay runnable under a Claude limit, since neither waits for 01.

## Done when
- A card with a reply, a plan and a mock-up: one box, counted once, its two proposals as links. The desk has no "Proposals to review".
- From a card's conversation, Next goes to its mock-up, then its plan, then the next card, whatever order the lead listed them in. The number doesn't change inside a card.
- On a phone, the steps sit under the reply, above Send.
- Comments typed on a conversation are still there after visiting its mock-up, and the strip says so.
- A plan page left open while the ADR's acceptance goes in enables Approve plan by itself.
