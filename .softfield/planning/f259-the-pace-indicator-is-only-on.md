# F259: The Planning room's week bar shows Claude's pace, as the Overview does

The planning thread behind F259's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-17 19:48

> The pace indicator is only on overview

## The lead, 2026-11-17 19:50

> I've drafted a fix that brings the week pace to the Planning room. It comes with a mock-up and one developer ticket, both waiting for your approval.
>
> 1. **Where the pace is missing**: Claude's week bar is drawn in only two places: the Overview's Agent allowance and the Planning room's "The lead's window" tile. Only the Overview's has the pace post. Right now that matters: the week is at 29% against today's pace of 22%, so the lead's tickets (F208, F71 first in line) wait until about Wed 18 Nov 13:36. The Planning room only says "week 29%", and nothing there tells you anything is held. No other page has a week bar, the top bar included.
>    Action: One developer ticket, f259-01-planning-week-pace.
> 2. **The same marks and words as the Overview**: The Planning room's week bar gets the dashed yellow post (today's pace), the striped stretch used beyond it, and the same "Over pace" plate saying when lead tickets go on again. When on pace, the week's small line says "on pace · today's 22%". In the week's last hours you get the "Last hours" plate. With the week's reserve lever on, there's neither. The 5-hour bar gets no post, because pace only applies to the week.
>    Action: Mock-up planning-week-pace.html, drawn on today's real readings.
> 3. **One shared piece for the plates, so the pages can't disagree**: Today the "Over pace" and "Last hours" plates are written out in the Overview's template. I'd move them into one shared piece that both pages use, so the times and words can never differ between the two pages. The Overview's existing pace tests must pass unchanged, which proves its look hasn't moved. Copying the plate into the Planning template would be quicker, but it would drift the first time someone edits one copy.
>    Action: Decision D1 on the card, written into the ticket.
> 4. **A small risk: "Over pace" in a room for planning**: The tile is where you check whether you can plan now, and planning is never held by pace. An "Over pace" plate there could read as "planning waits". The plate's second line already says "developers, planning, reviews and the fast lane go on", so I kept the words as they are rather than adding a Planning-only version.
>    Action: Nothing. If it reads wrong once it's live, say so on this thread and I'll shorten the plate for Planning.
>
> Proposals:
> - The week's pace in the Planning room (mockup)
> - F259, the Planning room's week bar shows Claude's pace (plan)
