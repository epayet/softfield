# Review: F6, the planning room

- **Status:** reviewed (round 1, 2026-10-08), waiting for the owner's sign-off
- **Stop reason:** none. Round 1 found 3 should-fix points and 1 nit. The lead fixed the 3 should-fix points (all small) and put the nit in the backlog. No ADR is needed.

## Sign-off sheet

### 1. What changed
- **`/planning` is your desk**, on a phone too. From top to bottom:
  - what the factory is doing now and when your next reply is due;
  - the lead's 5-hour window;
  - what is **Coming** (dashed orange: a plant or a message on its way);
  - what **didn't go through**, with your words, Try again and Dismiss;
  - the lead's replies waiting for your answers;
  - proposals to review;
  - finished milestones to talk through;
  - seeds nobody has asked about yet;
  - and **Archived** threads at the bottom.
- **Plant an idea** writes a seed card at the runner's next pick. "Plant and ask the lead" also opens its thread.
- **A thread** shows the conversation. The lead's latest points are agreed by default: Comment… only where you disagree, then Send. What you sent shows at once, marked "Sent", and the Send box goes until the lead replies.
- **A proposal's review page** shows its key points, plus Send back, Accept ADR, Approve plan or Plant it. Mock-ups show in a sandbox. For a plan or a replan, it also shows every ticket and doc that approving would change, with their text.
- **The lead spots duplicates** and proposes to merge them. Approving closes one and keeps the conversation in the other.
- **Pause and Resume** sit in every page's top bar. The bar says whether the factory is running, idle, pausing, paused or waiting, and says when the lead is answering while paused. **While paused**, your messages, approvals, plants and priority changes still apply within 5 seconds, and the lead still answers. Nothing else starts.
- **A replan can change a running milestone's ready tickets**, and only when you approve it. Approving lifts your pause.
- **↑ / ↓ priority** on Next in line and on the Milestones page. **Remove seed** on an idea's thread. Notifications while a dashboard page is open.

### 2. How to test it yourself
1. On your phone, on the home Wi-Fi, open `/planning`. Plant an idea with a short note. It should show under Coming at once. After the runner's next pick, it should be under Seeds.
2. Press **Pause** in the top bar. The bar should say "Pausing after this job", then "Paused by you".
3. While paused, open the new seed's thread, write a question and Send. Your message should show as "Sent". Within about a minute of the runner holding, the bar should say the lead is answering, and its reply should arrive with numbered points.
4. Comment… on one point and Send. If the lead proposes a plan, open it. Check that the review page lists the tickets it adds, with their text, then Approve plan. The tickets should appear in Next in line.
5. Move one ticket up with ↑ on Next in line. It should move at once and stay moved after the next pick.
6. Press **Resume**. The factory should take the next ticket.
7. On the laptop with notifications turned on, leave a page open and plant a question: a notification should come with the lead's reply.

### 3. Left for later
- From F6's "Later": cancel or edit a message before the lead picks it up (f14-03 is ready), parallel planner jobs, a streaming reply, a pause that stops a running job.
- The milestones you planted during F6 are ready, by priority:
  - F20 data safety: the daily Dropbox backup (f20-01, f20-02); I'd run it first;
  - F21 lead briefs: f21-01 to f21-03;
  - F31 settle and reject: f31-01 to f31-05;
  - F13 and F14 fixes: f13-01, f14-01 to f14-03;
  - and F9's line polish tickets.
- One test nit in [`docs/backlog.md`](../backlog.md) (f6-planning-room-C542-1).

### 4. Decisions waiting for you
- [ADR 23, parallel lanes](../adr/23-parallel-lanes.md): Proposed, and marked "to review after F6". Now is its time. It is not needed to sign F6 off.

### 5. How the work went
- 2026-10-06 16:47 → 20:25 ([1647](../sessions/2026-10-06-1647.md), [1940](../sessions/2026-10-06-1940.md), [2007](../sessions/2026-10-06-2007.md), [2025](../sessions/2026-10-06-2025.md)): the lead's runner tickets f6-01 to f6-05 and f6-11, all merged first time, each in a short session.
- 2026-10-06 23:42 ([2342](../sessions/2026-10-06-2342.md)): f5-12 notifications and f5-18 pause, both merged.
- 2026-10-07 00:51 ([0051](../sessions/2026-10-07-0051.md)), 445 min: f6-12 merged. Qwen got 0 of 4 page tickets (f6-07 to f6-10): it read for 10 minutes without an edit, or timed out. Opus finished all four.
- 2026-10-07 08:56 → 13:02 ([0856](../sessions/2026-10-07-0856.md), [0923](../sessions/2026-10-07-0923.md), [0953](../sessions/2026-10-07-0953.md), [1302](../sessions/2026-10-07-1302.md)): f6-13 to f6-18 merged.
- 2026-10-07 13:38 ([1338](../sessions/2026-10-07-1338.md)), 217 min: f6-19 to f6-22 merged; f6-21 took Qwen 3 attempts.
- 2026-10-07 21:33 → 22:31 ([2133](../sessions/2026-10-07-2133.md), [2231](../sessions/2026-10-07-2231.md)): the checkpoint fix tickets. f6-29 was escalated and finished by the lead; f6-24 and f6-30 merged.
- 2026-10-08 02:39 → 03:35 ([0239](../sessions/2026-10-08-0239.md), [0244](../sessions/2026-10-08-0244.md), [0335](../sessions/2026-10-08-0335.md)): f31-06 (refused words on the desk) merged.
- **Lessons:**
  - A page ticket that has to read new modules is past Qwen. Split it to one template or one function on an existing pattern (lead.md, Known range).
  - Assert a page's text after stripping tags, within the item. A test that only checks that a button exists can't catch what the button posts. Both are now worked examples in developer.md.
  - When a count doesn't match, find the extra row before changing the expected number (developer.md note 10, sharpened twice).
  - Assert what the browser draws, not the attribute that should cause it. The layout check now skips closed `<details>`.

### 6. What next
- **Factory:**
  - Run F20 (the backup) next. Planning threads and ratings live only in the metrics database.
  - Then F21: lead briefs that are shorter and cheaper.
  - Write the page tickets as one template on an example, or route them to the lead. On F6's page work, delegating cost $10.40 more than doing it.
  - Review ADR 23 (parallel lanes) now that the planning room exists.
- **Product:** on hold, as you asked (2026-10-04). Once the factory settles, the planning room is the place to plant Mum's next ideas: a seed planted from the phone becomes a planned milestone without a terminal.

### 7. What clogged the factory line
I can't query the metrics database from this review job, so these hours are the session reports' durations, not `usage_events`.
- **Qwen on the page tickets:** about 7.4 h overnight on 2026-10-07 for 1 merge. 12 attempts timed out or stopped without an edit before Opus finished all four tickets. *Unclog:* split page tickets (now in Known range), or route them to the lead when they wire new modules (owner, 2026-10-07).
- **f6-21:** 3 Qwen attempts over 118 model-minutes for a 3-point ticket. *Unclog:* the same.
- **Short sessions:** almost every session ended with "the runner needs a fresh process" after a lead ticket changed `runner/`. The runner restarts itself (`runner/cli.py`), so this cost minutes, not hours. Nothing to change.

## What was built
Tickets f6-01 to f6-30 (see [the milestone](../milestones/f6-planning-room.md) and its two replans, f6-05 and f6-19), with f5-12, f5-18 and F31's f31-06. All 30 merged.
- **Runner:** `runner/planner.py`, which covers threads, the prompt, the reply block, drafts on `plan/<card>` and plan changes. In `runner/requests.py`: every planning request kind, approvals that pre-flight tickets and refuse what only the owner sets, merges, replans, priority, archive and dismiss. In `runner/loop.py`: planner jobs and the hold while paused.
- **Dashboard:** `factory_dashboard/planning.py` with the desk, thread and proposal pages. Also the top bar's status, notifications, and the phone "deck".

## Findings and resolutions
Round 1. The checkpoints' seven findings were all real, and fix tickets f6-25 to f6-30 resolved six of them before this review; the seventh (C542-1, a nit) went to the backlog.

| Id | Grade | What | Resolution |
|---|---|---|---|
| f6-planning-room-F1 | should-fix | Coming took a dead run's job as running, so its reply time ("after f1-04-live") disagreed with the tile above it ("at the factory's next pick") | Fixed by the lead: Coming keeps the live jobs, as the tile does. New test. |
| f6-planning-room-F2 | should-fix | A pending plant whose value isn't a JSON object made `/planning` and the Overview fail with a 500 until the runner refused it (`POST /requests` stores any value) | Fixed by the lead: both read the title leniently through `owners_words` (F31 D9), "Your idea" when there is none. New test on both pages. |
| f6-planning-room-F3 | should-fix | A Coming test said the thread moves to Your answers wanted but checked the general thread, which was there from the start | Fixed by the lead: it checks F6. |
| f6-planning-room-C542-1 | nit | Two Next in line tests read the row's `title` from the rest of the page | Backlog |

All three should-fix points were in diffs the checkpoints read (f6-20, f6-27 and f6-15), so they count as missed. No French to check: F6 is factory work, and the dashboard stays English (ADR 00 A2).

## Workflow observations
- The checkpoints worked: 7 of 7 findings were real, and Qwen fixed 5 of them in one attempt each, as small tickets. The review's three findings sat beside the code those checkpoints looked at. Two of them came from inconsistencies between neighbouring functions (a live filter, lenient reading), which a checkpoint reading one diff at a time is likely to miss.
- The planning room was used for real during its own build: F13 to F40 were planted from it, and F31's refused-words feature came from a failure the owner saw there.

<!-- runner report -->
## Numbers

_Written by `uv run runner report f6-planning-room` from the metrics database, which isn't in git: a snapshot. Run it again to refresh; edit outside these markers._

| Result | F6-PLANNING-ROOM |
|---|---|
| Tickets merged | 30 of 30 |
| First-attempt pass rate | 7/15 (47%) |
| Local attempts | 32 |
| Escalations, directions, checkpoints | 6, 8, 5 |
| Review rounds | 0 |
| Findings | 1 blocking, 4 should-fix, 2 nit |
| Local model | 55.9M tokens (55,488,978 in, 457,555 out) |
| Claude | $51.98 (11.9M token-equivalents) |

### Savings from delegating

What Claude would have spent writing the lines the developers merged, against what it spent supporting them: tickets, directions, escalations, and a share of the reviews and checkpoints (f1 D7). API-equivalent dollars.

| Developer | Tickets | Lines | Doing it itself | Supporting | Net |
|---|---|---|---|---|---|
| **All** | 15 | 656 | $5.50 | $15.90 | **-$10.40** |
| local-qwen3.6-35b-a3b | 15 | 656 | $5.50 | $15.90 | **-$10.40** |

Tokens underneath: doing it itself ≈1.1M token-equivalents, supporting ≈3.2M.

### By agent

| Agent | Jobs | Tokens (Claude: token-equivalents) | Dollars |
|---|---|---|---|
| claude-opus | 31 | 11.7M | $51.24 |
| claude-sonnet | 4 | 155k | $0.74 |
| copilot-auto | 1 | 0 | $0.00 |
| local-qwen3.6-35b-a3b | 32 | 55.9M | $0.00 |

### Trends

| Milestone | Merged | First-attempt | Attempts | Claude | Net savings |
|---|---|---|---|---|---|
| m1 | 5 | 4/5 (80%) | 7 | $1.51 | -$0.63 |
| m2 | 4 | 4/5 (80%) | 6 | $3.45 | -$2.63 |
| m3 | 10 | 10/11 (91%) | 13 | $4.95 | -$1.09 |
| m4 | 11 | 7/11 (64%) | 28 | $1.02 | $12.38 |
| f1 | 48 | 15/22 (68%) | 45 | $83.85 | $33.71 |
| f6-planning-room | 30 | 7/15 (47%) | 32 | $51.98 | -$10.40 |
| bugs | 0 | - | 0 | $0.00 | $0.00 |
| f2 | 12 | 1/3 (33%) | 9 | $39.43 | -$2.95 |
| f3 | 25 | 2/16 (12%) | 50 | $54.52 | -$18.83 |
| f4-always-on | 31 | 10/21 (48%) | 42 | $26.27 | -$3.99 |
| f5-board | 8 | - | 0 | $16.16 | $0.00 |
| f7-factory-fixes | 7 | - | 0 | $12.96 | $0.00 |
| f8-one-queue | 11 | 2/3 (67%) | 5 | $24.14 | $1.23 |
| f9-line-polish | 9 | 4/9 (44%) | 21 | $2.18 | $4.05 |
| f10-crates | 0 | - | 0 | $0.00 | $0.00 |
| f11-test | 0 | - | 0 | $0.50 | $0.00 |
| f12-turn-on-notifications-little-feedback-button | 0 | - | 0 | $1.86 | $0.00 |
| f13-planting-idea-ui-feedback | 0 | - | 0 | $0.52 | $0.00 |
| f14-coming-planted-ideas-not-clickable | 0 | - | 0 | $0.87 | $0.00 |
| f15-reprioritising-tickets | 0 | - | 0 | $0.00 | $0.00 |
| f16-planning-still-says-your-answer-wanted | 0 | - | 0 | $0.42 | $0.00 |
| f17-tighter-running-and-pause-presence-in | 0 | - | 0 | $0.94 | $0.00 |
| f18-arrow-to-reprioririse-queue | 0 | - | 0 | $0.00 | $0.00 |
| f19-will-i-need-to-refresh-planning | 0 | - | 0 | $0.65 | $0.00 |
| f20-data-safety | 0 | - | 0 | $0.00 | $0.00 |
| f21-lead-briefs | 0 | - | 0 | $0.00 | $0.00 |
| f22-move-archive-button-on-planning-desk | 0 | - | 0 | $1.02 | $0.00 |
| f23-when-i-click-comment-on-the | 0 | - | 0 | $1.00 | $0.00 |
| f24-bug-when-i-answer-a-ticket | 0 | - | 0 | $0.45 | $0.00 |
| f25-whenever-i-plant-something-does-it | 0 | - | 0 | $0.67 | $0.00 |
| f26-i-want-to-see-numbers-next | 0 | - | 0 | $0.53 | $0.00 |
| f27-when-i-pause-the-factory-i | 0 | - | 0 | $1.09 | $0.00 |
| f28-the-first-time-i-clicked-on | 0 | - | 0 | $0.65 | $0.00 |
| f29-the-top-was-saying-resuming-but | 0 | - | 0 | $0.62 | $0.00 |
| f30-on-conversations-i-want-to-the | 0 | - | 0 | $0.59 | $0.00 |
| f31-when-i-click-on-approve-plan | 0 | - | 0 | $0.67 | $0.00 |
| f32-the-5-hour-lead-s-window | 0 | - | 0 | $0.59 | $0.00 |
| f33-overview-now-check-all-how-long | 0 | - | 0 | $0.73 | $0.00 |
| f34-planner-tasks-cannot-be-paused-but | 0 | - | 0 | $0.39 | $0.00 |
| f35-when-i-m-reviewing-what-s | 0 | - | 0 | $0.00 | $0.00 |
| f36-whenever-the-planner-is-planning-and | 0 | - | 0 | $0.00 | $0.00 |
| f37-in-planning-mode-it-tends-to | 0 | - | 0 | $0.00 | $0.00 |
| f38-the-refresh-prompt-causes-layout-shifting | 0 | - | 0 | $0.00 | $0.00 |
| m0 | 0 | - | 0 | $0.00 | $0.00 |
| **All** | 211 | 66/121 (55%) | 258 | $337.17 | $10.85 |
<!-- /runner report -->
