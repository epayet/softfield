# Milestone F207: Every lead reply and proposal review opens with In short

> **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-11-02.

## Notes
I want a tl;dr of a planner response, whether it's chat or proposals. Then I can dig into all the points

## Outcome
Every reply of the lead on a thread, and every proposal's review, opens with "In short": a few plain sentences saying what it comes to and what it needs from the owner. The points follow, for digging in.

## Today
The lead already writes up to two lines before its `json` block (F41 D1), but `factory_dashboard/templates/thread.html` shuts them in a closed "Full reply" fold, and they say what the reply did ("I drafted…"), not what it comes to. A proposal has no such text: `factory_dashboard/templates/proposal.html` goes from the header, through a mock-up's frame, to the key points. Of the 288 lead replies with points, 50 have text over 400 characters, and the last of them is message 126: every reply since F41 is under it.

## Decisions
Mock-up: `.softfield/cards/f207-mockup/in-short.html`.

- **D1 A reply's In short is its text before the block.** No new field and no new column: `planner_messages.text` holds it, and the next job's history reads it as it does now.
- **D2 What the lead writes (`_PLANNER_HEAD`):** at most three short sentences, under 300 characters: what it found or recommends, and what it needs from the owner, naming each `question` point by its number. Nothing else outside the block. None on a reply of one point: the point says it all.
- **D3 A proposal's In short is a new optional field, `tldr`,** on the proposal in the block, stored with it in `planner_messages.proposals`. One or two short sentences: what approving it does, and its main cost or risk. On a mock-up's, what the picture shows. A value that is neither text nor null makes the block unread, as `summary` does on a merge.
- **D4 The thread:** a lead message with points and with text of at most 400 characters (a named constant in `factory_dashboard/thread.py`) shows the text open, in the In short plate, above the points; older ones and earlier ones in the thread alike. Text over 400 characters keeps today's closed "Full reply" fold, so the long replies from before F41 don't fill a page. A message with no points shows its text as today (F41 D3).
- **D5 The review:** the plate sits right under the header, above a mock-up's frame. No `tldr`, no plate.
- **D6 The plate:** `.in-short`, shared by both pages: the label "In short" (not "TL;DR": the owner's rule is no abbreviations on a page), the words at 16 px in `--fg` on `--plate`, the `--notch` corner and a `--stripe` edge. No new token, and no agent's or status colour.
- **D7 The points stay open.** They carry what counts as agreed when the owner sends, so a fold would hide what they agree to. A phone already shows them one at a time.
- **D8 What doesn't change:** the points and key points, comments, the deck, the desk's rows, notifications.

## Tickets
| # | Ticket | Who | Diff. | After | What |
|---|--------|-----|-------|-------|------|
| 01 | in-short-in-the-prompt | L | 2 | – | D1, D2, D3: the prompts and the block's check (protected: `runner/`) |
| 02 | in-short-on-the-pages | D | 3 | – | D4, D5, D6 |

## Not in this card
- F67, Key points say what they ask of you: the kinds of key point on the same review page, its own card.

## How to test
Send a message on any card once 01 has merged: the reply opens with "In short" above its points, says what it needs from you, and points to a question by its number. Open its plan's review: the plate is under the header, above the mock-up. Open an old thread: its short texts show in the plate, and a long one from before F41 is still in its fold. On a phone, the plate stays while you step through the points.
