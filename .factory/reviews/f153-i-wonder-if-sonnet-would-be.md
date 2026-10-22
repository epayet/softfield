# Review: F153, Sonnet does the easier lead tickets, Opus keeps planning and checks

## Sign-off sheet

### 1. What changed
Nothing you'll notice yet. The runner can now give the easier lead tickets to Sonnet, but your machine's config still lists only Opus, so every lead ticket runs on Opus as before. Once the two lines from ADR 32 are in `~/.config/softfield/factory.toml` (see "What next"):
- a lead ticket of difficulty 4 or below runs on Sonnet, and one of 5 and up (or with no difficulty) on Opus;
- when Sonnet's work fails `check-all`, Opus gets one fresh go on the same branch, told what Sonnet did and what failed, before the ticket is blocked;
- the board, the ticket's record, the merged line and the job's routing reason name whoever did the work ("claude-sonnet, a lead ticket of difficulty 3 (the first agent up to 4)", or "claude-opus steps up from claude-sonnet…");
- a lead ticket stopped half-way (a limit or a restart) carries on with the agent whose session it was;
- no lead merge is checkpointed, whoever did it (as you settled).

### 2. How to test it yourself
1. Add the two lines to `~/.config/softfield/factory.toml`: `lead-ticket = ["claude-sonnet", "claude-opus"]` under `[roles]`, and `lead_first_up_to = 4` under `[claude]`. The runner picks them up at its next start.
2. Wait for (or plant) a card whose lead tickets have difficulty 3 or 4. On the dashboard's line, the lead-ticket job shows as claude-sonnet; open the job to see the reason "a lead ticket of difficulty 3 (the first agent up to 4)".
3. A ticket of difficulty 5 or more shows claude-opus, with "the second agent above 4".
4. If a Sonnet ticket fails its checks, the same ticket shows a second lead-ticket job on claude-opus, with "steps up" in its reason; the ticket ends merged by Opus or blocked, never blocked straight after Sonnet.
5. To go back: `lead_first_up_to = 0` (or remove the line) and restart the runner.

### 3. Left for later
Three nits in `docs/backlog.md`, all rare corners of the step-up:
- an Opus step-up that waited on a red main is credited to Sonnet when it merges later (F2);
- a stop in the seconds between Sonnet's failed checks and Opus's start loses Sonnet's work (F3);
- a lead job's "passed" means its session ended well, not that its checks passed, so the trial's pass rate must be read from the tickets and the step-up jobs (F4).

### 4. Decisions waiting for you
None. ADR 32 was accepted on 2026-10-20 and this milestone builds it as written.

### 5. How the work went
- 2026-10-22 22:20 ([session](../sessions/2026-10-22-2220.md)): `f153-01-lead-ticket-by-difficulty` (routing by difficulty, the agent recorded), Opus, merged first time in 17 minutes for $1.93; 0 local tokens.
- 2026-10-22 22:41 ([session](../sessions/2026-10-22-2241.md)): `f153-02-sonnet-lead-checked-and-stepped-up` (the Opus step-up), Opus, merged first time in 6 minutes for $1.01; 0 local tokens.
- Lessons: two small, well-cut lead tickets with the decisions in the card went through first time for $2.94, under ADR 32's $5 estimate. The developers' docs were the gap: neither ticket listed `docs/workflow.md`, so the rule change reached the code and not the description of the workflow; the review added it. A ticket that changes a workflow rule should list the doc that states the rule.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** turn the trial on: the two config lines above (I can't write outside the repo from a headless job; the next terminal session can, or you can). Then let about 15 Sonnet lead tickets run and read ADR 32 item 6 at the next factory review: first-time pass rate per model (from tickets and step-ups, not `jobs.outcome`), review findings in Sonnet's lead work against Opus's, dollars per ticket with step-ups, and how often Claude parked. If Sonnet does well at 4, try 5.

### 7. What clogged the factory line
- Two lead jobs, 23 minutes in all; nothing waited on limits, failed attempts or the owner.
- Each merge changed `runner/`, so each run ended on the designed stop and a fresh process started: about 4 minutes from f153-01's merge (22:37) to f153-02's start (22:41), and 4 more before this review (22:48 to 22:52). That is the price of the restart-on-runner-change rule; nothing to unclog.

## What was built
- `runner/config.py`: `[claude] lead_first_up_to` (`Config.lead_first_up_to`, default 0), refused unless a whole number of 0 or more.
- `runner/router.py`: `route` for `lead-ticket` (`_lead`): with two agents and a limit, the first takes a ticket of difficulty up to it and the second the rest and any unestimated one; with one agent or the limit 0, the last listed. One reason line each.
- `runner/loop.py`:
  - `run_lead_task` routes through `_lead_route`: an interrupted or parked ticket resumes on the agent stored with its session, else the router decides;
  - the agent is now stored in `state.interrupted` by `_park` and `_recover`;
  - `_settle_or_step_up`: when the agent wasn't the last listed and `check-all` failed (main not red), one fresh job by the next agent on the same branch with `LEAD_STEP_UP_NOTE`, then settled as the last attempt;
  - `_settle_lead_task` names the agent in `record_ticket` and the merged line, and writes the real attempt count in the footer.
- Tests: config (read, default, refused), router (four cases), loop (routing by difficulty with the record and merged line, resume on the stored agent, the step-up passing and failing, the last agent blocked at once, no checkpoint). Two existing tests were edited, only to add the new `"agent"` key to their expected `interrupted` entry; neither lost an assertion.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | `docs/workflow.md` and `docs/how-it-works.md` still said a lead ticket is one Opus attempt, then blocked | Fixed: a "Who does a lead ticket" bullet in workflow.md step 4; the flowchart's lead box names Sonnet and the step-up |
| F2 | nit | backlog | An Opus step-up that waited on a red main is re-routed by difficulty when main passes: credited to Sonnet, 1 attempt, and a second step-up on failure | `docs/backlog.md` |
| F3 | nit | backlog | A stop between Sonnet's failed check-all and Opus's job start leaves no `interrupted` entry; the next run's `fresh_branch` drops Sonnet's work | `docs/backlog.md` |
| F4 | nit | backlog | A lead job's `jobs.outcome` is its session's; a Sonnet attempt that failed check-all reads "passed", so the trial must read pass rate elsewhere | `docs/backlog.md`, and noted in ADR 02's log and "What next" |

No checkpoint ran (both tickets were lead tickets), so there are no checkpoint verdicts. Score: 8/10. Both tickets match D1–D4 closely, the routing reasons read well, and the loop tests drive the real path (Sonnet fails, Opus builds on the same tree); the only real gap was the docs.

The French: no `coucou/locale/fr/` change in this milestone.

## Factory
- Flow: two lead tickets, first attempt each, no stops for the owner, no limit waits, no parks; each run ended on the designed `runner/` stop.
- Models: Claude Opus built both ($1.93 and $1.01); the local model had nothing to do (protected code). Sonnet has still done no lead ticket: the trial begins with the config change.
- What to change: a ticket that changes a workflow rule lists the doc that states it (`docs/workflow.md`) in `files:`. Once here; a line in `docs/task-writing.md` if it recurs.

<!-- runner report -->
<!-- /runner report -->
