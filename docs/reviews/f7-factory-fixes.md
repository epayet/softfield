# F7 review: factory fixes

- **Status:** review round 2 done, 2026-10-05; every blocking and should-fix finding resolved. Waiting for the owner's sign-off.
- **Reviewed:** `git diff f7-factory-fixes-start..main`, 2026-10-05, by the lead (headless). Round 1: the six tickets f7-01…06, their tests, and the two logs in the milestone doc. Round 2: f7-07, its test and its "Void benches" log.

## Sign-off sheet

### 1. What changed
- **Ratings hold now** ([ADR 24](../adr/24-ratings-that-hold.md)):
  - A review's findings cost a ticket's author one quarter step once per ticket, not once per finding.
  - Bench replays count as games.
  - A new model routes at the floor (1) until it has played 3 coding games, whatever its estimate.
  - `uv run runner ratings --replay` recomputes every agent from scratch. It ran once: Qwen went from 1.00 to 2.52.
  - The OpenCode benches from before 2026-10-05 were invalid (see below), so they are now void and the recompute ran again without them: gpt-oss-120b went from 1.00 to 1.43, and gemma4 back to its estimate (5). gpt-oss-120b ends short of the ≈2 the plan hoped for: without the benches it still lost six tickets against seven merges. That's its real record, not a bug.
- **Escalations leave a trail:** a ticket that Claude implemented during an escalation now carries `Task:` in its commit, so the bench can find it.
- **Closing the terminal stops everything.** Ctrl-C, SIGTERM and now SIGHUP (closing the terminal) stop the gate the runner was running. A second Ctrl-C no longer leaves it behind. On 2026-10-04 a pytest ran on for 16 hours.
- **Sign-off follows the ticket's `milestone:`, not its id.** `runner signoff` counts a re-homed ticket (f3-08 moved to F5) for its new milestone. Since this review, so do the verdict's "needs you" list and the owner items.
- **The bench stays in its copy.** OpenCode took its folder from `PWD`, which the runner passed on from the main checkout. Every OpenCode bench before 2026-10-05 therefore worked in your checkout. The runner now sets `PWD`. Each replay also checks `git status` of your checkout before and after: any change stops the bench and voids the replay. The 19 old OpenCode bench jobs are void (f7-07).
- Mum sees nothing new: F7 is factory-only.

### 2. How to test it yourself
1. `uv run runner ratings`: Qwen reads ≈2.5, gpt-oss-120b ≈1.4, and the untested Ollama models (gemma4 included) keep their estimates. Routing reads them as 1 until they've played 3 games (the dashboard's Agents page shows the stored rating).
2. Start `uv run runner run` in a terminal while a gate is running (watch the dashboard's Now), then close the terminal window. `ps -ef | grep pytest` shows no leftover pytest a few seconds later.
3. `uv run runner signoff f3-factory-line` no longer complains about `f3-08-field-cards`, which moved to F5 (it may still list F3's own unfinished tickets).
4. Optional, about 10 minutes: `uv run runner bench f4-25-<…> --agents ollama-gpt-oss-120b`, then `git status`: nothing changed in your checkout.

### 3. Left for later
- **Backlog** (three nits, `[f7-review …]` in `docs/backlog.md`): a weakened CLI test, no canary on `bench --review`, and `--void-benches-before` alone leaving the stored ratings stale (it was run with `--replay`, so your data is right).

### 4. Decisions waiting for you
- None. Voiding the old benches is a data correction under ADR 24, not a new rule, so the lead decided it (f7-07).

### 5. How the work went
| Session | Merged | Claude (token-equivalents) |
|---|---|---|
| [2026-10-04 23:04](../sessions/2026-10-04-2304.md) | f7-01 ratings rules | ≈603k |
| [2026-10-04 23:32](../sessions/2026-10-04-2332.md) | f7-02 ratings replay | ≈941k |
| [2026-10-05 00:01](../sessions/2026-10-05-0001.md) | f7-03 escalation trailer | ≈111k |
| [2026-10-05 00:12](../sessions/2026-10-05-0012.md) | f7-04 gates stop with the runner | ≈152k |
| [2026-10-05 00:25](../sessions/2026-10-05-0025.md) | f7-05 signoff by milestone | ≈109k |
| [2026-10-05 00:39](../sessions/2026-10-05-0039.md) | f7-06 bench isolation | ≈628k |
| [2026-10-05 00:59](../sessions/2026-10-05-0059.md) | f7-07 void leaked benches (review fix) | ≈982k |

All lead tickets, all first time, no escalation, no local tokens. The lessons that mattered:
1. **Probe before fixing.** f7-06 ran a real `opencode run` and found that `PWD` was the cause. Two earlier fixes (f2-12, f4-19) had guessed wrong. What changed: `run_streaming` sets `PWD`, and the canary proves every bench.
2. **Check the data a recompute replays.** The replay faithfully played benches that the probe then showed were invalid. What changed: f7-07 voided them and recomputed, and a Known range note in `lead.md` says no bench before 2026-10-05 counts.
3. **A plan line can shrink in its ticket.** The plan said "`signoff` and `_ids` read `milestone:`", and f7-05's ticket named only `signoff`. The verdict kept listing tickets by id. This review fixed it.

### 6. What next
- **Product:**
  - Nothing has changed for Mum since M4. A small product milestone (ADR 10's gallery, or the duck key) would give her something new and give the developers real, picture-backed work.
  - F5's board (steering from the phone) is the owner-facing next step: sign off and queue tickets from the sofa.
- **Factory:**
  - Run a clean Ollama bench (gpt-oss-120b, gemma4, nemotron-3-super on 3–4 small finished tickets). These would be the first valid bench games, and with 3 of them a model leaves the floor. Every Ollama model but gpt-oss-120b now routes at the floor, so this is how the cloud developers get real work again.
  - Batch lead tickets on `runner/` into fewer runs, or let the runner reload in place: each of F7's six runs ended with "needs a fresh process".
  - Give `bench --review` the same canary (backlog).

### 7. What clogged the factory line
This headless review can't query the metrics database (its shell is limited to the check commands), so this comes from the session reports. The milestone page on the dashboard has the exact hours.
- **Restarts:** seven runs for seven tickets (six planned, one from review), each ending with "the runner needs a fresh process" after a lead ticket changed `runner/`. Each restart costs seconds (`runner run` restarts itself), so nothing was really lost.
- **No waits for Claude's limit, no failed attempts, no stops for the owner.** The six tickets ran back to back in ≈1 h 55 min (23:04 to 00:59). f7-07 took another 28 min after round 1.

## What was built
- `runner/ratings.py`: `FINDING_LABEL`, `bench_game`, `routing_rating` and `MIN_GAMES`; `judged_games` charges once per ticket (f7-01).
- `runner/loop.py`:
  - `routing_ratings` and the floor in `current_ratings` (f7-01);
  - `rate_bench` and `_bench_game` (f7-01, f7-06's `void`);
  - `rate_verdicts` skips tickets already penalised (f7-01);
  - `replay_ratings`, rewritten as the ADR 24 recompute, with `_recorded_games` and `Replayed` (f7-02);
  - an `implemented` escalation's commit carries `Task:` (f7-03).
- `runner/cli.py`: `ratings --replay` prints each agent's before and after (f7-02).
- `runner/procs.py`: SIGHUP unwinds like SIGTERM (unless under `nohup`); a second Ctrl-C still SIGKILLs the group (f7-04); `run_streaming` sets `PWD` (f7-06).
- `runner/owner.py`: tickets counted by `milestone:` (f7-05, extended by this review).
- `runner/bench.py`: the main-checkout canary, `void` replays, and a rating game per replay (f7-06).
- `runner/loop.py`'s `void_benches_before` and `runner ratings --void-benches-before` (f7-07), run once on the real database: "## Void benches" in the milestone doc.

## Findings and resolutions
| Id | Severity | What | Route | Resolution |
|---|---|---|---|---|
| f7-factory-fixes-F1 | blocking | The replay log's ratings include OpenCode bench replays from before f7-06's `PWD` fix. Those agents worked in the main checkout while their gates ran in an untouched copy, so their results are void. gpt-oss-120b's three lost benches keep it at 1.00, so the milestone's outcome (≈2, a first attempt again) isn't met. | ticket (lead) | **Fixed by [f7-07](../../tasks/done/f7-07-void-leaked-benches.md)** (round 2): 19 OpenCode bench jobs voided, then the recompute. gpt-oss-120b 1.00 → 1.43, gemma4 back to 5.00. The ≈2 was ADR 24's estimate; 1.43 is its real record without the benches. |
| f7-factory-fixes-F2 | should-fix | The plan's row 05 said "`signoff` and `_ids` read `milestone:`". f7-05 changed only `signoff`: `verdict` and `owner_items` still listed escalated and blocked tickets by id prefix, and so did `_reserve_waits` and `_cleared_by_rerun`. A re-homed ticket (f3-25 → F9) showed under F3's "needs you", and F9's rerun would never clear its owner item. | lead | **Fixed:** `owner._milestone_of` reads a ticket's `milestone:` (falling back to its id). `_ids`, `_reserve_waits` and `_cleared_by_rerun` use it. New test `test_the_verdict_lists_a_rehomed_ticket_under_the_milestone_it_names`. Two fixtures that named the wrong milestone now name theirs. |
| f7-factory-fixes-F3 | nit | `test_ratings_replay_twice_gives_the_same_ratings` (test_cli) was loosened to "some replay rows exist". | backlog | Backlog. |
| f7-factory-fixes-F4 | nit | `bench --review` has no main-checkout canary, and old OpenCode review benches may have read the wrong tree. | backlog | Backlog. |
| f7-factory-fixes-F5 | nit | `ratings --void-benches-before` without `--replay` voids the jobs but leaves the stored ratings stale, silently; no CLI test covers the flag or its refusal of a zoneless time. Found in round 2. | backlog | Backlog. |

`uv run pytest -q tests/unit tests/integration tests/runner`: 1309 passed, 1 skipped, after the F2 fix; 1310 passed, 1 skipped in round 2. `ruff` and `mypy` are clean on `runner/`.

### Round 2: f7-07
- **The code:** `void_benches_before` picks `bench` jobs with a ticket (so not review benches), from an agent whose harness is `opencode`, not void yet, and compares their start with `_moment`, so a time in another offset or with no zone compares right. Each voided job's note says why. The CLI refuses a cut-off with no zone.
- **The test** (`test_benches_before_the_cut_off_void_only_opencodes_ticket_replays`) covers what the ticket asked and more: a job after the cut-off that sorts earlier as text, a Claude job, a review bench, an already-void job, a second run voiding nothing, and the recompute checked against an independent `rate`. No existing test was edited.
- **The log:** the "Void benches" table matches the code's output shape and corrects the earlier replay log (nemotron-3-super's one game is f2-07, not a bench).

### The checkpoints' findings
None: F7 had no developer merges, so no checkpoint ran, and none could have missed anything.

### Tests the lead tickets edited
- **f7-01** changed `test_the_reviews_verdicts_are_rated_once_with_distinct_moments`: the missed F3 no longer charges `local` a second time. Correct under ADR 24 item 1. It added the bench, floor and once-per-ticket tests.
- **f7-02** deleted the two M1–M4 replay tests in `test_ratings.py`, which tested the seeding that the recompute replaces. It also rewrote `test_ratings_replay_twice_gives_the_same_ratings` (test_cli) more loosely (F3). Its real checks moved to `test_the_recompute_replays_a_collapsed_rating_to_its_game_level` (test_loop), which compares every rating against an independent `rate` call.
- **f7-05** gave `test_a_named_milestone_finds_its_short_tickets_and_its_docs` a `milestone: f3` ticket. With F2's fix, `test_a_factory_milestone_uses_its_key_everywhere` and `test_a_rerun_resolves_the_milestones_rerun_items_at_once` needed the same: their fixtures had `f1-…` and `m2-…` tickets with `milestone: 1`.
- **f7-01** made `_routed` prove `local-m` and Sonnet with three games each, since the floor would otherwise route them at 1.

### French
Nothing in `coucou/locale/` changed.

## Workflow observations (Factory)
- **Flow:** six lead tickets in six runs, ≈1 h 55 min end to end, plus f7-07 from review in 28 min, with no stops, parks or owner interventions. Every run ended with a restart for a `runner/` change.
- **Models:** Opus did all seven first time. No developer, Ollama or checkpoint work.
- **What to change:**
  - A plan's table row and its ticket should name the same functions. Here the ticket dropped `_ids` (F2). The replan rule covers chains of three or more; for small milestones, the lead should reread the table against the tickets once before "go".
  - Treat any data a recompute replays as suspect until its producer is proven (F1).
- **Stop reason:** none. Round 2 closes the review: score 8/10.

<!-- runner report -->
<!-- /runner report -->
