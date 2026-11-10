# Review: F139, the folder is `.softfield`

- **Status:** done, signed off by the owner on 2026-11-10.

## Sign-off sheet

### 1. What changed
- **Softfield's files now live in `.softfield/`, not `.factory/`,** in Softfield, Coucou and Travel Companion. You shouldn't notice anything else: the dashboard shows the new path in the same two places, and all three projects' commit hooks point at the new folder.
- **What keeps the word "factory":** `factory_dashboard/`, `~/.config/softfield/factory.toml`, the `factory` area and the page styles, as you agreed in the plan.
- **Five plans can't be approved yet: F133, F140, F51, F82 and F191.** They were drafted before the move, and they now clash with main in 95 to 169 places. An approval is refused with main untouched, but it names over 2,000 paths, and each plan's page lists them too. Refresh against main doesn't repair them. **f139-03 fixes this and is next in line;** round 1 of this review said it was already fixed, and that was wrong (see Findings). Your other seven open plans aren't affected.
- **A plan on a file main has since renamed can be approved again.** Round 1's fix had broken this, and round 2 repaired it.
- **F139's own card is repaired,** where the move had turned your note into "the .softfield folder should actually be .softfield".

### 2. How to test it yourself
Steps 1 and 2 only work once f139-03 has merged.
1. Open F133 on the board and press Refresh against main. When the lead has replied, its file list should show only the plan's own files, a handful rather than thousands.
2. Approve it if you still want that plan. It should go through.
3. Open another of the five that you haven't refreshed. Its page should say it clashes and to press Refresh, in place of the list of files.
4. Open F139's card. The title should read "Projects keep Softfield's files in .softfield, not .factory".
5. Let the next ticket run in Coucou or Travel Companion. It should pick up, run and merge as usual.

### 3. Left for later
- **bug-55:** replaying a ticket merged before the move on the bench would crash, because its old tree has no `.softfield/protected-paths.txt`. I found this by reading the code and didn't run a replay. The bench last ran on 2026-10-07, so it can wait.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-27: one planning job drafted the plan ($1.40), and you approved it on 2026-10-28.
- 2026-11-02: you chose to move all three projects in your terminal session while the runner was stopped, each guarded by its full check. Softfield's move was 1,392 files in one commit, `ffa04854`, plus one commit on each open branch. The script wasn't kept and f139-02 was dropped. No developer or checkpoint saw it.
- 2026-11-03: this review, round 1. It fixed two findings itself and set one aside.
- 2026-11-03: this review, round 2. It ran round 1's fix on the live branches, found it didn't work for any of the five, and wrote f139-03. It also fixed the regression that fix had caused.
- **Lessons:**
  - Passing every check on the moved tree didn't prove the moved branches still worked. The checks look at one tree, and approval compares across history. The plan promised approval would work as before, and nothing tested that, because the script and its tests were never built.
  - **A fix for a real case has to be run on that case.** Round 1 modelled F133 with one file in a test, and told you F133 would show "about six" files without trying it. The real branch has 169 conflicts, so the fix fell through to the old behaviour. Round 2 found this by running it on the branch. What changes: f139-03 asks for a test built like the real branches, with a ticket main finished and a card it changed.
  - A blind find-and-replace damages the one document that has to name both the old and the new. Only F139's own records were affected; a search for such contrasts found no others.

Session reports: [2026-11-02 22:10](../sessions/2026-11-02-2210.md) is the first run after the move.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Once f139-03 has merged, go through the five stuck plans. F133 and F140 date from 2026-10-27, so some may no longer be wanted. Each Refresh is a planning job, about the $1.40 F133's first draft cost.
  - Next time a one-shot script rewrites history-sensitive state, try the real next step on one branch (here, an approval) before calling it done. This same advice was here in round 1, and I didn't follow it in my own fix, so I now think it deserves a line in the lead's review craft: a fix for a fault seen on live data is tried on that data.

### 7. What clogged the factory line
From the jobs table and the commit dates. Almost none of this card's 19 days was lost to the factory.
- **Waiting its turn, about 12 days** from planting on 2026-10-15 to the plan on 2026-10-27, then **about 5 days** from approval to the move on 2026-11-02. It wasn't urgent, and the board's order decided. **To unclog:** nothing.
- **The review's wait, about 13.5 hours,** from the move at 20:19 to the start of this review at 09:50. Reviews were being parked for Claude's limits that night ([session](../sessions/2026-11-02-2210.md)), and F175's and F127's reviews ran first. The database doesn't split those hours between the causes. **To unclog:** nothing for one night's wait.
- **Five plans have been stuck since the move, 2026-11-02 at 20:20.** Nothing was lost to it yet, as none of the five was approved in that time, but F191 had two more planning jobs drafted on its clashing branch that night. **To unclog:** f139-03.
- No failed attempts and no stops for you.

## What was built
Commit `ffa04854`, made by a script that was not kept:
- **The folder:** `.factory/` renamed to `.softfield/`, ignored files included.
- **Every tracked text file:** `.factory` replaced where no letter, digit, `_` or `-` touches it, so `.card.factory` and `.factory-status` stayed.
- **The code around it:** lines the longer name pushed over the limit were rewrapped.
- **Open branches:** one commit each with the same move. The card counts 15; 12 of those commits are still reachable here.
- **The database:** paths moved for the three live projects.
- **Commit hooks:** `core.hooksPath` is `.softfield/hooks` in all three repos' git settings.

`runner/home.py`, its tests and f139-02 were never built, by the owner's choice recorded on the card. `f139-01` is in `done/` with a footer saying so, so its Done when items weren't met as written.

Checked and sound: before this review's own writing, the only mention of `.factory` as a folder in Softfield's files was one line of F175's review, which is correct history. No `.factory/` is left on disk in Softfield. The dashboard's changes are paths and comments only, with no page style renamed. The live projects' database rows hold no old path.

Coucou and Travel Companion each have `.softfield/project.toml`, no `.factory/project.toml` and no `.factory` mention in a file. This job can't run git in other repos, so I didn't read their move commits or their branches.

Tests: no test was edited for this milestone beyond the move. I listed every test hunk with a line that doesn't name the folder, and they are all line wrapping from the longer name, with no assertion lost. No test covers the move itself, since its script was never kept.

## Findings and resolutions
| Id | Grade | Finding | Resolution |
|---|---|---|---|
| F1 | blocking | A moved plan branch that hadn't caught up couldn't be approved, and its page listed the whole move | **Not resolved; reopened in round 2.** `planner.plan_range` (round 1) is correct for a branch that merges cleanly, but all five such branches clash, so they take its fallback, the old range. Goes to f139-03 |
| F7 | should-fix | Round 1's fix refused a plan editing a file main has since renamed, with a raw `GitError`: `_owners_marks` read the merged path from the branch | Fixed in round 2: `_owners_marks` reads the merged tree (`planner.merged_tree`); new test, seen failing first. The page still shows such a file without its text, as `draft` reads the branch: rare, so reported only |
| F2 | should-fix | The text pass rewrote F139's card, done ticket and planning export into nonsense, including the owner's note | Restored `.factory` where the old folder is meant |
| F3 | should-fix | A bench replay from before the move crashes on the missing protected-paths file | Set aside: bug-55 |
| F4 | nit | Stray one-word docstring lines from rewrapping, in `runner/metrics.py:558`, `runner/bench.py:7`, `runner/milestone.py:488` | Reported only (the one in `plan_changes` went with round 2's docstring fix) |
| F5 | nit | The forgotten test projects' rows still name `.factory` | Reported only: their folders are gone, so the paths lead nowhere either way |
| F6 | nit | Old session reports and reviews name a folder that didn't exist when they were written | Reported only: D2 chose this, and it keeps their links working |

**On F1, round 2.** I ran `plan_range` and `plan_changes` on all twelve open plan branches:

| Branches | Merged with main | Paths listed |
|---|---|---|
| F133, F140, F51, F82, F191 | clash, 95 to 169 conflicts | 2,137 to 2,577 |
| F194, F195, F197, F198, F199, F206, F207 | clean | 2 to 7 |

The seven clean ones started from main after the move, so the fix changes nothing for them. The conflicts come from the branch's move commit: tickets main had finished and moved to `done/` went to `ready/` on the branch, and both sides changed the same text.

Round 1 also said a planner reply would repair a branch by catching it up. It wouldn't: `_catch_up` fails on the same clash, and `_plan_branch` then drafts on the old branch, as `plan/f191`'s two jobs that night show (session of 2026-11-02 22:10).

Why a ticket and not a fix here: the repair moves branches, which this job can't do, and it needs a real design and tests. **The fix proposed in f139-03:** a planner job rebuilds a clashing branch on main from the plan's own commits, keeping the old tip under `superseded/`; until then the page and the approval say to press Refresh. The rebuild hasn't been tried on the real branches; f139-03's test is built like them, and a replay that fails leaves everything as it was.

`plan_range` stays, since it is correct and it is what `_drafts` needs once a branch is rebuilt. `_renumber_mentions` (`runner/requests.py`) still reads the old range, which a rebuilt branch makes harmless.

**The round 2 probe.** To read the live branches I ran two throwaway test files from `/tmp` through `uv run pytest`, as this job's shell allows no other way. They called `git merge-tree` and the code under review, and only added unreferenced tree objects to this repo's git store (git cleans those up). They changed no branch, and they aren't committed.

**Tests of round 1's fix:** they pass and are correct for what they model, but `test_what_main_and_the_branch_both_changed_alike_is_not_the_plans` and `test_a_plan_behind_a_change_main_also_made_is_approved` use a move with nothing else in the way, unlike any real branch. That is how the gap got through.

**Checks after round 2:** `tests/runner` and `tests/factory_dashboard` pass (2,935), run in four parts because one run together hit the job's time limit. ruff passes on the changed files, and mypy on `runner/planner.py` and `runner/requests.py`.

**French:** no change in this milestone.

**Checkpoints:** none ran, so there is nothing to judge.

**How the commits were found:** none named a ticket id, so I used `git log -i --grep=f139`: `ffa04854` (the move), `78aaa8ec` (the session's cards) and the branch commits. Other projects' moves are in their own repos.

## Factory
- **Flow:** no run, no limits hit by this work and no parks of its own apart from the review's night wait. The owner stepped in once, by choice: moving everything by hand while the runner was stopped, which avoided the self-restart in D5.
- **Models:** Opus planned and reviewed. No local model work, as the plan said.
- **What to change:** the lead's review craft should say that a fix for a fault seen on live data is tried on that data before it is called fixed. The plan's route (a tested `move_home`, then the runner's start) would have cost two lead tickets and left migration code behind; the owner's route has so far cost one bug, two review rounds and one lead ticket, with five plans stuck meanwhile. That is closer than I said in round 1: D3's tests, built on a real branch, might have shown the clash before the move.

## Workflow observations
- A change built outside the runner reaches the review as its first and only reader. That worked here, as it did for F127, but both reviews found a blocking bug that passed every check.
- The bench isn't exercised by any regular work, so a break like F3 stays silent until someone wants a replay.

<!-- runner report -->
<!-- /runner report -->
