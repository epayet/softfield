# F61: Claude's meters say when the window runs out at this rate

The planning thread behind F61's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:25

> 'at this rate you'll be out by Friday afternoon's

## The lead, 2026-10-26 23:15

> I've planned F61 as one small developer ticket with a mock-up, and drafted both on `plan/f61`. Last week's readings show the warning would have come a day and a half before the week ran out.
>
> 1. **Yes, and last week shows it would have helped**: Last week's Claude week ran out on Thursday 23 Oct at 19:38 and only came back on Monday at 17:00, so there was almost no Claude for three days. On Wednesday at 22:44 the meter read 58% and was green, under its mark, so nothing looked wrong. The same readings at the rate so far say 'out Thursday 13:38'. That would have been a day and a half of warning, and it was about six hours early: it ran out at 19:38 because the pace held lead tickets back near the end.
>    Action: Ticket f61-01-at-this-rate (developer, about half an hour): one line under each of Claude's two meters, plus a hatched ghost on the meter showing where it will be at the reset.
> 2. **How 'at this rate' is worked out**: It takes the latest reading and divides it by the time since the window started, the way Claude's own page does. It is rough on purpose: the pace holds and your reserve switch aren't counted. For the first 10% of a window (30 minutes for the 5-hour window, about 17 hours for the week) it says nothing. At 23:12 tonight the 5-hour window read 46% after 22 minutes, which would have said 'out in half an hour'.
>    Action: Card F61 D2 and D3; nothing for you to do.
> 3. **Mock-up: the line and the ghost**: The mock-up uses the real readings from Wednesday night. Under each Claude meter there is a line: 'at this rate: out Thu 13:38, 3 days 3 h before the reset' in yellow, or 'lasts to the reset, about 79% by then' in grey. A hatched ghost on the meter runs to where the use will be at the reset. F9, Line polish already plans an 'on pace / over pace' line for the same meter (f9-29), so it is drawn dotted beside this one and the ticket waits for it. Copilot's month gets no line: the runner already paces it and it has never run out.
>    Action: Look at .factory/cards/f61-mockup/at-this-rate.html. Tell me if you'd like the ghost gone or Copilot's month included.
> 4. **The forecast warns you but won't stop the week running out**: The runner's pace only holds back lead tickets. Of last week's $305 of Claude jobs, planner jobs cost $150, about half, and by your rule (ADR 20 item 2) they run on the reserve, so nothing paces them. Reviews cost another $58. The new line will tell you on Wednesday that Thursday is the end, but the only thing you can do then is plan less. My recommendation is a separate card that paces the planner as well: Opus while the week is on pace, Sonnet or wait for your next message once it isn't, and your high-priority questions always on Opus. It goes against your 'planning is worth Opus' rule, so it should be your choice.
>    Action: If you agree, paste this in the Plant box: 'Planning ate half of last week's Claude ($150 of $305) and the week ran out on Thursday. Pace the planner like lead tickets: Opus while on pace, Sonnet once over pace, high-priority questions always Opus.'
> 5. **When it would run**: F61 sits at 90 on the board, below all 33 ready cards, and its ticket also waits for f9-29 in F9, Line polish. As things stand it is days away. If you want the warning before the next Thursday, drag F61 up next to F9 once you approve.
>    Action: Nothing, unless you drag the card.
>
> Proposals:
> - F61: Claude's meters say when the window runs out at this rate (plan)

## The owner, 2026-10-27 00:53

> I don't see the mock-up. Again...

## The lead, 2026-10-27 13:55

> The page only shows a mock-up for a proposal whose `path` is the mock-up file, and I listed it only inside the plan. This reply lists it on its own.
>
> 1. **My mistake: the mock-up wasn't listed on its own**: I drew the mock-up but only mentioned it inside the plan, and the plan's path pointed at the card's doc. The proposal page shows a mock-up only for a proposal whose path is the mock-up file, so you saw no picture. The file was on the branch the whole time. It now has its own proposal: open 'F61 mock-up: at this rate, out by…' under Proposals from this card. Tap Today or Proposed on a phone; on a wide screen they sit side by side.
>    Action: Open the mock-up proposal below.
> 2. **Why it happened again, and what stops it**: The same slip hid F152's mock-up. The fix is already a ready ticket: f152-02 in F152, Every mock-up is listed. After a planner reply, the runner adds a mock-up proposal for any mock-up file the reply forgot. F165, Every mock-up has its point (f165-02) keeps mock-ups from earlier turns listed. F152 sits at 9 on the board, behind 13 cards, so it is about a day of work away.
>    Action: Drag F152, Every mock-up is listed, to just below F173 on the board. It is one lead ticket, about half an hour, and it ends the 'I don't see the mock-up' problem for every card.
> 3. **The plan is unchanged**: Nothing in the plan or the ticket changed. It waits for your Approve, after you have looked at the mock-up.
>    Action: Approve the plan, or comment on a point of the mock-up.
>
> Proposals:
> - F61 mock-up: at this rate, out by… (mockup)
> - F61: Claude's meters say when the window runs out at this rate (plan)
