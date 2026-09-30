"""Prompts for the local model and headless Claude. Kept in one place so they're reviewable."""

from runner.tasks import Task

# The junior's prompt stays short: it drops instructions from long prompts (ADR 01).
LOCAL = """\
Implement the task below in the Coucou repository. Start from the files under `files:`;
change other files only if the goal needs it. Write or update tests for what "Done when"
asks, in the test files under `tests:`. Never edit protected paths
(workflow/protected-paths.txt) and never run git. If you're stuck, write BLOCKED.md as
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
WARNING: a previous attempt failed the `{gate}` gate and the branch has been reset.
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

# ADR 12 item 5: a retry after a timeout says so, before the gate output.
TIMED_OUT = """
Your previous attempt ran out of time. Keep what works and finish the smallest remaining piece
first.
"""

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
WARNING: your previous attempts failed (last: the `{gate}` gate) and the branch has been reset.
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

DIRECTION = """\
You are the lead. A junior (a local model) has failed task {id} twice; it gets one last
attempt, on a fresh branch. Give it direction (ADR 12 item 6; docs/agents/lead.md,
Escalations).

- Task: {task}
- Its work: branch task/{id} (`git diff main...task/{id}`) and {logs}/last.diff
- Gate output per attempt: {logs}/gates-*.txt
- Its thinking per attempt: {thinking}
- Longest run of edits without running a command: {streak}; attempts that timed out: {timeouts}

Write {logs}/direction.md: 3-8 lines addressed to the junior, saying what went wrong and the
facts it is missing. No code: no snippets, no diffs, no reference implementation (ADR 07).
If the ticket itself is wrong (a missing or false fact, a protected file, something its tools
can't do), also write {logs}/ticket.md: the whole corrected ticket, frontmatter included.
Write nothing else. Read-only git (diff, log, show) is fine.
"""

ESCALATION = """\
You are the lead, handling an escalated task in the Coucou repo. Follow
docs/agents/lead.md (Escalations).

- Task: tasks/escalated/{id}.md
- Why it was escalated: {reason}
- Run logs: {logs}/ (OpenCode output, gate output, last.diff). The local model's work is on
  branch task/{id}; you are on main.
- The local model's thinking: {thinking}. Read it: it shows why, where the gate logs don't.

Do exactly one of:
1. requeue: repair or split the ticket and write the task file(s) to tasks/ready/
   (docs/task-format.md). Add facts, not a solution.
2. requeue: answer the model's question by adding the facts to the task's Context, and write
   the task to tasks/ready/{id}.md.
3. implemented: if the task is hard or protected, implement it yourself on main and make
   `uv run pytest -q tests/unit tests/integration tests/runner` pass.
4. owner: only for what docs/agents/lead.md reserves for the owner: draft an ADR in
   docs/adr/ (status Proposed). The task and its dependants wait for the owner's decision.

Code you change must pass `uv run runner check-all`; if it doesn't, none of it reaches main.
Then write {logs}/decision.json as {{"outcome": "requeue" | "implemented" | "owner"}}, and
for "owner" also {{"adr": "docs/adr/NN-slug.md", "question": "<one line for the owner>"}}
and {logs}/escalation.md: 3-6 lines on what happened, what the local model got wrong, and
the lesson. Turn the lesson into a check, an example or a line in docs/agents/junior.md
(its budget is in lead.md), and say which. Read-only git (diff, log, show) is fine; don't
commit and don't edit tasks/escalated/: the runner commits and moves files.
"""

LEAD_TICKET = """\
You are the lead, doing your own ticket in the Coucou repo: {task}. Follow
docs/agents/lead.md ("Your own work"): test-first, isolation tests for protected paths, and
docs/security.md for anything security-related. You are on branch task/{id}.

When it's done, `uv run runner check-all --fix --task {id}` must pass. Don't commit: the runner
checks and merges your work. Read-only git (diff, log, show) is fine. If the ticket can't be
done as written, change nothing and say why in your final message.
"""

CHECKPOINT = """\
You are the lead, doing a checkpoint in the middle of a milestone (ADR 12 item 8). Juniors
(a local model) just merged these tickets:
{merges}

Read those diffs, code and tests, as in docs/agents/lead.md (Review): does the screen show
what the ticket asks, do the tests act as a person would and check content, not presence,
is anything masked instead of fixed? Don't read the junior's thinking unless a finding needs
explaining. Then do what helps the next tickets most, any of:
- nothing, if it's sound
- a fix ticket in tasks/ready/ (docs/task-format.md, `finding:` in the frontmatter), and add
  its id to `depends_on` of the ready tickets that build on the problem
- tighten upcoming tickets in tasks/ready/ with what you saw (facts, not solutions)
- one line in docs/agents/junior.md (its budget is in lead.md)

Write {out}: 2-5 lines on what you found and did. Change nothing else; don't run git beyond
diff, log and show.
"""

REVIEW = """\
You are the lead, reviewing milestone {milestone} of Coucou. Follow docs/agents/lead.md
(Review) and docs/workflow.md (Milestone review loop).

Round {round} of at most {max_rounds}. {scope}

Read the tests as closely as the code: missing edge cases, and every existing test a junior
edited (the session reports in docs/sessions/ list them). Check the French.

Grade each finding blocking / should-fix / nit and route it:
- local: write a ticket in tasks/ready/ (docs/task-format.md), `finding: <id>` in the
  frontmatter. Findings listed as recurring must NOT go to the local model.
- claude: fix it yourself now, keeping `uv run pytest -q tests/unit tests/integration
  tests/runner` green.
- adr: only for what lead.md reserves for the owner. Draft an ADR (status Proposed) and set
  "stop": "adr-needed". Decide everything else yourself; never park a finding for the owner.
- backlog: nits and should-fix points about untouched code go to docs/backlog.md.
Recurring findings (fix these yourself): {recurring}

Write {out} as:
{{"findings": [{{"id": "{milestone}-F1", "severity": "...", "route": "...",
  "summary": "...", "resolved": false, "security": false}}],
  "stop": null | "adr-needed" | "security-unresolved" | "unforeseen-cross-milestone"}}
Keep ids stable across rounds; mark findings fixed since the last round "resolved": true.
Also create or update docs/reviews/{milestone}.md. It starts with the owner's sign-off
sheet (lead.md, "Sign-off sheet"), ending with "6. What next": your product and factory
suggestions. Then what was built, findings and resolutions, backlog and workflow
observations. The numbers come from `uv run runner report {milestone}`, between the
`<!-- runner report -->` markers: leave that block as it is and don't recount them.
Read-only git (diff, log, show) is fine; don't commit: the runner does.
"""

NARRATIVE = """\
Read {report}, the runner's report of the last build session, and the logs it mentions under
var/runs/. Replace the text under "## Narrative" with 5-12 lines for the owner, who wants to
learn how the frontier + local workflow performs: what went well, what didn't, what the
local-vs-Claude token split means here, and concrete improvement opportunities (task size, context,
prompts, gates). Edit only that section.
"""


def local_prompt(task: Task, extra: str = "") -> str:
    return LOCAL.format(
        id=task.id,
        extra=extra,
        task=task.path.read_text(encoding="utf-8"),
    )
