"""Prompts for the local model and headless Claude. Kept in one place so they're reviewable."""

from runner.tasks import Task

LOCAL = """\
Implement the task below in the Coucou repository. Change only the files listed under
`files:`. Never edit existing tests and never run git. If you're stuck, write BLOCKED.md
as AGENTS.md describes, then stop.

{task}

Finish by running `uv run pytest -q {tests}`, `uv run ruff format {files}`,
`uv run ruff check {files}` and `uv run mypy coucou tests runner`, and fix what they report.
{extra}"""

# On a retry the gate output goes last: the local model follows the end of a long prompt best
# (ADR 01, item 3).
_NOT_YOURS = (
    "If the failing file isn't listed under `files:`, you can't fix it: write BLOCKED.md with\n"
    "`CATEGORY: needs-file` naming that file, and stop."
)

RETRY = (
    """
IMPORTANT: your previous attempt failed the `{gate}` gate. Fix exactly that.
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
Don't repeat it.
"""
    + _NOT_YOURS
    + """
What went wrong last time:
```
{output}
```
"""
)

ESCALATION = """\
You are handling an escalated task in the Coucou repo. Follow CLAUDE.md (Escalations).

- Task: tasks/escalated/{id}.md
- Why it was escalated: {reason}
- Run logs: {logs}/ (OpenCode output, gate output, last.diff). The local model's work is on
  branch task/{id}; you are on main.

Do exactly one of:
1. requeue: repair or split the spec and write the task file(s) to tasks/ready/
   (skeleton-first: add any stubs or failing tests the task needs).
2. requeue: answer the model's question by adding the facts to the task's Context, and write
   the task to tasks/ready/{id}.md.
3. implemented: if the task is hard or protected, implement it yourself on main and make
   `uv run pytest -q tests/unit tests/integration tests/runner` pass.
4. owner: if it needs the owner's decision, draft an ADR in docs/adr/ (status Proposed).

Then write {logs}/decision.json as {{"outcome": "requeue" | "implemented" | "owner"}}
and {logs}/escalation.md: 3-6 lines on what happened, what the local model got wrong, and how
the task format or sizing could have prevented it (the owner reads these to learn).
Don't run git and don't edit tasks/escalated/: the runner commits and moves files.
"""

REVIEW = """\
You are reviewing milestone {milestone} of Coucou. Follow CLAUDE.md (Review loop) and
docs/workflow.md (Milestone review loop).

Round {round} of at most {max_rounds}. {scope}

Grade each finding blocking / should-fix / nit and route it:
- local: write a fix task in tasks/ready/ (docs/task-format.md), `finding: <id>` in the
  frontmatter, skeleton-first. Findings listed as recurring must NOT go to the local model.
- claude: fix it yourself now, keeping `uv run pytest -q tests/unit tests/integration
  tests/runner` green.
- adr: draft an ADR (status Proposed) and set "stop": "adr-needed".
- backlog: nits and should-fix points about untouched code go to docs/backlog.md.
Recurring findings (fix these yourself): {recurring}

Write {out} as:
{{"findings": [{{"id": "m{milestone}-F1", "severity": "...", "route": "...",
  "summary": "...", "resolved": false, "security": false}}],
  "stop": null | "adr-needed" | "security-unresolved" | "unforeseen-cross-milestone"}}
Keep ids stable across rounds; mark findings fixed since the last round "resolved": true.
Also create or update docs/reviews/m{milestone}.md (what was built, findings and resolutions,
backlog, workflow observations; the runner appends metrics). Don't run git.
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
        tests=" ".join(task.tests),
        files=" ".join(f for f in task.files if f.endswith(".py")) or ".",
        extra=extra,
        task=task.path.read_text(encoding="utf-8"),
    )
