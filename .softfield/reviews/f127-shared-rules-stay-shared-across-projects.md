# Review: F127, the factory is optional

## Sign-off sheet

### 1. What changed
- **Projects look normal again.** The factory now leaves only its `.softfield` folder in a project. Travel Companion has no `AGENTS.md`, `CLAUDE.md` or `opencode.json` left at its root. Coucou keeps an `AGENTS.md` with its own rules.
- **Agents the factory starts get its rules directly,** in their system prompt, instead of being asked to read a file. Local models sometimes skipped that step. A project's own `opencode.json` can't block the developer any more.
- **A plain `claude` or `opencode` in a project now stays plain.** To be the lead in a terminal, you start `softfield lead`.
- **Lessons reach every project.** The shared rules and lessons live in Softfield, so updating Softfield updates them all, with nothing copied around.
- **This review fixed two things that were broken:**
  - `softfield lead` did nothing at all: it exited without starting Claude.
  - A developer writing down a discovery, as its rules tell it to, would have failed its ticket. No run has hit this yet.

### 2. How to test it yourself
1. In a terminal in Softfield's folder, start `softfield lead`. Claude should open, and it should know your preferences if you ask about them. I tested this with Claude's start faked, not with a real session, so this is its first real run.
2. In Travel Companion's folder, start a plain `claude` and ask what it knows about Softfield. It should know nothing about the factory.
3. On the dashboard, let the next developer ticket run. It should pass or fail as usual, with its rules in place and no complaint about a missing file.

### 3. Left for later
- **f127-02, who reads what:** the Projects page listing each role's files and where they come from. It needs a mock-up first.
- **bug-54:** `softfield init` replaces a repo's own git hooks setting without saying so. No project here uses one, so it matters once others use Softfield.

### 4. Decisions waiting for you
None.

One thing to know: [ADR 41](../adr/41-the-factory-is-optional.md) says removing the factory means deleting its folder. That is nearly true, because one git setting stays behind (finding F3). The folder's README now says so. I left your accepted ADR's wording alone.

### 5. How the work went
- 2026-10-27 and 2026-10-29: three planning jobs drafted and rewrote the ADR with you ($4.53 together; [the last one's session](../sessions/2026-10-29-0914.md)).
- 2026-11-02: built in your terminal session, one commit (`2887ea89`), so no developer or checkpoint saw it. No local model work.
- 2026-11-03: this review. Round 1 made six fixes itself ($2.76). Round 2 re-read them, found them sound and changed no code.
- **Lessons:**
  - Testing the pieces isn't testing the command. All 2,926 tests passed while `softfield lead` did nothing, because the tests called the function behind it and never the command itself. There is now a test through the command.
  - Moving a file can change which rules apply to it. The discoveries file moved into a protected folder, and only one of the two gates had an exception for it.
  - A review needs to be told when it found nothing. The runner told this one its commits were "none", because the ticket was written after the commit and the commit didn't name it. It now says where to look instead.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Try `softfield lead` first: it is the one thing here that no real session has run.
  - In the next terminal session in Coucou and Travel Companion, copy the new README wording into their `.softfield` folders (finding F10).
  - A lesson that holds everywhere now needs a Softfield card to travel (ADR 41 item 7), so watch whether the reviews actually suggest them.

### 7. What clogged the factory line
From the jobs, runs and usage tables. Very little was lost to the factory: most of this card's 19 days from planting to build were a design waiting its turn and your review of it.
- **Waiting for the owner's session, about 4 days.** The last planning job ended on 2026-10-29 and the ADR was settled in your terminal session on 2026-11-02. That was deliberate: you rewrote it twice. **To unclog:** nothing.
- **The review's wait, about 13 hours.** The commit landed on 2026-11-02 at 20:35 and this review started on 2026-11-03 at 09:21. The review was parked at least twice that night ([session](../sessions/2026-11-02-2210.md)), and Claude's 5-hour limit refused a job at 22:32. F175's review also went first. The database doesn't split those hours between the causes. **To unclog:** nothing for one night's wait.
- No failed attempts and no stops for you.

## What was built
[ADR 41](../adr/41-the-factory-is-optional.md), in commit `2887ea89`:
- **OpenCode:** `opencode_config` in `runner/local_model.py` builds each run's config, passed through `OPENCODE_CONFIG_CONTENT`.
- **Claude jobs:** `--append-system-prompt`, with the same text on a resumed session.
- **Copilot:** still pasted in the prompt.
- **The package:** instructions moved to `runner/instructions/`, the author's opinions to `author/`, replaceable from `~/.config/softfield/`.
- **`softfield init`:** writes only inside the dot folder.

## Findings and resolutions
| Id | Grade | Finding | Resolution |
|---|---|---|---|
| F1 | blocking | The protected-paths gate refused `.softfield/discoveries.md`, where the rules send a developer's discoveries | That one file passes; test seen failing first |
| F2 | blocking | `softfield lead` was never routed, so it exited without starting Claude | Routed; test through `main`, seen failing first |
| F3 | should-fix | The README said nothing changes for you, but `init` sets `core.hooksPath`, which also outlives the folder | README says so and gives the removal command; test extended; Softfield has its own copy now |
| F4 | should-fix | Claude lead jobs lost the rules on scope, dependencies, Accepted ADRs and tests | One line in lead.md's "Your own work"; test seen failing first |
| F5 | should-fix | A review with no commit found by ticket id was told "none" | The prompt says how to find them and to report it; test seen failing first |
| F6 | nit | Stale pointers after the move, and prompts broken mid-line, one through inline code | Corrected |
| F7 | nit | `init` overwrites a repo's own `core.hooksPath` | Set aside: bug-54 |

**On F4:** I did not inject `rules.md` into lead jobs. Its "never edit a protected path" and "nobody is there to answer" are wrong for a lead, whose job is often exactly that. So its title now says it is for developers, and lead.md holds the part that applies.

Said here only (route `report`):
- **F8:** the review prompt, lead.md and task-format.md cite `docs/workflow.md`, which the package doesn't ship (against ADR 41 item 8). Your machine runs from `live`, which has it. F204's notes already carry this for tickets, and the fix belongs with that packaging work: move the review loop into `runner/instructions/`.
- **F9:** from reading the code, not seen happening: a malformed `.softfield/opencode.json` would raise out of `run_opencode`. Only a lead edits that file. If it ever happens, add a check to `softfield doctor`.
- **F10:** Coucou's and Travel Companion's READMEs keep the old wording from F3. They are those projects' own files and this job works in Softfield only, so the next terminal session in each copies the new text.
- **F11:** a review's own fixes don't get the line F4 added, because a review isn't given "Your own work". Its fixes are small, so the risk is low. If a review ever breaks one of these rules, repeat the line under "Review".
- **F12:** the runner's `-metrics.md` says the local model built this card's ticket, which it didn't, and credits the card with about 144M token-equivalents, because it adds up every transcript since the card's start tag. Nothing reads that file now that `softfield report` gives the numbers, so stop writing it when that code is next touched.
- **F13:** the search F5 suggests has no word boundary, so `f12` also finds `f127`. It can only add noise, not hide a commit. If it ever misleads a review, add a word boundary.

**Round 2:** I re-read the whole fix diff against each finding. F1 to F6 are resolved, and no fix brought a new problem.
- **F1:** the test also pins that a neighbouring `.softfield` file is still refused, and OpenCode's permissions allow the write.
- **F2:** I read argparse's code in Python 3.13: it drops the `--`, so Claude gets the arguments as options. This is still not run against a real Claude, which is why it's your first test above.
- **The fixes' tests:** they only add. The one existing test changed, the removal test in `test_setup.py`, gained checks and lost none.
- **Checks:** `softfield check-all` passed in full on main. F11 to F13 are new and only reported, as they are small and F11 and F12 sit in code the fixes didn't touch.
- **French:** none in the fixes either.
- **Score:** still 6, because the score is about what was built, and the fixes don't change that.

**What was checked in round 1:**
- **The scope:** the runner listed no commits for this card (F5). I reviewed `2887ea89`, which the card and the ticket name, and read its code and tests in full. Its edits to docs, ADRs and cards I saw only as a list of files, apart from grepping the factory's code and instructions for old paths. I left the other commits in the range out. The ticket quotes a commit subject that doesn't exist; `2887ea89` is the closest match.
- **Tests:** before the fixes, 2,926 of 2,926 passed on 16 workers, in 3 min 16 s. After them, `softfield check-all` passed in full (ruff, format, mypy, translations, layout, tests).
- **Edited tests:** the commit changed many, nearly all to follow the moved paths. The real changes follow from the decision:
  - The two tests on `owner.md` not being pasted twice went, with the `imports` function they pinned.
  - The resumed-session test now expects the brief on every run, which is what a system prompt needs.
  - The planner test was rewritten the same way and is no weaker.
- **The two other projects:** I checked which files they hold. Both have the new `.softfield` files. Coucou's permissions keep `msgfmt`, and Travel Companion's `BLOCKED.md` stays out of git.
- **Not checked by me:** the card's three proofs (a captured request on a hostile `opencode.json`, a clean install of the package, equal token cost on resume). They were done in the terminal session, and I took them from the card.
- **French:** none, as the commit touched no translations.
- **Checkpoints:** none ran on this card, so there is nothing to judge.

Score 6: the design is sound and simple, and the card records real proofs of its riskiest part. But the card's one new command did nothing, and an everyday developer rule would have failed a ticket. A single large terminal commit had no checkpoint to catch either.

## Set aside
bug-54, from F7.

## Factory
- **Flow:** one lead ticket, built in a terminal session, with no stops and no escalation. Planning took three jobs and two rewrites with you, which was the valuable part: it replaced copying files with injecting them.
- **Models:** planning on Opus, $4.53; the review's first round on Opus, $2.76. The terminal session's cost isn't in the numbers, and round 2's wasn't when this was written. No local model work.
- **The gap:** a commit of 103 files built in a terminal gets no checkpoint, so the review was its first reader.
- **What to change:**
  - F5 makes the empty list visible, and lead.md already asks for the ticket's id in the commit subject. A ticket written after its commit is what breaks that, so write it first.
  - A new command should get a test through `main` (F2). I added this one; a general check isn't worth it yet, so I'd make one only if it happens again.

<!-- runner report -->
<!-- /runner report -->
