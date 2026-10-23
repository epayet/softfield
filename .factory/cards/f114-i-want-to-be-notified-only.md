# Milestone F114: Notifications only for what needs me, one per bundle, opening its page

> **State:** done · **Priority:** 2 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-23. Base: git tag `f114-i-want-to-be-notified-only-start`. Report: [`.factory/reviews/f114-i-want-to-be-notified-only.md`](../reviews/f114-i-want-to-be-notified-only.md).
> Planted by the owner on 2026-10-13.

## Notes
I want to be notified only for things that need my attention: a new feature to sign off, an answer to my question/threads, a new proposal. Is this currently the case? I don't want to be notified every time a ticket is finished for example. When mockups/proposals/adrs come in bundled, I just need one notification

## Expected outcome
- A notification says what it is about, with the card's own title, and a tap opens the page where the owner answers it.
- Whatever arrives together is one notification.
- Nothing notifies that doesn't need the owner. A finished ticket never does (it doesn't today either).

## Done when
- f114-01 and f114-02 merged.
- To test, with any dashboard page open (the Overview or the Board, not only Planning) and notifications allowed: send a message on a card and wait for the lead's reply. One notification comes, named after the card, saying how many proposals it carries; tapping it opens that card's page.
- While tickets merge, no notification comes.

## What happens today (from the code, 2026-10-13)
- **What notifies:** `notify.js` compares, every 5 seconds on an open page, the open "Needs you" items (`_live_context` in `factory_dashboard/overview.py`, its `notify`) with what it saw last, and shows one notification per new item, plus one when all the work is done. The items are the runner's stored rows (`owner_items`) and two things the dashboard sees itself.
- **A finished ticket:** nothing stores an item for it, so nothing notifies.
- **A lead's reply:** one item per thread (`run_planner` in `runner/loop.py`), so one notification per reply, whatever it carries (a mock-up, a plan and an ADR together are one).
- **A sign-off:** one item per card, stored at the review's verdict (`verdict` in `runner/owner.py`).
- **The others:** a decision (an ADR from an escalation), a blocked or escalated ticket, a review that stopped, Claude's reserve or 5-hour share asking for a choice, the runner's heartbeat stopped mid-job, tickets waiting with no runner, and all the work done.
- **Gap 1, the words:** every notification is titled "Needs you". A sign-off's body is its test steps or the review's path, without the card's name; a reply's says "F114", not the title.
- **Gap 2, the tap:** it brings forward whichever dashboard page is open, or opens the Overview; never the page concerned.
- **Gap 3, several at once:** a review's verdict can open three items in one go (a decision, a blocked ticket, the review's stop): three notifications.
- **Any dashboard page will do:** the Overview, the Board, Planning or any other. Every page loads `notify.js` and the 5-second look (`factory_dashboard/templates/base.html`), and what was seen is kept per browser, so two open tabs don't notify twice.
- **Gap 4, only while some dashboard page is open:** a phone freezes a background page after a few minutes ([ADR 26](../adr/26-notifications-on-the-home-wifi.md)), and what arrived while every page was closed is never notified: it only shows on the desk. Not in this card (see "Not in this milestone").

## Decisions
- **D1: the dashboard words each notification, from the item's kind and its card.** A new function `notices` in `factory_dashboard/overview.py` gives, for each open item, a title, a body and a link. Nothing changes in `runner/`. `#live-facts` carries them in a new attribute, `data-notices` (id → `{"title", "body", "link"}`), beside `data-needs`, which f114-02 removes once `notify.js` no longer reads it.

  | What | Title | Body | A tap opens |
  |---|---|---|---|
  | The lead replied (`planning`) | The lead replied: *card title* | "2 proposals to review", or "Your answer is wanted" | the card's thread, `/planning/<card>` |
  | The lead's job failed (`planning`) | The lead couldn't answer: *card title* | Send your message again | the card's thread |
  | A sign-off (`signoff`) | Ready for your sign-off: *card title* | Reviewed, waits for you | `/planning/<card>` |
  | A review that stopped (`review-stop`) | The review stopped: *card title* | the stored reason | `/planning/<card>` |
  | A decision (`adr`) | A decision for you | the stored question | the Overview |
  | A blocked or escalated ticket | A ticket is blocked | the stored words | the Overview |
  | Claude's reserve, the 5-hour share | Claude's allowance: your choice | the stored words | the Overview |
  | The runner stopped mid-job | The runner stopped | as today | the Overview |
  | Tickets wait, no runner | The runner is idle | "73 tickets waiting" | the Overview |
  | All the work done | All work done | as today | the Overview |

  The thread of the general conversation is titled "General", as on the desk (`_thread_title` in `factory_dashboard/planning.py`).
- **D2: one notification per look.** When several new items appear in the same 5-second look, `notify.js` shows one: with one item, its own title and body; with more, "3 things need you", their titles one per line, and a tap opens the desk (`/planning`).
- **D3: the tap goes to the page.** The link travels in the notification's `data`. The service worker's scope is `/static/`, so it controls no page and can't navigate one: it focuses an open dashboard page and posts it the link (`postMessage`), and the page goes there; with no page open it opens the link itself. Without a service worker, the notification's own click does the same in the page.
- **D4: what notifies stays the list above.** Each one stops work or waits for the owner. All the work done stays: an empty queue is the moment to plan more.
- **D5: a blocked ticket notifies twice once F106 has landed,** at the block and again when the lead's look arrives with a fix. Kept: the look can wait hours for Claude's allowance, and the owner should know at once that tickets are paused behind it.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | notices-say-what-and-where | D | 4 | – | D1: `notices`, and `data-notices` on `#live-facts` |
| 02 | one-notification-opens-its-page | D | 5 | 01, f95-01, f12-05 | D2, D3: `notify.js` and `sw.js`; `data-needs` goes |

02 waits for f95-01 and f12-05: both have a "Done when" on `data-needs` or on the title "Needs you", which 02 changes.

No mock-up: no dashboard page changes, only the phone's and the desktop's own notifications; D1's table is their words.

## Not in this milestone
- **Notifications with every dashboard page closed** (gap 4): the roadmap has it ("Push notifications to a closed page"). It needs either an ntfy server on this machine and its app on the phone, or https with a certificate installed on each device (ADR 26, B), so it starts as an ADR.
