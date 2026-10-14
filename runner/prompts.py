"""Prompts for the local model and headless Claude. Kept in one place so they're reviewable."""

from pathlib import Path

from runner.tasks import Task

# f21 D2: every lead job's prompt starts with the owner's preferences and the lead.md sections
# its role needs, pasted in: a pointer was skipped (neither planner job of 2026-10-07 opened
# lead.md). Sections are named by their `## ` heading; tests/runner/test_prompts.py reads the
# real lead.md, so a renamed heading fails at commit.
OWNER_DOC = "docs/agents/owner.md"
LEAD_DOC = "docs/agents/lead.md"
_PLANS = ("Authority", "Plan", "Planning room", "Tickets")
_SUPPORTS = ("Known range", "Escalations (headless or interactive)", "Your own work")
_REVIEWS = ("Review", "Sign-off sheet", "Reporting")
SECTIONS: dict[str, tuple[str, ...]] = {
    "planner": _PLANS,
    "lead-ticket": ("Your own work", "Tickets"),
    "escalation": _SUPPORTS,
    "direction": _SUPPORTS,
    "checkpoint": _REVIEWS,
    "review": _REVIEWS,
}
_BRIEF_SECTIONS = "From docs/agents/lead.md, the sections this job needs:\n\n"
_BRIEF_END = "---\n\n"


def sections(text: str) -> dict[str, str]:
    """A document's `## ` sections by heading, each from its heading to the next one."""
    found: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = found.setdefault(line[3:].strip(), [])
        if current is not None:
            current.append(line)
    return {heading: "\n".join(lines).strip() for heading, lines in found.items()}


def brief(repo: Path, role: str) -> tuple[str, list[str]]:
    """What goes first in a lead job's prompt (f21 D2): owner.md, then the lead.md sections
    ``role`` needs, the same text for every job of the role, so jobs close together share
    Claude's prompt cache. Also what the map names and wasn't found: the job goes with the
    rest. Empty for a role with no sections, and in a repo without a lead.md."""
    lead = repo / LEAD_DOC
    if role not in SECTIONS or not lead.is_file():
        return "", []
    missing: list[str] = []
    parts: list[str] = []
    owner = repo / OWNER_DOC
    if owner.is_file():
        parts.append(owner.read_text(encoding="utf-8").strip() + "\n\n")
    else:
        missing.append(OWNER_DOC)
    found = sections(lead.read_text(encoding="utf-8"))
    missing += [name for name in SECTIONS[role] if name not in found]
    wanted = [found[name] + "\n\n" for name in SECTIONS[role] if name in found]
    if wanted:
        parts += [_BRIEF_SECTIONS, *wanted]
    return "".join(parts) + _BRIEF_END if parts else "", missing


# The developer's prompt stays short: it drops instructions from long prompts (ADR 01).
LOCAL = """\
Implement the task below in the Coucou repository. Start from the files under `files:`;
change other files only if the goal needs it. Write or update tests for what "Done when"
asks, in the test files under `tests:`. Never edit protected paths
(.factory/protected-paths.txt) and never run git. If you're stuck, write BLOCKED.md as
AGENTS.md describes, then stop. Run commands exactly as written: pipes (`|`), redirections
and unknown flags are refused, and a refused command returns nothing.

{task}

Finish by running `uv run runner check-all --fix --task {id}` and fixing what it reports.
{extra}"""

# On a retry the gate output goes last: the local model follows the end of a long prompt best
# (ADR 01, item 3). The hint says what to do about it (ADR 07 item 6).
_NOT_YOURS = (
    "If the failure is in a protected file, you can't fix it: write BLOCKED.md with\n"
    "`CATEGORY: needs-file` naming that file, and stop."
)

RETRY = (
    """
IMPORTANT: your previous attempt failed the `{gate}` gate. {hint}
"""
    + _NOT_YOURS
    + """
Gate output:
```
{output}
```
"""
)

FRESH = (
    """
WARNING: a previous attempt failed the `{gate}` gate. {branch}
Don't repeat it. {hint}
"""
    + _NOT_YOURS
    + """
What went wrong last time:
```
{output}
```
"""
)

# ADR 15 item 7: the next attempt builds on the branch; it starts from main only when the work
# is judged unusable, and the prompt says which happened.
KEPT = "Your work so far is still on this branch: build on it."
RESET = {
    "direction": "The lead judged the work unusable, so the branch has been reset to main.",
    "timeout": "It ran out of time before its first edit, so the branch has been reset to main.",
    "conflict": "Its work clashed with newer changes on main, so the branch has been reset to"
    " main.",
}
# A requeued ticket's first attempt, on the branch its earlier run left.
EARLIER = """
NOTE: this branch already holds an earlier run's work on this task, which the lead sent back
with the ticket above. Check it and build on it. Files it changed: {files}
"""

# ADR 12 item 5: a retry after a timeout says so, before the gate output.
TIMED_OUT = """
Your previous attempt ran out of time. Keep what works and finish the smallest remaining piece
first.
"""
# f79-01: what the branch holds against main (every attempt's files, deleted ones too), for a
# developer that never runs `git diff`.
TIMED_OUT_FILES = "Files changed on this branch so far: {files}\n"

# ADR 12 item 4: an attempt that changed nothing, by cause.
EMPTY = {
    "timeout": "It ran out of time before its first edit: start editing sooner, one small change"
    " at a time.",
    "refused": "Its commands were refused. Run commands exactly as the task writes them: no"
    " pipes, redirections or extra flags.",
    "stopped": "It stopped before editing anything. The task isn't done yet: make the changes"
    " it asks for, starting with the smallest.",
}

# ADR 12 item 6: the lead's direction replaces the canned hint on the last attempt, and goes
# last, where the local model follows best.
DIRECTED = (
    """
WARNING: your previous attempts failed (last: the `{gate}` gate). {branch}
"""
    + _NOT_YOURS
    + """
What went wrong last time:
```
{output}
```

The lead read your work and your thinking, and says:
{direction}
"""
)

# ADR 14 item 13: directions and escalations already read the developer's thinking.
PROCESS_NOTE = """\
Also write {logs}/note.md, for the record, not the developer: 2-4 lines on how it worked. Did
it follow the ticket, run its checks, go round in circles? Describe; don't score.
"""

DIRECTION = (
    """\
You are the lead. A developer (a local model) has failed task {id} twice; it gets one last
attempt, which builds on its work on the branch. Give it direction (ADR 12 item 6; ADR 15
item 7), as "Escalations" above says.

- Task: {task}
- Its work: branch task/{id} (`git diff main...task/{id}`) and {logs}/last.diff
- Gate output per attempt: {logs}/gates-*.txt
- Its thinking per attempt: {thinking}
- Longest run of edits without running a command: {streak}; attempts that timed out: {timeouts}

Write {logs}/direction.md: 3-8 lines addressed to the developer, saying what went wrong and the
facts it is missing. No code: no snippets, no diffs, no reference implementation (ADR 07).
If its work is unusable and the last attempt should start again from main, make the first line
`reset: true` (the developer doesn't see that line).
If the ticket itself is wrong (a missing or false fact, a protected file, something its tools
can't do), also write {logs}/ticket.md: the whole corrected ticket, frontmatter included.
"""
    + PROCESS_NOTE
    + """Write nothing else. Read-only git (diff, log, show) is fine.
"""
)

ESCALATION = (
    """\
You are the lead, handling an escalated task in the Coucou repo. Follow
"Escalations" above.

- Task: .factory/tasks/escalated/{id}.md
- Why it was escalated: {reason}
- Run logs: {logs}/ (OpenCode output, gate output, last.diff). The local model's work is on
  branch task/{id}, with main merged in; you are on main.
- The local model's thinking: {thinking}. Read it: it shows why, where the gate logs don't.

Do exactly one of:
1. finish: when its gates fail on a small, clear gap, run `git checkout task/{id}`, finish the
   work there and make `uv run runner check-all --task {id}` pass. The runner merges the
   branch, crediting you both. Check out nothing else, and only for this outcome.
2. requeue: repair or split the ticket and write the task file(s) to .factory/tasks/ready/
   (docs/task-format.md). Add facts, not a solution. Its next run builds on the branch; if
   the work there is unusable, add "reset": true to decision.json and it starts from main.
3. requeue: answer the model's question by adding the facts to the task's Context, and write
   the task to .factory/tasks/ready/{id}.md (as in 2, about the branch).
4. implemented: if the task is hard or protected, implement it yourself on main and make
   `uv run pytest -q tests/unit tests/integration tests/runner` pass.
5. owner: only for what the owner is asked for (their preferences, above): draft an ADR in
   .factory/adr/ (status Proposed). The task and its dependants wait for the owner's decision.

Code you change must pass `uv run runner check-all`; if it doesn't, none of it reaches main.
Then write {logs}/decision.json as
{{"outcome": "finish" | "requeue" | "implemented" | "owner"}}, for a requeue maybe with
"reset": true, and for "owner" also {{"adr": ".factory/adr/NN-slug.md", "question": "<one line
for the owner>"}}, and {logs}/escalation.md: 3-6 lines on what happened, what the local
model got wrong, and the lesson. Turn the lesson into a check, an example or a line in
docs/agents/developer.md (its budget is in docs/agents/lead.md ("Developers' notes")), and
say which. """
    + PROCESS_NOTE
    + """\
Read-only git (diff, log, show) is fine; don't commit and don't edit .factory/tasks/escalated/: the
runner commits and moves files.
"""
)

LEAD_TICKET = """\
You are the lead, doing your own ticket in the Coucou repo: {task}. Follow
"Your own work" above: test-first, isolation tests for protected paths, and
docs/security.md for anything security-related. You are on branch task/{id}.

When it's done, `uv run runner check-all --fix --task {id}` must pass. Don't commit: the runner
checks and merges your work. Read-only git (diff, log, show) is fine. If the ticket can't be
done as written, change nothing and say why in your final message.
"""

CHECKPOINT = """\
You are the lead, doing a checkpoint in the middle of a milestone (ADR 12 item 8).
Developers (a local model) just merged these tickets:
{merges}

Read those diffs, code and tests, as "Review" above says: does the screen show
what the ticket asks, do the tests act as a person would and check content, not presence,
is anything masked instead of fixed? Don't read the developer's thinking unless a finding needs
explaining. Then do what helps the next tickets most, any of:
- nothing, if it's sound
- a fix ticket in .factory/tasks/ready/ (docs/task-format.md, `finding:` in the frontmatter), and
  add its id to `depends_on` of the ready tickets that build on the problem
- tighten upcoming tickets in .factory/tasks/ready/ with what you saw (facts, not solutions)
- one line in docs/agents/developer.md (its budget is in docs/agents/lead.md ("Developers' notes"))

If you wrote or changed a ticket, run `uv run pytest -q tests/runner/test_tasks.py` and fix
what it reports: it checks the tickets' format and that every path they name exists
(repo-relative, e.g. `tests/factory_dashboard/conftest.py`, not `conftest.py`).

Write {out}: 2-5 lines on what you found and did. Also write {findings}, one entry per
problem you found (an empty list if none; the final review judges them):
{{"findings": [{{"severity": "blocking" | "should-fix" | "nit", "file": "coucou/x.py",
  "line": 12 | null, "summary": "one line", "detail": "what is wrong and why",
  "route": "local" | "backlog", "ticket": "<the merged ticket at fault>"}}]}}
route: "local" if you wrote a fix ticket for it, "backlog" otherwise.
Change nothing else; don't run git beyond diff, log and show.
"""

# ADR 14 item 12: beside the checkpoint, read-only; what it finds is recorded, never acted on.
CHECKPOINT_SHADOW = """\
Review these just-merged tickets of this repo, read-only: each ticket's file, then the files
it changed and their tests.
{merges}

Look for bugs, tests that check presence instead of content, and anything masked instead of
fixed. Change nothing. Answer with only this JSON, one entry per problem (an empty list if
none):
{{"findings": [{{"severity": "blocking" | "should-fix" | "nit", "file": "coucou/x.py",
  "line": 12 | null, "summary": "one line", "detail": "what is wrong and why",
  "route": "backlog", "ticket": "<the merged ticket at fault>"}}]}}
"""

# ADR 16 item 9: when Claude can't, a read-only agent does the checkpoint; the runner turns
# each finding that isn't a nit into a fix ticket for a developer.
CHECKPOINT_STAND_IN = """\
You are doing a checkpoint for this repo's lead, read-only: developers just merged these
tickets. Read each ticket's file, then the files it changed and their tests.
{merges}

Look for bugs, tests that check presence instead of content, and anything masked instead of
fixed. Change nothing. Skip nits: a local developer fixes each finding, from what you write.
Give each its kind of fix:
- "code": the code is wrong. Name the code file at fault, and quote in "detail" the line
  of the merged ticket (its Goal or Done when) that the code breaks.
- "test": the code is right, but a test is weak. Name the test file, and say what the test
  must check that it doesn't.
Write one entry per merged ticket and kind, every problem of that kind in its "detail".
"file" is a path from the repo's root, as in this example. Answer with only this JSON (an
empty list if none):
{{"findings": [{{"severity": "blocking" | "should-fix", "kind": "code" | "test",
  "file": "factory_dashboard/queries.py", "line": 12 | null, "summary": "one line",
  "detail": "what is wrong and why", "route": "backlog",
  "ticket": "<the merged ticket at fault>"}}]}}
"""

REVIEW = """\
You are the lead, reviewing milestone {milestone} of Coucou. Follow "Review" above and
docs/workflow.md (Milestone review loop).

Round {round} of at most {max_rounds}. {scope}

Read the tests as closely as the code: missing edge cases, and every existing test a
developer edited (the session reports in .factory/sessions/ list them). Check the French.

Grade each finding blocking / should-fix / nit and route it:
- local: write a ticket in .factory/tasks/ready/ (docs/task-format.md), `finding: <id>` in the
  frontmatter. Findings listed as recurring must NOT go to the local model.
- claude: fix it yourself now, keeping `uv run pytest -q tests/unit tests/integration
  tests/runner` green.
- adr: only for what the owner is asked for (their preferences, above). Draft an ADR (status
  Proposed) and set "stop": "adr-needed". Decide everything else yourself; never park a
  finding for the owner.
- backlog: nits and should-fix points about untouched code go to docs/backlog.md.
Recurring findings (fix these yourself): {recurring}

The checkpoints' findings so far, by key (ADR 14 item 13):
{checkpoints}
Judge each: "confirmed" (a real problem) or "rejected" (not one). Also mark "missed" each of
your own findings a checkpoint should have caught: in work merged before it ran, and visible
in the diffs it read. Score the milestone from 1 to 10.

Write {out} as:
{{"findings": [{{"id": "{milestone}-F1", "severity": "...", "route": "...",
  "summary": "one line", "file": "coucou/x.py", "line": 12 | null,
  "detail": "what is wrong and why", "ticket": "<the ticket at fault>" | null,
  "resolved": false, "security": false}}],
  "checkpoint_verdicts": {{"<checkpoint finding key or your finding id>": "confirmed" |
  "rejected" | "missed"}},
  "score": 1-10,
  "stop": null | "adr-needed" | "security-unresolved" | "unforeseen-cross-milestone"}}
Keep ids stable across rounds; mark findings fixed since the last round "resolved": true.
Give checkpoint_verdicts and score every round, as they stand: the last round's are kept.
Also create or update .factory/reviews/{milestone}.md. It starts with the owner's sign-off
sheet ("Sign-off sheet" above), ending with "6. What next": your product and factory
suggestions. Then what was built, findings and resolutions, backlog and workflow
observations. The numbers come from `uv run runner report {milestone}`, between the
`<!-- runner report -->` markers: leave that block as it is and don't recount them.
Read-only git (diff, log, show) is fine; don't commit: the runner does.
"""

# ADR 20 items 3–7, f6 D2 and D4: the planner plans as the lead did with the owner on
# 2026-10-02/03. A card's thread drafts on its plan branch; the general thread only talks.
_PLANNER_HEAD = """\
You are the lead, planning with the owner in the planning room \
(.factory/adr/20-planning-room.md). Plan as the owner's preferences and the lead's "Plan" and \
"Tickets" sections say: both were pasted at the start of this session. \
This is their message on {thread}.
{comments}
The owner's message:

{text}

On a card's thread, read its doc in .factory/cards/ first: the owner's notes are there, \
and their message may only point at them. \
Before answering, look for a repeat (f6-12): read the cards in .factory/cards/ whose state \
is idea, planning or ready, and think of the other threads. Other threads: {threads}. When \
this idea or message repeats another card or thread, even in other words, say so as a point \
and propose a `merge`: `path` the duplicate card's doc, `into` the short key of the card it \
joins (`f10`), key points saying what moves where. Keep the more advanced card (ready over \
planning over idea), else the older one. Don't edit or remove either card yourself: right \
after your reply the runner applies the merge on its own: it moves the duplicate's notes into \
the kept card, removes the duplicate and points its thread to the kept one, where the \
conversation goes on. It can't when the duplicate has tickets or drafts on its plan branch: \
then the merge waits for the owner. On a duplicate, say only which card it repeats and why \
that one is kept, in one or two points, and draft nothing: the runner brings their note to \
the kept card's thread and queues you there, and your full answer and the plan come on that \
thread (a card merged away can hold no plan). Never ask the owner to write "go", or anything \
else, on another page: what you need from them, ask here.

How to answer:
- Answer their questions and comments first, then revise what they asked you to change.
- The points in the `json` block carry everything (F41): every answer, risk, question and \
ask (a pause, a choice) is a point, in plain words, each with a title, an answer and a \
suggested action (a ticket, an ADR item, the roadmap, nothing). Don't write them out in the \
text too: before the block, at most two short lines on what this reply does, or nothing. \
Every point of yours they didn't comment on counts as agreed.
- Name a card with its title, every time ("F22, Archive at the bottom"), never a bare number.
- When their message is a bare "agreed" or "go" with nothing new, don't answer it point by \
point again: one point, saying the plan waits for their Approve, and nothing else.
- No point reports that a check found nothing (no repeat, no conflict): they have nothing \
to do with it. A repeat you do find is still a point and a `merge`.
- Challenge them: where their idea has a better option, a hidden cost or a risk, say so \
with your reasons and a recommendation. Agree only when you do.
"""

_PLANNER_TAIL = """\
- Nothing is queued without their approval. Never touch main: the owner approves a \
proposal from the dashboard, and only then does the runner merge the drafts and queue the \
tickets.

End your reply with one fenced `json` block, nothing after it. List every proposal you \
drafted or changed this turn with its key points, numbered, for the owner to review point \
by point (flag: true where a point deviates from an earlier decision). A new list replaces \
your last one (F31 D3): only its proposals keep their buttons, and the thread closes once \
they are settled. So also list, as it was, each earlier proposal that still waits for them \
unchanged; and when they sent one back and you keep it as it is, list it again, or they \
can't approve it. With nothing drafted or changed and nothing sent back, list none: the \
last list stands. Give each point its \
`outcome`, what it leads to: `info` (nothing for them to do), `ticket`, `adr`, `mockup`, \
`roadmap`, `merge` or `question` (you need their answer); and, when it leads to a proposal \
in this block, that proposal's id as `proposal`:

```json
{{"points": [{{"n": 1, "title": "…", "answer": "…", "action": "…",
    "outcome": "info" | "ticket" | "adr" | "mockup" | "roadmap" | "merge" | "question",
    "proposal": "…" (an id below, when it leads to one)}}],
  "proposals": [{{"id": "…", "kind": "adr" | "mockup" | "plan" | "seed" | "replan" | "merge",
    "title": "…", "path": "docs/…" | null, "into": "f10" (a merge only),
    "key_points": [{{"n": 1, "title": "…", "text": "…", "flag": false}}]}}]}}
```"""

PLANNER = (
    _PLANNER_HEAD
    + """\
- Proposals are drafts on the branch plan/{card} only, never main: you are on it (if not, \
run `git checkout plan/{card}`). ADRs in .factory/adr/ (status Proposed); mock-ups as \
self-contained HTML in .factory/cards/{card}-mockup/ (one file with its style, script and \
data inside: the owner reads it in a frame that runs its scripts and nothing else, so no \
localStorage, no alert or confirm, no form to submit, no request to the dashboard and no \
link to a new tab; any of these stops it answering); the card's milestone doc in \
.factory/cards/; tickets in .factory/tasks/later/ (docs/task-format.md). Edit nothing else, and \
don't commit: the runner commits the branch after your reply.
- A card that changes what a page shows or how it is laid out (a new view, an element \
added, moved or removed, a new state or colour) gets a mock-up without being asked (F72), \
on the dashboard (factory_dashboard/templates/) and in the app (coucou/templates/) alike. \
Not for wording only, a bug that restores the look a page already meant, or work with \
nothing on screen; when you skip one on a card with screen changes, say why in a point, so \
the owner can ask for one. It is one file in .factory/cards/{card}-mockup/ with a \
Today / Proposed switch at the top: on a phone the owner flips between two pictures of the \
same size, on a wide screen they sit side by side. Today is copied from the live template \
and its CSS (factory_dashboard/static/dashboard.css, or the app's), not redrawn from \
memory; Proposed marks each change with an outline and a short note; both show real values \
you can read (.factory/var/runs/state.json, .factory/tasks/, .factory/cards/), as \
.factory/cards/f17-mockup/top-bar.html does (for the switch, the copied Today and the \
marks, follow .factory/cards/f94-mockup/away-rows.html). The mock-up and the plan come in \
the same reply: each UI ticket names the mock-up file in its Context as the picture to build, and \
when the owner's comments change the mock-up, revise the tickets in the same turn.
- To redirect {card} while it runs, propose a `replan` (f6-13): on the branch it may also \
change {card}'s waiting tickets, .factory/tasks/ready/{card}-*.md: edit one, add one, or set one \
aside (move it to .factory/tasks/later/). Never another milestone's ticket, never the one in \
progress (`in_flight` in .factory/var/runs/state.json names it), never \
.factory/tasks/done/: the runner refuses the approval. Each changed ticket must pass \
pre-flight: after writing or changing tickets, run \
`uv run runner check-tickets` (every draft in .factory/tasks/later/; or name files) and fix \
what it reports, since Approve refuses the plan for the same problems. Only a `replan` may touch \
.factory/tasks/ready/.
- When a change touches tickets the line may start while you talk (a `replan`, a ticket \
reworked), suggest the owner pause the factory from the dashboard first, and say so in a \
point; approving the `replan` lifts their pause.
- When {card} is still an idea (its doc says `**State:** idea`) and this is your first reply \
on it, name it: give a short `title` at the top level of the block, beside `points` \
(`"title": "…"`), one line of at most 80 characters saying what the card is about. The \
runner then rewrites the card's heading on main. Don't edit the heading yourself, and give \
no `title` on any other card.
"""
    + _PLANNER_TAIL
)

# The general thread has no card, so no branch: an idea worth a card is proposed as a seed.
PLANNER_GENERAL = (
    _PLANNER_HEAD
    + """\
- This thread has no card, so no plan branch: read what you need and change nothing. An \
idea worth a card is a `seed` proposal (path null); the runner plants it once approved. \
Never write to .factory/tasks/: a card's own thread redirects its tickets.
"""
    + _PLANNER_TAIL
)

NARRATIVE = """\
Read {report}, the runner's report of the last build session, and the logs it mentions under
.factory/var/runs/. Replace the text under "## Narrative" with 5-12 lines for the owner, who wants
to learn how the frontier + local workflow performs: what went well, what didn't, what the
local-vs-Claude token split means here, and concrete improvement opportunities (task size, context,
prompts, gates). Edit only that section.
"""


def local_prompt(task: Task, extra: str = "") -> str:
    return LOCAL.format(
        id=task.id,
        extra=extra,
        task=task.path.read_text(encoding="utf-8"),
    )
