# Milestone F159: A set-aside ticket says it won't run, with a Queue it button on its page

> **State:** done · **Priority:** 3 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-23. Base: git tag `f159-there-s-a-bug-set-aside-start`. Report: [`.softfield/reviews/f159-there-s-a-bug-set-aside.md`](../reviews/f159-there-s-a-bug-set-aside.md).
> Planted by the owner on 2026-10-20.

## Notes
there's a bug set aside, what am i supposed to do about it? i currently can't do anything with that

## What we know (2026-10-20)
- The card is `bug-03-roadmap-items-to-seeds`, #1 in the board's Seed column. It is no bug: it turns the old roadmap's open items into seed cards, asked for by the owner on 2026-10-13, and filed under `bugs` because that is the only key a ticket outside a card can use. The lead wrote it straight into `.softfield/tasks/later/` (commit `44fa7a4`) and never asked the owner to queue it, so it has waited a week. None of the roadmap's items has become a card since.
- A set-aside ticket never runs until a `queue` request moves it to `.softfield/tasks/ready/` (`move_to_ready`, `runner/loop.py`). The only button that sends one is in the Tickets page's Set aside table; the board card opens `/tickets/<id>`, which shows the raw file, the state `later` and no button.
- F152 (A done card says where its review is, and set aside says it won't run) answers the same question for a card's set-aside tickets, which the owner has nothing to do with; F159 is the case where the owner does decide.

## Outcome
A set-aside ticket says, where the owner meets it, that it won't run until they queue it, and gives them the button; bug-03 runs.

## Done when
- open bug-03's card from the board on a phone: its page starts with "Set aside: this ticket won't run until you queue it" and a "Queue it" button; pressed, it shows on its way at once
- the page reads Goal and Done when as text, no front matter
- the board card reads "Set aside, won't run until you queue it ›"

## Decisions
- **D1. The button is the existing `queue` request,** posted as the Tickets page's Queue button does: nothing in the runner changes.
- **D2. The set-aside panel comes first on the ticket's page,** a plate with the hazard stripe, as `.softfield/cards/f159-mockup/set-aside-ticket.html` draws it; "later" reads "set aside" everywhere on the page.
- **D3. The ticket page reads its body:** Goal and Done when as text, Context folded, the front matter gone.
- **D4. No "throw away" button for now:** a set-aside ticket costs nothing while it waits, and removing one is runner code (a new request). Asked on the thread.
- **D5. bug-03 is refreshed and queued with this plan** (approving the plan queues every ticket the branch changed in `.softfield/tasks/later/`), at its priority 90.

## Tickets
- f159-01-set-aside-ticket-page (developer): D1–D3
- bug-03-roadmap-items-to-seeds (lead, already written; refreshed): D5
