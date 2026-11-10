# F231: Triage the set-aside bugs, and a Remove button for the ones not worth a run

The planning thread behind F231's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-06 19:24

> There are many bugs in the seed board row and I can't do anything about them apart from queuing. Tell me which ones are worth queuing and add a way to get rid of the rest

## The lead, 2026-11-09 16:11

> Merged F174 here: You asked which bugs were set aside in the Seed column (2026-10-23). The lead listed the 43 from the old backlog file in groups. It recommended queuing bug-05, bug-06, bug-07 and bug-44, offered a bug-48 for flaky tests (it became bug-49), and asked whether to fold the bugs into one plate in the Seed column, add a filter, or leave it. That question was never answered, and the thread was archived on 2026-10-26. F231 now settles it: most of those bugs are removed instead.

## The lead, 2026-11-09 16:11

> I sorted the 56 set-aside bugs: 7 to queue, 2 to leave, and 47 plus a stale F9 ticket to remove. The plan also adds a Remove button for set-aside tickets, with a mock-up. Your answer is needed on point 6.
>
> 1. **Worth queuing: 7 of the 56**: I checked each against today's code. These still hold and either cost money or protect the line. bug-56: every review now stops after its first round, because an old finding from M3 has stood at 3 since M3, so fixes are never checked again (11 milestones so far). bug-06: a review can't see the test suite finish within one call, so Opus reviews run blind. bug-49: two flaky timing tests that have already paid for an Opus step-up (I updated it: a third test it named is gone). bug-57: pre-flight sends two-page tickets to the lead before they burn three local attempts (f170-04 cost 7.3M tokens). bug-54: `softfield init` silently turns off a repo's own git hooks, which matters for every new project. bug-07 and bug-51: two dashboard tests, one for buttons that point at nothing and one for escaped markup on any page. Both are developer tickets, so they cost no Claude time.
>    Action: Approving the plan queues these 7 (each now says what I checked on 2026-11-09). That's about 4 hours of line time, 5 of the 7 on Claude.
> 2. **Left set aside: bug-36 and bug-60**: bug-36 (the 5-second refresh builds the board twice) is already handled: f228-03, in F228, The Overview and Milestones pages draw in about a second, removes it once its work is done. bug-60 stops a local attempt that repeats the same failing call. It waits for F195, I've reduced the context window size, because you asked to find out why the local model fails before working around it.
>    Action: Nothing: they stay in the Seed column until those cards decide.
> 3. **The other 47 bugs, and f9-12, are removed**: Covered by a card already: bug-23 and bug-42 (F132, One view of the whole factory), and bug-28, bug-30 and bug-58 (F216, A shorter, consistent review page, whose f216-02 rewrites the same markdown code). No longer bite: bug-05 (the runner now runs from its own live copy, so a half-saved file in the repo can't break it), bug-12 (that one-time clear-out ran long ago), bug-61 and bug-62 (leftovers of the week park that F219 removed). bug-44 just asked to delete f9-12, so f9-12 goes too. The remaining ~37 are rare cases never seen twice, or fixes that only correct a number in the reports. Nothing is lost: git keeps every ticket, and each finding stays in its review in .softfield/reviews/.
>    Action: f231-01 removes the 48 files in one go. It is a lead ticket of difficulty 1 that needs nothing new, so it can run first.
> 4. **A Remove button on every set-aside ticket**: A set-aside ticket's page gets Remove beside Queue it. It asks once more before sending, the way Remove seed does on a card's thread. Pressed, the panel turns to a dashed 'Removing · on its way' at once. On the board, the bug's card in the Seed column gets the same dashed edge, for a waiting Queue it too (today that shows nothing either). Only a set-aside ticket can be removed: a blocked one is set aside first. There is no new terminal command, because the dashboard does the asking.
>    Action: f231-02 (lead: the runner's request), then f231-03 and f231-04 (developers: the ticket page and the board card), from the mock-up.
> 5. **F174, Which bugs are set aside in the Seed column, joins this card**: F174 asked the same question on 2026-10-23 and got the list. Its four picks were never queued, its thread is archived, and its card still sits in the Seed column as a seed. Usually the older card is the one kept. I keep F231 instead because it holds the plan, and F174 only holds a settled question.
>    Action: Merge F174 into F231: its note and a summary of its thread move here, and one more seed leaves the column.
> 6. **Pushback: the column will fill up again unless reviews stop setting bugs aside**: 43 of these came from a single pass over the old backlog file. But 15 more (bug-48 to bug-62) came from reviews in the two weeks since, and I'd queue only 2 of them. A review that sets aside every small finding refills the column. My recommendation: a review sets a bug aside only when it would queue it itself; everything else stays a finding in its report. Changing what reviews do is a workflow rule (ADR 35's 'later' route), so it needs an ADR you accept. The alternative is to leave reviews as they are and use Remove now and then.
>    Action: Tell me 'tighten' or 'leave'. On 'tighten', I draft the ADR change on this thread next.
> 7. **Where it runs**: Once approved, F231 sits at priority 100, at the end of the board, behind about 117 tickets. The 7 bugs keep their own places: bug-06 and bug-07 near F10, Crates on the belts, and the rest at 50. If you want the column clear soon, drag F231 up after approving, or put it in the fast lane. f231-01 alone clears the column.
>    Action: Your call on the board, after you approve.
> 8. **The idea seeds already have Remove seed**: The Seed column also holds 18 idea cards. Each one already has Remove seed on its thread. F11, test, is clearly one to remove. Several others are old questions that have been answered (F105, F131, F145, F167).
>    Action: Nothing to build: press Remove seed on the ones you don't want.
>
> Proposals:
> - F231: queue 7 bugs, remove 48 set-aside tickets, and a Remove button (plan)
> - Remove beside Queue it, and the seed card on its way (mockup)
> - F174, Which bugs are set aside in the Seed column, joins F231 (merge)
