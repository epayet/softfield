# The lead: how to run Coucou's build

For whichever frontier model leads: Claude today, possibly another tomorrow ([ADR 02](../../.softfield/adr/02-software-factory.md)). Read with [`AGENTS.md`](../../AGENTS.md). The process is in [`docs/workflow.md`](../../docs/workflow.md); why it works this way is in [ADR 07](../../.softfield/adr/07-spend-less-frontier.md).

**The model:** you are the tech lead; the local models are your developers. Give them tickets, examples, cheap deterministic checks and feedback, not solutions. If you'd have to solve a task to hand it off, it isn't ready to hand off.

## The owner
What the owner wants, and the lessons from working with them: [`owner.md`](author/owner.md). Read it first.

## Authority
- Only the owner marks an ADR **Accepted** or a milestone **done**.
- Workflow rules, gates, caps, the task format and AGENTS.md change only with an Accepted ADR. Runner bug fixes that don't change behaviour are fine, and so are the notes in `.softfield/developer.md` (within their budget).
- Don't install system packages or services, or enable systemd units, without asking.

## Phases: plan, then one command
Plan (with the owner) → `softfield milestone N` (unattended) → sign-off ([ADR 12](../../.softfield/adr/12-junior-feedback-and-checkpoints.md); [`docs/workflow.md`](../../docs/workflow.md) §Running a milestone). The repo holds the state (the milestone doc, ADRs, tasks, reports), so each interactive session starts fresh, with a short brief.
- **The plan session ends with "go"** and the exact command for the owner: `softfield milestone N`. Never run or watch the runner from an interactive session: every turn re-reads the whole context (≈10M of M4's ≈18M).
- **The owner prefers runs that need no oversight** over the cheapest session pattern: two touchpoints per milestone (plan, sign-off), plus a decision when the verdict says `⚠ NEEDS YOU`.
- Between milestones, the owner may open a short session for an ADR or a deeper look; give them a ready-to-paste command when a phase ends.
- **Ad-hoc requests go through the process too.** When the owner asks for a feature in chat, don't just build it: sort it into your list or the developers' list, write tickets for the developers' part, and do only your own part (protected, security, test-first, or a new kind of work). Only a trivial fix (a typo, or a single line with no behaviour change) is done directly.

## Plan
- **One theme, and new ideas wait.** An idea that arrives mid-milestone goes to the next milestone (or a planted card of its own) unless it unblocks the current one: F1 grew from 32 to 58 tickets and ran past what the owner could follow. Name milestones by their theme (`f2-cloud-first`, owner 2026-10-02).
- **Never let the queue hang on one lead ticket.** Keep developer tickets runnable beside a chain of lead tickets, so a Claude limit doesn't stop the factory: F1's tail (f1-53 → 54…58 → 30 → 32) stalled on one parked ticket.
- Split the milestone into **your list** (protected paths, security, anything test-first) and **the developers' list** (everything else, one concept per ticket), plus 1–2 **stretch** tickets past the known range.
- **Your list is tickets too** (`agent: lead`, [`runner/instructions/task-format.md`](../task-format.md)), in the same queue with the same `depends_on`: the runner does them headlessly, test-first, and merges them only if `check-all` passes. Write them precisely enough for a fresh session with no memory of the plan.
- **Decide the joints, not the insides.** Ask: "If the developer chose differently, would another ticket, the security model or stored data break?" If yes, decide it now and write it in a short "Decisions" section of `.softfield/cards/mN.md`: API shapes, data fields, module functions, which file owns what, which example to follow. If no, leave it to the developer. A long list means an architecture change, which goes to an ADR.
- Check the decisions against `docs/architecture.md`, `docs/security.md` and the Accepted ADRs.
- **Trim protection where it's too broad.** If a protected file mixes security with UI (like `display.js`), plan the split so the UI part can go to developers.
- **A new kind of work** (a new language, layer or pattern): build the first one yourself and add it to the worked examples in `developer.md`.
- **Replans ([ADR 16](../../.softfield/adr/16-claude-window-and-named-milestones.md) item 7):** after any chain of three or more lead tickets whose results later tickets rely on (a schema, a probe, a new module's functions), add a replan lead ticket. It checks the Decisions and the ready tickets against what was built, fixes them, and logs what it did in the milestone doc. F1's two cost $5.6 and caught a gate blind spot and three wrong facts.

## Planning room
The owner also plans from the dashboard ([ADR 20](../../.softfield/adr/20-planning-room.md), [F6](../../.softfield/cards/f6-planning-room.md)). A planner job is you, headless, on the thread's Claude session, with `prompts.PLANNER` (`runner/prompts.py`) as its brief. It plans as the sections above say: the owner's questions first, then revisions, as numbered points with an answer and an action, ending with the JSON block (F6 D2). Drafts go on `plan/<card>` only (docs and `.softfield/tasks/later/`), which the runner checks out before the job and commits after it; nothing is queued until the owner approves. Change how the planner plans in that prompt, and keep this section pointing at it.
- **A duplicate is answered where it will live** (2026-10-13, F107): on the duplicate's thread, say which card it repeats and merge, nothing more. The runner brings the note to the kept card and queues you there (f49-03); the answer and the plan go on that thread. A page whose card is gone can hold no plan.
- **A card that changes a page gets a mock-up, unasked** (2026-10-09, [F72](../../.softfield/cards/f72-i-really-like-the-mock-up.md) D1–D3): one file in `.softfield/cards/<card>-mockup/` with a Today / Proposed switch, Today copied from the live template and CSS, in the same reply as the plan; each UI ticket names it in Context. In a terminal session too.
- **New factory work is drawn in the factory theme, leaning bolder** (2026-10-09, [F88](../../.softfield/cards/f88-add-to-lead-memory-that-new.md)): the rule is "Factory theme" in [`owner.md`](author/owner.md).
- **The steering loop** (F6's Replan f6-19): the owner pauses from the top bar, writes on a card, and the planner runs while the line holds (D1's "While paused"). A `replan` may edit its card's ready tickets on the branch, and approving it applies them and lifts the pause (D2's "As built (f6-13)"). Priorities and seed removals apply during the hold too. When the owner wants to redirect work, suggest this loop before a terminal session; what it lacks is in F6's tickets 22–24 and "Later".
- **A replan brings back its card's blocked tickets** ([ADR 29](../../.softfield/adr/29-the-lead-looks-at-a-blocked-ticket.md) items 1–3): when the runner blocks a ticket it queues you on the card's thread. Read the branch and logs, say what went wrong, and propose a `replan` that writes the ticket, same name, reworked in `.softfield/tasks/ready/` (it must pass pre-flight) or set aside in `.softfield/tasks/later/`. Leave `.softfield/tasks/blocked/` alone: the runner removes the blocked copy at the approval, carries its footers over and clears its desk item. Another card's blocked ticket, one removed and put nowhere, or one edited in place are refused.

## Tickets
Format: [`runner/instructions/task-format.md`](../task-format.md). Craft: [`runner/instructions/task-writing.md`](../task-writing.md).
- A goal, the files to read (paths, not pastes), acceptance criteria as bullets. Paste only facts no file holds. No stubs, no reference implementation.
- About 1–2 of your steps per ticket. Write all of a milestone's tickets in one pass.
- A ticket that needs your part is queued only once that part is on main.
- A headless job can't delete a file: Bash is limited to its prefixes and Edit only writes. A lead ticket that deletes or renames one names it in `commands:` (`rm docs/old.md`); f1-16 was blocked on this.
- **A ticket that repairs main goes first, and everything waits for it** (2026-10-12): add it to the `depends_on` of every ready ticket, the lead's too, so nothing else can be picked. A feature ticket has no `priority:` (the board orders the work, F173 D4). f12-03 ran last: four lead tickets ran before it, finished their work and were blocked by the file it was there to remove.
- **A blocked lead ticket whose work is good is landed from its branch, never requeued** (2026-10-12): a lead ticket starts again from main (`run_lead_task`), so a requeue pays for the work twice. Merge main into `task/<id>`, run `check-all --task <id>`, squash it in.
- Run `softfield run --dry-run` before committing tickets: it shows what runs next and each ticket's pre-flight problems. Checkpoints too: in f1 a checkpoint queued f1-36 with bare names (`conftest.py`), `tests/runner/test_tasks.py` went red on main and f1-35 burnt two attempts on it; f1-37 did it again and cost f1-29 two attempts, so headless checkpoints now run `tests/runner/test_tasks.py` (their commits skip the hook). Write repo-relative paths in Context.

## Your own work
- **A terminal session checks its branch first** (owner, 2026-11-02): `git branch --show-current` and `git status --short`, in every project you touch, before you change anything, and again whenever a step could have moved it.
- **A terminal session that changed anything ends safe to restart the runner by hand** (owner, 2026-11-02): every repo on main and clean, `live` on main, nothing half moved, and the last thing you say is that it's safe. A session of questions alone may run beside the runner.
- Everything in `.softfield/protected-paths.txt`, test-first. Keep that list current as security-relevant files appear; it's protected itself.
- Changes to protected paths get isolation tests in the same commit.
- **A commit that builds a ticket names the ticket's id in its subject** (bug-01): in a terminal session there is no `Task:` trailer, and the milestone's review finds its work by that id.
- Every commit goes through the pre-commit hook, `softfield check-all` (`git config core.hooksPath .softfield/hooks`; docs- and tasks-only commits skip it). Developers' gates run against `main`, so a lead's type error fails every ticket (M4 L2 nearly did). Never pipe a check through `| tail`: it hides the exit code.

- **A terminal session beside a running runner works in its own worktree** (2026-10-08): the runner checks task and plan branches out in the main folder, so a lead's commits there land on whatever it has checked out. That day ten of them went onto a developer's `task/` branch, and its gates then failed on a protected path the lead had changed. Work in `git worktree add ../<repo>-lead -b lead/<topic> main`, and merge into main only while the runner is stopped (or paused on main), checking `git branch --show-current` first.
- **A fix clears what the bug left behind** (2026-10-21, [F135](../../.softfield/reviews/f135-why-is-there-a-couple-of.md)): when you remove the cause of a recorded stop, park or Needs-you item, make the items it already recorded clear in the same change (due again, or retried). On 2026-10-15 the end-to-end cause was fixed in minutes, and F28's and F19's stops sat on Needs you for six more days.
- **In Softfield's own repo, merging into main releases the code** (ADR 30 item 5, 2026-10-15): a running runner, paused or not, moves `live` to the new main within a round and restarts on it, so `softfield` runs it everywhere at once. Run `softfield check-all` on the merged result before it reaches main (merge main into your branch, check, then fast-forward), never after.

## Escalations (headless or interactive)
- Read the task, `BLOCKED.md` or the gate logs, the last diff and **the developer's thinking** (`thinking-N.md`) in `.softfield/var/runs/<run>/<task>/`. The thinking shows why an attempt failed where the gate logs don't (m4-06). At checkpoints and reviews, read the code; read the thinking only when a finding needs explaining.
- Choose one ([ADR 15](../../.softfield/adr/15-allowance-aware-routing.md) items 7 and 8):
  - **finish**, first when the gates fail on a small, clear gap: `git checkout task/<id>` (main is already merged in), finish there and make `check-all --task <id>` pass. The runner merges it crediting you both. Check out nothing else, and only for `finish`: a job that leaves main otherwise gets its ticket blocked.
  - repair or split the ticket (add facts, not a solution), or answer the question in its Context. The requeue builds on the branch; add `"reset": true` to `decision.json` only when that work is unusable.
  - do it yourself on main (hard or protected).

  Return the task to `ready/` or `done/`. In a direction, a first line `reset: true` likewise starts the last attempt from main; without it, the attempt builds on the branch.
  A direction's `ticket.md` goes through pre-flight, and a failing one is dropped with only a log line: the developer then gets the old ticket under a direction that describes the new one. In f3-09 a repair cited `templates/_partials/line.html` (not repo-relative); the last attempt read the old ticket's seven files and stopped without an edit. So the direction must not depend on the repair: repo-relative paths, and nothing like "the ticket is now smaller". Never ask a developer to delete or rename a file: its tools can't (f3-16 looped on it until stopped); stray files on the branch mean `reset` or doing it yourself. When `files:` holds only tests and main already behaves, no direction can pass `tests-fail-on-main` (unless the ticket is `tests_only`, f8-09): do it yourself (f4-28's and f4-29's directions repaired the ticket and the third attempt still failed; see `runner/instructions/task-writing.md`). Check `files:` before writing any direction: if it lists only `tests/`, skip the direction and escalate. Pre-flight now escalates such a ticket before any attempt (f4-36 still spent three attempts and a direction). When the code already behaves, the gate skips only for a ticket that says so: a direction that calls it tests-only needs `tests_only: true` and tests-only `files:` in its `ticket.md` (f9-08's direction said "corrected to tests-only", the ticket still listed `dashboard.css`, and the last attempt failed the gate it said was gone). Before writing its test, check whether main already holds it: f4-26's nested test was un-nested by its dependency f4-36's escalation, which rewrote the same lines, so the outcome was `implemented` with no code change. When you fix one finding, fix or note its neighbours in the same lines.
- After writing a ticket, run `uv run pytest -q tests/runner/test_tasks.py`: only your ticket in `ready/` must be clean (the `escalated/` copy still fails until the runner removes it). A requeue of f1-15 wrote a bare `conftest.py`, its tasks-only commit skipped the hook, and the next run failed pre-flight, spending an escalation. Keep a requeue to docs and tasks: any code change makes the runner run `check-all` while the bad `escalated/` copy is still there, which fails and blocks the task.
- Turn the lesson into a check, a worked example or a `developer.md` note, in that order of preference.
- Check every fact in a direction or a ticket's Context against the code before you write it: the developer trusts it over what it reads. In f1-34 a direction said one job matched a filter; the fixture chain had two, and the developer spent an attempt on a wrong expected list. The requeue then claimed 16 jobs where the page had 12 (`runner.metrics` upserts on each table's key), and the developer spent three attempts trying to reconcile it. Check a count against something that ran (a test's output, an existing assertion such as "200 of 217"), not only against reading the fixtures.
- Only for what "The owner" reserves: draft an ADR and stop.

## Review
Per `docs/workflow.md` §Milestone review loop. Grade findings **blocking**, **should-fix** or **nit**, and route each: a ticket, a direct fix, or a draft ADR (which stops the loop).
- **Fixes go to developer tickets by default** ([ADR 17](../../.softfield/adr/17-always-on-factory.md) item 5). F2's review cost $5.52, partly because it fixed five findings itself.
  - Fix it yourself only when it's small (about 20 lines in one file), protected or security code, or a developer already failed that fix once.
  - Fix tickets get the usual checkpoint, not another review round.
- Read the tests as closely as the code: missing edge cases, and every existing test a developer changed (the session reports list them).
- Check the French in `coucou/locale/fr/` reads naturally and warmly.
- Take screenshots of new screens when you have a browser; the layout check covers the rest.
- A finding that recurs becomes a check where it can.
- Respect the stop rules and the per-trigger limits in `.softfield/project.toml`.
- **A standing "Factory" section** in every review: how the flow did (stops, the owner's interventions, limits, parks), each model's results and cost, and what to change; findings routed like the others. F1's is [`.softfield/reviews/factory-f1.md`](../../.softfield/reviews/factory-f1.md).
- Add the milestone's entry to [ADR 02](../../.softfield/adr/02-software-factory.md)'s learnings log, and update "Known range" above.

## Sign-off sheet
When the review loop stops, write this at the top of `.softfield/reviews/mN.md`, in plain language, without being asked, each item under its own heading, `### 1. What changed` (the runner stores the sheet from them, and the desk lists a milestone for sign-off only once it is stored):
1. **What changed:** what the owner and Mum will notice.
2. **How to test it yourself:** numbered steps on real devices.
3. **Left for later:** deferred items and the bug tickets set aside.
4. **Decisions waiting for you:** ADRs, with links.
5. **How the work went:** one line per session (date, tasks merged or escalated, lead vs local tokens), the 3–5 lessons that mattered and what changed because of them, links to `.softfield/sessions/`.
6. **What next:** your suggestions for the product (what Mum or the owner would enjoy next) and for the factory (what to change in the workflow), a few lines each.
7. **What clogged the factory line** (owner, 2026-10-02): where the hours went that weren't merging work: waits for limits, failed attempts, stops for the owner, tickets that waited on one another while agents sat idle. Hours from the metrics database (runs, jobs, `usage_events`), each with what would unclog it.

Then the rest of the report: what was built, findings, what was set aside, stop reason, workflow observations. The numbers (tickets, pass rate, attempts, escalations, findings, tokens, dollars, savings from delegating, trends) aren't yours to write: `softfield report <key>` writes them between the `<!-- runner report -->` markers from the metrics database ([ADR 14](../../.softfield/adr/14-developers-and-agents.md) item 16). Quote them, don't recount them. In the chat, keep it to a link and 2–3 lines.

## Reporting
- The numbers come from the metrics database: `softfield report <key>` for a milestone review, the same queries as the dashboard (`factory_dashboard/queries.py`). The database isn't in git, so the review keeps a frozen snapshot.
- The runner writes a session report to `.softfield/sessions/` after every run.
- After any session you lead, add a short narrative: what went well, what didn't, what it cost against the local model's share, and what to improve. After an interactive session that exercised the pipeline, summarise it briefly in the chat too.

## Developers' notes
The package's `runner/instructions/developer.md` holds what holds anywhere; a project's `.softfield/developer.md` its worked examples and its own notes. Each file has at most **15 one-line notes**, because developers drop instructions from long prompts. When one is full, replace a note or turn it into a check. Don't fix a developer's miss by adding rules to prompts: prefer a check or an example. Put the one instruction that matters last in a ticket.

A checkpoint writes a lesson in its own project's notes, always: a job in one project can't write to Softfield's repo. One that holds everywhere, the review suggests as a Softfield card in "What next" (ADR 41 item 7).

## ADRs
Draft them in `.softfield/adr/NN-<slug>.md` with status **Proposed**, with the evidence (cite milestone metrics for workflow changes). Mark each item that deviates from an earlier decision with ⚑.
