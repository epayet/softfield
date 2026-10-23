# Milestone F108: Desk boxes say when: proposals and sign-offs show their time too

> **State:** ready · **Priority:** 10 · **Area:** factory
> Planted by the owner on 2026-10-13.

## Notes
In 'your answers wanted', I see when the lead replied (2 minutes ago for example). I'd like to see something similar for the other stuff like proposals (updated 3 minutes ago for example)

## What the desk says today (read from the code, 2026-10-13)
All in `factory_dashboard/planning.py`; each box has a title and one line of words under it.
- "Your answers wanted" (`_answers_wanted`): "the lead replied 3 min ago". Archived (`archived`): "archived 2 h ago".
- "Proposals to review" (`_open_proposals`): "5 key points", no time. The query already reads the time of the lead's reply that lists the proposal (`m.at`) and only uses it to find the owner's later requests.
- "Finished, to talk through" (`_ripe`; "To sign off" after F63): "reviewed · waits for your sign-off", no time. The review is a finished job of role `review` with the milestone's id in `jobs`, so its end is stored.
- "Seeds, not asked about yet" (`_seeds`): no time, and none is stored: the card's doc holds only the day it was planted, and the database doesn't hold that.
- "Didn't go through" (`_refused`): the runner's reason, no time; the request's `done` is stored.

## Outcome
- A proposal's box says when the lead proposed it: "5 key points · proposed 3 min ago".
- A card to sign off says when it was reviewed: "reviewed 2 h ago · waits for your sign-off".
- Times are written as everywhere else on the dashboard ("30 s", "3 min", "2 h").

## Decisions
- **D1 Words only.** The time joins the item's `words`; `DeskItem`, the template and the counts don't change. The Overview's Needs you reuses the same words, so it shows the time too.
- **D2 "proposed", not "updated".** The time is that of the lead's reply that lists the proposal. A later reply lists the whole set again, changed or not, so "updated" would claim a change that may not be there.
- **D3 A box on its way keeps its words.** A proposal the owner approved or rejected says "on its way · the runner applies it at its next pick", as today: what is coming matters more than when it was proposed.
- **D4 The sign-off's time is its review's end:** the latest finished job of role `review` for the milestone. With none (a review written in a terminal session), the words stay as today.
- **D5 Left out:** seeds (no time stored; a column for a day isn't worth it), "Didn't go through" (its line is the runner's reason; a time there needs the template) and F106's "Blocked tickets" (not built yet).

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | desk-says-when | D | 2 | f75-01, f51-01 | D1–D4 |

Follows `_answers_wanted`'s own line in the same file: a developer ticket. After f51-01 and the chain f63-01 → f74-01 → f75-01, which rewrite the same functions.

## Done when
- With a proposal waiting on `/planning`: its box reads "… key points · proposed N min ago", and the time grows on refresh.
- Approve it: the box turns dashed and reads "on its way · …", with no time.
- With a card to sign off: "reviewed N h ago · waits for your sign-off".
