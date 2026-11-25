"""A developer ticket's job (`runner/developer_job.py`): its log folders, its prompts, when it
earns a direction and how check-all runs. The tests that run a ticket end to end drive
`work_queue`, and stay in `tests/runner/test_loop.py` (F290 D6)."""

from pathlib import Path

from runner import checks, developer_job, session
from runner.gates import GateResult
from runner.tasks import parse_task
from tests.runner.conftest import write_task
from tests.runner.test_loop import (
    _activity,
    _config,
)


def test_a_requeued_task_gets_its_own_log_folder(tmp_path):
    first = developer_job._logs_dir(tmp_path, "m1-01-thing")
    (first / "opencode-1.jsonl").write_text("first run")
    second = developer_job._logs_dir(tmp_path, "m1-01-thing")
    assert first == tmp_path / "m1-01-thing"
    assert second == tmp_path / "m1-01-thing-run2"
    assert (first / "opencode-1.jsonl").read_text() == "first run"


def test_retry_prompt_ends_with_the_gate_output(repo: Path):
    task = parse_task(write_task(repo / ".softfield" / "tasks" / "ready", "m1-01-thing"), 150)
    first = developer_job._prompt(task, None)
    assert "softfield check-all --fix --task m1-01-thing" in first
    retry = developer_job._prompt(
        task, GateResult("ruff", False, ".softfield/tasks/ready/m1-01-thing.md")
    )
    assert retry.index("### Goal") < retry.index("IMPORTANT")
    assert "uv run ruff check --fix" in retry  # the gate's hint
    assert retry.rstrip().endswith(".softfield/tasks/ready/m1-01-thing.md\n```")
    assert "CATEGORY: needs-file" in retry


def test_mechanical_failures_get_no_direction():
    assert not developer_job.needs_direction(["ruff", "translations"], [False, False])
    assert developer_job.needs_direction(["ruff", "ruff"], [False, False])  # the same gate twice
    assert developer_job.needs_direction(["ruff", "task-tests"], [False, False])
    assert developer_job.needs_direction(["ruff", "mypy"], [True, False])  # a timeout
    assert developer_job.needs_direction(["no-changes", "no-changes"], [False, False])
    assert not developer_job.needs_direction(["no-changes", "ruff"], [False, False])


def test_the_run_names_check_all_while_it_runs(repo, monkeypatch, tmp_path):
    seen: list[object] = []

    def check_all(repo_, timeout, *, task_id=None, fix=False):
        seen.append(_activity(repo)[0])
        return [checks.Check("tests", True, "")]

    monkeypatch.setattr(checks, "check_all", check_all)
    s = session.open_session(_config(repo))
    before = _activity(repo)
    assert developer_job._check_all(s, "m1-01-lead", tmp_path, "check-all.txt")
    assert developer_job._check_all(s, None, tmp_path, "check-all.txt")
    assert seen == ["check-all · m1-01-lead", "check-all on main"]
    assert _activity(repo) == before == ("picking the next ticket", None)
