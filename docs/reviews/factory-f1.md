# Factory review after F1

- **Date:** 2026-10-02, done interactively by the lead with the owner (in place of the headless f1-32).
- **Evidence:** the metrics database (`uv run runner report f1`, in [`f1.md`](f1.md)), `var/runs/state.json`, `workflow/runner.toml`, the runner's code, `docs/sessions/2026-09-30-*` to `2026-10-02-*`.
- **Not done:** the factory-line screenshots (the line moved to [F3](../milestones/f3.md)).

## Is the process viable? Yes, with one constraint

- **It ran unattended for 36 hours** (30 Sep 18:26 → 2 Oct 06:13) and merged 48 tickets: 28 lead tickets (14.8k lines) and 22 developer tickets (6.0k lines, 5.3k credited to developers). Main stayed green: every merge passed `check-all`.
- **The owner was needed** for the reserve question, two mid-milestone sessions, and the stops: a lead ticket that couldn't delete a file (f1-16), a review started with 15 tickets paused, and the final 5-hour limit.
- **The binding constraint is Claude's 5-hour window, not dollars.** Lead tickets were $68.9 of $83.9 (82%). Five refusals, all on Opus's 5-hour window; the week never went above 20%.
- **The second constraint is the local GPU's speed.** 42 local attempts averaged 28 minutes: 19.5 of the 27.8 hours of job time, for a third of the lines.

## What clogged the factory line
Of the 36 hours from first job to stop, about:
- **11 h waiting for Claude's 5-hour window**, four times, always Opus: 1 Oct 17:23 → 20:40, 23:52 → 01:40, 2 Oct 02:15 → 04:50, then 06:12 → 09:50, when the owner stopped it. Each time the next tickets were lead tickets or waited on one, so the GPU sat idle too. The last wait came from Sonnet's developer tickets using up the shared window (finding 1).
- **11 h of GPU on local attempts that failed** (24 of 42 attempts, 28 min each): mostly f1-34 (8 attempts for 57 lines), f1-15 (5), f1-35 (5) and f1-50 (3, then the lead finished it).
- **≈2.5 h stopped for the owner** on 1 Oct: f1-16 blocked (a headless job can't delete a file), then a review started with 15 tickets paused, which the owner interrupted, then the mid-milestone session.
- **The queue's shape:** one ticket at a time. f1-08, 11 and 12 were ready together after f1-33 but ran one after another, and the tail hung on f1-53 alone.

**What unclogs it, in order:** the 5-hour rules and lead-first routing (ADR 16), cloud developers beside the local one (F2), plans that keep developer work runnable beside lead chains (lead.md), then parallel developers (`docs/roadmap.md`).

## How good are the models?

| Who | Work | First attempt | Cost | Time |
|---|---|---|---|---|
| Opus (lead tickets) | 28 tickets, 14.8k lines, difficulty 3–8 | every lead ticket merged; its 6 unfinished jobs were 3 parks at a limit and 3 interruptions, none a failed check | $4.65 per 1,000 lines | 2–15 min a ticket |
| Qwen 3.6 35B (local) | 19 tickets, 5.3k lines, difficulty 2–6 | 12 of 19 (63%) | $0, plus ≈$0.60 of Claude support per ticket on average | 28 min an attempt |
| Sonnet (developer) | 3 tickets (f1-28, 31, 52), difficulty 3–5 | 3 of 3 | ≈$0.40 a ticket | 5–7 min |
| Sonnet (checkpoints) | 9 | – | $0.13–0.34 each | ≈1 min |
| Copilot (shadow) | 1 | – | free (2% of its month) | 2 min |
| Ollama Cloud | **never used**: declared in `runner.toml`, but no role lists it | – | – | – |

- **The local model's failures cost most of the support:** 4 tickets (f1-15, 34, 50, 35) took $7.9 of the $11.9 spent supporting developers. A first-time pass costs about $0.17 (its checkpoint share).
- **Per ticket, Sonnet was cheaper than local** (≈$0.40 against ≈$0.60 of expected support) and five times faster. But it draws on the same 5-hour window as the lead, which is what stopped the run.
- **Reviewing is about 10× cheaper than writing:** a Sonnet checkpoint reads ≈500 lines for ≈$0.24 (≈$0.50 per 1,000 lines), while Opus writes at $4.65 per 1,000. So "the cheap model writes, a stronger or different model reviews" pays off, as long as most first attempts pass.
- **A different model catches different things:** Copilot's shadow found a should-fix that Opus's checkpoint missed on the same merges (f1-S166-1: the bench page counts attempts by list length). It's one data point, but it supports ADR 15 item 9 (a reviewer is always a different model).

## The local developer (Qwen 3.6 35B-A3B on the GPU), in detail
F1 was its real test: 19 tickets, 42 attempts, on a new codebase (FastAPI, Jinja, htmx, SQLite fixtures).

**Where it's good.** 12 of 19 passed at the first attempt, all of difficulty 2–4:
- **Page tickets with a worked example:** f1-08, 09, 10, 12 and 14 all passed first time, at 390–660 lines each. That's more than M4's known range (180–500), in 22–27 minutes, with peak context at 41–57%.
- **Small fix tickets with exact facts:** f1-36 to f1-41 and f1-48 all passed first time (28–224 lines, 11–27 min).

**Where it fails, and why.** The 24 failed attempts fall into four groups:
| Cause | Attempts | Tickets | Whose fault |
|---|---|---|---|
| **Degenerate thinking:** a 200 KB loop ("Building the template structure…" thousands of times), or "I'm going to write the code now" and then stopping, with 0 edits after 25–30 min | 6 | f1-13 ×2, f1-15 ×2, f1-34 ×2 | the model; the runner could stop it at minute 5 |
| **Timeouts at 45 min,** still working | 6 | f1-11, 15 ×2, 34 ×2, 35 | difficulty 5–6 and fixture-heavy tests |
| **Fighting wrong facts or a red main:** a direction's wrong job count (f1-34), main failing its tests (f1-35, f1-50), a ticket missing a file (f1-29), an invalid ticket (f1-35) | ≈6 | f1-29, 34, 35, 50 | the lead and the runner (lead.md already has the f1-34 lesson; checkpoints now run `test_tasks.py`) |
| **Gate misses:** edited a protected path, ruff, its own tests | ≈6 | f1-11, 29, 34, 35, 50 | the model, mostly fixed on the retry with the gate output |

**Difficulty is a clean predictor.** At difficulty ≤4: 12 of 16 first time. At 5–6 (f1-11, 13, 15): 0 of 3, each taking 3–5 attempts and $0.45–2.66 of Claude support.

**What it costs.** $0 of tokens, but 28 minutes an attempt, and its failures drew ≈$9 of the $11.9 of Claude support (≈$0.60 a ticket on average, ≈$1.40 a failed one). Its 19 tickets saved ≈$27 net against the lead writing them (`runner report f1`).

**Going forward:**
- **Keep it as the floor and the night shift:** free, private and never limited. It passes first time on difficulty ≤4 tickets that follow a worked example.
- **Cloud first already holds** (ADR 15 item 6): a cloud developer whose rating covers the ticket takes it while it has allowance. Open question for ADR 16: when no cloud developer may take a difficulty 5–6 ticket, should it wait for one rather than go to local (0 of 3 first time, $0.45–2.66 of support each)?
- **Stop the degenerate attempts early** (F2): an attempt with no edit after 10 minutes, or whose thinking repeats the same line, is cut and counted as failed. That gives back about 2.5 h of GPU per F1-sized milestone and costs no Claude.
- **Our mistakes caused a quarter of its failures:** check facts against a run (lead.md), and keep main green before queueing (the `test_tasks.py` check).
- **Measure it against the Ollama models on the same tickets** with `runner bench` (F2): if a free cloud model passes difficulty 5–6 in a few minutes, local becomes the fallback rather than the default.

## The replans: worth it, make them standard at joints
- **f1-07 ($3.94):** changed no Decision, but found the gates' blind spot (queued tests skipped since f1 started; `test_loop.py` red on main) → f1-33.
- **f1-19 ($1.64):** fixed three wrong facts that tickets would have trusted: Ollama's refusal, Copilot's credits, and the separate reviewing rating.
- **Together $5.6, 7% of lead spend.** Recommendation (ADR 16 item 7): a replan after any chain of three or more lead tickets that produces facts later tickets rely on (a schema, a probe), not at fixed intervals.

## Findings
| # | Grade | Finding | Route |
|---|---|---|---|
| 1 | should-fix | The 5-hour window is a plain cap per agent. Opus and Sonnet share one window, nothing keeps room for the lead or the owner, and checkpoints skip the allowance (`runner/allowance.py`, `router._reviewer`). Sonnet took three developer tickets and the lead hit 100% at 06:12. | ADR 16, f2 |
| 2 | should-fix | The tail of F1 was one chain behind one lead ticket (f1-53 → 54…58 → 30 → 32), so a Claude limit stopped everything. Checkpoints and escalations also sleep through a limit instead of parking. | lead.md (plan craft), f2 |
| 3 | should-fix | Ollama Cloud's six agents are never routed: `[roles] developer` doesn't list them. | f2 (bench, then roles) |
| 4 | should-fix | Status: between tickets `runs.activity` is empty (the page shows a bare "Running"); "waiting for Claude" between jobs names no ticket; after Ctrl-C the run keeps `ended = NULL` and `reserve = 1` (run `20261002-055804`). | f2 |
| 5 | should-fix | Savings credit Sonnet's merged lines as 0 (the report shows −$1.33 for 3 merged tickets). | f2 |
| 6 | should-fix | Jobs don't record the exact model (only the raw log has `claude-opus-5-5`), so a new Sonnet can't be compared with the old one. | ADR 16, f2 |
| 7 | nit | Backfill sets a milestone's status to "done" or nothing: M4's "in review" is lost and M0 has none (`runner/backfill.py:559`). | f2 |
| 8 | nit | "Tickets merged 48 of 59" counts removed tickets in the total. | f2 |
| 9 | nit | f1-S166-1 (bench attempt count), f1-C165-1/2 and f1-S166-2/3 (loose substring tests, cached tokens left out). | backlog |
| 10 | process | Scope grew from 32 to 58 tickets mid-milestone (ADR 15 +7, the owner's watch +2, the factory line +6, fixes +9). | lead.md |
| 11 | owner | **M4 was never signed off** (`docs/milestones/m4.md` says "in review"), and its finding m4-F9 is still queued as `m4-12-send-recovers`. | the owner |
| 12 | should-fix | 6 local attempts (≈2.5 h of GPU) were degenerate: a thinking loop or a stop before any edit, run to 25–30 min. Nothing cuts them early. | f2 |

f1-52 (Sonnet, left unchecked when the run stopped) was read for this review. It's sound: the tests read the rendered panels, and the one gap is finding 4.

## What changed, and where each item went
- **Done in this session:** lead.md (the standing "Factory" section and "What clogged the factory line" in every review; new ideas wait for the next milestone; plans keep developer work runnable beside a lead chain; Known range with F1's numbers); the sign-off sheet's two new sections on the dashboard (f2-10).
- **ADR 16 (Proposed):** findings 1, 2 and 6; replans become standard (lead.md's "Replans" line changes when it's accepted).
- **[F2](../milestones/f2.md):** findings 1–8 and 12, as f2-01 to f2-09.
- **Backlog:** finding 9. **The owner:** finding 11 (M4's sign-off).
- **F1's Done when, not met as written:** no screenshots (every page answered 200 against the real database on 2026-10-02; the factory line's screenshots moved to F3); `runner report m4` can't reproduce M4's Claude numbers, since M4's lead work was interactive and only its 2 escalations are jobs.
