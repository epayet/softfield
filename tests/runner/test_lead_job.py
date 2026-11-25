"""A lead ticket's job and an escalation (`runner/lead_job.py`): the repair of a ticket a Claude
job wrote. The tests that run a lead ticket or an escalation end to end drive `work_queue`, and
stay in `tests/runner/test_loop.py` (F290 D6)."""

from datetime import timedelta
from pathlib import Path

from runner import lead_job, session
from runner.claude import UsageLimited
from tests.runner.conftest import write_task
from tests.runner.test_loop import (
    _config,
    _limited_then,
    _Login,
    _login_items,
    _rows,
)


def _repair(s: session.Session, repo: Path, monkeypatch) -> list[str]:
    path = write_task(repo / ".softfield" / "tasks" / "ready", "m1-01-thing")
    monkeypatch.setattr(lead_job, "_ticket_problems", lambda s_, p: ["names a missing path"])
    return lead_job._repair_ticket(
        s, path, "s1", role="escalation", wrote="requeued", milestone="m1", subject="m1-01-thing"
    )


def test_a_repair_refused_by_a_certain_limit_gives_up_without_waiting(repo, monkeypatch):
    """F191 D6: the job that wrote the ticket has ended: nothing to park, nothing to wait for."""
    calls = _limited_then(monkeypatch, UsageLimited(session.now() + timedelta(hours=3)))
    s = session.open_session(_config(repo))
    assert _repair(s, repo, monkeypatch) == ["names a missing path"]
    assert len(calls) == 1
    events = _rows(repo, "usage_events")
    assert [(e["agent"], e["kind"]) for e in events] == [("claude-opus", "refusal")]
    assert not s.state.interrupted and s.state.in_flight is None
    assert s.state.paused_until is None


def test_a_repair_stopped_by_an_expired_login_gives_up_and_the_item_shows(repo, monkeypatch):
    login = _Login(monkeypatch)
    s = session.open_session(_config(repo))
    assert _repair(s, repo, monkeypatch) == ["names a missing path"]
    assert len(login.jobs) == 1
    assert len(_login_items(repo)) == 1
    assert not s.state.interrupted and s.state.in_flight is None
