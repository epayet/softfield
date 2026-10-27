# Milestone F82: Text boxes grow with what you type, the Plant box first

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
the plant idea text box is quite small and doesn't expand when i type longer ideas

## What happens today
The Plant box on `/planning` (`factory_dashboard/templates/planning.html`) is a `<textarea rows="4">`: four lines high whatever is typed, then it scrolls inside itself, so a long idea is read through a four-line slot. Nothing on the dashboard sizes a box to its text (no `field-sizing`, no script). Every other free-text box has the same fixed height: a waiting plant's edit (`planning.html`, 4 rows), the reply and a sent message's change on a card's thread (`thread.html`, 2 and 4 rows), and the comment under a key point (`thread.html`, `proposal.html`, 2 rows).

## Expected outcome
Every text box on the dashboard grows with what is typed in it, line by line, up to about 60% of the screen's height, and only then scrolls inside. It never starts smaller than today, and it shrinks back when it is emptied (a plant sent, a box cleared).

## Decisions
- **D1 Every box, not only Plant** (the lead, 2026-10-26): the same fixed height is on the thread's reply and the point comments, where the owner writes as long; one rule covers all, so a box added later grows too.
- **D2 One script in `base.html`, not CSS alone:** `field-sizing: content` would be one CSS line, but the owner writes from a phone and older iPhone Safari ignores it. A delegated `input` listener in `base.html`'s script sets each `textarea`'s height to its content (`height = auto`, then `scrollHeight`), with a `max-height` of `60vh` in `dashboard.css` past which it scrolls. A value set by a script fires no `input` event, so the box is also fitted on `focus` (Try again puts a refused note in the Plant box and focuses it). A plant sent shrinks back by itself: the page draws a fresh Plant form after it (F13).
- **D3 Rows stay as the minimum:** each box keeps its `rows` as its starting height; growing never shrinks it below that.
- **D4 No mock-up:** nothing is added, moved or restyled; the same box only gets taller as you type, which a picture can't show better than the page will.

## Tickets
- f82-01-text-boxes-grow (developer): D1–D3.
