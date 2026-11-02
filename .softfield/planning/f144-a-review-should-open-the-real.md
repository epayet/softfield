# F144: A review reads the real page and real data before the tests

The planning thread behind F144's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 09:16

> I've drafted ADR 37, a one-ticket plan and the card's plan section. The ticket's only pre-flight problem is the one that's meant to be there: it waits for ADR 37 to be accepted.
>
> 1. **Why a rule and not a habit**: Four reviews in a row found their worst bug on real data, not in the tests: F109, When plans get merged (the merge fixtures were the opposite of a real merge); F94, Seeds and planting ("finished … finished" and "took 142.2 h" on /away); F30, Conversations (the leftover "6 points" on F95's real thread); and F158, Milestones don't show me their… (broken HTML that passed the text-only tests). Each time the reviewer looked because they chose to. The review brief only says `look` exists, because ADR 28 item 5 made it on demand.
>    Action: ADR 37 makes the look part of the review whenever a factory page changed.
> 2. **Going further than your note: the fixture check**: F109's lesson was wider than pages: the bad data was in the test fixtures, and reading real cards showed it. F49, Don't ask me to merge, hit it again. Opening the page catches the bug only when the live database already has the case. Comparing one fixture of each new test file with a real record catches the cause. It costs one read.
>    Action: Item 2 of ADR 37. A fixture that's tidier than real data becomes a should-fix finding on the test.
> 3. **Reviews only, not checkpoints**: ADR 02's F94 entry suggested checkpoints should read the page too. I'd hold off. Checkpoints run every two developer merges, mostly on Sonnet, and most merges change no page. All four bugs were caught at the review, so none got past it. If a review ever catches one too late, add checkpoints then.
>    Action: Item 4 of ADR 37. Tell me if you want checkpoints included now.
> 4. **It needs an ADR, a small one**: ADR 28 item 5 decided that jobs look only when they choose to. Requiring the look in reviews changes an accepted decision, so per the workflow rules it needs your acceptance first. The ticket waits for that.
>    Action: Accept ADR 37 from its page. f144-01 then queues as one lead ticket.
> 5. **No mock-up**: Nothing on screen changes. Only the review job's instructions and what its report says.
>    Action: Nothing.
>
> Proposals:
> - ADR 37: A review reads the real page first (adr)
> - F144: one lead ticket for the review's instructions (plan)
