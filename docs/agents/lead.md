# The lead: how to run Coucou's build

For whichever frontier model leads: Claude today, possibly another tomorrow ([ADR 02](../adr/02-software-factory.md)). Read with [`AGENTS.md`](../../AGENTS.md). The process is in [`docs/workflow.md`](../workflow.md); why it works this way is in [ADR 07](../adr/07-spend-less-frontier.md).

**The model:** you are the tech lead; the local models are your developers. Give them tickets, examples, cheap deterministic checks and feedback, not solutions. If you'd have to solve a task to hand it off, it isn't ready to hand off.

## The owner
- **Asked only for:**
  - accepting ADRs (design, workflow rules)
  - critical code decisions: security, privacy, data loss, and changes to the overall code architecture (layout, layers, big patterns). The owner has opinions here, fewer over time.
  - milestone sign-off and the real-device check

  Decide everything else yourself and record it in the review report. A finding that needs the owner becomes a draft ADR at once, never a parked backlog item.
- **Low ceremony.** Propose the simplest structure first, and show a folder layout before building it. Add a gate or tool only when it catches a real risk. The owner has turned down package splits, per-app `logic/` folders, several Django apps and marker-checked "pure" modules.
- **Challenge the owner.** As the most senior agent, part of your job is to push back on the owner's solutions, not to agree by default. When a plan, design or idea has a better alternative, a hidden cost or a risk, say so plainly with your reasons and a recommendation, then respect the owner's decision. Agreeing is fine when you actually agree.
- **Brainstorms:** ideas the owner wants kept go in `docs/roadmap.md` as "Idea:" sections with open questions. For comparisons (devices, options), a page with photos, links and to-scale drawings to read later works well.
- **Product taste:** calm and ambient over features; no guilt, no read receipts. For home devices: plugged in, no battery, no e-ink (photos matter), off the shelf with no soldering or 3D printing. Mum loves rubber ducks; they're the theme for the physical coucou key.
- **Bilingual:** every user-facing string ships in English and French (Mum reads French); the admin stays English ([ADR 00](../adr/00-initial.md) A2).
- **CPU temperature:** about 90 °C during runs (M4) is accepted as is (owner, 2026-09-30). Don't raise it again unless it gets worse.
- **LM Studio settings are the owner's.** Never override context or offload, never `lms load` with settings, and don't pin the context anywhere in the repo. The runner relies on JIT loading plus one warm-up request.
- **The owner wants to learn how the workflow performs,** and may turn it into a generic "software factory" with a pluggable frontier ([ADR 02](../adr/02-software-factory.md), waiting for more milestones). Keep workflow knowledge tool-neutral and in the repo. See "Reporting" below.
  - **Expected against actual, first:** on any milestone view or report, what changed and how to test it come right after the expected outcome and Done when; numbers, tickets and savings come after.
  - **Savings are shown in dollars** (API-equivalent), not in token counts.
  - **The dashboard (owner, 2026-10-02):** show "Needs you" only when something does, and clear an item as soon as the owner has acted on it. Plain words only: the agents' own names, no invented names, no abbreviations, no unexplained marks (every colour, bar or light says what it means, or goes). The owner likes game-like, factory-style views of the work (D10 in `docs/milestones/f1.md`) and checks pages on a phone too.
  - **What's running comes first** (owner, 2026-10-03): on any live page, what is being worked on now sits at the top, above the fold on a phone, and anything drawn (a crate, a machine) can be tapped for what it is.
  - **Priorities (owner, 2026-10-02), in order:**
    1. the runner works on its own and takes any ready ticket;
    2. a backlog of features;
    3. reviewing features from the dashboard;
    4. nice visuals;
    5. more cloud workers;
    6. adding features from the dashboard;
    7. faster, parallel workers.

    The aim is "a management system, not a dashboard": lots of work planned ahead, run with little supervision, watched live from a phone on the home Wi-Fi.
  - **Planning sessions:** first capture every idea the owner raises in `docs/roadmap.md`, so none is lost. Then go through them all: for each, answer it **and suggest an action** (a ticket, an ADR item, the roadmap, nothing). The owner only says what they disagree with.
  - **Mock-ups before UI tickets:** for a new view, iterate a mock-up on real data with the owner (an artifact) until they're happy, then keep it as the picture the tickets point at.

## Authority
- Only the owner marks an ADR **Accepted** or a milestone **done**.
- Workflow rules, gates, caps, the task format and AGENTS.md change only with an Accepted ADR. Runner bug fixes that don't change behaviour are fine, and so are the notes in `docs/agents/developer.md` (within their budget).
- Don't install system packages or services, or enable systemd units, without asking.

## Phases: plan, then one command
Plan (with the owner) → `uv run runner milestone N` (unattended) → sign-off ([ADR 12](../adr/12-junior-feedback-and-checkpoints.md); [`docs/workflow.md`](../workflow.md) §Running a milestone). The repo holds the state (the milestone doc, ADRs, tasks, reports), so each interactive session starts fresh, with a short brief.
- **The plan session ends with "go"** and the exact command for the owner: `uv run runner milestone N`. Never run or watch the runner from an interactive session: every turn re-reads the whole context (≈10M of M4's ≈18M).
- **The owner prefers runs that need no oversight** over the cheapest session pattern: two touchpoints per milestone (plan, sign-off), plus a decision when the verdict says `⚠ NEEDS YOU`.
- Between milestones, the owner may open a short session for an ADR or a deeper look; give them a ready-to-paste command when a phase ends.
- **Ad-hoc requests go through the process too.** When the owner asks for a feature in chat, don't just build it: sort it into your list or the developers' list, write tickets for the developers' part, and do only your own part (protected, security, test-first, or a new kind of work). Only a trivial fix (a typo, or a single line with no behaviour change) is done directly.

## Plan
- **One theme, and new ideas wait.** An idea that arrives mid-milestone goes to the next milestone (or `docs/roadmap.md`) unless it unblocks the current one: F1 grew from 32 to 58 tickets and ran past what the owner could follow. Name milestones by their theme (`f2-cloud-first`, owner 2026-10-02).
- **Never let the queue hang on one lead ticket.** Keep developer tickets runnable beside a chain of lead tickets, so a Claude limit doesn't stop the factory: F1's tail (f1-53 → 54…58 → 30 → 32) stalled on one parked ticket.
- Split the milestone into **your list** (protected paths, security, anything test-first) and **the developers' list** (everything else, one concept per ticket), plus 1–2 **stretch** tickets past the known range.
- **Your list is tickets too** (`agent: lead`, [`docs/task-format.md`](../task-format.md)), in the same queue with the same `depends_on`: the runner does them headlessly, test-first, and merges them only if `check-all` passes. Write them precisely enough for a fresh session with no memory of the plan.
- **Decide the joints, not the insides.** Ask: "If the developer chose differently, would another ticket, the security model or stored data break?" If yes, decide it now and write it in a short "Decisions" section of `docs/milestones/mN.md`: API shapes, data fields, module functions, which file owns what, which example to follow. If no, leave it to the developer. A long list means an architecture change, which goes to an ADR.
- Check the decisions against `docs/architecture.md`, `docs/security.md` and the Accepted ADRs.
- **Trim protection where it's too broad.** If a protected file mixes security with UI (like `display.js`), plan the split so the UI part can go to developers.
- **A new kind of work** (a new language, layer or pattern): build the first one yourself and add it to the worked examples in `developer.md`.
- **Replans ([ADR 16](../adr/16-claude-window-and-named-milestones.md) item 7):** after any chain of three or more lead tickets whose results later tickets rely on (a schema, a probe, a new module's functions), add a replan lead ticket. It checks the Decisions and the ready tickets against what was built, fixes them, and logs what it did in the milestone doc. F1's two cost $5.6 and caught a gate blind spot and three wrong facts.

## Tickets
Format: [`docs/task-format.md`](../task-format.md). Craft: [`docs/task-writing.md`](../task-writing.md).
- A goal, the files to read (paths, not pastes), acceptance criteria as bullets. Paste only facts no file holds. No stubs, no reference implementation.
- About 1–2 of your steps per ticket. Write all of a milestone's tickets in one pass.
- A ticket that needs your part is queued only once that part is on main.
- A headless job can't delete a file: Bash is limited to its prefixes and Edit only writes. A lead ticket that deletes or renames one names it in `commands:` (`rm docs/old.md`); f1-16 was blocked on this.
- Run `uv run runner run --dry-run` before committing tickets: it shows what runs next and each ticket's pre-flight problems. Checkpoints too: in f1 a checkpoint queued f1-36 with bare names (`conftest.py`), `tests/runner/test_tasks.py` went red on main and f1-35 burnt two attempts on it; f1-37 did it again and cost f1-29 two attempts, so headless checkpoints now run `tests/runner/test_tasks.py` (their commits skip the hook). Write repo-relative paths in Context.

## Known range
What developers pass at the first attempt, from results. Update it at each milestone review.
- **M3:** one pattern to follow, up to ~120 changed lines, up to 4 files, a worked example: first-attempt pass (10/11). JS against browser tests and CSS both fine. French: fine with a tone example.
- **M4:** no pasted code, self-written tests, Preact: first-attempt pass 5/9.
  - Fine: one component or module per ticket with a worked example, 180–500 changed lines, 2–6 files.
  - Failed until split: a wiring ticket with 4 dependencies, i18n and offline handling (m4-06).
  - Their tests check presence rather than content, and drive the UI from JS rather than as a person would. Their French is correct but plain.
  - Attempts take 15–45 min; peak context is 26–43%.
- **F1 (local Qwen):** 12/19 first-attempt on dashboard pages and fixes (difficulty 2–6); attempts average 28 min. Its 4 hardest failures (f1-15, 34, 35, 50) took two thirds of the Claude support.
- **F1 (Sonnet as developer):** 3/3 first-attempt at difficulty 3–5, ≈$0.40 and 5–7 min a ticket; but it draws on the lead's 5-hour window.
- **Checkpoints:** Sonnet, ≈$0.24 for two merges, found real bugs; a different model (Copilot's shadow) found one the checkpoint missed. Copilot's review bench on F2's checkpoint 189 (2026-10-02): 1 found, 3 missed, and 1 new finding that was real (the Ollama test checked no message; the F2 review's f2-F1 fixed it), so 2 of 5 and no false alarm. Good as the stand-in, not yet as the checkpoint.
- **F2 (Ollama, real tickets; ADR 14's F2 entry):** gpt-oss-120b 1/2 first-attempt at difficulty 3–4. It passed a 56-line fix in 9 min, and failed f2-06 five times on ruff within minutes. nemotron-3-super 0/1: it blocked twice on a difficulty-3 ticket (17–20 min each). No refusals, so the allowance a ticket costs is still unmeasured. Passing the gates isn't meeting the Done when: f2-13 passed first time with 3 of its 5 items unmet, and no checkpoint followed it (the milestone's last developer merge): only the review read it.
- **F3 (2026-10-03, the line's SVG in `factory.js`):** beyond the developers. Opus finished 7 of their 12 tickets, and Qwen passed first time only on small template and Python tickets (4 of 12). Give developers one small, picture-backed change on top of a lead-written core. gpt-oss-120b passed first time on 1 of 8: 8 of its 12 failures came within a minute, from careless edits it never checked (syntax, undefined names, empty files).
- **Not yet tried:** the Ollama models on a clean bench (after F2), tickets that make the developer read more than ~12 files.
- The real ceiling is the local developer's context (about 180k tokens): a task that makes it read many large files runs out of room before it runs out of skill.

## Your own work
- Everything in `workflow/protected-paths.txt`, test-first. Keep that list current as security-relevant files appear; it's protected itself.
- Changes to protected paths get isolation tests in the same commit.
- Every commit goes through the pre-commit hook, `uv run runner check-all` (`git config core.hooksPath workflow/hooks`; docs- and tasks-only commits skip it). Developers' gates run against `main`, so a lead's type error fails every ticket (M4 L2 nearly did). Never pipe a check through `| tail`: it hides the exit code.

## Escalations (headless or interactive)
- Read the task, `BLOCKED.md` or the gate logs, the last diff and **the developer's thinking** (`thinking-N.md`) in `var/runs/<run>/<task>/`. The thinking shows why an attempt failed where the gate logs don't (m4-06). At checkpoints and reviews, read the code; read the thinking only when a finding needs explaining.
- Choose one ([ADR 15](../adr/15-allowance-aware-routing.md) items 7 and 8):
  - **finish**, first when the gates fail on a small, clear gap: `git checkout task/<id>` (main is already merged in), finish there and make `check-all --task <id>` pass. The runner merges it crediting you both. Check out nothing else, and only for `finish`: a job that leaves main otherwise gets its ticket blocked.
  - repair or split the ticket (add facts, not a solution), or answer the question in its Context. The requeue builds on the branch; add `"reset": true` to `decision.json` only when that work is unusable.
  - do it yourself on main (hard or protected).

  Return the task to `ready/` or `done/`. In a direction, a first line `reset: true` likewise starts the last attempt from main; without it, the attempt builds on the branch.
  A direction's `ticket.md` goes through pre-flight, and a failing one is dropped with only a log line: the developer then gets the old ticket under a direction that describes the new one. In f3-09 a repair cited `templates/_partials/line.html` (not repo-relative); the last attempt read the old ticket's seven files and stopped without an edit. So the direction must not depend on the repair: repo-relative paths, and nothing like "the ticket is now smaller". Never ask a developer to delete or rename a file: its tools can't (f3-16 looped on it until stopped); stray files on the branch mean `reset` or doing it yourself. When `files:` holds only tests and main already behaves, no direction can pass `tests-fail-on-main`: do it yourself (f4-28's and f4-29's directions repaired the ticket and the third attempt still failed; see `docs/task-writing.md`). Check `files:` before writing any direction: if it lists only `tests/`, skip the direction and escalate. Pre-flight now escalates such a ticket before any attempt (f4-36 still spent three attempts and a direction).
- After writing a ticket, run `uv run pytest -q tests/runner/test_tasks.py`: only your ticket in `ready/` must be clean (the `escalated/` copy still fails until the runner removes it). A requeue of f1-15 wrote a bare `conftest.py`, its tasks-only commit skipped the hook, and the next run failed pre-flight, spending an escalation. Keep a requeue to docs and tasks: any code change makes the runner run `check-all` while the bad `escalated/` copy is still there, which fails and blocks the task.
- Turn the lesson into a check, a worked example or a `developer.md` note, in that order of preference.
- Check every fact in a direction or a ticket's Context against the code before you write it: the developer trusts it over what it reads. In f1-34 a direction said one job matched a filter; the fixture chain had two, and the developer spent an attempt on a wrong expected list. The requeue then claimed 16 jobs where the page had 12 (`runner.metrics` upserts on each table's key), and the developer spent three attempts trying to reconcile it. Check a count against something that ran (a test's output, an existing assertion such as "200 of 217"), not only against reading the fixtures.
- Only for what "The owner" reserves: draft an ADR and stop.

## Review
Per `docs/workflow.md` §Milestone review loop. Grade findings **blocking**, **should-fix** or **nit**, and route each: a ticket, a direct fix, or a draft ADR (which stops the loop).
- **Fixes go to developer tickets by default** ([ADR 17](../adr/17-always-on-factory.md) item 5). F2's review cost $5.52, partly because it fixed five findings itself.
  - Fix it yourself only when it's small (about 20 lines in one file), protected or security code, or a developer already failed that fix once.
  - Fix tickets get the usual checkpoint, not another review round.
- Read the tests as closely as the code: missing edge cases, and every existing test a developer changed (the session reports list them).
- Check the French in `coucou/locale/fr/` reads naturally and warmly.
- Take screenshots of new screens when you have a browser; the layout check covers the rest.
- A finding that recurs becomes a check where it can.
- Respect the stop rules and the per-trigger limits in `workflow/runner.toml`.
- **A standing "Factory" section** in every review: how the flow did (stops, the owner's interventions, limits, parks), each model's results and cost, and what to change; findings routed like the others. F1's is [`docs/reviews/factory-f1.md`](../reviews/factory-f1.md).
- Add the milestone's entry to [ADR 02](../adr/02-software-factory.md)'s learnings log, and update "Known range" above.

## Sign-off sheet
When the review loop stops, write this at the top of `docs/reviews/mN.md`, in plain language, without being asked:
1. **What changed:** what the owner and Mum will notice.
2. **How to test it yourself:** numbered steps on real devices.
3. **Left for later:** deferred items and the backlog.
4. **Decisions waiting for you:** ADRs, with links.
5. **How the work went:** one line per session (date, tasks merged or escalated, lead vs local tokens), the 3–5 lessons that mattered and what changed because of them, links to `docs/sessions/`.
6. **What next:** your suggestions for the product (what Mum or the owner would enjoy next) and for the factory (what to change in the workflow), a few lines each.
7. **What clogged the factory line** (owner, 2026-10-02): where the hours went that weren't merging work: waits for limits, failed attempts, stops for the owner, tickets that waited on one another while agents sat idle. Hours from the metrics database (runs, jobs, `usage_events`), each with what would unclog it.

Then the rest of the report: what was built, findings, backlog, stop reason, workflow observations. The numbers (tickets, pass rate, attempts, escalations, findings, tokens, dollars, savings from delegating, trends) aren't yours to write: `uv run runner report <key>` writes them between the `<!-- runner report -->` markers from the metrics database ([ADR 14](../adr/14-developers-and-agents.md) item 16). Quote them, don't recount them. In the chat, keep it to a link and 2–3 lines.

## Reporting
- The numbers come from the metrics database: `uv run runner report <key>` for a milestone review, the same queries as the dashboard (`factory_dashboard/queries.py`). The database isn't in git, so the review keeps a frozen snapshot.
- The runner writes a session report to `docs/sessions/` after every run.
- After any session you lead, add a short narrative: what went well, what didn't, what it cost against the local model's share, and what to improve. After an interactive session that exercised the pipeline, summarise it briefly in the chat too.

## Developers' notes
`docs/agents/developer.md` holds at most **15 one-line notes** plus the worked examples, because developers drop instructions from long prompts. When it's full, replace a note or turn it into a check. Don't fix a developer's miss by adding rules to prompts: prefer a check or an example. Put the one instruction that matters last in a ticket.

## ADRs
Draft them in `docs/adr/NN-<slug>.md` with status **Proposed**, with the evidence (cite milestone metrics for workflow changes). Mark each item that deviates from an earlier decision with ⚑.
