# Milestone F67: Key points say what they ask of you

> **State:** ready · **Priority:** 5 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
in proposals, sometimes i see D1 or D2, and some things are flags. Also, there are things that are just information, and things that need my attention, or even choice between options. The current list of key points doesnt make that super clear. i'd like information first. could the key points be better color coded? and the ones that i need to make choice have a ui for that?

## Outcome
- On a proposal's review page, each key point shows what it asks of the owner: nothing (information), a look (it needs their attention), or a pick (a choice between options). Information comes first, then what needs a look, then the choices.
- A choice is answered by tapping an option, not by writing a comment. The lead's pick is already selected, so leaving it counts as agreed, like every other point.
- No codes or marks the owner has to decode: no "D1" in a key point, no bare flag icon. Every colour on the page says what it means.

## Why it reads badly today
The planner's block gives each key point `n`, `title`, `text` and `flag` (`runner/prompts.py`, `_PLANNER_TAIL`); `factory_dashboard/templates/proposal.html` draws every point as the same box, with a ⚑ when `flag` is true. So a fact, a risk and a question between two options look alike, and the only way to pick an option is to write a comment. The lead also copies the milestone doc's decision numbers ("D1 Settled") into the titles.

## Decisions
- **D1 Three kinds of key point:** each key point gets `kind`, one of `info`, `attention`, `choice`. A point without `kind` (every proposal before this) shows as today. `flag` stays and keeps its meaning (changes an earlier decision); a flagged point is at least `attention`.
- **D2 How each kind looks:**
  - `info`: a plain numbered line, no box, muted, with a small Comment… link.
  - `attention`: a box with a hazard-yellow left edge and the word "Needs a look"; a flagged one also says "Changes an earlier decision" in words (the ⚑ goes).
  - `choice`: a box with an orange (`--opus`) left edge, the word "Your choice" and its options.
  - A one-line key above the points says what each colour means, as owner.md asks.
- **D3 Information first:** the page shows the `info` points, then `attention`, then `choice`, each in the order of its `n`; numbers stay as the lead gave them (comments are keyed by `n`). The prompt asks the lead to number them in that order too.
- **D4 Choices:** a `choice` point carries `options`, 2 to 4 of `{label, text}`, and `pick`, the index of the lead's recommendation. The page draws them as buttons (44 px, wrapping on a phone), the lead's pick selected and marked "Lead's pick". Tapping another option counts as a change: it joins the send-back comments as "Chose: <label>", and Approve gives way to "Send back", exactly as a comment does today. No new request kind, no server change. A choice that isn't well formed (one option, a bad `pick`) makes the block unread, as any bad field does.
- **D5 Plain words in key points:** the prompt says a key point never cites a decision or ticket number ("D2", "f31-03") as its title or in place of words; it says what changes.
- **D6 What doesn't change:** the thread's points (F31 D4 gives them their own `outcome`, built by f31-03 and f31-04), the send-back and approve requests, the dock, the deck on the phone.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | key-point-kinds | L | 4 | f31-03 | D1, D4's check, D3 and D5's prompt (protected: `runner/`) |
| 02 | key-points-by-kind | D | 5 | 01 | D2, D3, D4 on the review page, after the mock-up |

Mock-up: [`.softfield/cards/f67-mockup/review.html`](f67-mockup/review.html).

## Not in this card
- F66 (the key-point count in the proposal list) and F31 (thread points and "What to do now") are on the same pages; each stays its own card.

## How to test
Open the review page of a proposal whose key points carry kinds: the information lines come first, then the yellow "Needs a look" boxes, then the orange choices with the lead's pick selected. Tap another option: Approve goes and "Send 1 change back" shows; tap the lead's pick again and Approve returns. Open an older proposal: it shows as before.
