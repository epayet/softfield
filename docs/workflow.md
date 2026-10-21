# Workflow: how Coucou gets built

> Plain-language overview: [`how-it-works.md`](how-it-works.md).
>
> Reflects the brief §7, [ADR 00](../.factory/adr/00-initial.md), [ADR 07](../.factory/adr/07-spend-less-frontier.md) and [ADR 12](../.factory/adr/12-junior-feedback-and-checkpoints.md) (Accepted). Changes to anything here need an Accepted ADR (see [`docs/agents/lead.md`](agents/lead.md)).

## Roles

| Who | Does |
|---|---|
| **Owner** | Accepts ADRs and workflow changes, decides architecture and critical code questions, signs off milestones on real devices. |
| **Lead** (a frontier model; today Claude Code, Pro login) | The tech lead: plans, decides the contracts between pieces, writes tickets, builds protected paths test-first, handles escalations, reviews. See [`docs/agents/lead.md`](agents/lead.md). |
| **Runner** (`softfield`) | A deterministic Python script with **no AI in it**. It picks tasks, runs the local model and the gates, merges, retries and escalates, and calls the lead headlessly for lead tickets, directions, checkpoints, escalations and reviews. |
| **Developers** (local models: OpenCode + Qwen via LM Studio) | Implement one ticket at a time, tests included. See [`docs/agents/developer.md`](agents/developer.md). |

All coordination goes through files in the repo. Run logs go to `.factory/var/runs/<timestamp>-<task>/`, which is gitignored.

## Running a milestone (ADR 12)

1. **Plan** (the owner and the lead, interactive): the milestone doc and every ticket, the lead's (`agent: lead`) and the developers', in one pass. `softfield run --dry-run` shows what runs next. The session ends with "go".
2. **`softfield milestone N`**, in a plain terminal, with no interactive Claude session open (one kept open re-reads its whole context on every turn: most of M4's cost). It runs the queue, then the review loop and its fix tickets, and ends with a verdict:
   - `✅ READY FOR SIGN-OFF` (exit 0): the device-test steps from the review, then `softfield signoff N`.
   - `⚠ NEEDS YOU` (exit 2): each ADR a job drafted for the owner, with its question and the tickets paused behind it; blocked tickets with their reason; a review that stopped for the owner. Decide, then rerun the same command: it picks up where it stopped.
   - Exit 1: an error. Rerunning is safe; the state is in the repo and `.factory/var/runs/state.json`.
   The verdict is also appended to the session report. When an escalation changes `runner/`, the command restarts itself.
3. **Sign-off** (the owner): the real-device check, then `softfield signoff N` (marks the milestone doc and review done, tags `mN-done`; refuses while tickets are left, unless `--force`). An optional `--score 1-10` records how the result felt on the devices (ADR 14 item 14). ADRs: `softfield accept N` / `softfield reject N`. Only the owner runs these; headless jobs can't.

`softfield run`, the standing command (ADR 17), works through every milestone's tickets in `.factory/tasks/ready/`. When a milestone has every ticket in `done/` (one set aside in `later/` doesn't count), isn't signed off and has no review yet, the run reviews it before its next ticket, as step 2 does, and records the verdict. Then it goes back to the queue. It waits for a parked checkpoint or escalation first. With no `<key>-start` tag, the review tags the commit that added the milestone's doc. The line's queue, Now's "Next in line" and `--dry-run` show the due review as "review F3". `softfield review --milestone N` runs only the review loop.

**The standing command stays up** (F101). With nothing it can run, `runner run` no longer ends: it holds and says why on the console and in Now, each cause once, for example "Idle: 22 tickets wait for Claude's reserve · the week resets Mon 17:00", "Idle: nothing is ready", or what waits for the owner by kind. Every 5 seconds it applies the dashboard's requests, checks the backup and picks again, so a switch turned on, an approved plan's tickets or the week's reset start work with no terminal. The hold starts no job itself. To end the run, press Ctrl-C: while idle it writes the session report first. An idle run that has work to report also closes its session at the first poll of a new day and opens the next, so a run up for a week leaves a report per day worked and none for an empty day. `runner run --once`, `--dry-run` and `runner milestone` end as before.

## Per-task loop

1. Pick the next `.factory/tasks/ready/*.md` whose `depends_on` are all in `done/`.
2. Create the branch `task/<id>` from `main`.
3. **Pre-flight:** every backticked file in the task's Context and `Pattern to follow` exists or is listed in `files:`, and every quoted symbol is found (`def`/`class` grep). If not, escalate at once. `runner run --dry-run` prints the same problems before a session.
4. **Local model:**
   - Warm up LM Studio with one sequential request, which JIT-loads it with the owner's settings. The session report notes the context LM Studio loaded; `opencode.json` doesn't set one (ADR 00 A3).
   - Run `opencode run --title <id> -f <task> "<fixed instruction>"`, with a wall-clock timeout. The instruction is short: the task, then one finish line, `softfield check-all --fix --task <id>`, which runs every check the gates run (ADR 12 item 1). On a retry, the gate output comes last, because the local model follows the end of a long prompt best ([ADR 01](../.factory/adr/01-calibration-fixes.md)).
   - `agent: lead` tickets skip the local model: a headless lead job does them test-first on the branch, and they merge only if `check-all` passes; otherwise they go to `blocked/` with the branch kept (ADR 12 item 9).
     - **A red main blocks nothing** (F106 D5, ADR 29 item 7): when a lead ticket's `check-all` fails, the runner runs the checks that failed, and only those, on main. If main fails every one of them, main is red: the ticket stays in `ready/` with its work on `task/<id>`, the owner gets one item (kind `main-red`) naming the first failing check, its first lines and the ready ticket whose `files:` names the failing file, and no other lead ticket runs, except that one, until main passes. Developer tickets go on: their gates already compare with main. Each commit on main that touches more than docs and tickets runs those checks on main again; once they pass, the item resolves and the waiting ticket merges from its branch, with no new session, once its whole `check-all` passes. If main passes any of the failed checks, the ticket is blocked as before.
   - **A blocked ticket reaches the owner at once** ([F106](../.factory/cards/f106-where-do-blocked-tickets-go-for.md) D1, D3): `block` stores a `blocked` owner item, "<id> blocked: <reason>", plus how many ready tickets wait behind it; the verdict writes the same words. No command: the owner answers from the desk. **Try again** is a `queue` request, which takes the ticket from `blocked/` back to `ready/` (after `later/`, searched first) in a commit of its own; it first copies `task/<id>` to `blocked/<id>`, replacing an older copy, since a lead ticket starts again from main and its failed work must not be lost. **Set aside** is a `set_aside` request, which moves it from `blocked/` to `later/`, its branch left as it is; it takes nothing but a blocked ticket. Either resolves the item, and the ticket keeps its footers.
     - **Then the lead looks at it** ([ADR 29](../.factory/adr/29-the-lead-looks-at-a-blocked-ticket.md) items 1, 2, 4–6): `block` writes the runner's own message on the ticket's card's thread (author `runner`, shown as "The runner", never the owner's words, so never under "Didn't go through"), naming the ticket, the reason, its branch (`escalation/<id>` or `task/<id>`) and its run's log folder, and queues one planner row for it (subject `<card>#m<message id>`). An archived thread opens again. The job is a planner job like any other (on Opus, parked at Claude's limits, under the reserve): it reads the branch with read-only git and replies with what went wrong and a fix as a `replan`; the thread is then in "Your answers wanted". One look each time a ticket is blocked; the ticket goes back to the queue only when the owner approves or presses Try again. No look for a bug ticket (no card), nor without the metrics database: the ticket is blocked all the same.
5. **Gates, in order, stopping at the first failure:**
   1. `BLOCKED.md` present → see below
   2. no protected path touched (`.factory/protected-paths.txt`, which includes the tests that guard protected code)
   3. `no-new-skips`: no added `skip`/`xfail` in tests
   4. no dependency changes (`pyproject.toml` deps, `uv.lock`, `vendor/`)
   5. `max-diff`: under the 1000-line backstop against a rewritten file
   6. `layout`: test files match modules by name, one per module (`tests/unit` ↔ `coucou/`, `tests/runner` ↔ `runner/`, `tests/browser` ↔ `coucou/static/coucou/js/`)
   7. `test-patterns` (ADR 12 item 3): added lines in `tests/browser/` and `tests/e2e/` may not branch on `is_visible()`/`count()`, fire events or set `.value` from JavaScript, sleep, or give `wait_for_function` a bare expression (the real pages' CSP blocks it once it polls); no new empty module anywhere. A line ending in `# pattern-ok: <reason>` passes, and checkpoints read those.
   8. `translations`: every user-facing string has a compiled French translation
   9. `ruff check` + `ruff format --check` (Python files only; Markdown is excluded, [ADR 01](../.factory/adr/01-calibration-fixes.md))
   10. `mypy`
   11. the task's `tests:`
   12. all unit, integration, runner and browser tests ([ADR 06](../.factory/adr/06-sse-and-browser-tests.md): ES modules in headless Chromium), and the dashboard's: every test file on main, whatever the queue holds ([ADR 21](../.factory/adr/21-gate-every-test-file.md))
   13. `tests-fail-on-main`: the test files the task added or changed fail against main's code (with every other changed file put back as it is on main), so they test the change ([ADR 07](../.factory/adr/07-spend-less-frontier.md)). A `tests_only` ticket skips it and may change only `tests/` ([`docs/task-format.md`](task-format.md))

   `files:` is a pointer, not a gate: the session report lists files changed outside `files:` and `tests:`, and every existing test the developer changed, for the review.
6. **Pass:** squash-merge to `main` and `git mv` the task to `done/` with a result footer. The merge is authored by `Coucou local model` and carries `Agent: local-model` and `Task:` trailers (see §Who made each commit). **Checkpoint** (ADR 12 item 8): after every `checkpoint_every` (2) developer merges, a headless review of those diffs (by the `checkpoint` role's agent in `[roles]`, Sonnet) may queue a fix ticket the next ones wait for, tighten upcoming tickets, or add a `developer.md` note; its tools can't touch code. It also writes its findings to `checkpoint-<n>.json` (ADR 14 item 13), which become finding rows on its job, keyed `<milestone>-C<job>-<n>`; a malformed file is noted in the session report.
7. **Fail:**
   - attempt 2: same branch; the prompt adds the gate's one-line hint (what to do) and its exact output. After a timeout it also says the attempt ran out of time and lists the files changed on the branch so far; after an attempt that changed nothing, it says why (ran out of time, commands refused, or stopped early).
   - **the lead's direction** (ADR 12 item 6): before the last attempt, unless every failure was mechanical (`ruff`, `translations`, one empty attempt), a headless job reads the gate logs, the diff and the developer's thinking (copied read-only from OpenCode's `opencode.db` into the run logs) and writes a few lines of direction, no code. It may repair the ticket instead (committed on main). At most `directions_per_task` (1). Directions and escalations also write a 2–4 line process note (`note.md`: did the developer follow the ticket, run its checks, go round in circles), kept on the job's row and never scored (ADR 14 item 13).
   - attempt 3 ([ADR 15](../.factory/adr/15-allowance-aware-routing.md) item 7): builds on the branch, with `main` merged in, plus the gate output and the direction, last. The branch resets to `main` only when the direction's `reset: true` line says the work is unusable (the developer doesn't see that line), or the previous attempt timed out before its first edit, or `main` no longer merges cleanly. The prompt says which: kept, or reset and why.
   - still failing: move the task to `escalated/` with logs and the last diff, pause its dependants, continue with independent tasks. The branch is kept.
   - **a requeued ticket continues its branch** (with `main` merged in), and its first prompt lists the files the earlier run changed, unless the escalation's `decision.json` says `"reset": true`, which deletes the branch.
   - the runner logs the longest run of edits without a command per task (in the report and the direction prompt); it doesn't stop on it yet.
8. **`BLOCKED.md`** (categories in AGENTS.md):
   - `unrelated-problem`: append it to `docs/discoveries.md` and continue gating
   - anything else: escalate immediately; this doesn't count as a failed attempt
9. **Discoveries:** the local model may append to `docs/discoveries.md`. Claude triages it at milestone review into the backlog, tasks or ADRs.

## Escalation (headless Claude)

- **When:** at most `escalations_per_task` (2) per task. Past that, the task goes to `.factory/tasks/blocked/` with its reason, its dependants pause, and the verdict names it.
- **What Claude gets:** the task, `BLOCKED.md` or the gate logs, the last diff and the developer's thinking; the runner first merges `main` into `task/<task>`. Tools: Read/Edit/Write, `uv run pytest`/`ruff`/`mypy`/`runner check-all`, read-only git, and `git checkout task/<task>` (that branch only).
- **Its code must pass `check-all`** (ADR 12 item 11). If not, the work goes to the branch `escalation/<task>`, the task to `blocked/`, and nothing reaches main.
- **`finish`** ([ADR 15](../.factory/adr/15-allowance-aware-routing.md) item 8), first choice when the gates fail on a small, clear gap: the lead checks out `task/<task>` itself and finishes the work there. The runner commits it, runs `check-all --task <task>`, and squash-merges it as a developer pass: `Agent: claude-headless` with `Developer: local-model`, `Task:` and `Model:` trailers, and the ticket row's `merged_by` is the lead. The task moves to `done/`. If `check-all` fails, or the job left `main` without answering `finish` on that branch, the work stays on its branch and the task goes to `blocked/`.
- **Outcome:** `finish`, a repaired or split ticket back in `ready/` (building on the branch unless `"reset": true`), an answered question (facts added to Context), the lead doing the task itself, or **stop for the owner** (a draft ADR, only for what `docs/agents/lead.md` reserves for the owner; `decision.json` names the ADR and a one-line question, which the verdict shows). The lesson becomes a check, a worked example or a note in `docs/agents/developer.md`.

## Milestone review loop

**Trigger:** every task in the milestone is `done/` **and** `pytest -m e2e` passes on staging.

1. **Review round:** the headless lead reviews `git diff <milestone-base>..main`, tests as closely as code (missing edges, every existing test a developer changed), and the French. It writes the findings to `.factory/var/runs/review-mN-rK.json`, each with its file, line, detail and the ticket at fault. Each round also marks the checkpoints' findings `confirmed` or `rejected`, its own findings a checkpoint should have caught `missed`, and scores the milestone 1–10; the last round's verdicts and score are kept (ADR 14 item 13).
   - **Blocking:** bugs, security issues, AGENTS.md or ADR violations.
   - **Should-fix:** design drift, missing edge cases, weak tests.
   - **Nit** → `docs/backlog.md`. Nits never loop.
2. **Routing each blocking or should-fix finding:**
   - by default → a developer fix ticket (`finding: mN-F3`), checked by the usual checkpoint, not another round (ADR 17 item 5)
   - small (about 20 lines in one file), protected or security, or a developer already failed it once → Claude fixes it directly
   - needs the owner (`docs/agents/lead.md`) → a draft ADR, and **stop**. Never park a finding for the owner in the backlog.
3. **Re-review:** covers only the fix diffs and whether each finding is resolved. New blocking issues in the fixes count; should-fix points about untouched code go to the backlog.

**Stop rules** (the values are in `.factory/project.toml`):

| Rule | Default |
|---|---|
| Review rounds per milestone | 3 |
| Headless Claude runs | no milestone cap: 1 direction and 2 escalations per task, a checkpoint every 2 developer merges (ADR 12 item 10) |
| A finding recurs a 2nd time | Claude fixes it (not the local model) |
| A finding recurs a 3rd time | stop |
| This round's findings ≥ the previous round's | stop |
| ADR needed / unresolved security finding / cross-milestone surprise | stop immediately |

**Report:** `.factory/reviews/mN.md` starts with the owner's **sign-off sheet** (what changed, how to test it yourself, left for later, decisions waiting, how the work went; see `docs/agents/lead.md`), then covers what was built, the findings and their resolutions, the backlog items, the metrics (tasks, attempts per task, escalation rate, review rounds, headless runs), the stop reason and workflow observations. **Only the owner marks a milestone done.**

## Headless Claude invocation

- The environment has `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` **removed**, so the Pro login is always used.
- Flags: `claude -p --output-format json --permission-mode dontAsk [--model <m>] --allowedTools <per job>`, with a wall-clock timeout (this CLI version has no turn cap). Only checkpoints set a model.
- **Claude's allowance** ([ADR 15](../.factory/adr/15-allowance-aware-routing.md), [ADR 16](../.factory/adr/16-claude-window-and-named-milestones.md) items 1–4 and 9; `runner/allowance.py`, `[claude]` in the machine's `~/.config/softfield/factory.toml`):
  - **The owner's 25%:** unattended jobs of every role stop at 75% of Claude's 5-hour window (`five_hour_reserve`); the rest is for the owner's own sessions. The week keeps 30% (`reserve`) for the lead's support roles: directions, checkpoints, escalations and reviews may use it, lead tickets only with the week's switch on.
  - **Lead work first:** Claude takes a developer ticket only when no lead work is ready (a lead ticket, a parked direction, escalation or checkpoint, or a checkpoint due) and its 5-hour window is under 50% (`developer_five_hour_cap`). Otherwise the next permitted developer takes it, local at worst.
  - **Two switches, one per window, never a question** ([ADR 22](../.factory/adr/22-one-visible-queue.md) item 4): "Let the factory use the week's reserve" and "Let the factory use your 25% of the 5-hour window", kept in `.factory/var/runs/state.json` across commands and restarts. Off (the default): at the week's reserve a lead ticket waits for the owner (a Needs-you item naming the switch); at 75% of the 5-hour window it parks until the reset and then goes on by itself (also a Needs-you item until then). Either parks only when nothing else can run. On lets it run; one switch doesn't turn on the other. The console asks nothing.
  - **Turning them on:** `softfield reserve week|five-hour on|off`, the dashboard's `reserve` request, or `softfield run --use-reserve` as a run starts (`--use-reserve week` or `five-hour` for one). On lasts 24 hours, then turns itself off and a Needs-you item asks to turn it on again (owner, 2026-10-04). A live run takes a switch at its next pick, or within a minute while it sleeps for the owner's 25%.
  - **Parking:** a lead ticket, a direction, a checkpoint or an escalation that Claude can't take (a limit, or the owner's 25%) parks: its work is kept on a branch, its session in `.factory/var/runs/state.json`, and the queue runs developer tickets meanwhile. Parked jobs go first after the reset; with nothing else to run, the runner sleeps until then. The review, with nothing else to run, waits (the 5-hour switch turned on ends the wait).
  - **Copilot stands in:** a checkpoint due while Claude can't take it goes to `[roles] checkpoint-stand-in` (`copilot-auto`, read-only), whose month is then a cap rather than a pace. Its findings are recorded on its job, and each one that isn't a nit becomes a fix ticket (`finding:` in its frontmatter) for a developer. With no stand-in permitted, the checkpoint parks.
- **What a job can run:** only the command prefixes in its tool list (`runner/claude.py`, `shell_note`), in the foreground: a headless job can't watch anything it starts in the background. A planner job drafting on `plan/<card>` also has `softfield check-tickets [files]`: the problems Approve would refuse its tickets for (the format, pre-flight, a Proposed ADR), read-only; with no file, every ticket in `.factory/tasks/later/`.
  - **`softfield look`** ([ADR 28](../.factory/adr/28-lead-jobs-can-look.md); `runner/look.py`): planner and review jobs, and nobody else's, can read the metrics database and the dashboard's pages. It writes nothing, and unlike the other runner commands it applies none of the owner's requests first.
    - `softfield look sql "<one SELECT>"` prints the rows under their column names, at most 200, a cell at most 500 characters, and says when it cut. The database is opened read-only and SQLite's authorizer allows reads only, so a write, an `ATTACH` or a changing `PRAGMA` is refused by SQLite. `PRAGMA table_list` and `PRAGMA table_info(<table>)` show the schema.
    - `softfield look page <address>` prints a dashboard page as plain text (`/`, `/planning`, `/milestones/f95`), or its data as is where the address serves JSON (`/line/live`, `/line/replay`), at most 40,000 characters. It is one GET on the dashboard's own app, in the same process: no server, no form sent, so nothing can be approved or signed off.
    - An error (bad SQL, no such page) is one line and a non-zero exit.
- **Usage limit inside a job that doesn't park** (a narrative): parse the reset time, record `paused_until` in `.factory/var/runs/state.json`, sleep and resume. Fallback backoff runs from 15 min up to 5 h. The runner never loops tightly.

## Who made each commit

[ADR 00 A4](../.factory/adr/00-initial.md): every automated commit says who made it.

| Made by | Author | Trailer |
|---|---|---|
| Local model (merges and task-branch WIP) | `Coucou local model` | `Agent: local-model`, plus `Task:`, `Model:`, `Attempts:` on merges |
| Runner bookkeeping | `Coucou runner` | `Agent: runner` |
| Headless Claude (lead tickets, directions, checkpoints, escalations, reviews) | owner | `Agent: claude-headless` (plus `Task:` on a lead ticket's merge and an `implemented` escalation's commit, and `Developer:`, `Task:`, `Model:` on a finished branch's merge) |
| Interactive Claude | owner | `Co-Authored-By: Claude …` |
| Owner (including `runner signoff`, `accept`, `reject`) | owner | none |

`softfield commits --milestone N` lists the local model's commits since `mN-start`. Milestone reports include that list.

## Bench

`softfield bench` replays finished tickets for chosen agents ([ADR 14](../.factory/adr/14-developers-and-agents.md) item 8; `runner/bench.py`). Each ticket × agent works in its own clone of the repo under `[bench] dir` in `.factory/project.toml` (default `~/.cache/software-factory/bench/`, which must be outside the repo), removed afterwards; the logs stay in `.factory/var/bench/`. A clone, never a `git worktree`: OpenCode takes its project from the git common dir, so in a worktree a bench agent edited the main checkout (2026-10-02, f2-12).

`softfield bench --review <milestone…> --agents <id…>` replays past checkpoints instead ([ADR 16](../.factory/adr/16-claude-window-and-named-milestones.md) item 10): each agent reviews each checkpoint's merges read-only (the checkpoint shadow's prompt), in a clone at the last of them, and is scored against the findings already known: the checkpoint's own, plus the checkpoints' and reviews' later findings on the same tickets, without those the review rejected. A known finding it also reports (the same summary, or the same file within 5 lines) is found, one it doesn't is missed, and a missed blocking one is counted apart. A finding nobody knew isn't scored: the command prints it and keeps it in `.factory/var/bench/<run>/checkpoint-<job>-<agent>/new-findings.json` for the lead to judge. Each replay is a `bench` job with no ticket and its score as its note; an agent's own checkpoints are skipped, and the first refusal stops the bench. The merges a checkpoint reviewed come from the metrics database: the developer tickets whose last job ended since the checkpoint before it, plus those its findings name. The Agents page's eligibility reads these replays, not shadow jobs: ADR 14 item 12's bars, with "2+ milestones" read as replays of 2+ milestones' checkpoints.

## Backups

The metrics database holds what lives nowhere else: planning threads, the owner's requests and desk items, the ratings ([ADR 13](../.factory/adr/13-factory-dashboard.md), F20). The runner copies it once a day into `[backup] dir` (`~/Dropbox/software-factory-backups`), keeping the last 14 as `factory-metrics-<YYYYMMDD-HHMM>.sqlite` (`runner/backup.py`); a failed copy is a line in the session report, never a stop. An approved plan's thread is also in git, in `.factory/planning/`.

To restore a copy: stop `runner run` and `runner dashboard`, move the live `factory-metrics.sqlite` and its `-wal` and `-shm` files aside (a stale `-wal` must not meet the restored file), copy the chosen backup to `[metrics] db` under the live name, then start them again. Runs since the copy come partly back with `softfield backfill` (from `.factory/var/runs/`).

## Improving the workflow

Evidence from milestone reports leads to an ADR, and nothing changes until the owner accepts it. Runner bug fixes that don't change behaviour are exempt.

## Session reports

The owner wants to learn how the frontier + local workflow performs, so every runner session leaves a report.

- **Deterministic part:** the runner writes `.factory/sessions/YYYY-MM-DD-HHMM.md` at the end of each session, with no AI involved and no Pro usage. It covers:
  - tasks attempted, their outcomes and attempts, and wall-clock time per task and phase (warm-up, model, gates)
  - gate failures by gate, plus BLOCKED and escalation events
  - **local tokens:** input and output tokens processed by the local model, from OpenCode's JSON events
  - **headless Claude:** run count and token usage, from `claude -p --output-format json`
  - **local model vs Claude:** local tokens, and Claude's own tokens (new, and re-read from its cache) from Claude Code's transcripts, which cover interactive and headless sessions. Rough by design, with no prices. Each task's footer records its local tokens, and the milestone metrics end with a "who did the work" paragraph (`softfield status --milestone N` prints it any time).
- **Narrative part:** what went well, what didn't, improvement opportunities and interesting observations.
  - Claude writes it whenever Claude is in the loop: calibration, milestone reviews, escalations and interactive sessions.
  - An optional headless narrative at the end of a session (`narrative = true` in `.factory/project.toml`) is **off by default**, because it costs Pro usage.
- Milestone reports (`.factory/reviews/mN.md`) summarise the session reports of that milestone.
