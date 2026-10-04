"""The owner's requests from the dashboard (ADR 18 item 2, f5 D2): applied as the console
commands would, each finished once with its result."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner import cli, loop, metrics, requests
from tests.runner.conftest import git, write_task
from tests.runner.test_cli import in_repo  # noqa: F401 - a fixture
from tests.runner.test_owner import _milestone

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _new_command(monkeypatch):
    monkeypatch.setattr(loop, "FIVE_HOUR", loop.ReserveAnswer())


def _db(repo: Path) -> Path:
    return repo / "var" / "factory-metrics.sqlite"


def _ask(repo: Path, kind: str, subject: str | None = None, value: str | None = None) -> int:
    """The dashboard's write: one request row for this repo's project."""
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        return metrics.add_request(conn, project, kind, subject, value, NOW.isoformat())
    finally:
        conn.close()


def _request(repo: Path, request_id: int) -> tuple[object, object]:
    conn = metrics.open_db(_db(repo))
    try:
        row = conn.execute(
            "SELECT done, result FROM owner_requests WHERE id = ?", (request_id,)
        ).fetchone()
        return row["done"], row["result"]
    finally:
        conn.close()


def _apply(repo: Path) -> list[str]:
    return requests.apply_requests(repo, _db(repo), NOW)


def _later(repo: Path, *ids: str) -> None:
    for task_id in ids:
        write_task(repo / "tasks" / "later", task_id)
    git(repo, "add", "tasks")
    git(repo, "commit", "-q", "-m", "set aside")


def test_a_signoff_request_signs_off_as_the_command_does(repo):
    _milestone(repo)
    asked = _ask(repo, "signoff", "m1")
    assert _apply(repo) == ["signoff m1: signed off m1"]
    assert git(repo, "tag").split() == ["m1-done"]
    assert git(repo, "log", "-1", "--format=%s").strip() == "M1 signed off by the owner"
    assert "Status: done." in (repo / "docs" / "milestones" / "m1.md").read_text()
    assert _request(repo, asked) == (NOW.isoformat(), "signed off m1")
    assert _apply(repo) == []  # finished once


def test_a_signoff_request_with_work_left_is_finished_with_the_commands_error(repo):
    _milestone(repo)
    write_task(repo / "tasks" / "escalated", "m1-02-photos")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "escalated")
    head = git(repo, "rev-parse", "HEAD")
    doc = (repo / "docs" / "milestones" / "m1.md").read_text()
    asked = _ask(repo, "signoff", "m1")
    error = "work is left: m1-02-photos (escalated). Finish it, or sign off with --force."
    assert _apply(repo) == [f"signoff m1: {error}"]
    assert _request(repo, asked) == (NOW.isoformat(), error)
    # Nothing changed: no commit, no tag, the doc as it was, a clean tree.
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "tag") == "" and git(repo, "status", "--porcelain") == ""
    assert (repo / "docs" / "milestones" / "m1.md").read_text() == doc
    assert _apply(repo) == []  # never retried


def test_a_signoff_request_for_a_bad_key_is_refused_before_any_file_is_read(repo):
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "signoff", "../../etc/passwd")
    [line] = _apply(repo)
    assert "must be a number or a key like f1" in line
    assert _request(repo, asked)[1] == line.split(": ", 1)[1]
    assert git(repo, "rev-parse", "HEAD") == head and git(repo, "tag") == ""


def test_a_queue_request_moves_the_ticket_and_commits_as_the_command_does(repo):
    _later(repo, "m4-12-send-recovers", "f3-01-other")
    asked = _ask(repo, "queue", "m4-12-send-recovers")
    assert _apply(repo) == ["queue m4-12-send-recovers: queued m4-12-send-recovers"]
    assert (repo / "tasks" / "ready" / "m4-12-send-recovers.md").is_file()
    assert not (repo / "tasks" / "later" / "m4-12-send-recovers.md").exists()
    assert (repo / "tasks" / "later" / "f3-01-other.md").is_file()  # only the one asked for
    assert git(repo, "log", "-1", "--format=%s").strip() == (
        "queue m4-12-send-recovers (by the owner)"
    )
    changed = git(repo, "show", "--name-only", "--no-renames", "--format=", "HEAD").split()
    assert sorted(changed) == [
        "tasks/later/m4-12-send-recovers.md",
        "tasks/ready/m4-12-send-recovers.md",
    ]
    assert git(repo, "status", "--porcelain") == ""
    assert _request(repo, asked) == (NOW.isoformat(), "queued m4-12-send-recovers")


def test_a_queue_request_for_a_missing_ticket_is_finished_with_the_error(repo):
    _later(repo, "m4-12-a")
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "queue", "m9-01-nothing")
    [line] = _apply(repo)
    error = "m9-01-nothing matches no ticket in tasks/later/. Choices: m4-12-a"
    assert line == f"queue m9-01-nothing: {error}"
    assert _request(repo, asked)[1] == line.split(": ", 1)[1]
    assert git(repo, "rev-parse", "HEAD") == head
    assert _apply(repo) == []


@pytest.mark.parametrize(("value", "yes", "no"), [("yes", True, False), ("no", False, True)])
def test_a_five_hour_answer_with_no_question_waiting_holds_for_the_command(repo, value, yes, no):
    asked = _ask(repo, "five_hour", value=value)
    [line] = _apply(repo)
    assert (loop.FIVE_HOUR.yes, loop.FIVE_HOUR.no) == (yes, no)
    assert line.startswith(f"five_hour {value}: ")
    assert _request(repo, asked)[0] == NOW.isoformat()


def test_a_later_five_hour_answer_overrides_an_earlier_one(repo):
    _ask(repo, "five_hour", value="no")
    _ask(repo, "five_hour", value="yes")
    _apply(repo)
    assert loop.FIVE_HOUR.yes and not loop.FIVE_HOUR.no


@pytest.mark.parametrize(
    ("kind", "subject", "value", "error"),
    [
        ("five_hour", None, "maybe", "a 5-hour answer is yes or no, not 'maybe'"),
        ("reboot", "now", None, "unknown request: reboot"),
    ],
)
def test_a_request_the_runner_cant_read_is_finished_with_why(repo, kind, subject, value, error):
    asked = _ask(repo, kind, subject, value)
    _apply(repo)
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert not loop.FIVE_HOUR.yes and not loop.FIVE_HOUR.no


def test_another_projects_requests_are_left_alone(repo):
    _later(repo, "m4-12-a")
    conn = metrics.open_db(_db(repo))
    other = metrics.upsert_project(conn, "elsewhere")
    theirs = metrics.add_request(conn, other, "queue", "m4-12-a", None, NOW.isoformat())
    conn.close()
    assert _apply(repo) == []
    assert _request(repo, theirs) == (None, None)
    assert (repo / "tasks" / "later" / "m4-12-a.md").is_file()


def test_without_a_database_there_is_nothing_to_apply_and_none_is_made(repo):
    assert _apply(repo) == []
    assert not _db(repo).exists()


def test_a_five_hour_answer_is_taken_once_for_a_waiting_question(repo):
    asked = _ask(repo, "five_hour", value="yes")
    _ask(repo, "queue", "m4-12-a")  # not an answer: left for the next pick
    conn = metrics.open_db(_db(repo))
    project = metrics.find_project(conn, repo.name)
    assert project is not None
    try:
        assert requests.take_five_hour(conn, project, NOW) == "yes"
        assert requests.take_five_hour(conn, project, NOW) is None
        assert [r["kind"] for r in metrics.open_requests(conn, project)] == ["queue"]
    finally:
        conn.close()
    done, result = _request(repo, asked)
    assert done == NOW.isoformat() and "yes" in str(result)
    assert not loop.FIVE_HOUR.yes  # the question that waited sets it, not the take


# --- at the start of every command (f5 D2) --------------------------------------------------


def test_a_request_made_while_nothing_runs_is_applied_by_the_next_command(in_repo, capsys):  # noqa: F811
    _later(in_repo, "m4-12-a", "m4-13-b")
    asked = _ask(in_repo, "queue", "m4-12-a")
    assert cli.main(["queue", "m4-13"]) == 0
    assert (in_repo / "tasks" / "ready" / "m4-12-a.md").is_file()
    assert (in_repo / "tasks" / "ready" / "m4-13-b.md").is_file()
    subjects = git(in_repo, "log", "-2", "--format=%s").splitlines()
    assert subjects == ["queue m4-13-b (by the owner)", "queue m4-12-a (by the owner)"]
    assert _request(in_repo, asked)[1] == "queued m4-12-a"
    assert "queued m4-12-a" in capsys.readouterr().out


def test_a_live_run_applies_its_own_requests_not_another_command(in_repo):  # noqa: F811
    _later(in_repo, "m4-12-a")
    asked = _ask(in_repo, "queue", "m4-12-a")
    conn = metrics.open_db(_db(in_repo))
    project = metrics.upsert_project(conn, in_repo.name)
    beat = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
    metrics.upsert_run(conn, project, "20261003-120000", started=beat, heartbeat=beat)
    conn.close()
    assert cli.main(["accept", "99"]) == 1  # any command; this one changes nothing
    assert _request(in_repo, asked) == (None, None)
    assert (in_repo / "tasks" / "later" / "m4-12-a.md").is_file()


def test_the_checks_never_apply_requests(in_repo):  # noqa: F811
    """check-all runs inside jobs and as the pre-commit hook: a commit there would land on a
    task branch, or in the middle of the owner's own."""
    _later(in_repo, "m4-12-a")
    asked = _ask(in_repo, "queue", "m4-12-a")
    cli.main(["check-layout"])
    assert _request(in_repo, asked) == (None, None)
