from pathlib import Path

from runner.messages import (
    done_message,
    escalation_message,
    merge_message,
    session_message,
)
from runner.report import SessionReport, TaskRecord
from runner.tasks import parse_task
from tests.runner.conftest import write_task


def _record(**fields) -> TaskRecord:
    base = {"id": "m1-01-thing", "milestone": 1, "result": "done", "attempts": 1}
    return TaskRecord(**{**base, **fields})


def test_merge_message_tells_the_story(tmp_path: Path):
    task = parse_task(write_task(tmp_path, "m1-01-thing"), 150)
    rec = _record(attempts=2, model_s=121, gates_s=7, tokens_in=62765, tokens_out=2165)
    rec.gate_failures = ["ruff"]
    message = merge_message(
        task, rec, "qwen", [("coucou/thing.py", 3, 1), ("coucou/locale/x.mo", None, None)]
    )
    subject, _, body = message.partition("\n\n")
    assert subject == "m1-01-thing: Make the thing work."
    assert "via the runner in 2 attempts; earlier gate failures: ruff." in body
    assert "Model 2.0 min, gates 7 s; 62,765 tokens in / 2,165 out." in body
    assert "  coucou/thing.py     +3 -1" in body and "coucou/locale/x.mo  (binary)" in body
    assert "Defined by: tests/unit/test_thing.py (all gates green)" in body
    assert "Spec: tasks/done/m1-01-thing.md" in body


def test_long_subjects_are_shortened(tmp_path: Path):
    path = write_task(tmp_path, "m1-01-thing")
    path.write_text(path.read_text().replace("Make the thing work.", "word " * 30))
    task = parse_task(path, 150)
    subject = merge_message(task, _record(), "qwen", []).splitlines()[0]
    assert len(subject) <= 72 and subject.endswith("…")


def test_done_message():
    rec = _record(model_s=100, gates_s=20, commit="25af31b49abcdef")
    subject, _, body = done_message("m1-01-thing", rec).partition("\n\n")
    assert subject == "runner: m1-01-thing done, merged as 25af31b49"
    assert body.startswith("1 attempt, 2.0 min in all;")


def test_escalation_message_keeps_the_tail_of_the_output():
    output = "\n".join(f"line {i}" for i in range(30))
    message = escalation_message("m1-01-thing", "gates failed 3x (last: ruff)", output, "var/x")
    assert message.startswith("runner: escalate m1-01-thing: gates failed 3x (last: ruff)")
    assert "  line 29" in message and "line 17" not in message
    assert message.endswith("Logs: var/x/ (model transcripts, gate output, last.diff)")


def test_session_message_summarises():
    from datetime import datetime

    report = SessionReport(started=datetime(2026, 9, 28, 15, 49))
    report.tasks = [
        _record(tokens_in=1000),
        _record(id="m1-02-x", result="escalated", attempts=3, tokens_in=500),
    ]
    message = session_message(report, "docs/sessions/2026-09-28-1549.md")
    assert message.splitlines()[0] == (
        "runner: session report: 1 merged, 1 not, 1,500 local tokens in"
    )
    assert "  m1-02-x: escalated after 3 attempt(s)" in message
    assert message.endswith("Report: docs/sessions/2026-09-28-1549.md")
