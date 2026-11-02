"""Commit messages the runner writes, so `git log` alone tells the story (ADR 00 A4).

Plain functions: the loop passes in what happened, these only format it.
"""

from collections.abc import Sequence

from runner.report import SessionReport, TaskRecord
from runner.tasks import Task

SUBJECT_MAX = 72
DETAIL_LINES = 12

# (path, added, removed); None for binary files
FileChange = tuple[str, int | None, int | None]


def _duration(seconds: float) -> str:
    return f"{seconds / 60:.1f} min" if seconds >= 60 else f"{seconds:.0f} s"


def _subject(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= SUBJECT_MAX else text[: SUBJECT_MAX - 1].rstrip() + "…"


def _changes(changes: Sequence[FileChange]) -> list[str]:
    width = max((len(path) for path, _, _ in changes), default=0)
    lines = []
    for path, added, removed in changes:
        counts = "(binary)" if added is None or removed is None else f"+{added} -{removed}"
        lines.append(f"  {path.ljust(width)}  {counts}")
    return lines


def merge_message(
    task: Task,
    rec: TaskRecord,
    model: str,
    changes: Sequence[FileChange],
    *,
    by: str = "the local model",
) -> str:
    """The squash-merge of a task a developer (``by``, on ``model``) finished."""
    attempts = f"{rec.attempts} attempt{'s' if rec.attempts != 1 else ''}"
    failures = (
        f"; earlier gate failures: {', '.join(rec.gate_failures)}" if rec.gate_failures else ""
    )
    lines = [
        _subject(f"{task.id}: {task.goal}"),
        "",
        task.goal,
        "",
        f"Implemented by {by} ({model}) via the runner in {attempts}{failures}.",
        f"Model {_duration(rec.model_s)}, gates {_duration(rec.gates_s)};"
        f" {rec.tokens_in:,} tokens in / {rec.tokens_out:,} out.",
        "",
        "Changed:",
        *_changes(changes),
        "",
        "Defined by: " + ", ".join(task.tests) + " (all gates green)",
        f"Spec: .softfield/tasks/done/{task.path.name}",
    ]
    return "\n".join(lines)


def finish_message(task: Task, model: str, changes: Sequence[FileChange]) -> str:
    """The squash-merge of a developer's branch the lead finished after an escalation."""
    lines = [
        _subject(f"{task.id}: {task.goal}"),
        "",
        task.goal,
        "",
        f"Started by the local model ({model}) via the runner; finished by the lead on its"
        " branch after an escalation (check-all green).",
        "",
        "Changed:",
        *_changes(changes),
        "",
        f"Spec: .softfield/tasks/done/{task.path.name}",
    ]
    return "\n".join(lines)


def done_message(task_id: str, rec: TaskRecord) -> str:
    """Moving the task file to done/, right after its merge commit."""
    attempts = f"{rec.attempts} attempt{'s' if rec.attempts != 1 else ''}"
    return "\n".join(
        [
            _subject(f"runner: {task_id} done, merged as {rec.commit[:9]}"),
            "",
            f"{attempts}, {_duration(rec.model_s + rec.gates_s)} in all;"
            f" moved the spec to .softfield/tasks/done/ with its result footer.",
        ]
    )


def escalation_message(task_id: str, reason: str, detail: str, logs: str) -> str:
    lines = [_subject(f"runner: escalate {task_id}: {reason}"), ""]
    detail_lines = [line for line in detail.strip().splitlines() if line.strip()]
    if detail_lines:
        lines += ["Last output:", *(f"  {line}" for line in detail_lines[-DETAIL_LINES:]), ""]
    lines.append(f"Logs: {logs}/ (model transcripts, gate output, last.diff)")
    return "\n".join(lines)


def session_message(report: SessionReport, report_path: str) -> str:
    merged = sum(t.result == "done" for t in report.tasks)
    other = len(report.tasks) - merged
    tokens = sum(t.tokens_in for t in report.tasks)
    summary = f"{merged} merged, {other} not, {tokens:,} local tokens in"
    lines = [_subject(f"runner: session report: {summary}"), ""]
    lines += [f"  {t.id}: {t.result} after {t.attempts} attempt(s)" for t in report.tasks]
    if report.claude_runs:
        lines.append(f"  headless Claude runs: {len(report.claude_runs)}")
    lines += ["", f"Report: {report_path}"]
    return "\n".join(lines)
