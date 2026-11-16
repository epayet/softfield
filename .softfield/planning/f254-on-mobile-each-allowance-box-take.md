# F254: The allowance takes less height on a phone

The planning thread behind F254's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-16 22:26

> On mobile each allowance box take a lot of vertical space for nothing

## The lead, 2026-11-16 22:29

> I've drawn a phone mock-up and drafted one developer ticket. The Overview's allowance goes from about 420px to about 260px tall on a phone, and every word stays.
>
> 1. **Why it's tall today**: On a phone each window (Claude's 5-hour window, Claude's week, Copilot's month) is a box with its own border and padding. Inside it are three layers: a line with the name, the percent and the 'use reserve' lever (44px tall so a thumb can hit it), then the meter, then the small words. Those words are spread across the width, so they wrap into two or three lines. With tonight's readings that comes to about 420px for three windows.
>    Action: Fixed by the plan in point 2.
> 2. **The fix: rows, not boxes**: Phone only. Each window becomes a row with a thin rule between rows, and no box. The name, the percent and the meter sit in the lever's 44px band instead of on a line of their own. The reset, 'read at' and mark words run together as one line of text with '·' between them. 'At this rate' keeps its own line because it's the warning. Total: about 260px. The wide screen doesn't change.
>    Action: Ticket f254-01-allowance-rows-on-a-phone (developer: CSS in the phone block, plus a wrapper in the template if needed).
> 3. **Mock-up: Today and Proposed on a phone**: Both show tonight's real readings: 5-hour window 84% (runs out at 23:03 at this rate), week 7% (on pace), Copilot month 7%. Dashed green marks what changes.
>    Action: Read .softfield/cards/f254-mockup/allowance-phone.html; the ticket builds its Proposed.
> 4. **Why not fold the small words behind a tap**: That would save more height (about 180px). But the allowance redraws every 5 seconds, so anything you open folds again within 5 seconds, and the reset time and 'read at' are what you check most. Shortening the labels would make them harder to read. I recommend keeping every word visible. If you still want a fold, it needs the 5-second redraw to remember what's open, which is more work.
>    Action: Nothing, unless you want the fold.
> 5. **Another ticket edits the same template**: F243, I can't undo a fast lane lever: its ticket f243-02 also edits the lever in the allowance template. The two changes don't touch the same lines, so whichever runs second merges cleanly. I left the order to the board.
>    Action: Nothing.
>
> Proposals:
> - F254: the allowance as compact rows on a phone (plan)
> - F254 mock-up: the allowance on a phone (mockup)
