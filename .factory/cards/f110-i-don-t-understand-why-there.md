# Milestone F110: Ripe on the board but no Sign off button: one rule for both

> **State:** done · **Priority:** 1 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-16. Base: git tag `f110-i-don-t-understand-why-there-start`. Report: [`.factory/reviews/f110-i-don-t-understand-why-there.md`](../reviews/f110-i-don-t-understand-why-there.md).
> Planted by the owner on 2026-10-13.

## Notes
I don't understand why there are ripe tickets in the new board view but no sign off button. Same with some 'needs you' signoff from overview. I think you still don't have access to db and there is a ticket for that, prioritise tash first

## Expected outcome
- A card the board calls ripe always has a Sign off button on its page and sits on the desk under "Finished, to talk through": the three places follow one rule.
- A ripe card on the board says where to sign off in plain words, not as a terminal command.

## Done when
- A milestone whose tickets are all done except ones set aside or removed, with its review written, is ripe on the board, on the line's field and on the desk, and its page has the Sign off button.
- A ripe card on the board reads "Read the review and sign off" and opens the card's page at the button.
- To test: open the board, tap each ripe card, and check the button is there. Today F31, When I click on Approve plan, is the one to try: five tickets done, one set aside.

## Decisions
- **D1: the board's rule is the right one.** A ticket set aside (`later`) or removed counts for no stage (`_OFF` in `factory_dashboard/board.py`), and `runner signoff` doesn't refuse for one either (`_UNFINISHED` in `runner/owner.py` is ready and stopped tickets only). The line's field (`_field` in `factory_dashboard/line.py`) counted them as unfinished, so such a card was ripe on the board and nowhere else. The button on the card's page and the desk's item both read the field, so the field changes; the board and the runner don't.
- **D2: no Sign off button on the board itself.** The sign-off sits beside the review's sheet (F50 D2), so the owner reads what changed before marking it done. The board's card leads there in one tap.
- **D3: the Overview's extra sign-offs are F95's.** `f95-01-sign-offs-counted-once` removes the stored rows from Needs you; nothing here repeats it.
- **D4: sprouting is a live conversation** (the owner, 2026-10-13: "sprouting but their conversation are archived or have nothing going on"). The board took any thread, archived or not, as planning: F11, F15, F18 and F105 sprouted with archived conversations. Only an open thread counts, and the card says who it waits for ("waits for your answer since 9 Oct", "the lead is answering"); an idea whose thread is archived is a seed again.

## Tickets
- `f110-01-ripe-is-one-rule` (developer): the line's field leaves set-aside and removed tickets out when it decides a card is ripe.
- `f110-02-ripe-card-leads-to-sign-off` (developer): the board's ripe card says "Read the review and sign off" and opens the page at the button, in place of the command.
- `f110-03-sprouting-is-a-live-conversation` (developer): D4, after `f110-02` (both change the board's card).
