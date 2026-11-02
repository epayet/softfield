# F77: Allowance bars: the same length on the Overview, the same colours on every page

The planning thread behind F77's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:26

> And the colors are different between pages

## The lead, 2026-10-26 23:20

> I found two causes for F77 in the code and drafted a two-ticket fix. I didn't make a mock-up because the fix only restores the look the bars were meant to have.
>
> 1. **Why the colours differ between pages**: Each page decides the bar's colour separately. The Overview has three colours: green under the mark, yellow past it, red above 95%. The planning room's "The lead's window" has its own copy with only green and yellow, so a 97% reading is red on the Overview and yellow on Planning. Today both read 60% and 5%, so the bars match right now, but the gap shows as Claude nears the end of a window. The tile's heading is also in the lead's orange, unlike the Overview's panel heading. That colour comes from the heading, not the bar, so I'm leaving it.
>    Action: Ticket f77-02: one shared bar used by both pages, so the colour rule is written once.
> 2. **Why the bars are not the same size**: On the Overview, each window is only as wide as its own words. Claude's rows carry the "use reserve" lever, Copilot's month doesn't, and "5-hour window: 60%" is longer than "week: 5%". Each bar fills its window, so you get three lengths.
>    Action: Ticket f77-01: the windows sit in equal columns, so every bar has the same length. The phone layout, one row per window, stays as it is.
> 3. **Waits for two tickets already working on the same bars**: F9, Line polish (f9-29, the week's pace tick) and F32, the 5-hour lead's window doesn't say when it resets (f32-01) both edit these templates now. F77 runs after them so nothing conflicts. The shared bar takes the pace tick along with it.
>    Action: Already set as the tickets' dependencies.
> 4. **Other bars stay as they are**: The board's progress bars and a job's context bar are orange because they measure something else (work done, memory used), not an allowance. Making them green or yellow would make them look like an allowance warning. If those were the bars you meant, tell me here.
>    Action: Nothing, unless you say otherwise.
>
> Proposals:
> - F77: allowance bars, same length and same colours on every page (plan)
