# Milestone F37: Every number the lead writes says what it is, and links to it

> **State:** ready · **Priority:** 90 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
in planning mode it tends to be lots of mentions of F numbers, like F22 or F53, i don't know what these are these are not helpful

either give them names, or link to them or something? perhaps a note for the lead on writing styles?

On 2026-10-26: I prefer small summaries next to the number whenever mentioned, and with links when relevant.

## Outcome
- Whatever the lead writes for the owner (a planning reply, a review, an escalation, a desk note) puts a few words beside every number it mentions: a card, a ticket, an ADR, a decision.
- On a planning thread and a proposal's review page, every card number is a link to its thread and every ticket a link to its page; when the lead left a name out, the page adds it.

## Why it reads badly today
The planner's brief already says "name a card with its title" (`runner/prompts.py`, the line F31 D6 added), but only for cards, and only in the planner. On F173's reply of 26 Oct, F15 had its name and F73, F42, F26, F63 and F132 didn't; tickets (`f5-13`) and ADRs have no rule. The page links `/planning/<key>` paths only, and only in a lead message without points (`_text_with_links` in `factory_dashboard/planning.py`). F31's ticket that would have linked card numbers (`f31-04-what-to-do-now`, waiting in `.softfield/tasks/later/`) never ran.

## Decisions
- **D1 The lead writes the words.** A new line in `docs/agents/owner.md` (dated 2026-10-26), which every lead job reads: every card, ticket, ADR or decision the owner reads comes with a few words saying what it is, and a card with its title ("F22, Archive at the bottom"); a decision ("D2") is said in words, never alone. The planner's line in `runner/prompts.py` grows to the same rule.
- **D2 The page adds the links, and the names the lead left out.** One function in `factory_dashboard/planning.py`, grown from `_text_with_links`: escape the text first, then
  - a card number (`F37`, a card on main or in `_card_titles`) becomes a link to `/planning/f37` (with the page's `?project=`). When the words right after it aren't already its title (", " then the title's first 12 letters, ignoring case), the link also carries ", <title>" in muted ink, cut to 40 letters at a word with "…", the whole title as the link's `title`;
  - a ticket id (`f15-06-card-actions`, `bug-31-…`) with a ticket in the metrics database becomes a link to `/tickets/<id>`; a short one (`f63-01`) that names exactly one ticket links there and gains its slug's words (", desk order");
  - `ADR 29` gains ", <its title>" from `.softfield/adr/29-*.md`'s heading, with no link (no page shows ADRs);
  - anything that names nothing stays as it is. The owner's own messages stay plain text.
- **D3 Where:** a lead message's text (with points too, inside Full reply), each point's title, answer and action, the runner's messages, and a proposal's key points on its review page. Not the board, desk or Overview: their rows are already names.
- **D4 What doesn't change:** the planner's block (no new field), the points' order and comments, the review sheet of a milestone.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | names-beside-numbers | L | 2 | | D1: owner.md and the planner's line (protected: `docs/agents/`, `runner/`) |
| 02 | thread-links-numbers | D | 5 | | D2, D3 on a thread |
| 03 | proposal-links-numbers | D | 3 | 02, f67-02 | D3 on a proposal's key points |

Mock-up: [`.softfield/cards/f37-mockup/thread-names.html`](f37-mockup/thread-names.html).

## Not in this card
- F67, Key points say what they ask of you, drops "D1" from key points' titles (its D5) and redraws the review page's points; 03 waits for it so the two don't fight over `proposal.html`.
- `f31-04-what-to-do-now` (F31, When I click on approve plan) carries a bullet that 02 builds; whoever queues it drops that bullet.
- Links in milestone review sheets (`.softfield/reviews/`): a card of its own if the owner wants them.

## How to test
Open F173's thread: every F-number in its points is a link, and those the lead left bare show their card's name in grey; `f63-01-desk-order` opens its ticket page. Open an old reply where the lead wrote "F15, Reprioritising tickets": the name isn't doubled. Your own messages show no links.
