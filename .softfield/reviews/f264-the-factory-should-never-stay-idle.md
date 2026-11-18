# F264 review: the factory should never stay idle

- **Status:** done, signed off by the owner on 2026-11-18.

## Sign-off sheet

### 1. What changed
- **The line no longer stops for Claude's pace.** Over the week's pace line, past the week's 70% mark or past the 5-hour window's 75% mark, developer tickets still go first. When none can start, the runner now takes the next lead ticket in the board's order instead of sitting idle. Only Claude's real limit stops lead work: a window at 100%, or a window resting after a refusal.
- **Nothing parks at the 5-hour mark any more.** A lead ticket, a review, a direction, an escalation or a checkpoint goes on past 75%. The desk item "waits for Claude's 5-hour window, kept for you" is gone, and an older run's park and item are cleared when a run starts.
- **The dry run and the idle line say the same thing.** A lead ticket held by the pace reads "goes when nothing else can (Claude's week over its pace)". The idle line counts a lead ticket as waiting only at the real limit, and says until when ("for Claude's week · until about Mon 16:00").
- **The Overview's words match.** Over the pace, the plate reads "Over pace · developers first; the lead takes over when nothing else can run", and a lead row reads "goes when nothing else can". At 100% they read "lead tickets wait until about …" with the reset. Both marks read "lead tickets go last from here". The levers read "keep board order", and the legend says what the mark, the post, the stripes and the levers now do.
- **The review's own fixes:** the lead row now asks the runner's own limit check, so a full 5-hour window shows "waits for Claude until about 17:00" instead of "goes when nothing else can". The lever's tooltip, its desk item and `docs/workflow.md` now describe the new rule, and the legend's post and stripe lines no longer say lead tickets stop.

No mock-up (words only, on existing elements), so there is nothing to compare.

### 2. How to test it yourself
1. On a day like 2026-11-18 (the week over its pace, every developer ticket waiting for a lead ticket), open the Overview on your phone. Claude's week plate should read "developers first; the lead takes over when nothing else can run", and the first lead row in Next in line should read "goes when nothing else can".
2. Watch the floor: within a pick, a lead ticket should be on Claude's bay, with no "Idle" line.
3. When a developer ticket is free, it should go before the lead ticket.
4. Open "How to read the allowance": the mark's line should say "only 100% makes them wait", and the levers should read "keep board order". Long-press a lever: its tooltip should say "Keep the board's order past …".
5. Past 75% of the 5-hour window, nothing should appear in Needs you, and lead work should go on.

### 3. Left for later
- The 5-hour switch's old wait machinery is now dead code (see Factory in item 6).
- Two small wording nits, set out under Findings (F7, F9).

### 4. Decisions waiting for you
None. [ADR 50](../adr/50-the-line-never-idles-for-the-pace.md) is accepted, and this milestone is that ADR built.

### 5. How the work went
- **2026-11-18 08:11–08:34** ([session](../sessions/2026-11-18-0834.md) run): f264-01 merged on attempt 1 by Sonnet in 19 min ($1.11). It changed `runner/`, so the runner restarted.
- **2026-11-18 08:35–09:13** ([session](../sessions/2026-11-18-0834.md)): f264-03 merged on attempt 1 by Sonnet in 33 min ($1.03). Claude ≈583k token-equivalents, 0 local.
- **2026-11-18 09:13–11:51** ([session](../sessions/2026-11-18-0913.md)): f264-02 merged by Qwen on attempt 3. Attempt 1 stopped with no edit after 20 min, attempt 2 timed out after 78 min, then an Opus direction ($0.58) repaired the ticket and attempt 3 passed in 58 min. Local 7.7M tokens in, Claude ≈138k.
- **Lessons:**
  - The rule lived in more places than the plan listed: the lever's tooltip and desk item (`loop.SWITCHES`), two legend lines and `docs/workflow.md` still said the old rule. The review fixed them, and ADR 02's log now says that a rule change starts by searching for the rule's own words.
  - The Overview built its own "at the limit" answer beside the runner's. It missed the 5-hour window, which ADR 50 item 7 ("one rule, one path") exists to prevent. It now calls `loop._held_at_the_limit`.
  - A words-only developer ticket still cost Qwen about 2.5 hours. The direction that worked named the phone-layout test and the reset-date trap up front. A ticket that changes text a layout test measures should say so from the start.

### 6. What next
- **Product:** product work is on hold; nothing to suggest.
- **Factory:**
  - With the line never idling for the pace, the week will now usually end at its limit days before the reset (ADR 50, Consequences). Watch how many hours the factory spends at 100% in the next week before tuning anything.
  - > In `runner/loop.py`, remove the 5-hour switch's dead wait machinery F264 left behind (`FIVE_HOUR_HELD`, `Hold.five_hour`, `_five_hour_switched`, `_five_hour_switched_on`, the poll in `wait_for_room` and `wait_for_claude`) and fix `_passing_over`'s docstring, since nothing parks at the 5-hour mark any more.
  - > When a plan changes a factory rule, have the planner grep for the rule's own words (labels, legend lines, desk items, docs/workflow.md) and list every hit in the tickets, because F264's plan missed four of them.

### 7. What clogged the factory line
- **About 6 h idle, 02:04 to 08:11** (the problem itself): the week's pace held all 101 ready lead tickets, and all 40 developer tickets waited for one of them. Only probes and planning ran. Fixed by this milestone.
- **About 50 min of planning, 07:17 to 08:07:** ten Opus planner jobs ($16.64) while the owner and the lead settled ADR 50. That was the owner's own steering, not a clog.
- **About 1 h 38 min of failed Qwen attempts on f264-02** (09:14 to 10:52): one stop with no edit after 20 min, then a 78-min timeout. The direction that unblocked it named the phone layout test. Unclog: a ticket whose words change what a layout test measures names that test and the CSS rule in its first draft.
- **Two runner restarts** after the `runner/` lead tickets (a few minutes each). Expected; nothing to change.

---

## What was built
- **f264-01 lead-fills-the-gap** (Sonnet): `_held_at_the_limit` (both windows as caps on their whole capacity) beside `_passed_over`. In `choose_ticket`, while the pace holds, developer tickets go first, and with none startable the first free lead ticket fills the gap, unless the real limit holds. The dry run's line, and the idle line's count and its "until", come from the same check.
- **f264-03 no-park-at-the-five-hour-mark** (Sonnet): `at_five_hour`, `_at_five_hour` and `_end_unbegun_parks` removed. `claude_hold` lets every support job use both reserves, and an older run's 5-hour parks and desk items are cleared at the start of a run.
- **f264-02 overview-says-the-lead-fills** (Qwen): plate, row, mark, lever and legend words; the lever label wraps on a phone.

## Findings and resolutions
| id | severity | route | what | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | `overview.claude_pace` built its own "at the limit" test from `_passing_over`, which leaves out the 5-hour window. With the week over its pace and the 5-hour window at 100%, the lead row said "goes when nothing else can" while the pick held it. At the real limit it also said "waits for Claude's week pace". | Fixed: the row asks `loop._held_at_the_limit` and names the latest reset of the full windows ("waits for Claude until about …"). New test: the week over its pace with the 5-hour window full. |
| F2 | should-fix | claude | Two legend lines still said lead tickets "start only under" the post and "wait until the post catches up". | Fixed in `_partials/allowance.html`, with asserts in the legend test. |
| F3 | should-fix | claude | `loop.SWITCHES`, the lever's tooltip and aria-label, its console lines and the lapsed-switch desk item still said "Let the factory use the week's reserve" and "your 25% of the 5-hour window". ADR 50 item 6 renames them. | Fixed: "Keep the board's order past the week's pace and mark" and "… past the 5-hour mark". Tests updated. |
| F4 | should-fix | claude | `docs/workflow.md` (Claude's allowance) still described the stop at the pace line, the owner's 25% and the 5-hour park. | Rewritten to ADR 50. |
| F5 | nit | later | The 5-hour switch's wait machinery is dead now that `Hold.five_hour` is always False. | Quoted under Factory in item 6. |
| F6 | should-fix | claude | The 100% plate test asserted only `"until" in plate`, which the plate's own words already contain, so it didn't check the reset time. | Fixed: it asserts the reset date and the lead row's wait. |
| F7 | nit | report | The dry run says "Claude's 5-hour window over its pace", but the 5-hour window has a mark, not a pace line. | Reported only. |
| F8 | nit | report | An older run's queued support row flagged `FIVE_HOUR_HELD` isn't cleared at the start of a run: it waits out its own reset, at most 5 hours, once. | Reported only. |
| F9 | nit | report | `allowance_bar.html` has a `state == "on" and limit` branch that can't occur (the pace line tops out at the mark), duplicating the limit plate. The phone CSS also set `.reading` to `nowrap`, beyond the ticket's "let the lever's label wrap". The layout test passes at 390 px. | Reported only. |

No checkpoint ran (ADR 38: the review reads these merges), so there are no checkpoint findings to judge. Existing tests the developers changed: in f264-01 and f264-03, about 30 tests in `test_loop.py`, `test_dispatch.py` and `test_milestone.py` moved from "waits or parks" to "goes after the developers". Five were removed with the behaviour they pinned (switch-on-during-a-wait and the 5-hour park). Each change follows ADR 50, and the new parametrised cases cover the week and the 5-hour window at their mark, at 100% and with a developer free. In f264-02, `test_planning.py` (outside `files:`) moved to the new plate words, as it had to. No French in this milestone.

## What was set aside
- `milestone._fix_held_by_the_week` still ends a review round when the pace line holds a lead fix ticket. That is still right: the fix now runs as a gap filler after the developers, and the review comes due again when it is done.

## Stop reason
None: round 1 resolved every finding that needed a fix. Score 7.

## Workflow observations
- A plan for a rule change should search for the rule's words first (see item 6).
- The fast lane card went straight in, as it should. Its two lead tickets took 52 min of Sonnet for $2.14, while its developer ticket took 2 h 37 min of Qwen.

<!-- runner report -->
<!-- /runner report -->
