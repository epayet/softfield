# Milestone F30: on conversations, i want to the latest answer first so that i don't have to scroll

> **Status: done.** Signed off by the owner on 2026-10-16. Base: git tag `f30-on-conversations-i-want-to-the-start`. Report: [`.factory/reviews/f30-on-conversations-i-want-to-the.md`](../reviews/f30-on-conversations-i-want-to-the.md).
> Planted by the owner on 2026-10-07.

## Notes
(none)

## Outcome
- A card's thread (`/planning/<card>`) opens on the lead's latest answer, at the top, above the fold on a phone: no scrolling to reach it.
- Send sits right under that answer's points, where the owner comments on them.
- The older messages are folded under "Earlier in this thread (N)", newest first; one tap opens them.

## Decisions
- **D1 Top to bottom:**
  1. when a message waits for the lead: "Next for the lead · …" and the owner's waiting messages (dashed orange), newest first;
  2. the lead's latest message, with its points and Comment…;
  3. Send (when nothing waits);
  4. "Earlier in this thread (N)", a closed `<details>` holding every older message, newest first.

  With no lead message yet, the owner's messages show open, newest first, and there is no Earlier.
- **D2 Same data, same page:** only `factory_dashboard/templates/thread.html` and the order of `messages` in `thread_page` change. The re-fetch of `#conversation` after Send (f6-21) still redraws all of it, so a sent message shows at the top at once.
- **D3 Only the thread page:** the proposal review page and the desk keep their order; they aren't conversations.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | thread-latest-first | D | 3 | – | D1, D2 |

## Done when
- On a phone, open a thread with several exchanges: the lead's latest answer and Send are on the first screen; Earlier opens the older messages, newest first.
- Send a reply: it shows at the top, dashed orange, without a reload.
