# Milestone F302: Edit a review's idea in its own plate before planting it

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-25.

## Notes
on factory suggestions i can plant or plant and ask the lead. when i like the idea but want to tweak it a bit, i'd like to have the option to edit the text myself before planting

## Why
A review's idea plate (F164) plants the lead's words as they are. On 2026-11-25 the owner wanted F290's idea 1 with changes, so they copied it into the Plant box with a note (F303). That plant carried no `from`, so F290's plate still offers Plant and Plant and ask the lead for an idea already planted.

## Outcome
Each idea plate gets a third button, Edit first. It turns the idea's words into a box the owner can change; Plant and Plant and ask the lead then send those words, and the plate links to the new card as it does today.

## Done when
- an idea plate that can still be planted shows Edit first beside Plant and ask the lead and Plant
- Edit first replaces the quote with a box holding the words a plant sends today (the idea's text, then "From F290's review."), and marks the tag "your words"
- either Plant button then sends a `plant` request whose `text` is the box's words, with the idea's `ask`, `area` and `from` as today
- an emptied box greys out both Plant buttons; "Put them back" restores the lead's words
- once sent, the plate shows "On its way" and then "Planted", after a reload too (the plant still names its idea)

## Decisions
- **D1. The dashboard only.** The runner's `_plant` (`runner/requests.py`) already plants any `text` in a `plant` request, and `review_ideas` in `factory_dashboard/milestones.py` matches a plant to its idea by `from`, not by its words. So the request keeps its shape (`kind: plant`, value `{text, ask, area, from}`, from `idea_vals`); only `text` changes. Nothing in `runner/` changes.
- **D2. One partial.** The change lives in `factory_dashboard/templates/_partials/idea.html` and its CSS beside F164's (`.idea …` in `dashboard.css`). The thread's review, the milestone page's sheet and F59's report (f59-04 uses the same partial) all get it.
- **D3. The words are read at the press.** The Plant buttons keep their `hx-vals`; while the box is open, an `hx-on::config-request` on each replaces `text` inside the request's `value` with the box's words. No new endpoint, form or field.
- **D4. The box holds what is planted.** It is filled with the exact `text` the plant would send, the "From …'s review." source included, so what the owner sees is what lands in the card's Notes. They may delete the source line.
- **D5. Not stored.** An edit that isn't sent is gone at a reload, as an unsent Plant box is. The lead's words stay on the plate under the box ("The lead wrote: …").
- **Builds on** F164's plate and `idea_vals`; makes nothing removable.

## Before and after
- `/planning/f290`
- `/milestones/f290-runner-loop-py-is-6-500`

## Tickets
- `f302-01-edit-an-idea-first` (developer)
