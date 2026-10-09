# F63: I want to see cards in planning by order of importance.…

The planning thread behind F63's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 18:30

> There are items finished to talk through and need my sign off apparently but I can't do anything with those, there is no sign off button. And one of them is completely empty

## The lead, 2026-10-08 18:30

> The lead merged F63 into F50: its notes are on F50's card now. The conversation goes on on F50's thread: /planning/f50

## The lead, 2026-10-08 18:30

> F63 asks for what F50 already plans, and F50 is ready with its three tickets queued. I'm proposing to merge F63 into it.
>
> 1. **This is already planned as F50, ready and queued**: F50 ('a finished card shows its review') came from your note this morning that 'the data safety review it asks has no info'. It found three things wrong, and they match what you describe. (1) The dashboard calls a card finished as soon as its last ticket is merged, before the lead has written its review. (2) The card's page never shows the review. (3) No button on the dashboard sends a sign-off. The runner already accepts one; only the button is missing. Its three tickets are in tasks/ready/: f50-01 ripe-after-review, f50-02 thread-signoff-sheet and f50-03 signoff-button. I'm merging this card into F50.
>    Action: A merge of F63 into F50 (the proposal below).
> 2. **The empty one is almost certainly F20, Data safety**: F20 was planned in a terminal session, so it has no conversation in the planning room, and its review hasn't run yet. Its page only shows a title and an empty reply box. F20's work itself is done and working: the daily Dropbox backup exists. When F50 is built, F20 will leave 'Finished, to talk through' until its review is written. It will come back with What changed, How to test and a Sign off button.
>    Action: Nothing new: F50's tickets 01 and 02 cover it.
> 3. **Until F50 ships, sign off from a terminal**: Once a card's review is written, `uv run runner signoff <key>` (for example `uv run runner signoff f20-data-safety`) does what the button will do. Don't sign off F20 yet: its review hasn't been written. Leave the cards on the desk alone for now. They're harmless, and F50 tidies them.
>    Action: Nothing.
> 4. **Move F50 up if you want it sooner**: F50 is at priority 2, behind F20, F21 and F31 at priority 1. It is next to F8 and F48, also at 2. Its tickets are small developer work. I'd move it up: this is the only part of the desk where you can't act at all, and the button is the last link between the finished work and the end of a milestone. Only you set priorities, so this one is your tap.
>    Action: Tap ↑ on F50 in Next in line or on the Milestones page. Otherwise nothing.
>
> Proposals:
> - Merge F63 into F50 (a finished card shows its review) (merge)

## The owner, 2026-10-08 23:25

> I want to see cards in planning by order of importance. Sign off first, then proposals then conversations then archives. 'comikg' can come first as it's temporary and it shows me what I've just done, like what I just planted

## The lead, 2026-10-08 23:26

> I've drafted F63's plan to reorder `/planning` the way you asked, with one small developer ticket. Two changes are mine, and the last point asks for one choice.
>
> 1. **The order you asked for**: Top to bottom: Coming (only while something is on its way), then the cards to sign off, proposals, conversations and seeds, then Archived, closed, last. Today the conversations come first and the sign-offs fourth. The Overview's Needs you list, the Planning tab's count and the Previous / Next arrows on each page all use the same list, so they change with it: one order everywhere.
>    Action: The plan below: one developer ticket, f63-01-desk-order.
> 2. **Coming goes first, across the whole width**: Agreed. It's temporary and shows what you just did. Today it sits beside the Plant box. It moves above it, as wide as the page, and still shows only when something is on its way.
>    Action: Part of f63-01.
> 3. **I'd keep 'Didn't go through' above the sign-offs**: You didn't name it. It holds your own words that the runner refused, the plants lost unseen on 2026-10-07. It shows only when there are some and goes once you dismiss them. Below the sign-offs you could miss it again.
>    Action: Part of f63-01. Say if you want it lower.
> 4. **Renaming 'Finished, to talk through' to 'To sign off'**: That's the word you used, and since F50 the card's page has a Sign off button. The current name made it sound like there was something to discuss.
>    Action: Part of f63-01.
> 5. **Your choice: where the Plant box goes**: You didn't place it. I recommend (A): Coming, then the Plant box, then the cards. It's the page's only box to write in, and a plant then shows just above where you typed it. (B): Coming, the cards, then the Plant box. Sign-offs come straight after Coming, but on a phone planting means scrolling past the whole list.
>    Action: A is in the plan. Say B and I'll change D2 and the ticket.
>
> Proposals:
> - F63: the planning page in order of importance (plan)
