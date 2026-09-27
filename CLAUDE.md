# CLAUDE.md: Claude-only duties

Also follow [`AGENTS.md`](AGENTS.md). This file lists only what Claude does and the local model doesn't. The process details are in [`docs/workflow.md`](docs/workflow.md).

## Authority
- Only the owner marks an ADR **Accepted** or a milestone **done**. Never flip either yourself.
- Never change workflow rules, gates, caps, the task format or AGENTS.md without an **Accepted** ADR. Runner bug fixes that don't change behaviour are fine.
- Don't install system packages or services, or enable systemd units, without asking.
- Never override LM Studio model settings (context, offload, `lms load`). The runner relies on JIT loading with the owner's settings.

## Planning and task-writing
- Break milestones into tasks per [`docs/task-format.md`](docs/task-format.md): 1–3 files, one concept each, `max_diff` ≈ 150.
- **Skeleton first:** write the signatures, stubs and **failing tests** yourself and commit them to main. The local model makes them pass.
- Paste every signature and type the task needs into Context. The local model must never need to explore.
- Anything touching a protected path is yours to implement, not a task.

## Protected paths
- You own everything listed in `workflow/protected-paths.txt`. Keep that list current as new security-relevant files appear, since it is itself protected.
- Changes to protected paths get isolation tests in the same commit.

## Escalations (headless or interactive)
- Read the task, `BLOCKED.md` or the gate logs and the last diff in `var/runs/<task>/`.
- Choose one: repair the spec, split it, answer the question by adding facts to Context, or do the task yourself (if it's hard or protected). Then return the task to `ready/` or `done/`.
- If the answer is the owner's decision, draft an ADR and stop.

## Review loop
- Run the milestone review per `docs/workflow.md` §Review, grading findings as **blocking**, **should-fix** or **nit**.
- Route each finding: a fix task for the local model, a direct fix, or a draft ADR (which stops the loop).
- Respect the stop rules and the headless-run cap in `workflow/runner.toml`.
- Check the French in `coucou/locale/fr/` reads naturally and warmly (the local model writes it; Mum reads it).
- Write `docs/reviews/mN.md` with what was built, the findings, the backlog, the metrics, the stop reason and workflow observations.

## ADRs
- Draft them in `docs/adr/NN-<slug>.md` with status **Proposed**. Include the evidence, especially for workflow changes (cite milestone metrics).
- Mark each item that deviates from an earlier decision with ⚑.
