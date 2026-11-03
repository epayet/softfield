# Review: F139, the folder is `.softfield`

## Sign-off sheet

### 1. What changed
- **Softfield's files now live in `.softfield/`, not `.factory/`,** in Softfield, Coucou and Travel Companion. You shouldn't notice anything else: the dashboard shows the new path in the same two places, and all three projects' commit hooks point at the new folder.
- **What keeps the word "factory":** `factory_dashboard/`, `~/.config/softfield/factory.toml`, the `factory` area and the page styles, as you agreed in the plan.
- **This review fixed one thing the move broke:** approving F133's plan would have been refused, with about 1,100 files named as outside the plan. Its page would have listed them all too. Approving a plan that hasn't caught up with main now counts only the plan's own changes.
- **It also repaired F139's own card,** where the move had turned your note into "the .softfield folder should actually be .softfield".

### 2. How to test it yourself
1. Open F133 on the board and look at its proposal. Its file list should show only the plan's own files, about six rather than a thousand.
2. Approve it if you still want that plan. It should go through. It was drafted on 2026-10-27, so you may prefer to send it back for a refresh; that also works.
3. Open F139's card. The title should read "Projects keep Softfield's files in .softfield, not .factory".
4. Let the next ticket run in Coucou or Travel Companion. It should pick up, run and merge as usual.

### 3. Left for later
- **bug-55:** replaying a ticket merged before the move on the bench would crash, because its old tree has no `.softfield/protected-paths.txt`. I found this by reading the code and didn't run a replay. The bench last ran on 2026-10-07, so it can wait.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-27: one planning job drafted the plan ($1.40), and you approved it on 2026-10-28.
- 2026-11-02: you chose to move all three projects in your terminal session while the runner was stopped, each guarded by its full check. Softfield's move was 1,392 files in one commit, `ffa04854`, plus one commit on each open branch. The script wasn't kept and f139-02 was dropped. No developer or checkpoint saw it.
- 2026-11-03: this review, round 1. It fixed two findings itself and set one aside.
- **Lessons:**
  - Passing every check on the moved tree didn't prove the moved branches still worked. The checks look at one tree, and approval compares across history. The plan promised approval would work as before, and nothing tested that, because the script and its tests were never built.
  - A blind find-and-replace damages the one document that has to name both the old and the new. Only F139's own records were affected; a search for such contrasts found no others.

Session reports: [2026-11-02 22:10](../sessions/2026-11-02-2210.md) is the first run after the move.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Look at F133 next: it has waited since 2026-10-27 and was the one live plan this bug would have stopped.
  - Next time a one-shot script rewrites history-sensitive state, try the real next step on one branch (here, an approval) before calling it done. I don't think this needs a rule yet.

### 7. What clogged the factory line
From the jobs table and the commit dates. Almost none of this card's 19 days was lost to the factory.
- **Waiting its turn, about 12 days** from planting on 2026-10-15 to the plan on 2026-10-27, then **about 5 days** from approval to the move on 2026-11-02. It wasn't urgent, and the board's order decided. **To unclog:** nothing.
- **The review's wait, about 13.5 hours,** from the move at 20:19 to the start of this review at 09:50. Reviews were being parked for Claude's limits that night ([session](../sessions/2026-11-02-2210.md)), and F175's and F127's reviews ran first. The database doesn't split those hours between the causes. **To unclog:** nothing for one night's wait.
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
| F1 | blocking | A moved plan branch that hadn't caught up couldn't be approved, and its page listed the whole move | `planner.plan_range`: main against the two merged, the old range on a clash; used by `_drafts` and `plan_changes`; three tests, the two on the fault seen failing with the fix undone; the full suite passes (2,934) |
| F2 | should-fix | The text pass rewrote F139's card, done ticket and planning export into nonsense, including the owner's note | Restored `.factory` where the old folder is meant |
| F3 | should-fix | A bench replay from before the move crashes on the missing protected-paths file | Set aside: bug-55 |
| F4 | nit | Stray one-word docstring lines from rewrapping, in `runner/metrics.py:558`, `runner/bench.py:7`, `runner/milestone.py:488`, `runner/planner.py:234` | Reported only |
| F5 | nit | The forgotten test projects' rows still name `.factory` | Reported only: their folders are gone, so the paths lead nowhere either way |
| F6 | nit | Old session reports and reviews name a folder that didn't exist when they were written | Reported only: D2 chose this, and it keeps their links working |

**On F1:** I fixed the comparison rather than merging main into `plan/f133`, because this job can't change a branch and the same fault would catch any other branch behind a change main also made. A planner reply on the thread would also have repaired the branch, since it catches up first, but that means asking you to send it back for a problem you didn't cause. `_renumber_mentions` (`runner/requests.py`) still reads the old range. It only touches files that mention the ADR being renumbered, and F133's drafts hold no ADR, so I left it.

**French:** no change in this milestone.

**Checkpoints:** none ran, so there is nothing to judge.

**How the commits were found:** none named a ticket id, so I used `git log -i --grep=f139`: `ffa04854` (the move), `78aaa8ec` (the session's cards) and the branch commits. Other projects' moves are in their own repos.

## Factory
- **Flow:** no run, no limits hit by this work and no parks of its own apart from the review's night wait. The owner stepped in once, by choice: moving everything by hand while the runner was stopped, which avoided the self-restart in D5.
- **Models:** Opus planned and reviewed. No local model work, as the plan said.
- **What to change:** nothing in the workflow. The plan's route (a tested `move_home`, then the runner's start) would have cost two lead tickets and left migration code behind; the owner's route cost one bug and one review fix. For a move that happens once, that was the better trade, and the review caught the gap.

## Workflow observations
- A change built outside the runner reaches the review as its first and only reader. That worked here, as it did for F127, but both reviews found a blocking bug that passed every check.
- The bench isn't exercised by any regular work, so a break like F3 stays silent until someone wants a replay.

<!-- runner report -->
<!-- /runner report -->
