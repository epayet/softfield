# Review: F219, lead tickets follow Claude's week pace

- **Status:** round 2 done. Every fix is checked and no ticket is left to run.

## Sign-off sheet

### 1. What changed
- **Lead tickets now follow Claude's week pace line for real.** Over the line, a lead ticket off the fast lane doesn't start. It's passed over, with nothing on your desk, and starts by itself once the line allows it.
- **In the week's last 10% (about 17 hours), a lead ticket may use the whole reserve,** up to 100% of the week.
- **Developers, planning, reviews and the fast lane carry on.** So does a ticket that was cut off mid-work once its reset has passed.
- **The runner and its dry run now choose the next ticket with the same code,** so they can't disagree the way they did with bug-59.
- **When the run has nothing else to do, the top bar says so:** for example "Idle: 22 lead tickets wait for Claude's week · until about Sun 23:12".
- **A review doesn't pay for rounds with nothing to read.** If its lead fix ticket is held by the week, the review ends for now and comes back by itself once the fix is done.
- **The Overview doesn't show any of this yet.** That is f9-29 (see 3). Until it runs, the legend still says "the factory stops here", and Next in line lists held lead tickets with no wait.

### 2. How to test it yourself
The week is at 78% and today's line is about 36%, so the rule is in force now.
1. Open the Overview on your phone and look at Next in line, then at what's running over the next few hours. Only developers, planning, reviews and fast lane cards (F219, F171) should start.
2. When nothing else is left, the top bar should read "Idle: … lead tickets wait for Claude's week · until about Sun 23:12".
3. Pull the "use reserve" lever on Claude's week. At the next pick a lead ticket should start, and the runner should stop being idle. Push the lever back if you only wanted to try it.
4. On Sunday night after 23:12, without the lever, lead tickets should start by themselves.

### 3. Left for later
- **f9-29, the Overview's drawing of this rule.** The plan's "Done when" counts on it, but it belongs to card F9, so it's a lead ticket held like any other: at 78%, not before about Sun 8 Nov 23:12. If you want it sooner, put F9 in the fast lane on the board; I recommend that, because the Overview is misleading until then. It would also take f9-27 with it.
- **bug-61:** `softfield milestone`, the terminal command, wrongly says held lead tickets are behind a blocked one, and opens a desk item. The standing run doesn't do this.
- **bug-62:** removes leftover code for the old park at the week's reserve.

### 4. Decisions waiting for you
None. [ADR 44](../adr/44-lead-tickets-stop-at-the-reserve.md) is already accepted, and the one fast lane choice is under 3.

### 5. How the work went
- 2026-11-05, 05:49 to 06:18: f219-01 merged at the first attempt (Opus, 25 minutes, $4.03). [Session](../sessions/2026-11-05-0247.md).
- 2026-11-05, 06:18 to 06:27: f219-02 merged at the first attempt (Sonnet, 5 minutes, $0.20). [Session](../sessions/2026-11-05-0618.md).
- 2026-11-05, 06:31 to 07:21: review round 1 (Opus, $3.32), which found one fix for a ticket (f219-03) and made three small fixes itself. [Session](../sessions/2026-11-05-0627.md).
- 2026-11-05, 07:21 to 07:26: f219-03 merged at the first attempt (Sonnet, 5 minutes, $0.35). [Session](../sessions/2026-11-05-0721.md).
- 2026-11-05, from 07:33: review round 2, which checked the fixes and made one small fix itself.
- Lessons:
  - **Removing a park changes more than the pick.** The pick was tested thoroughly, but the review's rounds and `softfield milestone` also relied on a held ticket being parked. f219-03 and bug-61 cover those two.
  - **The line now holds its own follow-up work.** A card's page change that lands on another card waits like any lead ticket, so the review now says so and points to the fast lane.
  - **A new result has to reach every caller.** f219-03's tests covered the standing run, but "parked" also reached `softfield milestone`, which read it as ready for sign-off. Round 2 fixed that and added a test.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** put F9 in the fast lane, so the Overview shows the rule. Then watch the first full week: ADR 44 expects few lead tickets outside the fast lane until F177 cuts the cost of planner replies, and 61 of the 105 ready tickets are lead tickets.

### 7. What clogged the factory line
Nothing clogged this card. It took about 40 minutes from its first job to its review, with no failed attempts, limits or stops for you. The two first tickets did wait for each other, but f219-02 depended on f219-01's function, and it took only 5 minutes. Its one fix ticket then ran at once, since F219 is on the fast lane, and round 2 started 7 minutes after it ended.

## What was built
- **`allowance.lead_hold`** is the one rule, with `lead_goes_at` for "until about when". `allowance.answer` gives every other caller the same answers as before.
- **`loop.choose_ticket`** chooses the next ticket for both the runner and the dry run, and `_claude_windows_from` builds the windows for both, refusals included.
- **The park at the week's reserve is gone,** and old entries and their desk items are cleared at the start of a run.
- **f9-29 was rewritten** from the F219 mock-up, and ADR 25 points at ADR 44.

**Tests:** read closely, and sound. The edited tests recorded the old rule, as the ticket said they would: parks at the reserve became "passed over", and two tests swap monkeypatches for real readings, which makes them stronger. `test_the_runner_and_the_dry_run_choose_the_same_next_ticket` covers all eight cases the ticket lists.

No French changed: this is the factory, in English.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | ticket | A review pays for further rounds while its lead fix ticket is held by the week | Resolved by f219-03: the review ends with no stop and comes due again when the fix is done |
| F9 | should-fix | fixed | With that fix, `softfield milestone` would read a waiting review as ready for sign-off and put a sign-off on the desk | Fixed in round 2, with a new test: no verdict, and it says what the review waits for |
| F2 | should-fix | later | `softfield milestone` blames a blocked ticket for what the week holds, and opens a desk item | Set aside as bug-61: only the terminal command reaches it |
| F3 | should-fix | fixed | `docs/workflow.md` still described the old park | Fixed in this round |
| F5 | should-fix | fixed | The dry run listed a lead ticket as runnable while a parked job's limit held it | Fixed in this round, with a new test |
| F6 | should-fix | report | The Overview doesn't show the rule yet, and f9-29 is held until about Sun 23:12 | Yours to choose: see 3 in the sheet |
| F4 | nit | later | Code for the old park is still there | Set aside as bug-62 |
| F7 | nit | fixed | f9-29 said to keep a pace-line function that doesn't exist | Reworded |
| F8 | nit | report | The idle line doesn't count a fast lane lead ticket held by a resting window | Not fixed: rare and short, and the run picks it up by itself |

**F1's choice:** I made the review wait for its fix rather than exempting fix tickets from the line. An exemption would be a new exception to ADR 44, while the fast lane and the lever already get a fix past the line.

What held up when I looked for trouble:
- **The 5-hour window:** a lead ticket still parks there only when nothing else can run, in the last 10% too. A park whose reset has passed, over the week's line, ends and leaves the desk.
- **The last 10% in a real run:** `at_five_hour` lets a ticket go at 72% of the week with the 5-hour window under its mark, and the lead's job checks no other allowance. No test runs that whole path, but the pick's tests and this reading agree.
- **"Until about":** `lead_goes_at` can't return nothing for Claude's windows, because `_windows_from` drops a reading with no reset, so the `max()` in the idle line is safe.
- **Fast lane or lever at 100% of the week:** one job can start and be refused, then it parks and the window rests. That was already so, and ADR 44 says the limit is real.

What held up in round 2:
- **f219-03's return:** the row is finished and no stop recorded, so no crate lingers on the line, and `due_reviews` lists the card again only once the fix is in `done/`. A fix parked for a real limit or a resting window waits the same way, which is the right result too.
- **Its tests:** they replace `_passed_over` and the queue, so they cover the loop's decision, not the real windows. The pace rule and the lever's reading have their own tests from f219-01, so this is enough.
- **The dry run's fix (F5):** `dispatch.plan` orders its lines without looking at the windows, so pairing the two plans line by line is sound.

Checkpoints: none read these tickets, so there's nothing to judge and no "missed".

## What was set aside
bug-61 and bug-62 are on the board as seeds. F6 and F8 are only reported here.

## Workflow observations
- **How the flow went:** two tickets, both first attempts, no stops and no interventions from you. Opus was right for f219-01, and Sonnet for the rewrite.
- **What to change:** when a plan's "Done when" counts on a ticket from another card, the plan should say what happens if the new rule holds that ticket. Here, the rule F219 added holds the ticket that was meant to show it. That is advice for planners, not a gate. Also, a new return value of `review_milestone` should be followed to each of its three callers: f219-03's ticket said "whatever `park` is" and named only the queue's path. That is advice for whoever writes such a ticket, not a check.

<!-- runner report -->
<!-- /runner report -->
