# ADR 23: Parallel lanes: several jobs at once, merged one at a time

- **Status:** Proposed (drafted by the lead, 2026-10-04; for the owner to review after F6)
- **Date:** 2026-10-04
- **Deciders:** project owner (accepts), Claude (drafts)
- **Builds on:** [ADR 22](22-one-visible-queue.md) (one visible queue), which must be built first.
- **Amends:** [ADR 15](15-allowance-aware-routing.md) item 10 (the GPU never idles) and the one-job-at-a-time loop in `docs/workflow.md`.
- **Evidence:**
  - `docs/roadmap.md` "parallel developers" and "cloud and local jobs at the same time": in F1, f1-08, 11 and 12 were ready at once and ran one after another.
  - The owner (2026-10-04): "running work in parallel … will introduce complexity like merging work together and re-reviewing".
  - Their priority list ranks "faster, parallel workers" 7th of 7.

## Context
- **One job at a time** is the rule today. The GPU idles while Claude works on an escalation, and Claude idles while Qwen spends 20–45 minutes on an attempt.
- **The resources are separate:**
  - the GPU (LM Studio, one model, `--parallel 1`);
  - Ollama Cloud (one concurrent request on the owner's plan);
  - Claude (the Pro login: one session at a time is the safe assumption, bounded by its windows);
  - Copilot (read-only reviews).
- **What makes parallel hard:**
  - two branches that touch the same files;
  - merges that are each green alone but red together;
  - checkpoints that count merges landing together;
  - one working tree shared by every job;
  - the runner as git's one writer.

## Decisions (draft; ⚑ = deviates from an earlier decision)
1. **⚑ Lanes, one per resource:** `gpu`, `ollama`, `claude` (and `copilot` for read-only reviews), each running at most one job. An agent belongs to its harness's lane. The picker (ADR 22) fills every free lane from the same queue, in the same order, skipping jobs whose lane is busy.
2. **⚑ Every running job works in its own clone,** as the bench does (`runner/bench.py`): a copy with its own `.git` under `[bench] dir`, never a `git worktree`, because OpenCode then edits the main checkout (f2-12, f4-19). The main checkout only receives merges.
3. **No two jobs at once whose `files:` overlap.** A ticket waits while another running ticket lists any of the same files (tests included). Developer tickets list 2–6 files, so most pairs run. A lead ticket on `runner/` waits for nothing, but nothing on `runner/` runs beside it.
4. **⚑ Merges go one at a time, through a merge step:**
   - A passed job's branch gets main merged in, then `check-all --task <id>` runs again on the result, then the squash-merge happens.
   - A conflict, or a red check after the merge, sends the ticket back to the queue on fresh main, with the conflict as its gate output. That doesn't count as an attempt.
   - The merge step runs in the runner process, which stays git's only writer.
5. **Checkpoints and reviews are unchanged:** they read merged diffs on main, so work merged in parallel is reviewed the same way. `checkpoint_every` counts merges in the order they land. Two that land together are checked together.
6. **Support jobs keep their order within the `claude` lane** (ADR 22's kind order). Planner jobs (ADR 20) take the `claude` lane first. Developer tickets fill the `gpu` and `ollama` lanes meanwhile.
7. **The runner restarts only between jobs:** a lead ticket that changes `runner/` makes the runner stop taking new jobs, wait for the running ones, then restart (`RESTART_NOTE`), as today.
8. **Start with two lanes,** `gpu` and `claude`. Add `ollama` once the bench (ADR 16 item 10) shows an Ollama model passing first attempts at the local model's rate or better.

## Consequences
- The GPU stops idling during Claude's escalations and reviews, and Claude's lead tickets stop waiting behind a 45-minute local attempt.
- More developer work runs, so more of it fails and asks for Claude (directions, escalations). Since F3, Claude finishing failed tickets has been the bottleneck. Parallel helps only if the developers' first-attempt rate holds.
- Merges re-run `check-all` (about 5–10 min each with ADR 21), which is the price of not breaking main.
- The dashboard's line finally shows several machines working at once, as the F1 mock-up drew it.

## Open questions
1. Does Claude Code's Pro login allow two headless sessions at once (a planner beside an escalation)? A probe answers it; until then, one `claude` lane.
2. Should a ticket that conflicts at merge twice go to the lead as an escalation?
3. Gates on two clones at once double the CPU load (about 90 °C already during runs, accepted for one). Measure before adding a third lane.
4. Should the `ollama` lane wait for a cheaper attempt rule (a quick syntax and ruff check fed back within the attempt; `docs/roadmap.md`)?
