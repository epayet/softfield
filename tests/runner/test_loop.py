"""The whole task loop on a real temporary git repo, with the model and command gates faked."""

import json
import sqlite3
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner import checks, gates, loop, metrics
from runner.claude import ClaudeJob, ClaudeResult, UsageLimited
from runner.config import Config
from runner.gates import GateResult
from runner.local_model import OpencodeRun, StreamFacts, TokenTotals
from runner.report import SessionReport
from runner.state import load_state, save_state
from runner.tasks import parse_task
from tests.runner.conftest import git, write_task


def _config(repo: Path) -> Config:
    return Config(
        repo=repo,
        max_attempts=3,
        directions_per_task=1,
        escalations_per_task=2,
        checkpoint_every=2,
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
        metrics_db=repo / "var" / "factory-metrics.sqlite",  # never the real one
        checkpoint_model="sonnet",
    )


@pytest.fixture
def fake_model(monkeypatch):
    """Scripted 'model': each call runs the next function against the repo."""
    script: list[Callable[[Path, str], None]] = []

    def run_opencode(repo, model, title, prompt, timeout, log_path, **live):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(prompt)
        run = script.pop(0)(repo, prompt)
        if isinstance(run, OpencodeRun):
            return run
        return OpencodeRun(exit_code=0, duration_s=1.0, tokens=TokenTotals(1000, 50, 10, 2))

    monkeypatch.setattr(loop, "run_opencode", run_opencode)
    monkeypatch.setattr(loop, "warmup", lambda *a: 0.1)
    monkeypatch.setattr(loop, "loaded_context_length", lambda *a: None)
    file_gates = tuple(
        g
        for g in gates.GATES
        if g.__name__
        in {
            "gate_protected",
            "gate_no_new_skips",
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
    # Who did what is visible in the log (ADR 00 A4).
    merge = report.tasks[0].commit
    assert git(repo, "log", "-1", "--format=%an", merge).strip() == "Coucou local model"
    assert "Agent: local-model\nTask: m1-01-thing\nModel: m\nAttempts: 1" in git(
        repo, "log", "-1", "--format=%B", merge
    )
    assert git(repo, "log", "-1", "--format=%an%n%B").startswith("Coucou runner\nrunner: session")
    assert f"`{merge[:9]}`" in next((repo / "docs" / "sessions").glob("*.md")).read_text()
    body = git(repo, "log", "-1", "--format=%B", merge)
    assert "Changed:\n  coucou/thing.py  +1 -1" in body
    assert "Defined by: tests/unit/test_thing.py" in body
    done = git(repo, "log", "--format=%s", "--grep=^runner: m1-01-thing done")
    assert done.strip() == f"runner: m1-01-thing done, merged as {merge[:9]}"


def test_retry_gets_gate_output_and_a_hint_and_can_recover(repo, fake_model):
    _add_task(repo, "m1-01-thing")

    def stray(repo, prompt):
        (repo / "coucou" / "secret.py").write_text("X = 1\n")

    def fix(repo, prompt):
        assert "protected-paths" in prompt and "coucou/secret.py" in prompt
        assert "Undo your changes to the protected files" in prompt  # the gate's hint
        (repo / "coucou" / "secret.py").unlink()
        _implement(repo, prompt)

    fake_model.extend([stray, fix])
    report = _run(repo, once=True)
    task = report.tasks[0]
    assert (task.result, task.attempts, task.gate_failures) == ("done", 2, ["protected-paths"])
    assert not (repo / "coucou" / "secret.py").exists()


def test_skipped_tests_are_rejected_then_escalated(repo, fake_model):
    _add_task(repo, "m1-01-thing")
    _add_task(repo, "m1-02-next", "[m1-01-thing]")

    def cheat(repo, prompt):
        path = repo / "tests" / "unit" / "test_thing.py"
        path.write_text("import pytest\n\n\n@pytest.mark.skip\n" + path.read_text())

    fake_model.extend([cheat, cheat, cheat])
    report = _run(repo)
    assert [t.result for t in report.tasks] == ["escalated"]
    assert report.tasks[0].gate_failures == ["no-new-skips"] * 3
    escalated = (repo / "tasks" / "escalated" / "m1-01-thing.md").read_text()
    assert "gates failed 3x" in escalated
    message = git(repo, "log", "-1", "--format=%B", "--grep=^runner: escalate")
    assert "Last output:" in message and "@pytest.mark.skip" in message
    # The dependant is paused, not attempted.
    assert (repo / "tasks" / "ready" / "m1-02-next.md").exists()
    assert "Paused (dependency escalated): m1-02-next" in report.notes
    assert "skip" not in (repo / "tests" / "unit" / "test_thing.py").read_text()


def test_juniors_may_edit_tests_and_touch_other_files_and_the_report_says_so(repo, fake_model):
    """ADR 07 items 4 and 9: `files:` is a pointer and existing tests may change; the
    session report lists both for the milestone review."""
    _add_task(repo, "m1-01-thing")

    def wider(repo, prompt):
        _implement(repo, prompt)
        (repo / "coucou" / "helper.py").write_text("HELP = 1\n")
        (repo / "tests" / "unit" / "test_thing.py").write_text(
            "def test_thing():\n    assert True\n"
        )

    fake_model.append(wider)
    report = _run(repo)
    task = report.tasks[0]
    assert task.result == "done"
    assert task.outside_files == ["coucou/helper.py"]
    assert task.changed_tests == ["tests/unit/test_thing.py"]
    text = next((repo / "docs" / "sessions").glob("*.md")).read_text()
    assert "edited existing tests (review these): tests/unit/test_thing.py" in text


def test_dry_run_shows_preflight_problems(repo, capsys):
    _add_task(repo, "m1-01-thing")
    task = repo / "tasks" / "ready" / "m1-01-thing.md"
    task.write_text(
        task.read_text().replace(
            "### Pattern to follow\n`coucou/thing.py`", "### Pattern to follow\n`render.js`"
        )
    )
    git(repo, "commit", "-qam", "bare name")
    assert loop.run_session(_config(repo), once=False, dry_run=True, escalate=False) is None
    out = capsys.readouterr().out
    assert "-> m1-01-thing: runnable" in out
    assert "pre-flight: referenced path does not exist: render.js" in out


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


def test_session_stops_when_an_escalation_changes_the_runner(repo, fake_model, monkeypatch):
    """m4-07: an escalation fixed runner/tasks.py and requeued the task, but the running
    session still had the old module loaded and failed the task again."""
    _add_task(repo, "m1-01-thing")
    (repo / "coucou" / "thing.py").write_text("X = 1\n")  # pre-flight fails
    git(repo, "commit", "-qam", "break the skeleton")
    calls: list[str] = []

    def fix_runner_and_requeue(s, task, logs, reason):
        assert not calls, "the session ran the requeued task with stale runner code"
        calls.append(task.id)
        (repo / "runner").mkdir(exist_ok=True)
        (repo / "runner" / "tasks.py").write_text("# fixed\n")
        git(repo, "mv", "tasks/escalated/m1-01-thing.md", "tasks/ready/m1-01-thing.md")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "escalation: requeue")

    monkeypatch.setattr(loop, "handle_escalation", fix_runner_and_requeue)
    report = loop.run_session(_config(repo), once=False, dry_run=False, escalate=True)
    assert report is not None
    assert calls == ["m1-01-thing"]
    assert loop.RESTART_NOTE in report.notes
    assert "a lead ticket or an escalation" in loop.RESTART_NOTE


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
    assert "uv run runner check-all --fix --task m1-01-thing" in first
    retry = loop._prompt(task, 2, GateResult("ruff", False, "tasks/ready/m1-01-thing.md"))
    assert retry.index("### Goal") < retry.index("IMPORTANT")
    assert "uv run ruff check --fix" in retry  # the gate's hint
    assert retry.rstrip().endswith("tasks/ready/m1-01-thing.md\n```")
    assert "CATEGORY: needs-file" in retry


def test_an_attempt_that_changes_nothing_fails_instead_of_merging(repo, fake_model):
    """m4-06: an attempt ended without an edit; the untouched tree passed every gate, and
    squash-merging an empty branch crashed the runner."""
    _add_task(repo, "m1-01-thing")

    def nothing(repo, prompt):
        pass

    def fix(repo, prompt):
        assert "changed nothing" in prompt
        _implement(repo, prompt)

    fake_model.extend([nothing, fix])
    report = _run(repo, once=True)
    task = report.tasks[0]
    assert (task.result, task.attempts, task.gate_failures) == ("done", 2, ["no-changes"])


def _stray(repo: Path, prompt: str) -> None:
    (repo / "coucou" / "secret.py").write_text("X = 1\n")


def _timed_out(repo: Path, prompt: str) -> OpencodeRun:
    return OpencodeRun(exit_code=None, duration_s=2700.0, tokens=TokenTotals(), facts=StreamFacts())


@pytest.fixture
def fake_lead(monkeypatch):
    """Scripted headless Claude: each call runs the next function with the job and the repo."""
    script: list[Callable[[ClaudeJob, Path], None]] = []
    jobs: list[ClaudeJob] = []

    def run_claude(job, repo, timeout, log_path, now, resume=None):
        jobs.append(job)
        script.pop(0)(job, repo)
        return ClaudeResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(loop, "run_claude", run_claude)
    return script, jobs


def _logs_in(prompt: str) -> Path:
    marker = "Write "
    start = prompt.index(marker) + len(marker)
    return Path(prompt[start:].split("/direction.md", 1)[0].strip("`"))


def test_a_retry_after_a_timeout_says_so(repo, fake_model):
    _add_task(repo, "m1-01-thing")

    def fix(repo, prompt):
        assert "ran out of time" in prompt
        _implement(repo, prompt)

    fake_model.extend([_timed_out, fix])
    report = _run(repo, once=True)
    assert report.tasks[0].result == "done"


def test_the_lead_gives_direction_before_the_last_attempt(repo, fake_model, fake_lead, monkeypatch):
    _add_task(repo, "m1-01-thing")
    monkeypatch.setattr(loop, "session_reasoning", lambda db, session: "I think secret.py…")
    script, jobs = fake_lead

    def direct(job, repo_):
        logs = repo_ / _logs_in(job.prompt)
        assert (logs / "gates-2.txt").is_file() and (logs / "last.diff").is_file()
        (logs / "direction.md").write_text("Leave coucou/secret.py alone: it is protected.")

    def follow(repo, prompt):
        assert prompt.rstrip().endswith("Leave coucou/secret.py alone: it is protected.")
        _implement(repo, prompt)

    fake_model.extend([_stray, _stray, follow])
    script.append(direct)
    report = _run(repo, once=True)
    assert [j.kind for j in jobs] == ["direction"]
    assert (report.tasks[0].result, report.tasks[0].attempts) == ("done", 3)
    assert "var/runs/" in jobs[0].prompt and "/thinking-1.md" in jobs[0].prompt
    rows = _rows(repo, "jobs")
    roles = ["developer", "developer", "direction", "last-attempt"]
    assert [(j["role"], j["agent"]) for j in rows] == list(
        zip(roles, ["local-m", "local-m", "claude-opus", "local-m"], strict=True)
    )
    assert [j["attempt"] for j in rows] == [1, 2, 1, 3]  # the attempt number within the task


def test_direction_can_repair_the_ticket(repo, fake_model, fake_lead):
    _add_task(repo, "m1-01-thing")
    script, _ = fake_lead
    ticket = repo / "tasks" / "ready" / "m1-01-thing.md"

    def repair(job, repo_):
        logs = repo_ / _logs_in(job.prompt)
        (logs / "direction.md").write_text("The ticket was wrong; it is fixed.")
        (logs / "ticket.md").write_text(ticket.read_text().replace("Make the thing", "Fix it"))

    def follow(repo, prompt):
        assert "Fix it work." in prompt
        _implement(repo, prompt)

    fake_model.extend([_stray, _stray, follow])
    script.append(repair)
    _run(repo, once=True)
    assert "Fix it work." in (repo / "tasks" / "done" / "m1-01-thing.md").read_text()
    assert git(repo, "log", "--format=%s", "--grep=^direction m1-01-thing").strip()


def test_a_repaired_ticket_without_max_diff_gets_the_default(repo, fake_model, fake_lead):
    """f0: the direction dropped a too-low cap, but the re-parse kept it as the default."""
    ticket = write_task(repo / "tasks" / "ready", "m1-01-thing")
    capped = ticket.read_text()
    ticket.write_text(capped.replace("milestone: 1\n", "milestone: 1\nmax_diff: 1\n"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add m1-01-thing")
    script, _ = fake_lead

    def repair(job, repo_):
        logs = repo_ / _logs_in(job.prompt)
        (logs / "direction.md").write_text("The cap was too low; it is gone.")
        (logs / "ticket.md").write_text(capped)

    fake_model.extend([_implement, _implement, _implement])
    script.append(repair)
    report = _run(repo, once=True)
    assert (report.tasks[0].result, report.tasks[0].attempts) == ("done", 3)


def test_mechanical_failures_get_no_direction():
    assert not loop.needs_direction(["ruff", "translations"], [False, False])
    assert loop.needs_direction(["ruff", "ruff"], [False, False])  # the same gate twice
    assert loop.needs_direction(["ruff", "task-tests"], [False, False])
    assert loop.needs_direction(["ruff", "mypy"], [True, False])  # a timeout
    assert loop.needs_direction(["no-changes", "no-changes"], [False, False])
    assert not loop.needs_direction(["no-changes", "ruff"], [False, False])


def _passes(monkeypatch, ok: bool = True) -> list[str | None]:
    """Fake check-all; returns the task ids it was run for."""
    calls: list[str | None] = []

    def check_all(repo, timeout, *, task_id=None, fix=False):
        calls.append(task_id)
        return [checks.Check("tests", ok, "" if ok else "1 failed")]

    monkeypatch.setattr(checks, "check_all", check_all)
    return calls


def _lead_task(repo: Path, task_id: str) -> None:
    path = write_task(repo / "tasks" / "ready", task_id)
    path.write_text(path.read_text().replace("milestone: 1\n", "milestone: 1\nagent: lead\n"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"add {task_id}")


def _lead_implements(job, repo_):
    assert job.kind == "lead-ticket" and "Bash(uv run runner check-all:*)" in job.allowed_tools
    _implement(repo_, "")


def test_a_lead_ticket_runs_headless_and_merges_when_check_all_passes(
    repo, fake_model, fake_lead, monkeypatch
):
    _lead_task(repo, "m1-01-lead")
    script, _ = fake_lead
    script.append(_lead_implements)
    calls = _passes(monkeypatch)
    report = _run(repo)
    assert [t.result for t in report.tasks] == ["done"]
    assert calls == ["m1-01-lead"]
    assert "return 42" in (repo / "coucou" / "thing.py").read_text()
    assert (repo / "tasks" / "done" / "m1-01-lead.md").exists()
    assert "Agent: claude-headless" in git(repo, "log", "-1", "--format=%B", report.tasks[0].commit)


def test_a_lead_tickets_commands_join_its_tools(repo, fake_model, fake_lead, monkeypatch):
    _lead_task(repo, "m1-01-lead")
    ticket = repo / "tasks" / "ready" / "m1-01-lead.md"
    ticket.write_text(
        ticket.read_text().replace("agent: lead\n", "agent: lead\ncommands: [gh api]\n")
    )
    git(repo, "commit", "-qam", "probe")
    script, jobs = fake_lead
    script.append(_lead_implements)
    _passes(monkeypatch)
    _run(repo)
    assert "Bash(gh api:*)" in jobs[0].allowed_tools


def test_a_lead_ticket_that_fails_check_all_is_blocked_with_its_branch_kept(
    repo, fake_model, fake_lead, monkeypatch
):
    _lead_task(repo, "m1-01-lead")
    _add_task(repo, "m1-02-after", "[m1-01-lead]")
    script, _ = fake_lead
    script.append(_lead_implements)
    _passes(monkeypatch, ok=False)
    report = _run(repo)
    assert [t.result for t in report.tasks] == ["stopped"]
    assert "check-all failed" in (repo / "tasks" / "blocked" / "m1-01-lead.md").read_text()
    assert "task/m1-01-lead" in git(repo, "branch")
    assert "raise NotImplementedError" in (repo / "coucou" / "thing.py").read_text()
    assert (repo / "tasks" / "ready" / "m1-02-after.md").exists()  # paused, not run


def test_a_checkpoint_runs_after_every_two_junior_merges(repo, fake_model, fake_lead):
    for n in (1, 2, 3):
        _add_task(repo, f"m1-0{n}-thing")
    script, jobs = fake_lead

    def change(n: int):
        def run(repo, prompt):
            (repo / "coucou" / f"part{n}.py").write_text(f"PART = {n}\n")

        return run

    def review(job, repo_):
        out = job.prompt.split("Write ", 1)[1].split(":", 1)[0]
        (repo_ / out).parent.mkdir(parents=True, exist_ok=True)
        (repo_ / out).write_text("Sound. Tightened m1-03.")

    fake_model.extend([change(1), change(2), change(3)])
    script.append(review)
    report = _run(repo)
    assert [t.result for t in report.tasks] == ["done"] * 3
    assert [j.kind for j in jobs] == ["checkpoint"]
    assert "m1-01-thing" in jobs[0].prompt and "m1-02-thing" in jobs[0].prompt
    assert "m1-03-thing" not in jobs[0].prompt
    assert jobs[0].model == "sonnet"
    assert "Checkpoint: Sound. Tightened m1-03." in report.notes


def _escalate_on_protected(repo, fake_model) -> None:
    _add_task(repo, "m1-01-thing")
    _add_task(repo, "m1-02-after", "[m1-01-thing]")
    fake_model.extend([_stray, _stray, _stray])


def test_escalations_past_the_limit_block_the_task_without_calling_claude(
    repo, fake_model, fake_lead
):
    _escalate_on_protected(repo, fake_model)
    script, jobs = fake_lead
    script.append(lambda job, repo_: None)  # the direction
    state = load_state(repo / "var" / "runs" / "state.json")
    state.escalations["m1-01-thing"] = 2
    save_state(state, repo / "var" / "runs" / "state.json")
    report = loop.run_session(_config(repo), once=False, dry_run=False, escalate=True)
    assert report is not None
    assert [j.kind for j in jobs] == ["direction"]
    blocked = (repo / "tasks" / "blocked" / "m1-01-thing.md").read_text()
    assert "2 escalations used" in blocked
    assert any(n.startswith("Blocked m1-01-thing") for n in report.notes)


def test_an_escalation_whose_work_fails_check_all_stays_off_main(
    repo, fake_model, fake_lead, monkeypatch
):
    _escalate_on_protected(repo, fake_model)
    script, _ = fake_lead

    def breaks_code(job, repo_):
        (repo_ / "coucou" / "thing.py").write_text("def thing() -> int:\n    return 'x'\n")
        logs = repo_ / job.prompt.split("Run logs: ", 1)[1].split("/ ", 1)[0]
        (logs / "decision.json").write_text('{"outcome": "implemented"}')

    script.extend([lambda job, repo_: None, breaks_code])
    _passes(monkeypatch, ok=False)
    report = loop.run_session(_config(repo), once=False, dry_run=False, escalate=True)
    assert report is not None
    assert "raise NotImplementedError" in (repo / "coucou" / "thing.py").read_text()
    assert "return 'x'" in git(repo, "show", "escalation/m1-01-thing:coucou/thing.py")
    assert "failed check-all" in (repo / "tasks" / "blocked" / "m1-01-thing.md").read_text()
    assert git(repo, "status", "--porcelain") == ""


def test_a_requeued_ticket_keeps_its_escalated_footer(repo, fake_model, fake_lead):
    """f0: the escalation rewrote the ticket, so its done/ file lost the 3 failed attempts
    and their tokens, and the metrics said "escalated: 0"."""
    _escalate_on_protected(repo, fake_model)
    fake_model.extend([_implement, lambda repo_, _: (repo_ / "coucou" / "after.py").write_text("")])
    script, _ = fake_lead
    clean = (repo / "tasks" / "ready" / "m1-01-thing.md").read_text()

    def requeue(job, repo_):
        logs = repo_ / job.prompt.split("Run logs: ", 1)[1].split("/ ", 1)[0]
        (repo_ / "tasks" / "ready" / "m1-01-thing.md").write_text(clean)
        (logs / "decision.json").write_text('{"outcome": "requeue"}')

    script.extend([lambda job, repo_: None, requeue, lambda job, repo_: None])  # + checkpoint
    loop.run_session(_config(repo), once=False, dry_run=False, escalate=True)
    done = (repo / "tasks" / "done" / "m1-01-thing.md").read_text()
    assert done.count("# --- runner ---") == 2
    assert done.index("result: escalated") < done.index("result: done")


def test_a_decision_for_the_owner_is_recorded(repo, fake_model, fake_lead):
    _escalate_on_protected(repo, fake_model)
    script, _ = fake_lead

    def needs_owner(job, repo_):
        logs = repo_ / job.prompt.split("Run logs: ", 1)[1].split("/ ", 1)[0]
        (logs / "decision.json").write_text(
            '{"outcome": "owner", "adr": "docs/adr/14-x.md", "question": "Keep originals?"}'
        )

    script.extend([lambda job, repo_: None, needs_owner])
    loop.run_session(_config(repo), once=False, dry_run=False, escalate=True)
    state = load_state(repo / "var" / "runs" / "state.json")
    assert state.owner == {
        "m1-01-thing": {"adr": "docs/adr/14-x.md", "question": "Keep originals?"}
    }
    assert (repo / "tasks" / "escalated" / "m1-01-thing.md").exists()


def _limited_then(monkeypatch, *outcomes):
    """Fake run_claude: each outcome is an exception to raise or a result to return."""
    calls: list[tuple[str, str | None]] = []

    def run_claude(job, repo, timeout, log_path, now, resume=None):
        calls.append((job.prompt, resume))
        outcome = outcomes[len(calls) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(loop, "run_claude", run_claude)
    monkeypatch.setattr("time.sleep", lambda seconds: None)
    return calls


def _job() -> ClaudeJob:
    return ClaudeJob(kind="lead-ticket", prompt="Do the ticket.", allowed_tools=("Read",))


def test_a_job_cut_off_by_a_usage_limit_resumes_its_session(repo, monkeypatch):
    """f1: a lead ticket stopped mid-way by a limit carries on where it was, after the reset."""
    done = ClaudeResult(ok=True, text="", duration_s=1.0, num_turns=4, session_id="s1")
    calls = _limited_then(monkeypatch, UsageLimited(None, session_id="s1"), done)
    s = loop.open_session(_config(repo))
    assert loop.call_claude(s, _job(), "m1", "m1-01-lead") is done
    assert calls[0] == ("Do the ticket.", None)
    assert calls[1][1] == "s1" and "usage limit" in calls[1][0]
    assert any("usage limit" in note for note in s.report.notes)


def test_a_session_that_cant_resume_starts_afresh_told_about_its_partial_work(repo, monkeypatch):
    lost = ClaudeResult(ok=False, text="No conversation found", duration_s=1.0, num_turns=0)
    done = ClaudeResult(ok=True, text="", duration_s=1.0, num_turns=4)
    calls = _limited_then(monkeypatch, UsageLimited(None, session_id="s1"), lost, done)
    s = loop.open_session(_config(repo))
    assert loop.call_claude(s, _job(), "m1", "m1-01-lead") is done
    prompt, resume = calls[2]
    assert resume is None
    assert prompt.startswith("Do the ticket.") and "git diff" in prompt


def test_an_unrecognised_limit_is_retried_a_few_times_then_fails(repo, monkeypatch):
    unsure = UsageLimited(None, certain=False)
    calls = _limited_then(monkeypatch, unsure, unsure, unsure, unsure)
    s = loop.open_session(_config(repo))
    result = loop.call_claude(s, _job(), "m1", "m1-01-lead")
    assert not result.ok
    assert len(calls) == 1 + loop.UNSURE_LIMIT_RETRIES


# --- the metrics database (f1 D2, D3) ---------------------------------------------------


def _rows(repo: Path, table: str) -> list[dict[str, object]]:
    conn = sqlite3.connect(_config(repo).metrics_db)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY id")]  # noqa: S608
    finally:
        conn.close()


def _measured(change: Callable[[Path, str], None]) -> Callable[[Path, str], OpencodeRun]:
    def attempt(repo: Path, prompt: str) -> OpencodeRun:
        change(repo, prompt)
        return OpencodeRun(
            exit_code=0,
            duration_s=1.0,
            tokens=TokenTotals(1000, 50, 10, 2, peak=700),
            facts=StreamFacts(session_id="ses_1", edit_streak=3, refused=1, edits=4),
        )

    return attempt


def _undo_and_implement(repo: Path, prompt: str) -> None:
    (repo / "coucou" / "secret.py").unlink()
    _implement(repo, prompt)


def test_a_session_writes_its_run_and_a_job_per_attempt(repo, fake_model, monkeypatch):
    _add_task(repo, "m1-01-thing")
    monkeypatch.setattr(loop, "loaded_context_length", lambda *a: 131072)
    fake_model.extend([_measured(_stray), _measured(_undo_and_implement)])
    _run(repo, once=True)
    [run] = _rows(repo, "runs")
    assert run["command"] == "run" and run["started"] and run["heartbeat"] and run["ended"]
    assert run["verdict"] == "1 merged, 0 not"
    [ticket] = _rows(repo, "tickets")
    assert ticket["ticket"] == "m1-01-thing"
    failed, passed = _rows(repo, "jobs")
    for n, job in enumerate((failed, passed), start=1):
        key = (job["run_id"], job["ticket_id"], job["role"], job["attempt"], job["agent"])
        assert key == (run["id"], ticket["id"], "developer", n, "local-m")
        assert (job["tokens_in"], job["tokens_out"], job["steps"]) == (1000, 60, 2)
        assert (job["peak_context"], job["context_limit"]) == (700, 131072)
        assert (job["edit_streak"], job["refused_commands"], job["session_id"]) == (3, 1, "ses_1")
        assert str(job["log_path"]).endswith(f"m1-01-thing/opencode-{n}.jsonl")
        assert job["started"] and job["ended"]
    assert (failed["outcome"], passed["outcome"]) == ("failed", "passed")
    failed_gates = json.loads(str(failed["gates"]))
    assert failed_gates[-1]["name"] == "protected-paths" and failed_gates[-1]["ok"] is False
    for gate in failed_gates:
        assert isinstance(gate["seconds"], float) and gate["log"].endswith("gates-1.txt")
    assert all(gate["ok"] for gate in json.loads(str(passed["gates"])))


def test_a_timed_out_attempt_is_a_timeout(repo, fake_model):
    _add_task(repo, "m1-01-thing")
    fake_model.extend([_timed_out, _implement])
    _run(repo, once=True)
    assert [j["outcome"] for j in _rows(repo, "jobs")] == ["timeout", "passed"]


def test_an_interrupted_attempt_stays_running_with_the_heartbeat_set(repo, fake_model):
    _add_task(repo, "m1-01-thing")

    def crash(repo_: Path, prompt: str) -> None:
        raise RuntimeError("OpenCode died")

    fake_model.append(crash)
    with pytest.raises(RuntimeError, match="OpenCode died"):
        _run(repo)
    [job] = _rows(repo, "jobs")
    [run] = _rows(repo, "runs")
    assert (job["outcome"], job["ended"]) == ("running", None)
    assert run["heartbeat"] and run["ended"] is None


def test_a_live_update_changes_tokens_steps_and_heartbeat_only(repo, monkeypatch):
    s = loop.open_session(_config(repo))
    job = loop.record_start(s, "m1-01-thing", "m1", "developer", "local-m", log_path="x.jsonl")
    [job_before], [run_before] = _rows(repo, "jobs"), _rows(repo, "runs")
    monkeypatch.setattr(loop, "now", lambda: datetime(2030, 1, 1, tzinfo=UTC))
    loop.live_update(s, job, TokenTotals(500, 20, 5, 3, peak=400))
    [job_after], [run_after] = _rows(repo, "jobs"), _rows(repo, "runs")
    assert {k for k in job_before if job_before[k] != job_after[k]} == {
        "tokens_in",
        "tokens_out",
        "steps",
    }
    assert (job_after["tokens_in"], job_after["tokens_out"], job_after["steps"]) == (500, 25, 3)
    assert {k for k in run_before if run_before[k] != run_after[k]} == {"heartbeat"}
    assert run_after["heartbeat"] == "2030-01-01T00:00:00+00:00"


def test_every_claude_job_writes_a_row_and_keeps_its_own_log(repo, monkeypatch):
    logs: list[Path] = []

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        log_path.write_text(job.kind)
        logs.append(log_path)
        usage = {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 100}
        return ClaudeResult(ok=True, text="", duration_s=1.0, usage=usage, cost_usd=0.75)

    monkeypatch.setattr(loop, "run_claude", run_claude)
    s = loop.open_session(_config(repo))
    kinds: list[tuple[str, str | None]] = [
        ("direction", "m1-01-thing"),
        ("escalation", "m1-01-thing"),
        ("escalation", "m1-01-thing"),
        ("checkpoint", None),
        ("lead-ticket", "m1-02-lead"),
        ("review", None),
        ("narrative", None),
    ]
    for kind, ticket in kinds:
        job = ClaudeJob(kind, "Do it.", ("Read",), model="sonnet" if kind == "checkpoint" else "")
        loop.call_claude(s, job, "m1", ticket or kind, ticket=ticket)
    jobs = _rows(repo, "jobs")
    assert [j["role"] for j in jobs] == [kind for kind, _ in kinds]
    assert [j["agent"] for j in jobs] == ["claude-opus"] * 3 + ["claude-sonnet"] + [
        "claude-opus"
    ] * 3
    for j in jobs:
        assert (j["outcome"], j["cost_usd"]) == ("passed", 0.75)
        assert (j["tokens_in"], j["tokens_out"], j["tokens_cached"]) == (10, 5, 100)
        assert j["started"] and j["ended"]
    escalations = [j for j in jobs if j["role"] == "escalation"]
    assert [j["attempt"] for j in escalations] == [1, 2]
    assert escalations[0]["log_path"] != escalations[1]["log_path"]
    assert len(set(logs)) == len(logs)
    assert [p.read_text() for p in logs] == [kind for kind, _ in kinds]


def test_a_usage_limit_pause_is_a_refusal_event(repo, monkeypatch):
    resets = loop.now() + timedelta(hours=1)
    done = ClaudeResult(ok=True, text="", duration_s=1.0, num_turns=4)
    _limited_then(monkeypatch, UsageLimited(resets, session_id="s1"), done)
    s = loop.open_session(_config(repo))
    loop.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    [event] = _rows(repo, "usage_events")
    assert (event["agent"], event["kind"]) == ("claude-opus", "refusal")
    assert event["resets_at"] == resets.isoformat()


def test_a_database_that_cant_be_opened_does_not_stop_the_session(repo, fake_model):
    _add_task(repo, "m1-01-thing")
    (repo / "var").mkdir()
    (repo / "var" / "a-file").write_text("")
    cfg = replace(_config(repo), metrics_db=repo / "var" / "a-file" / "metrics.sqlite")
    fake_model.append(_implement)
    report = loop.run_session(cfg, once=False, dry_run=False, escalate=False)
    assert report is not None
    assert [t.result for t in report.tasks] == ["done"]
    assert len([n for n in report.notes if "metrics database" in n]) == 1


def test_a_failing_write_is_noted_once_and_the_run_goes_on(repo, fake_model, monkeypatch):
    _add_task(repo, "m1-01-thing")

    def broken(*args: object, **kwargs: object) -> None:
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(metrics, "finish_job", broken)
    fake_model.extend([_stray, _undo_and_implement])
    report = _run(repo, once=True)
    assert [t.result for t in report.tasks] == ["done"]
    notes = [n for n in report.notes if "metrics database" in n]
    assert len(notes) == 1 and "disk I/O error" in notes[0]
