---
id: f110-03-sprouting-is-a-live-conversation
milestone: f110-i-don-t-understand-why-there
difficulty: 3
depends_on: [f110-02-ripe-card-leads-to-sign-off]
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
On the board a card is sprouting only while its conversation is open, and it says who the conversation waits for; an idea whose conversation is archived is a seed again.

### Context
Read `docs/milestones/f110-i-don-t-understand-why-there.md` (D4). In `factory_dashboard/board.py`: `_milestone_stage` (rule 2) and, in `_cards`, the `threads` query and how a bug's `note` is set. In `factory_dashboard/templates/board.html`: the `card_link` macro, where `c.note` shows. Follow `test_an_idea_is_a_seed_and_sprouting_once_a_thread_is_about_it` in `tests/factory_dashboard/test_board.py`.
- The owner (2026-10-13): "there are tickets on the board that are sprouting but their conversation are archived or have nothing going on". Today `threads` holds every thread's card, archived or not, so an idea that was ever talked about sprouts for good: F11, F15, F18 and F105 were sprouting with archived conversations, F27 and F54 with a reply unanswered for days.
- `threads` takes only the threads that are not archived (`archived IS NULL`). An idea whose thread is archived is a seed, as one with no thread. A card whose state is `planning` still sprouts.
- A sprouting card's `note` says who it waits for, from its thread's latest message: the lead wrote last, `waits for your answer since 9 Oct` (the day and short month of that message, local time, from `now`'s timezone); the owner wrote last, `the lead is answering`. No thread or no message (state `planning` alone): no note.
- The note shows on the card as a bug's does. Other stages' cards are unchanged.

### Done when
- an idea whose thread is archived is in the seed column, not in sprouting
- an idea with an open thread whose latest message is the lead's is sprouting, and its card reads "waits for your answer since" with that message's day
- the same with the owner's message last reads "the lead is answering"
- a card in state `planning` with no thread is sprouting with no note
- a planted, a growing and a ripe card show neither phrase
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
