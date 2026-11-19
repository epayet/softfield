# Milestone F122: Start a new project from the Projects page

> **State:** ready · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

ADR 30 left this for later: start a project from the phone instead of a terminal.

On the Projects page: a big text box for the idea, a name, and a send. It's a request (the
dashboard never touches folders, ADR 18), shown at once as "New project on its way"; the runner,
which runs on this machine, carries out what `softfield init` does under `~/projects/<name>`
(runner/setup.py `init`), registers it paused ("setting up"), and the setup conversation that
the terminal Claude session does today (runner/instructions/bootstrap.md: the idea saved word for word in
seed.md, the stack, ADR 00 reviewed in the owner's format, the checks, the first card) happens
on that project's Planning desk instead. When `doctor` passes, the project goes to the runner.

Open questions: where the folder goes (a fixed root in the machine's factory.toml?), how Claude
gets trust for a new folder headless (`--add-dir`, `dontAsk`), and how ADR 00 is accepted from
the web (today a card's Accept needs a planner proposal).

## Plan (lead, 2026-11-13)
**Expected outcome.** From the Projects page, the owner writes an idea and a name and presses
Start. The plate shows at once; minutes to hours later the lead's setup waits on the project's
first card (M1) with ADR 00 to approve; approving it puts the project in the factory, and the
lead plans M1 on the same thread, mock-ups included. An app gets its Docker stack in the setup, so
Run works on its plate from day one.

**Done when.** At sign-off the owner starts a small app from their phone, approves its ADR 00 on
M1's thread, presses Run on its plate and sees its one page.

**What the seed got right, and what moved since 2026-10-14.** The request, the runner doing
`init`, the setup on the Planning desk: kept. Changed: F236 (`softfield create` adds a project,
only on the owner's yes) is the step ADR 00's approval now triggers; ADR 46 (Docker stacks) puts
the stack in the setup; the root is a setting, not `~/projects`; and the setup is one round, not a
chat, because a planner reply waits from minutes to hours (ADR 48's evidence). The three open
questions: the root is D1; trust is a non-issue (headless jobs run with `--permission-mode
dontAsk` and an allow-list in any folder, `runner/claude.py`, as they do in coaster-ranker); ADR
00 is accepted by the planning room's existing `adr` proposal Approve (`_accept_adr` in
`runner/requests.py`, which commits "ADR 0 accepted by the owner", what `doctor` looks for).

**Waits for** F236, softfield init adds the project only when its setup ends and doctor passes
(`softfield create`), which itself waits for F136, softfield init asks what to do with a
forgotten project of the same name. Joints in [ADR 48](../adr/48-start-a-project-from-the-projects-page.md)
(Proposed): nothing is queued before it is Accepted.

## Decisions
- **D1. The root.** `config.projects_root() -> Path`: `[projects] root` in the machine's file,
  `~` expanded; without it, the common parent folder of the live (not forgotten) projects' repos
  when they all share one, else `~/projects`. On this machine that is `~/projects/epayet`.
- **D2. The request.** Kind `new_project`, posted on Softfield's own project row (as
  `project_order` is), `value` JSON `{"name", "idea", "built_with", "app"}`. The runner's handler
  in `runner/requests.py`:
  - the folder name is `name` made a slug (lower case, `a-z0-9-`, at most 40), or the idea's first
    words when the name is empty; a folder that exists or a live project of that name takes `-2`
    (the first free), never a refusal. A forgotten project of that name: F136's "keep";
  - only an empty idea is refused, and the refusal shows where the request did;
  - `setup.init` in the new folder, then `.softfield/seed.md` (`# Seed`, the date, the idea word
    for word), `.softfield/cards/m1-first-version.md` (`# Milestone M1: First version of <name>`,
    state idea, priority 1, area product, the idea under `## Notes`, "built with" and "app" as a
    line under it), one commit; then `setup.register` (paused `setting up`), `publish_cards`,
    and a `setup` work item on the thread `m1`.
- **D3. The `setup` job** (ADR 48 item 4): work kind `setup`, subject the thread; brief
  `prompts.SETUP`, from `bootstrap.md` plus its new section "From the Projects page"; tools as
  ADR 48 item 4; cwd the project's folder on main. Its final message is the planner's JSON shape
  (points, proposals) and is stored as the lead's message on M1's thread, with ADR 00 as an `adr`
  proposal (`path` `.softfield/adr/00-initial.md`). A `plan_message` on a `setting up`
  project's thread queues `setup`, not `planner`.
- **D4. ADR 00's approval adds the project** (ADR 48 item 6): after `_accept_adr` on a `setting up`
  project, the runner runs F236's `create` checks; pass: unpaused, cards published, "Plan this
  card." queued on M1 even though its thread has begun (`plan_first_card` gets a way to say so);
  fail: a `setup` job with the failing findings as its message, at most two in a row, then an
  owner item "<name>'s setup stopped at: …".
- **D5. The stack** (ADR 48 item 7): with `app` true the setup follows `run-stack.md`. Both
  paths: `bootstrap.md`'s "Both" gets the step, for a project with pages.
- **D6. The page:** as in `.softfield/cards/f122-mockup/projects-new.html`. "Start a project" at
  the bottom of the Projects page; the plate drawn at once from the waiting request, dashed orange;
  a `setting up` plate shows its line of four stations (Asked, Set up by the lead, ADR 00 for you,
  In the factory) and "Answer on its first card" (`/planning/m1?project=<name>`).

## Tickets
| Ticket | Who | What | Waits for |
|---|---|---|---|
| f122-01-new-project-request | lead | D1, D2 | f236-02 |
| f122-02-the-setup-job | lead | D3, D5 | 01 |
| f122-03-adr-00-adds-the-project | lead | D4 | 02 |
| f122-04-replan | lead | ADR 16 item 7 | 03 |
| f122-05-start-a-project-on-the-page | developer | D6 | 04 |

## Replan
Checked by the lead on 2026-11-19 against what f122-01, f122-02 and f122-03 built (ADR 16 item 7),
for f122-05. What differs from the Decisions above, and what f122-05 relies on:
- **D2, the card has no priority.** `setup.start_project` writes M1 through `planner.seed_card`:
  state idea, area product, the idea and the "Built with: … · an app, opened in a browser" line
  under `## Notes`. ADR 45 retired the card's priority, so D2's "priority 1" is not built.
- **D2, the request's shape.** Kind `new_project` (`runner.requests.NEW_PROJECT`, already in
  `factory_dashboard/requests.py`'s `KINDS`), `value` JSON `{"name", "idea", "built_with", "app"}`.
  `app` counts as ticked for `true`, `"yes"`, `"on"`, `"true"` or `"1"`; an empty `name` or
  `built_with` is fine (the idea's first words; "what the lead recommends"); a value that isn't
  that JSON is taken as the idea itself. Only an empty idea is refused. The handler ignores the
  request's `project`, so the page posts it with the page's own `project` field, as the order
  form does, not a hard-coded Softfield.
- **D2, the thread.** M1's thread key is `m1` (`planner.thread_key(setup.FIRST_CARD)`); the page
  is `/planning/m1?project=<name>`, a route that exists. Nothing waits between the request and the
  plate: the handler registers the project, queues its `setup` job and marks the request done in
  one go, so a project's plate replaces its waiting request's with no gap.
- **D1, the root.** `config.projects_root(db=None)` in `runner/config.py` is as written; the
  page shows it plus the name as typed (the folder name itself is the runner's slug, `-2` if
  taken, so the page says "as typed").
- **D3/D6, what a setting-up plate reads.** `ProjectCard.paused == metrics.SETTING_UP` is already
  there. "Set up by the lead" is an open `work_queue` row of kind `dispatch.SETUP` on the project
  (`metrics.open_jobs`; a row stays open while its job waits or runs, and a later round on the
  thread is a new row, subject `m1#<request>` or `m1#m<message>`). "ADR 00 for you" is the
  card's `for_you` (`waiting_for_you(desk(...))`): after a setup reply the runner leaves a
  `planning` owner item on `m1` and the lead's ADR 00 `adr` proposal, which the desk groups as
  one item. A failed setup reply leaves that item too (without ADR 00), so the station reads
  "for you" there as well; the link to M1 is the answer in both cases.
- **D4, a stopped setup.** After ADR 00's approval fails its checks twice more, the runner leaves
  a `setup_stopped` owner item and no `setup` row: the plate then has no lit "Set up by the
  lead" station. f122-05 shows nothing special for it (it is on the desk and on M1's thread).
- Nothing else differs. D3 (`prompts.SETUP`, `loop.run_setup`, `SETUP_COMMANDS`) and D4
  (`_accept_adr` calling `_setup_checked`, `setup.join`) are built as written.

f122-05's Context is fixed to name these, and no code changed.

## Fix after the owner's try (2026-11-19)
- **The plate drawn twice.** After Start, the "Asked" line in `#start-sent` polls its request
  every 5 s; the poll's htmx events bubble to the start form's listeners, which add one more
  plate per poll until the runner takes the request (waifu-gallery's took about 2 hours). A
  reload draws from the database, so one plate. Only one request was written: the runner made one
  project. `f122-06-start-plate-once` (developer) guards both listeners as the order form's are.

## Later (not this card)
- The runner builds a new project's stack once when it joins, and says on the thread if it fails.
- Pick the stack from a list once F121, projects on any main branch in any language, lands.
- Start from an existing git repository (a URL to clone).
- Cancel a setup from its plate.

## Before and after
- `/projects`
