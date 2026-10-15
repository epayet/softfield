# Milestone F140: Copilot takes checkpoints first, within its pace From the…

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-15.

## Notes
Copilot takes checkpoints first, within its pace

From the owner's terminal session of 2026-10-15 (started in Coucou's repo; the work is Softfield's). The owner's decision; it needs an ADR that amends ADR 16 items 9–10 and f8-08's re-check. Planted for later because a runner was live and its checkout was on a task branch.

## What the owner asked
"Why hasn't Copilot been used in a while?" Then: use Copilot first within its pace, as a priority, to save Claude tokens, assuming it does a good job. Below its pacing threshold (the same pacing logic as Claude's) → Copilot first. Beyond its pace → Claude. Claude at its threshold → Copilot even beyond its pace. The goal is to make the most of the free Copilot tier and save Claude.

## Why Copilot was idle (findings, 2026-10-15)
- Copilot (`copilot-auto`, Copilot Free through its CLI, read-only) has one role: `[roles] checkpoint-stand-in` in ~/.config/softfield/factory.toml. It does a checkpoint only when Claude is held: past 75% of its 5-hour window, or refused (`claude_hold`, ADR 16 item 9). It never develops (`READ_ONLY_HARNESSES` in runner/router.py).
- Its last job was a checkpoint on 2026-10-07 at 14:46 (softfield, f6-15 and f6-20); Claude re-checked them at 16:56 (f8-08).
- Since then, every one of the 22 checkpoints (up to 2026-10-15 09:51) went to claude-sonnet, and none was parked (`work_queue.not_before` empty). So Claude was never held when a checkpoint came due, and the stand-in was never needed.
- Its allowance wasn't the reason: the month was 18.8% used (resets 2026-11-01), at about 1 credit per checkpoint. No run note said "No checkpoint stand-in may run now".
- Coucou has never had a Copilot job; every one was Softfield's.

## Shadowing, and how it was replaced
- ADR 14 item 12: an agent earned a role by shadowing it, doing the job alongside the holder, its output recorded but never acted on, over 2+ milestones.
- ADR 16 item 10 replaced shadowing with the bench: `runner bench` replays past checkpoints and scores findings against known ones. `[roles] checkpoint-shadow` is empty; `shadow_checkpoint` stays, unused.
- ADR 16 item 10 also says Copilot's normal use is its bench replays, paced over its month. ADR 16 item 9 lets the stand-in go past pace, up to the month's capacity.

## Pacing already exists
runner/allowance.py treats Copilot's month (`windows = [{ name = "month", capacity = 200 }]`) as a fixed, paced window, the same logic as Claude's week (ADR 15, ADR 25's margin). `router.stand_in` calls `allowance.answer(..., use_reserve=True)`, a cap. `use_reserve=False` gives the pace line.

## Quality and savings: the risk the owner accepted
- Bench, 2026-10-04 (jobs 383–391, plus 205 on 10-02): Copilot found about 7 of about 35 known findings (about 20% recall) and missed 1 blocking one. It also raised about 18 "new to judge", which nobody has judged yet.
- Live stand-in checkpoints (jobs 228, 231, 292, 420, 423, 467, 529) filed 25 findings (1 blocking, 24 should-fix). Claude re-checked each of those merges.
- Since 2026-10-08, sonnet checkpoints found 59 (1 blocking, 36 should-fix, 22 nit).
- Claude spend since 2026-10-08 by role (cost_usd): opus planner 107.43, lead-ticket 44.71, review 37.74, escalation 19.41, direction 16.08; sonnet checkpoint 3.38 (18 jobs); haiku probe 0.11. Checkpoints are about 1.5% of Claude's spend, so the saving is small.
- Other limits: `auto` doesn't say which model it is and can change without notice, so ADR 15 item 9's other-model rule can't be checked. Copilot reviews from a file list with no git and no pytest, where Sonnet can run both.
- What was offered: re-bench first (free credits), Claude auditing about 1 in 4 Copilot checkpoints, and switching back to Claude after a missed blocking finding. The owner chose plain pace-first: "in the future factory reviews we can review". The Opus milestone review stays the backstop.
- Also raised but not chosen: Copilot could take part of the larger Opus spend instead (milestone review, direction).

## The rule
Whenever a checkpoint is due and there are unchecked merges:
1. Copilot is within its monthly pace line → Copilot does the checkpoint, read-only. Its result is final: findings that aren't nits become fix tickets (routed local) as Claude's would, and Claude doesn't re-check them.
2. Otherwise, if Claude may run → Claude (Sonnet, or Opus when Sonnet wrote the code), as now.
3. Claude held → Copilot up to its month's cap (ADR 16 item 9), now also final with no re-check.
4. Nobody may run → park, as now.
A Copilot job that fails within pace falls through to step 2. Copilot is still never used on merges a Copilot-harness developer wrote (there are none).

## Where (design sketch)
- runner/router.py `stand_in`: a keyword `paced: bool`. True → `allowance.answer(..., use_reserve=False)` (the pace line); False → the cap, as today. The reason line says "within its pace" or "stands in for Claude".
- runner/loop.py `checkpoint()`: before `claude_hold`, when `state.unchecked` is non-empty, try `stand_in_checkpoint(..., paced=True)`. If it succeeded and `state.recheck` is empty, return. The held branch passes `paced=False`.
- runner/loop.py `stand_in_checkpoint`: take a reason string instead of a `Hold`. Stop adding to `state.recheck` / `recheck_filed`, but keep the fields and `_recheck_note` so leftover entries drain to Claude. Commit and report wording: "(by copilot-auto, within pace)" or "(…, standing in for Claude)".
- runner/prompts.py `CHECKPOINT_STAND_IN`: likely unchanged.
- factory.toml (machine config): the comment on `checkpoint-stand-in`; the key stays.
- ADR 31 (draft for the owner to accept); ADR 16 items 9–10 point to it; docs/agents/lead.md if it says who does checkpoints.
- The dashboard's "who did each ticket" and stand-in labels may need the new wording.

## Tests
- tests/runner/test_router.py: paced refuses past the pace line and allows under it; the cap allows up to capacity; the author-harness skip still holds.
- tests/runner/test_loop.py: within pace, Copilot runs, Claude isn't called and `recheck` stays empty; past pace with Claude free, Claude runs; past pace with Claude held, Copilot runs capped; Copilot failing within pace falls to Claude.

## Done when
New checkpoint jobs on copilot-auto with a "within … pace" routing_reason; Copilot's month reading rises along its pace line; Sonnet checkpoints only when Copilot is past pace; a factory review compares Copilot checkpoints' findings against what the milestone reviews catch afterwards.
