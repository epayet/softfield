# F86: idea: tracking time the human spent on a project

The planning thread behind F86's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:28

> Plan this card.

## The lead, 2026-10-27 03:59

> I've drafted F86's plan on `plan/f86`: the card's doc, a mock-up and three tickets. All three pass `softfield check-tickets`.
>
> 1. **Your time is counted from your presses, not watched**: Every message, approval, sign-off, plant, pause and reorder you make on the dashboard is already saved with its time: 859 since 7 Oct. Grouping them into sittings (a gap of more than 20 minutes starts a new one, and each sitting adds 5 minutes for the reading before your first press) gives 12.5 h the week of 5 Oct (counted from Wednesday 7 Oct), 12.8 h the week of 12 Oct and 11.5 h the week of 19 Oct. That last week was 28 sittings over 6 days. Nothing new gets stored, and every week since 7 Oct shows from day one. The cost: reading that ends without a press and your terminal sessions are missed, so the page says "on the dashboard". I considered a signal sent while a page is open, but that's a new table and a request from your phone every minute, before we know the presses miss much. It's listed in Later instead.
>    Action: Ticket 01 computes it (D1, D2).
> 2. **It goes on F59, A weekly report page, rather than a page of its own**: F59 (A weekly report page: the factory's numbers over time and the lead's read) already lists this card in its Later list as one more section of the report. So I'm not merging it: F59 is approved with four tickets queued, and adding to it now would grow a card that's already running. F86 stays its own small card, and its tickets wait for F59's first three. Your time sits beside what the agents did that week, for the whole factory or one project.
>    Action: Tickets 02 and 03 depend on f59-02 and f59-03.
> 3. **What the page adds (mock-up)**: Two tiles at the end of the week's numbers: "Your time 11.5 h" (12.8 h the week before) and "Waited for you 5.5 h", the median wait over 62 desk items (8.2 h the week before). Your hours are stacked on each week's bar in "Hours worked, by agent". A new panel, "Where your time went", lists the top 6 cards, then "Everything else", then your presses by kind. Your parts are drawn in a new plain-ink token, `--owner`, so they never look like an agent or a status. Today is F59's approved picture, because its page isn't built yet. Mock-up: .softfield/cards/f86-mockup/your-time.html.
>    Action: Ticket 02 builds it.
> 4. **The first numbers already say something**: Of last week's 11.5 h, 1 h 35 went to planting (32 plants) and 1 h 27 to steering the line (pauses, reserves, reorders): almost a quarter of your time went to no card's thread. The longest card threads were travel-companion's F1, the rename (38 min), and F172, Mark a card to use Claude's reserve (33 min). I'm not proposing a fix yet. The weekly read will say where your time went and give at most one idea to save some, as a plantable line.
>    Action: Ticket 03, on the lead's brief for the weekly report.
> 5. **A trap found while measuring**: Times are saved with different offsets (+01:00 and +00:00). Sorted as text, they put actions out of order: my first count gave 5.5 h for the week of 19 Oct instead of 11.5 h. Ticket 01 tests this case. F59's first ticket already says to compare times as datetimes, so nothing to change there.
>    Action: A done-when line in ticket 01.
> 6. **Who builds, and when**: 01 developer: Python and tests, following F59's ticket 01. 02 developer: two tiles, a panel and part of a bar, on a page that will already exist. 03 lead: runner/prompts.py is protected. None can start before F59's first three tickets merge, so approving now changes nothing in what runs next.
>    Action: Nothing beyond approving.
>
> Proposals:
> - F86: the weekly report shows the owner's time (plan)

## The owner, 2026-10-27 08:07

> On point 3: what mockup, i don't see it. again...
> On point 5: would it be best to store dates in timezone aware?

## The lead, 2026-10-27 18:50

> The mock-up was on the branch all along, but the page only shows one when it is listed as its own proposal. I've listed it below. On dates, I recommend a separate change, with its text ready to plant.
>
> 1. **Why you saw no mock-up, again**: The file was drawn and is on the plan branch (.softfield/cards/f86-mockup/your-time.html), but I only named it inside the plan. The review page shows a mock-up only when it has its own proposal pointing at the file. The same thing happened on F152 (A done card says where its review is, and set aside says it won't run), and its ticket f152-02 already fixes it for good: when a lead reply forgets a mock-up it drew, the runner lists it. That ticket waits for nothing, but it is 25th in the line. This time the mock-up is listed below as its own proposal, so it opens.
>    Action: Drag F152 to the top of the board so f152-02 (a lead ticket, about half an hour) runs next and this can't happen again.
> 2. **Times are already timezone-aware, but written two ways**: Every saved time already carries its offset. The trouble is that the runner writes your local time (+01:00 until the clocks went back on 25 Oct, +00:00 since), while the dashboard writes UTC. In the database, 1,377 jobs carry +01:00 against 73 with +00:00; your presses split 154 and 706. Two times written in different offsets sort wrong as text, and the night the clocks go back repeats an hour. About 30 places in 13 files sort or compare times as text. My recommendation: write every time in UTC, show local time only on screen, and convert the old rows once, right after the daily backup. The alternative is to leave the stored times as they are and always read them as real times, which is what F86's and F59's tickets already do. It works, but every new query has to remember it, and my first count for this card got it wrong. Converting stored data is your call, and it's a new theme, so it gets its own card rather than growing this one. F86 works either way.
>    Action: If you agree, paste this into the Plant box: "Store every time in UTC. The runner writes local time (+01:00 before 25 Oct) and the dashboard writes UTC, so times sort wrong as text. Write UTC everywhere, show local time on screen only, and convert the old rows once after the daily backup."
>
> Proposals:
> - F86 mock-up: your time on the weekly report (mockup)
> - F86: the weekly report shows the owner's time (plan)
