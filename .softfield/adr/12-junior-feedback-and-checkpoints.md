# ADR 12: Juniors check their own work; the lead steers mid-milestone; one command runs it all

- **Status:** Accepted (by the owner, 2026-09-30; shaped item by item in conversation)
- **Date:** 2026-09-30
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

M4 was the first milestone run the ADR 07 way (tickets, not solutions; juniors write their own tests). From [`.softfield/reviews/m4.md`](../reviews/m4.md):
- **First-attempt pass rate: 5/9.** Escalations: 7, against a target of ≤ 3. Blocking findings in juniors' code: 1, against a target of 0. ADR 07's rule says to tighten, not to go back.
- **Gate failures the junior could have caught itself:** translations ×2 (m4-04) and ruff ×6 (m4-06). It has no command for the translations or layout checks, and the prompt asks it to run only its own tests.
- **Wasted attempts:**
  - 8 of m4-06's 9 attempts hit the 30-minute timeout
  - one attempt made 20+ near-identical edits without running a test
  - one ended without editing anything and passed every gate on an untouched tree, then crashed the merge
- **Silent failures in its tools:** piped commands (`| head`) are refused with empty output, and OpenCode's 2-minute shell limit cut off test runs whose failing tests each waited 30 s.
- **The review found problems the gates can't see, and later tickets built on them.** m4-06 wired up m4-01 and m4-04's components before anyone had read them. The "two or more dependants" tickets (m4-01, m4-06) were the source of m4-F1, F2 and F3.
- **Where escalations came from:** m4-04, m4-06 (three rounds) and m4-07 reached their last attempt; most of the 7 escalations followed. Reading the junior's thinking explained m4-06 at once (a CSP trap); the canned retry hints didn't.
- **The lead also slipped:**
  - I committed type errors twice (`mypy | tail` hides the exit code)
  - a headless escalation committed one
  - one lead session stayed open through every phase, re-reading a 300k+ context at each turn (about 10M of M4's ≈18M, escalations included)
- **The headless cap of 10 per milestone** skips runs silently when reached, and counts runs rather than cost. With checkpoints, even a normal milestone would pass it.

## Decisions (⚑ = deviates from an earlier decision)

### A. Juniors
1. **One command runs every check.** `uv run runner check-all` runs ruff format and check, mypy, `check-i18n`, `check-layout` and the full `pytest -q` (34 s when green), and exits non-zero on any failure. It's allowed in `opencode.json`, and it's the whole finish line, on one line, last in the prompt (juniors drop long instructions). If a junior skips it, the gates still run everything and the next attempt gets the output: the cost is an attempt, never correctness.
2. **The prompt says** that pipes, redirections and unknown flags are refused and return nothing, so commands must be run exactly as written.
3. **A `test-patterns` gate,** after `layout`, on the junior's added lines in `tests/browser/` and `tests/e2e/`:
   - `if … is_visible()` / `if … count()` branches (a test that skips a step passes without testing)
   - `dispatchEvent(…)` or setting `.value` from JavaScript (tests states a person can't reach; m4-F1)
   - `time.sleep` / `wait_for_timeout`
   - `wait_for_function` given a bare expression, not a function (the real pages' CSP blocks it once it polls; m4-06)
   - and, anywhere, a new module with no code in it (m4-F7)

   Each has a one-line hint. A line ending in `# pattern-ok: <reason>` passes; checkpoints read those. More patterns only when a finding recurs.

### B. The runner, within a ticket
4. **An empty attempt fails.** An attempt that changes no file is a failed `no-changes` attempt (already in `main`, `7655448`; confirmed here). The runner reads OpenCode's stream to say why (it timed out, it thinks it's done, or it's stuck on a refused command or a question) and gives the hint for that cause.
5. **A retry after a timeout says so:** "your previous attempt ran out of time. Keep what works and finish the smallest remaining piece first". The timeout itself is operational: 2700 s in `runner.toml`, so a ticket can take over 2 hours in the worst case.
6. ⚑ **The lead gives direction before the last attempt.**
   - **When:** before attempt 3 (`max_attempts = 3`), only if the failure isn't mechanical: a timeout, the task's tests, `layout`, `protected-paths`, the same gate failing twice, or an empty attempt twice. When ruff, format or i18n is the only failure, the gate output is enough.
   - **What it does:** a short headless job reads the gate logs, the last diff and the junior's thinking (OpenCode's `opencode.db`, `part` rows of type `reasoning`, read-only). It writes a direction of a few lines: what went wrong and the facts the junior is missing, **no code** (ADR 07). It replaces the canned hint. If the ticket itself is wrong, it repairs the ticket instead.
   - At most one per ticket.
7. **Loops are logged, not stopped.** The runner counts steps that edit without running a command (from OpenCode's JSON stream) and puts the longest streak in the direction prompt and the session report. Stopping an attempt on it waits until M5 shows the problem recurring.

### C. The runner, across tickets
8. ⚑ **A checkpoint every 2 merges** (replaces this ADR's draft "checkpoint tickets" and "plan depth ≤ 3").
   - After every second merged ticket, the runner pauses the queue and runs a short headless review of those diffs.
   - It reads the code and tests, not the junior's thinking (that's only for explaining a finding).
   - It does one or more of: approve; queue a fix ticket that the next tickets wait for; tighten upcoming tickets with what it saw; add a `junior.md` note.
   - Try the Sonnet model for it, and compare what it catches at the M5 review.
9. ⚑ **The lead's own work goes in the queue.** The lead's items (protected, security, test-first, a new kind of work) become tickets with `agent: lead`, with the same `depends_on` as juniors' tickets. The runner runs them as headless `claude -p` jobs, test-first, and they must pass `check-all`. The plan session writes both kinds of ticket in one pass.
10. ⚑ **Limits per trigger replace the cap of 10 headless runs per milestone** (amends ADR 07, "the headless cap stays"):
    - at most 1 direction per ticket
    - a checkpoint every 2 merges
    - at most 2 escalations per ticket
    - 1 review loop per milestone (its existing rounds and stop rules)

    A ticket past its limits goes to `.softfield/tasks/blocked/` and is named in the report, **never skipped silently**. `headless_claude_runs_per_milestone` is removed. The Pro usage-limit backoff stays.
11. **An escalation must pass `check-all`** before the runner commits its work. If it fails, the work goes to an `escalation/<task>` branch, the ticket goes to `blocked/`, and nothing reaches `main`.

### D. The owner's workflow
12. ⚑ **`uv run runner milestone N` runs a whole milestone,** in a plain terminal, with no interactive Claude session open (replaces "one fresh session per phase" as the rule the owner follows):
    1. the queue, lead and junior tickets, in dependency order, with directions, checkpoints and escalations
    2. the review loop (today's `runner review`), with its fix tickets
    3. the report

    It's safe to rerun at any time (the state lives in the repo and `var/`), and it restarts itself when an escalation changes `runner/`, instead of stopping.
13. **The report ends with a verdict**, printed last and written to the session report:
    - **`✅ READY FOR SIGN-OFF`**: the device-test steps and the exact `runner signoff N` command.
    - **`⚠ NEEDS YOU`**: each ADR a job drafted for the owner, with its one-line question and the tickets paused behind it; each blocked ticket with its reason; the exact next step ("decide ADR 14, then rerun `uv run runner milestone 5`").

    Exit codes: 0 ready, 2 needs you, 1 crashed. A decision for the owner pauses only the tickets that depend on it; everything else carries on.
14. ⚑ **Commands for the owner:**
    - `uv run runner signoff N`: sets `.softfield/cards/mN.md` and `.softfield/reviews/mN.md` to done with the date, tags `mN-done` and commits. It refuses while tickets are paused behind an ADR the owner hasn't decided.
    - `uv run runner accept N` / `uv run runner reject N`: sets ADR N's status with the date and commits.
    - Headless jobs never get these commands: only the owner accepts ADRs and signs off.

    The owner's milestone becomes: a plan session ending in "go" → `runner milestone N` → read the verdict → (decide any ADRs, rerun) → the device check → `runner signoff N`.

### E. The lead
15. **A pre-commit hook runs `runner check-all`** before every commit. It skips commits that only touch `docs/` or `.softfield/tasks/`; the runner's merge commits bypass it, since they already passed the gates.
16. **The lead reads the junior's thinking when something went wrong:** always at directions and escalations; at checkpoints and reviews only when a finding needs explaining.
17. **Dropped: plan depth.** Checkpoints steer instead. `runner/instructions/task-writing.md` gets one ticket rule: a junior ticket depends on at most two other junior tickets; past that, split it or make it a lead ticket.

## Consequences
- **Juniors:** one extra command at the end of each attempt, and fewer failed attempts on checks they can now run.
- **Runner:** new code for `check-all`, the pattern gate, the empty-attempt triage, directions, checkpoints, lead tickets, the per-trigger limits, `milestone`, the verdict, `signoff`/`accept`/`reject` and the hook, each with runner tests. It's a lead milestone in itself, split into lead tickets.
- **Cost:** checkpoints and directions add headless runs (about 0.3–0.6M each, from M4's escalations). They should pay for themselves in fewer escalations and less review work. No interactive session stays open during a run.
- **The owner:** two touchpoints per milestone (the plan and the sign-off), plus a decision when the verdict says so.
- **Measured at the M5 review, against M4:**
  - should-fix issues per junior ticket (8/9)
  - escalations (7)
  - first-attempt pass rate (5/9)
  - timeouts (9)
  - checkpoint and direction runs, and what each caught
  - lead spend per junior task (≈2M)
