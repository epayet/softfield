"""What every runner job shares (`runner/session.py`), on a real temporary git repo with Claude
faked: the clock, the session and its recovery, the heartbeat, the job rows and ``call_claude``."""

import sqlite3
import threading
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner import (
    backup,
    claude,
    metrics,
    session,
)
from runner.agents import JobResult, JobSpec, Reading
from runner.claude import Progress, TransientError, UsageLimited
from runner.config import Backup, Config
from runner.local_model import TokenTotals
from runner.state import State, save_state
from tests.runner.conftest import git, write_task
from tests.runner.test_loop import (
    OWNER_MD,
    ROLE_SECTIONS,
    ROLES,
    _activity,
    _add_task,
    _config,
    _headings,
    _job,
    _lead_docs,
    _limited_then,
    _rows,
    _state,
    _switch_on,
)


def test_the_clock_is_utc_whatever_the_zone(paris):
    assert session.now().utcoffset() == timedelta(0)
    assert session.now().isoformat().endswith("+00:00")


def test_a_run_stores_utc_and_its_folder_is_named_in_local_time(repo, paris):
    s = session.open_session(_config(repo), "run")
    assert s.db is not None
    started = s.db.execute("SELECT started FROM runs").fetchone()["started"]
    assert started.endswith("+00:00")
    assert s.run_dir.name == f"{s.report.started.astimezone():%Y%m%d-%H%M%S}"
    assert s.run_dir.name != f"{s.report.started:%Y%m%d-%H%M%S}"
    session.wait_for_claude(s, 0, session.now(), "x")
    at, resets = s.db.execute("SELECT at, resets_at FROM usage_events").fetchone()
    assert at.endswith("+00:00") and resets.endswith("+00:00")
    session.close_session(s)


OLD_AT = "2026-09-30T15:00:00+01:00"
OLD_AS_UTC = "2026-09-30T14:00:00+00:00"


def _old_database(cfg: Config, *, collide: bool = False) -> None:
    """A metrics database that still owes the F187 step, with a time in +01:00."""
    conn = metrics.open_db(cfg.metrics_db)
    conn.execute("DELETE FROM once_steps WHERE name = ?", (metrics.UTC_STEP,))
    for at in (OLD_AT, *([OLD_AS_UTC] if collide else [])):
        conn.execute("INSERT INTO usage_events (agent, at, kind) VALUES ('claude', ?, 's')", (at,))
    conn.close()


def _usage_times(path: Path) -> list[str]:
    conn = sqlite3.connect(path)
    try:
        return [r[0] for r in conn.execute("SELECT at FROM usage_events ORDER BY id")]
    finally:
        conn.close()


def test_the_old_times_are_converted_after_a_copy_beside_the_database(repo, capsys):
    cfg = _config(repo)
    _old_database(cfg)
    s = session.open_session(cfg, None)
    session.check_backup(s)
    [copy] = cfg.metrics_db.parent.glob("factory-metrics-*.sqlite")
    assert _usage_times(copy) == [OLD_AT]  # the owner's data, as it was
    assert _usage_times(cfg.metrics_db) == [OLD_AS_UTC]
    assert "converted 1 stored times to UTC (F187)" in capsys.readouterr().out
    session.check_backup(s)
    assert capsys.readouterr().out == ""
    assert len(list(cfg.metrics_db.parent.glob("factory-metrics-*.sqlite"))) == 1


def test_the_old_times_are_converted_once_the_backup_copy_is_written(repo, tmp_path, capsys):
    folder = tmp_path / "Dropbox"
    cfg = replace(_config(repo), backup=Backup(folder, 14, 24))
    _old_database(cfg)
    s = session.open_session(cfg, None)
    s.backups = backup.Backups(cfg.metrics_db, Backup(folder, 14, 24))
    session.check_backup(s)
    [copy] = folder.glob("factory-metrics-*.sqlite")
    assert _usage_times(copy) == [OLD_AT]
    assert _usage_times(cfg.metrics_db) == [OLD_AS_UTC]
    assert not list(cfg.metrics_db.parent.glob("factory-metrics-*.sqlite"))
    capsys.readouterr()
    session.check_backup(s)  # no new copy is due, and nothing is owed
    assert capsys.readouterr().out == ""


def test_a_collision_changes_nothing_and_is_said_once(repo, capsys):
    cfg = _config(repo)
    _old_database(cfg, collide=True)
    s = session.open_session(cfg, None)
    session.check_backup(s)
    session.check_backup(s)
    assert _usage_times(cfg.metrics_db) == [OLD_AT, OLD_AS_UTC]
    conn = metrics.open_db(cfg.metrics_db)
    assert metrics.utc_step_owed(conn)
    conn.close()
    out = capsys.readouterr().out
    assert out.count("Converting the stored times to UTC (F187)") == 1
    assert len([n for n in s.report.notes if "F187" in n]) == 1


def test_a_wait_until_a_stored_time_says_it_in_local_time(repo, paris, monkeypatch):
    s = session.open_session(_config(repo), None)
    seen: list[str] = []
    monkeypatch.setattr(
        session, "set_activity", lambda s, activity, until=None: seen.append(activity)
    )
    session.wait_for_claude(s, 0, datetime(2026, 10, 29, 8, 0, tzinfo=UTC), None, limit=False)
    assert "until 09:00" in seen[0]
    session.close_session(s)


def test_a_job_cut_off_by_a_usage_limit_resumes_its_session(repo, monkeypatch):
    """f1: a lead ticket stopped mid-way by a limit carries on where it was, after the reset."""
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4, session_id="s1")
    calls = _limited_then(monkeypatch, UsageLimited(None, session_id="s1"), done)
    s = session.open_session(_config(repo))
    assert session.call_claude(s, _job(), "m1", "m1-01-lead") is done
    assert calls[0] == ("Do the ticket.", None)
    assert calls[1][1] == "s1" and "usage limit" in calls[1][0]
    assert any("usage limit" in note for note in s.report.notes)


def test_a_session_that_cant_resume_starts_afresh_told_about_its_partial_work(repo, monkeypatch):
    lost = JobResult(ok=False, text="No conversation found", duration_s=1.0, num_turns=0)
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    calls = _limited_then(monkeypatch, UsageLimited(None, session_id="s1"), lost, done)
    s = session.open_session(_config(repo))
    assert session.call_claude(s, _job(), "m1", "m1-01-lead") is done
    prompt, resume = calls[2]
    assert resume is None
    assert prompt.startswith("Do the ticket.") and "git diff" in prompt


@pytest.mark.parametrize("role", sorted(ROLE_SECTIONS))
def test_a_lead_job_starts_with_owner_md_and_exactly_its_roles_sections(repo, monkeypatch, role):
    """f21 D2: pasted in, first, the same text for every job of the role."""
    _lead_docs(repo, monkeypatch)
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    calls = _limited_then(monkeypatch, done, done)
    s = session.open_session(_config(repo))
    session.call_claude(s, JobSpec(role, "Do the job.", timeout=1), "m1", "m1-first")
    session.call_claude(s, JobSpec(role, "Do the other job.", timeout=1), "m1", "m1-second")
    [(first, _), (second, _)] = calls
    assert first.startswith(OWNER_MD)
    assert _headings(first) == ROLE_SECTIONS[role]
    for heading in ROLE_SECTIONS[role]:
        assert f"## {heading}\nWhat {heading} says.\n" in first
    assert "The model." not in first and first.endswith("\n\nDo the job.")
    # the same start, so jobs close together share the prompt cache
    assert second.removesuffix("Do the other job.") == first.removesuffix("Do the job.")
    assert not [note for note in s.report.notes if "went without" in note]


def test_a_job_that_is_not_the_leads_gets_no_sections(repo, monkeypatch):
    _lead_docs(repo, monkeypatch)
    calls = _limited_then(monkeypatch, JobResult(ok=True, text="", duration_s=1.0))
    s = session.open_session(_config(repo))
    session.call_claude(s, JobSpec("narrative", "Tell it.", timeout=1), "m1", "narrative")
    assert calls[0][0] == "Tell it."


def test_a_resumed_session_keeps_its_system_prompt_and_one_that_cant_resume_starts_again(
    repo, monkeypatch
):
    """ADR 41 item 2: a system prompt isn't in the session's history, so each run sends it, the
    same text. Lost, the session starts again as a new one would."""
    _lead_docs(repo, monkeypatch)
    lost = JobResult(ok=False, text="No conversation found", duration_s=1.0, num_turns=0)
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    calls = _limited_then(monkeypatch, done, lost, done)
    s = session.open_session(_config(repo))
    job = JobSpec("planner", "The owner's message.", timeout=1, resume="s1")
    session.call_claude(s, job, "m1", "f7:1")
    session.call_claude(s, job, "m1", "f7:2")
    assert calls[0][1] == calls[1][1] == "s1"
    assert calls[0][0] == calls[1][0] and calls[0][0].endswith("The owner's message.")
    assert calls[0][0].startswith(OWNER_MD)
    prompt, resume = calls[2]
    assert resume is None and prompt.startswith(OWNER_MD)
    assert _headings(prompt) == ROLE_SECTIONS["planner"]


def test_a_heading_missing_from_lead_md_is_a_report_note_and_the_job_runs(repo, monkeypatch):
    _lead_docs(repo, monkeypatch, without="Tickets")
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    calls = _limited_then(monkeypatch, done, done)
    s = session.open_session(_config(repo))
    assert session.call_claude(s, _job(), "m1", "m1-01-lead") is done
    assert session.call_claude(s, _job(), "m1", "m1-02-lead") is done
    prompt, _ = calls[0]
    assert prompt.startswith(OWNER_MD) and _headings(prompt) == ["Your own work"]
    assert prompt.endswith("Do the ticket.")
    notes = [note for note in s.report.notes if "went without" in note]
    assert len(notes) == 1  # said once, however many jobs
    assert "lead-ticket" in notes[0] and "Tickets" in notes[0]


def test_an_unrecognised_limit_is_retried_a_few_times_then_fails(repo, monkeypatch):
    unsure = UsageLimited(None, certain=False)
    calls = _limited_then(monkeypatch, unsure, unsure, unsure, unsure)
    s = session.open_session(_config(repo))
    result = session.call_claude(s, _job(), "m1", "m1-01-lead")
    assert not result.ok
    assert len(calls) == 1 + session.UNSURE_LIMIT_RETRIES


def _sleeps(monkeypatch) -> list[float]:
    slept: list[float] = []
    monkeypatch.setattr("time.sleep", slept.append)
    return slept


def test_a_known_limit_without_a_time_retries_every_backoff_min_without_giving_up(
    repo, monkeypatch
):
    """f1: the wait was exponential (15 min, 30, 60 … 5 h), overshooting a 5 h window by hours.
    A refused call costs nothing, so retry at the minimum every time."""
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4, session_id="s1")
    limited = UsageLimited(None, session_id="s1")
    calls = _limited_then(monkeypatch, limited, limited, limited, limited, limited, done)
    slept = _sleeps(monkeypatch)
    s = session.open_session(_config(repo))
    assert session.call_claude(s, _job(), "m1", "m1-01-lead") is done
    assert len(calls) == 6
    assert slept == [s.cfg.backoff_min] * 5


def test_a_dropped_connection_resumes_after_short_waits(repo, monkeypatch):
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4, session_id="s1")
    blip = TransientError("Connection error.", session_id="s1")
    calls = _limited_then(monkeypatch, blip, blip, done)
    slept = _sleeps(monkeypatch)
    s = session.open_session(_config(repo))
    assert session.call_claude(s, _job(), "m1", "m1-01-review") is done
    assert [resume for _, resume in calls] == [None, "s1", "s1"]
    assert slept == list(session.TRANSIENT_WAITS[:2])


def test_a_connection_that_stays_down_fails_the_job(repo, monkeypatch):
    blip = TransientError("Connection error.")
    calls = _limited_then(monkeypatch, *[blip] * (len(session.TRANSIENT_WAITS) + 1))
    _sleeps(monkeypatch)
    s = session.open_session(_config(repo))
    assert not session.call_claude(s, _job(), "m1", "m1-01-review").ok
    assert len(calls) == len(session.TRANSIENT_WAITS) + 1
    assert any("Connection error." in note for note in s.report.notes)


def test_a_live_update_changes_tokens_steps_and_heartbeat_only(repo, monkeypatch):
    s = session.open_session(_config(repo))
    job = session.record_start(s, "m1-01-thing", "m1", "developer", "local-m", log_path="x.jsonl")
    [job_before], [run_before] = _rows(repo, "jobs"), _rows(repo, "runs")
    monkeypatch.setattr(session, "now", lambda: datetime(2030, 1, 1, tzinfo=UTC))
    session.live_update(s, job, TokenTotals(500, 20, 5, 3, peak=400))
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
        return JobResult(ok=True, text="", duration_s=1.0, usage=usage, cost_usd=0.75)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    s = session.open_session(_config(repo))
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
        session.call_claude(
            s, JobSpec(kind, "Do it.", timeout=1), "m1", ticket or kind, ticket=ticket
        )
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


def test_a_job_runs_and_records_the_agent_its_role_resolves_to(repo, monkeypatch):
    """ADR 14 item 3: `[roles]` decides who does a job, and its row says who did."""
    models: list[str] = []

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        models.append(job.model)
        return JobResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    roles = {**ROLES, "review": ("claude-sonnet",), "checkpoint": ("claude-opus",)}
    s = session.open_session(replace(_config(repo), roles=roles))
    for role in ("review", "checkpoint"):
        session.call_claude(s, JobSpec(role, "Do it.", timeout=1), "m1", role)
    assert [j["agent"] for j in _rows(repo, "jobs")] == ["claude-sonnet", "claude-opus"]
    assert models == ["sonnet", "opus"]


def test_a_usage_limit_pause_is_a_refusal_event(repo, monkeypatch):
    resets = session.now() + timedelta(hours=1)
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    _limited_then(monkeypatch, UsageLimited(resets, session_id="s1"), done)
    s = session.open_session(_config(repo))
    session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    [event, wait] = _rows(repo, "usage_events")  # and the runner's wait for it (f3-04)
    assert (event["agent"], event["kind"]) == ("claude-opus", "refusal")
    assert event["resets_at"] == resets.isoformat()
    assert (wait["agent"], wait["kind"]) == ("runner", "wait")


def _readings(five_hour: float, seven_day: float) -> tuple[Reading, ...]:
    resets = datetime(2026, 10, 5, 16, 0, tzinfo=UTC)
    return (Reading("five_hour", five_hour, resets), Reading("seven_day", seven_day, resets))


def test_a_jobs_readings_are_usage_events_and_the_same_readings_twice_change_nothing(
    repo, monkeypatch
):
    """f1-44: Claude's allowance, as each job's stream reports it (ADR 15 item 3)."""
    at = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(session, "now", lambda: at)
    done = JobResult(ok=True, text="", duration_s=1.0, readings=_readings(0.07, 0.79))
    _limited_then(monkeypatch, done, done)
    s = session.open_session(_config(repo))
    for _ in range(2):
        session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    events = _rows(repo, "usage_events")
    assert [(e["agent"], e["kind"], e["window"], e["value"]) for e in events] == [
        ("claude-opus", "reading", "five_hour", 0.07),
        ("claude-opus", "reading", "seven_day", 0.79),
    ]
    assert {e["at"] for e in events} == {at.isoformat()}
    assert {e["resets_at"] for e in events} == {"2026-10-05T16:00:00+00:00"}


def test_a_refusal_names_its_window_and_keeps_the_readings_before_it(repo, monkeypatch):
    resets = session.now() + timedelta(hours=1)
    limit = UsageLimited(resets, "s1", window="five_hour", readings=_readings(1.0, 0.5))
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    _limited_then(monkeypatch, limit, done)
    s = session.open_session(_config(repo))
    session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    events = {(e["kind"], e["window"]): e for e in _rows(repo, "usage_events")}
    assert set(events) == {
        ("refusal", "five_hour"),
        ("reading", "five_hour"),
        ("reading", "seven_day"),
        ("wait", None),  # the runner's wait for the reset (f3-04)
    }
    assert events["refusal", "five_hour"]["resets_at"] == resets.isoformat()
    assert events["reading", "five_hour"]["value"] == 1.0


def test_a_claude_job_past_10_minutes_prints_progress(repo, monkeypatch, capsys):
    ticks = iter(range(0, 10**6, 400))  # every read of the clock is 400 s later
    monkeypatch.setattr(session, "clock", lambda: next(ticks))
    monkeypatch.setattr(session, "POLL_S", 0.01)

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        time.sleep(0.2)
        return JobResult(ok=True, text="Sorted it.\nDetails.", duration_s=1.0, cost_usd=1.5)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    s = session.open_session(_config(repo))
    session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    out = capsys.readouterr().out
    assert "▶ [claude-opus] lead-ticket\n" in out
    assert "… [claude-opus] lead-ticket still running · " in out
    assert "■ [claude-opus] lead-ticket done · " in out and "$1.50" in out
    assert "↳ [claude-opus] Sorted it.\n" in out


def test_a_claude_job_summary_comes_from_its_note(repo, monkeypatch, capsys):
    note = repo / "var" / "escalation.md"

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        note.write_text("\nRequeued with the missing unit.\n")
        return JobResult(ok=True, text="Done, see the note.", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    s = session.open_session(_config(repo))
    session.call_claude(s, _job(), "m1", "m1-01-lead", notes=(repo / "var" / "decision.json", note))
    out = capsys.readouterr().out
    assert "↳ [claude-opus] Requeued with the missing unit.\n" in out


def test_a_usage_limit_pause_prints_the_resume_time(repo, monkeypatch, capsys):
    fixed = datetime(2026, 10, 1, 18, 0).astimezone()
    monkeypatch.setattr(session, "now", lambda: fixed)
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    _limited_then(monkeypatch, UsageLimited(fixed + timedelta(hours=1)), done)
    s = session.open_session(_config(repo))
    session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    out = capsys.readouterr().out
    assert "⏸ [claude-opus] Claude usage limit · resumes 19:01 (in 1 h 01)" in out
    assert "▶ [claude-opus] lead-ticket resumed" in out


# --- the heartbeat thread (f1-49) ---------------------------------------------------------


def _heartbeats(repo: Path, seconds: float, sleep: Callable[[float], None]) -> set[object]:
    """Every heartbeat the run's row shows over ``seconds``, read every 20 ms."""
    seen: set[object] = set()
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        seen |= {r["heartbeat"] for r in _rows(repo, "runs")}
        sleep(0.02)
    return seen


@pytest.fixture
def fast_beat(monkeypatch):
    monkeypatch.setattr(session, "HEARTBEAT_EVERY", 0.05)


def test_the_heartbeat_advances_while_a_claude_job_blocks(repo, monkeypatch, fast_beat):
    # f1-18-probes: the Overview called a runner busy in check-all dead, and the owner stopped it
    seen: set[object] = set()

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        seen.update(_heartbeats(repo, 0.5, time.sleep))
        return JobResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    s = session.open_session(_config(repo))
    session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    session._finish_run(s, "done")
    assert len(seen) >= 3  # the job's start, then two beats at least


def test_the_heartbeat_advances_during_a_usage_limit_pause(repo, monkeypatch, fast_beat):
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    _limited_then(monkeypatch, UsageLimited(None), done)
    real_sleep, seen = time.sleep, set()

    def pause(seconds: float) -> None:
        seen.update(_heartbeats(repo, 0.5, real_sleep))

    monkeypatch.setattr("time.sleep", pause)
    s = session.open_session(_config(repo))
    session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    session._finish_run(s, "done")
    assert len(seen) >= 3  # the job's start, then two beats at least


def test_no_beat_lands_after_the_run_ends(repo, fast_beat):
    s = session.open_session(_config(repo))
    thread = s.heartbeat
    assert thread is not None and thread.is_alive()
    time.sleep(0.2)
    session._finish_run(s, "done")
    assert not thread.is_alive()
    time.sleep(0.2)
    [run] = _rows(repo, "runs")
    assert run["ended"] and run["heartbeat"] == run["ended"]


def test_a_failing_heartbeat_is_noted_once_and_the_run_goes_on(repo, monkeypatch, fast_beat):
    beat = metrics.update_run_heartbeat

    def broken(conn: sqlite3.Connection, run_id: int, at: str) -> None:
        if threading.current_thread() is not threading.main_thread():
            raise sqlite3.OperationalError("disk I/O error")
        beat(conn, run_id, at)

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        time.sleep(0.3)
        return JobResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(metrics, "update_run_heartbeat", broken)
    monkeypatch.setattr(claude, "run_claude", run_claude)
    s = session.open_session(_config(repo))
    assert session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead").ok
    session._finish_run(s, "done")
    notes = [n for n in s.report.notes if "metrics database" in n]
    assert len(notes) == 1 and "disk I/O error" in notes[0]
    [run] = _rows(repo, "runs")
    assert run["verdict"] == "done"


def test_a_session_with_no_command_starts_no_heartbeat(repo, fast_beat):
    before = set(threading.enumerate())
    s = session.open_session(_config(repo), None)
    assert s.heartbeat is None
    assert set(threading.enumerate()) == before


def test_an_interrupted_job_on_main_is_kept_on_its_own_branch(repo, monkeypatch):
    def write_then_crash(job, repo_, timeout, log_path, now, resume=None):
        (repo_ / "coucou" / "fix.py").write_text("FIXED = True\n")
        raise RuntimeError("crash")

    monkeypatch.setattr(claude, "run_claude", write_then_crash)
    s = session.open_session(_config(repo), None)
    review = JobSpec("review", "Review it.", timeout=1)
    with pytest.raises(RuntimeError, match="crash"):
        session.call_claude(s, review, "m1", "m1-review-r1")
    assert _state(repo).in_flight is not None

    s = session.open_session(_config(repo), None)
    assert s.git.current_branch() == "main" and s.git.is_clean()
    assert not (repo / "coucou" / "fix.py").exists()
    kept = git(repo, "show", "--format=%s", "--name-only", "interrupted/review-m1")
    assert "coucou/fix.py" in kept and "(interrupted)" in kept
    assert s.state.in_flight is None
    assert s.state.interrupted == {
        "review:m1-review-r1": {
            "session_id": "",
            "branch": "interrupted/review-m1",
            "agent": "claude-opus",
        }
    }

    calls = _limited_then(monkeypatch, JobResult(ok=True, text="", duration_s=1.0))
    session.call_claude(s, review, "m1", "m1-review-r1")
    [(prompt, resume)] = calls
    assert resume is None  # no session id was known: it starts again, told where its work is
    assert prompt.startswith("Review it.") and "interrupted/review-m1" in prompt
    assert _state(repo).interrupted == {}


def test_a_pause_for_a_limit_or_a_passing_error_shows_on_the_run_until_it_ends(repo, monkeypatch):
    resets = session.now() + timedelta(hours=1)
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    blip = TransientError("Connection error.", session_id="s1")
    _limited_then(monkeypatch, UsageLimited(resets, session_id="s1"), blip, done)
    seen: list[tuple[object, object]] = []
    monkeypatch.setattr("time.sleep", lambda seconds: seen.append(_activity(repo)))
    s = session.open_session(_config(repo))
    before = _activity(repo)
    session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    assert before == ("picking the next ticket", None)
    until = [datetime.fromisoformat(str(at)) for _, at in seen]
    assert until[0] > resets and until[1] > session.now()
    assert [activity for activity, _ in seen] == [
        f"waiting for Claude · m1-01-lead until {at:%H:%M}" for at in until
    ]
    assert _activity(repo) == before  # what the run did before the wait


def test_a_wait_for_a_limit_is_kept_but_not_a_pause_for_a_passing_error(repo, monkeypatch):
    """f3-04: ``waiting_until`` is cleared when the wait ends, so the minutes the line lost
    to Claude's limit are kept as a ``wait`` usage event, from its start to when it resumes."""
    resets = session.now() + timedelta(hours=1)
    done = JobResult(ok=True, text="", duration_s=1.0, num_turns=4)
    blip = TransientError("Connection error.", session_id="s1")
    _limited_then(monkeypatch, UsageLimited(resets, session_id="s1"), blip, done)
    seen: list[tuple[object, object]] = []
    monkeypatch.setattr("time.sleep", lambda seconds: seen.append(_activity(repo)))
    s = session.open_session(_config(repo))
    session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    waits = [e for e in _rows(repo, "usage_events") if e["kind"] == "wait"]
    assert [(e["agent"], e["resets_at"]) for e in waits] == [("runner", seen[0][1])]
    assert str(waits[0]["at"]) < str(seen[0][1])


def test_a_job_starting_keeps_the_runs_activity_for_after_it(repo):
    """The page shows the job while it runs; when it ends, the run still says what it does."""
    s = session.open_session(_config(repo))
    session.set_activity(s, "m1-01-thing")
    session.record_start(s, "m1-01-thing", "m1", "developer", "local-m")
    assert _activity(repo) == ("m1-01-thing", None)


def test_a_claude_jobs_row_shows_its_tokens_and_steps_before_it_ends(repo, monkeypatch):
    """f1-51: Claude jobs showed elapsed time only (f1 D3, amended)."""
    monkeypatch.setattr(session, "POLL_S", 0.01)
    seen: list[dict[str, object]] = []

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        assert job.on_progress is not None
        job.on_progress(Progress(tokens_in=10, tokens_cached=100, tokens_out=5, turns=2))
        deadline = time.monotonic() + 5
        while not (row := _rows(repo, "jobs")[0])["steps"] and time.monotonic() < deadline:
            time.sleep(0.01)
        seen.append(row)
        return JobResult(ok=True, text="", duration_s=1.0, num_turns=3)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    s = session.open_session(_config(repo))
    session.call_claude(s, _job(), "m1", "m1-01-lead", ticket="m1-01-lead")
    [live] = seen
    assert live["outcome"] == "running"
    assert (live["tokens_in"], live["tokens_cached"], live["tokens_out"], live["steps"]) == (
        10,
        100,
        5,
        2,
    )
    [job] = _rows(repo, "jobs")
    assert (job["outcome"], job["steps"]) == ("passed", 3)


@pytest.mark.parametrize(("switch", "reserve"), [("week", True), ("five_hour", False)])
def test_a_run_started_with_the_week_switch_on_is_on_the_reserve(repo, switch, reserve):
    _switch_on(repo, switch, at=session.now())
    session.open_session(_config(repo))
    assert [bool(run["reserve"]) for run in _rows(repo, "runs")] == [reserve]


def test_a_ticket_deleted_from_tasks_leaves_the_queue(repo):
    """f1-30-allowance-forecast, deleted by ADR 15, kept a `ready` row."""
    conn = metrics.open_db(_config(repo).metrics_db)
    project = metrics.upsert_project(conn, repo.name)
    metrics.upsert_ticket(conn, project, "m1-09-gone", state="ready")
    conn.close()
    _add_task(repo, "m1-01-thing")
    session.open_session(_config(repo))
    states = {row["ticket"]: row["state"] for row in _rows(repo, "tickets")}
    assert states == {"m1-09-gone": "removed", "m1-01-thing": "ready"}


def test_a_deleted_tickets_row_leaves_whatever_its_state_but_done(repo):
    """f4-21's `blocked` row, its file deleted, kept "1 blocked now" on the Overview (f6-17);
    a done ticket's row is history and stays."""
    conn = metrics.open_db(_config(repo).metrics_db)
    project = metrics.upsert_project(conn, repo.name)
    for ticket, state in (("m1-07-stuck", "blocked"), ("m1-08-aside", "later")):
        metrics.upsert_ticket(conn, project, ticket, state=state)
    metrics.upsert_ticket(conn, project, "m1-06-shipped", state="done")
    conn.close()
    _add_task(repo, "m1-01-thing")
    session.open_session(_config(repo))
    states = {row["ticket"]: row["state"] for row in _rows(repo, "tickets")}
    assert states == {
        "m1-07-stuck": "removed",
        "m1-08-aside": "removed",
        "m1-06-shipped": "done",
        "m1-01-thing": "ready",
    }


def test_a_ticket_naming_its_milestone_short_sits_on_its_cards_row(repo):
    """F2's ticket said `milestone: f2`: its row was a second F2 card, waiting for a review
    that was done, while the card with the review's sheet showed no tickets (2026-10-22)."""
    docs = repo / ".softfield" / "cards"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "f2-a-readme.md").write_text("# Milestone F2: a readme\n\n> **State:** ready\n")
    path = write_task(repo / ".softfield" / "tasks" / "ready", "f2-01-readme")
    path.write_text(path.read_text().replace("milestone: 1\n", "milestone: f2\n"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a card and its ticket")
    session.open_session(_config(repo))
    keys = {row["id"]: row["key"] for row in _rows(repo, "milestones")}
    tickets = {row["ticket"]: keys[row["milestone_id"]] for row in _rows(repo, "tickets")}
    assert tickets == {"f2-01-readme": "f2-a-readme"}
    assert "f2" not in keys.values()


def test_a_card_whose_doc_is_gone_leaves_the_board(repo):
    """A card merged away or `git rm`ed stayed a seed on the desk (f6-17): its row is
    `removed`. A milestone row that was never a card (no state) is left as it is."""
    docs = repo / ".softfield" / "cards"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "f10-one-queue.md").write_text("# Milestone F10: one queue\n\n> **State:** idea\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a card")
    conn = metrics.open_db(_config(repo).metrics_db)
    project = metrics.upsert_project(conn, repo.name)
    metrics.upsert_milestone(conn, project, "f12-queue-once", title="queue once", state="idea")
    metrics.upsert_milestone(conn, project, "f10", state="idea")  # the doc names it in full
    metrics.upsert_milestone(conn, project, "m1", status="done")
    conn.close()
    session.open_session(_config(repo))
    states = {row["key"]: row["state"] for row in _rows(repo, "milestones")}
    assert states == {
        "f12-queue-once": "removed",
        "f10": "idea",
        "m1": None,
        "f10-one-queue": "idea",
    }


def test_a_ticket_set_aside_is_recorded_as_later(repo):
    """ADR 17 item 3; a later ticket that was ready before leaves the queue too."""
    conn = metrics.open_db(_config(repo).metrics_db)
    project = metrics.upsert_project(conn, repo.name)
    metrics.upsert_ticket(conn, project, "m1-02-aside", state="ready")
    conn.close()
    write_task(repo / ".softfield" / "tasks" / "later", "m1-02-aside")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "aside")
    session.open_session(_config(repo))
    states = {row["ticket"]: row["state"] for row in _rows(repo, "tickets")}
    assert states == {"m1-02-aside": "later"}


def test_an_interrupted_job_whose_branch_is_gone_starts_again(repo, capsys):
    """The owner's first `softfield run` after the split (2026-10-14): state.json said f19-02
    was cut off on task/f19-02-one-live-poll, a branch left in Coucou's repo; the run crashed.
    Now it says so, forgets the job, and the ticket starts again from main."""
    cfg = _config(repo)
    in_flight = {
        "kind": "local", "ticket": "m1-01-thing", "branch": "task/m1-01-thing",
        "agent": "local-qwen", "attempt": 2, "job_id": 1,
        "started": "2026-10-14T07:25:51+01:00",
    }  # fmt: skip
    save_state(State(in_flight=in_flight), cfg.runs_dir / "state.json")
    s = session.open_session(cfg, None)
    assert s.git.current_branch() == "main" and s.git.is_clean()
    assert s.state.in_flight is None and _state(repo).in_flight is None
    assert s.state.timed_out == {}  # it didn't run out of time: it never ran here
    assert (
        "m1-01-thing's branch task/m1-01-thing is gone: it starts again" in capsys.readouterr().out
    )
