"""The whole task loop on a real temporary git repo, with the model and command gates faked."""

from collections.abc import Callable
from pathlib import Path

import pytest

from runner import gates, loop
from runner.config import Config, Price
from runner.gates import GateResult
from runner.local_model import OpencodeRun, TokenTotals
from runner.report import SessionReport
from runner.tasks import parse_task
from tests.runner.conftest import git, write_task


def _config(repo: Path) -> Config:
    return Config(
        repo=repo,
        max_attempts=3,
        headless_runs_per_milestone=10,
        review_rounds=3,
        default_max_diff=150,
        warmup_timeout=1,
        opencode_timeout=1,
        claude_timeout=1,
        gate_timeout=60,
        lm_base_url="http://x",
        lm_model="m",
        opencode_model="lmstudio/m",
        backoff_min=1,
        backoff_max=2,
        narrative=False,
        prices={"Claude Sonnet 5": Price(2.0, 10.0)},
    )


@pytest.fixture
def fake_model(monkeypatch):
    """Scripted 'model': each call runs the next function against the repo."""
    script: list[Callable[[Path, str], None]] = []

    def run_opencode(repo, model, title, prompt, timeout, log_path):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(prompt)
        script.pop(0)(repo, prompt)
        return OpencodeRun(exit_code=0, duration_s=1.0, tokens=TokenTotals(1000, 50, 10, 2))

    monkeypatch.setattr(loop, "run_opencode", run_opencode)
    monkeypatch.setattr(loop, "warmup", lambda *a: 0.1)
    monkeypatch.setattr(loop, "loaded_context_length", lambda *a: None)
    file_gates = tuple(
        g
        for g in gates.GATES
        if g.__name__
        in {
            "gate_allowed_files",
            "gate_protected",
            "gate_tests_unchanged",
            "gate_dependencies",
            "gate_diff_size",
            "gate_layout",
        }
    )
    monkeypatch.setattr(gates, "GATES", file_gates)
    return script


def _run(repo: Path, once: bool = False) -> SessionReport:
    report = loop.run_session(_config(repo), once=once, dry_run=False, escalate=False)
    assert report is not None
    return report


def _implement(repo: Path, prompt: str) -> None:
    (repo / "coucou" / "thing.py").write_text("def thing() -> int:\n    return 42\n")


def _add_task(repo: Path, task_id: str, deps: str = "[]") -> None:
    write_task(repo / "tasks" / "ready", task_id, deps)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"add {task_id}")


def test_task_merges_on_first_attempt(repo, fake_model):
    _add_task(repo, "m1-01-thing")
    fake_model.append(_implement)
    report = _run(repo)
    assert [t.result for t in report.tasks] == ["done"]
    assert "return 42" in (repo / "coucou" / "thing.py").read_text()
    done = repo / "tasks" / "done" / "m1-01-thing.md"
    assert "result: done" in done.read_text()
    assert "task/m1-01-thing" not in git(repo, "branch")
    assert list((repo / "docs" / "sessions").glob("*.md"))
    assert git(repo, "status", "--porcelain") == ""


def test_retry_gets_gate_output_and_can_recover(repo, fake_model):
    _add_task(repo, "m1-01-thing")

    def stray(repo, prompt):
        (repo / "coucou" / "other.py").write_text("X = 1\n")

    def fix(repo, prompt):
        assert "allowed-files" in prompt and "coucou/other.py" in prompt
        (repo / "coucou" / "other.py").unlink()
        _implement(repo, prompt)

    fake_model.extend([stray, fix])
    report = _run(repo, once=True)
    task = report.tasks[0]
    assert (task.result, task.attempts, task.gate_failures) == ("done", 2, ["allowed-files"])
    assert not (repo / "coucou" / "other.py").exists()


def test_protected_and_test_edits_are_rejected_then_escalated(repo, fake_model):
    _add_task(repo, "m1-01-thing")
    _add_task(repo, "m1-02-next", "[m1-01-thing]")

    def cheat(repo, prompt):
        (repo / "tests" / "unit" / "test_thing.py").write_text("# gutted\n")

    fake_model.extend([cheat, cheat, cheat])
    report = _run(repo)
    assert [t.result for t in report.tasks] == ["escalated"]
    assert report.tasks[0].gate_failures == ["allowed-files"] * 3
    escalated = (repo / "tasks" / "escalated" / "m1-01-thing.md").read_text()
    assert "gates failed 3x" in escalated
    # The dependant is paused, not attempted.
    assert (repo / "tasks" / "ready" / "m1-02-next.md").exists()
    assert "Paused (dependency escalated): m1-02-next" in report.notes
    assert "gutted" not in (repo / "tests" / "unit" / "test_thing.py").read_text()


def test_blocked_escalates_immediately(repo, fake_model):
    _add_task(repo, "m1-01-thing")

    def blocked(repo, prompt):
        (repo / "BLOCKED.md").write_text("CATEGORY: needs-info\nWhich unit is the result in?\n")

    fake_model.append(blocked)
    report = _run(repo)
    task = report.tasks[0]
    assert (task.result, task.blocked, task.attempts) == ("blocked", "needs-info", 1)
    assert (repo / "tasks" / "escalated" / "m1-01-thing.md").exists()
    assert not (repo / "BLOCKED.md").exists()


def test_unrelated_problem_does_not_block(repo, fake_model):
    _add_task(repo, "m1-01-thing")

    def noticed(repo, prompt):
        (repo / "BLOCKED.md").write_text("CATEGORY: unrelated-problem\nTypo in README.\n")
        _implement(repo, prompt)

    fake_model.append(noticed)
    report = _run(repo)
    assert report.tasks[0].result == "done"


def test_preflight_failure_escalates_without_calling_the_model(repo, fake_model):
    _add_task(repo, "m1-01-thing")
    (repo / "coucou" / "thing.py").write_text("X = 1\n")
    git(repo, "commit", "-qam", "break the skeleton")
    report = _run(repo)
    assert report.tasks[0].result == "preflight"
    assert report.tasks[0].attempts == 0  # the model was never called


def test_refuses_to_start_on_a_dirty_tree(repo, fake_model):
    (repo / "dirty.txt").write_text("x")
    with pytest.raises(loop.RunnerError, match="clean main"):
        loop.run_session(_config(repo), once=False, dry_run=False, escalate=False)


def test_a_requeued_task_gets_its_own_log_folder(tmp_path):
    first = loop._logs_dir(tmp_path, "m1-01-thing")
    (first / "opencode-1.jsonl").write_text("first run")
    second = loop._logs_dir(tmp_path, "m1-01-thing")
    assert first == tmp_path / "m1-01-thing"
    assert second == tmp_path / "m1-01-thing-run2"
    assert (first / "opencode-1.jsonl").read_text() == "first run"


def test_retry_prompt_ends_with_the_gate_output(repo: Path):
    task = parse_task(write_task(repo / "tasks" / "ready", "m1-01-thing"), 150)
    first = loop._prompt(task, 1, None)
    assert "uv run mypy" in first
    retry = loop._prompt(task, 2, GateResult("ruff", False, "tasks/ready/m1-01-thing.md"))
    assert retry.index("### Goal") < retry.index("IMPORTANT")
    assert retry.rstrip().endswith("tasks/ready/m1-01-thing.md\n```")
    assert "CATEGORY: needs-file" in retry
