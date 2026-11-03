"""The owner's commands exit 0 when ready, 2 when something needs them, 1 on an error."""

import os
import re
import sys
from datetime import UTC, datetime, timedelta

import pytest

from runner import cli, loop, metrics, owner, procs
from runner.config import load_config
from runner.milestone import RESTART
from runner.report import SessionReport
from runner.state import load_state, save_state
from tests.runner.conftest import git, write_task


@pytest.fixture
def in_repo(repo, monkeypatch, machine):
    toml = (cli._repo() / ".softfield" / "project.toml").read_text()
    test_db = (repo / "var" / "factory-metrics.sqlite").as_posix()
    metrics_db = f'\n[metrics]\ndb = "{test_db}"\n'  # over the machine's real one
    # the project is its folder's name
    toml = re.sub(r'^name = ".*"\n', "", toml, count=1, flags=re.M)
    (repo / ".softfield" / "project.toml").write_text(toml + metrics_db)
    monkeypatch.chdir(repo)
    return repo


def test_softfield_lead_starts_claude_and_passes_its_arguments_on(in_repo, monkeypatch):
    """ADR 41 item 3, through `main`: it was parsed and then did nothing (f127 review, F2)."""

    class Started(Exception):
        pass

    seen = []

    def execvp(file, args):
        seen.append(args)
        raise Started

    monkeypatch.setattr(os, "execvp", execvp)
    with pytest.raises(Started):
        cli.main(["lead", "--", "--model", "opus"])
    assert seen[0][0] == "claude" and seen[0][-2:] == ["--model", "opus"]
    assert "--append-system-prompt" in seen[0]


@pytest.mark.parametrize(("code", "expected"), [(0, 0), (2, 2)])
def test_milestone_exits_with_the_verdicts_code(in_repo, monkeypatch, capsys, code, expected):
    monkeypatch.setattr(cli, "run_milestone", lambda cfg, n, base: "clean")
    monkeypatch.setattr(owner, "verdict", lambda repo, n, state, stop, db: (code, "VERDICT\n"))
    monkeypatch.setattr(owner, "record_verdict", lambda repo, text: None)
    assert cli.main(["milestone", "1"]) == expected
    assert capsys.readouterr().out.endswith("VERDICT\n")


def test_an_owner_command_that_refuses_exits_1(in_repo, capsys):
    assert cli.main(["accept", "99"]) == 1
    assert "ADR 99 not found" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv", [["milestone", "bugs"], ["signoff", "bugs"], ["review", "--milestone", "bugs"]]
)
def test_the_milestone_commands_refuse_bugs(in_repo, monkeypatch, capsys, argv):
    """ADR 19 item 2: bug tickets run under `runner run`, with no plan, review or sign-off."""
    for name in ("run_milestone", "review_milestone"):
        monkeypatch.setattr(cli, name, lambda *a: pytest.fail("a milestone command ran"))
    monkeypatch.setattr(owner, "signoff", lambda *a, **k: pytest.fail("bugs signed off"))
    assert cli.main(argv) == 1
    assert "bugs is no milestone: its tickets run under `runner run`" in capsys.readouterr().err


@pytest.mark.parametrize(("arg", "key"), [("4", "m4"), ("f1", "f1")])
def test_milestone_takes_a_number_or_a_key(in_repo, monkeypatch, arg, key):
    seen: list[tuple[str, str]] = []

    def run(cfg, key, base):
        seen.append((key, base))
        return "clean"

    monkeypatch.setattr(cli, "run_milestone", run)
    monkeypatch.setattr(owner, "verdict", lambda repo, k, state, stop, db: (0, "V\n"))
    monkeypatch.setattr(owner, "record_verdict", lambda repo, text: None)
    assert cli.main(["milestone", arg]) == 0
    assert seen == [(key, f"{key}-start")]


def test_milestone_resolves_its_rerun_items_before_it_runs(in_repo, monkeypatch):
    seen: list[tuple[str, str, object]] = []

    def run(cfg, key, base):
        seen.append(("run", key, None))
        return "clean"

    def rerun_started(repo, key, db):
        seen.append(("rerun", key, db))

    monkeypatch.setattr(cli, "run_milestone", run)
    monkeypatch.setattr(owner, "rerun_started", rerun_started)
    monkeypatch.setattr(owner, "verdict", lambda repo, k, state, stop, db: (0, "V\n"))
    monkeypatch.setattr(owner, "record_verdict", lambda repo, text: None)
    assert cli.main(["milestone", "f1"]) == 0
    db = in_repo / "var" / "factory-metrics.sqlite"
    assert seen == [("rerun", "f1", db), ("run", "f1", None)]


class Restarted(Exception):
    pass


def test_a_restart_hands_no_reserve_answer_on_the_switches_outlive_it(in_repo, monkeypatch):
    """ADR 22 item 4: the switches are in state.json, so a restart needs no environment for
    them, and nothing it starts inherits one."""
    envs: list[dict[str, str]] = []
    seen: list[bool] = []
    state_path = in_repo / ".softfield" / "var" / "runs" / "state.json"

    def run(cfg, key, base):
        seen.append(loop.switch_on(load_state(state_path), "week", loop.now()))
        if len(seen) == 1:
            state = load_state(state_path)
            state.switches["week"] = loop.now().isoformat()  # the owner turned it on
            save_state(state, state_path)
            return RESTART
        return "clean"

    def execve(path, args, env):
        envs.append(dict(env))
        raise Restarted

    monkeypatch.setattr(cli, "run_milestone", run)
    monkeypatch.setattr(os, "execve", execve)
    monkeypatch.setattr(owner, "verdict", lambda repo, k, state, stop, db: (0, "V\n"))
    monkeypatch.setattr(owner, "record_verdict", lambda repo, text: None)
    with pytest.raises(Restarted):
        cli.main(["milestone", "1"])
    assert not [name for name in envs[0] if name.startswith("COUCOU_RUNNER_") and "YES" in name]
    monkeypatch.setenv(cli.RESTARTED_ENV, envs[0][cli.RESTARTED_ENV])
    assert cli.main(["milestone", "1"]) == 0  # the restarted process
    assert cli.main(["milestone", "1"]) == 0  # the owner's next command
    assert seen == [False, True, True]


def test_runner_run_restarts_itself_after_a_runner_change(in_repo, monkeypatch):
    """2026-10-03: `runner run`, the standing command (ADR 17), stopped for good after f4-01
    changed runner/; only `runner milestone` restarted itself."""
    envs: list[dict[str, str]] = []
    argvs: list[list[str]] = []

    def execve(path, args, env):
        argvs.append(list(args))
        envs.append(dict(env))
        raise Restarted

    def run_session(cfg, *, once, dry_run, escalate):
        return SessionReport(started=datetime.now(UTC), restart=True)

    monkeypatch.setattr(cli, "run_session", run_session)
    monkeypatch.setattr(os, "execve", execve)
    monkeypatch.setattr(sys, "argv", ["runner", "run"])
    with pytest.raises(Restarted):
        cli.main(["run", "--here"])
    assert argvs[0][-1] == "run"
    assert "-P" in argvs[0]  # 2026-10-29: run from the repo, its work tree's code shadowed live's
    assert envs[0][cli.RESTARTED_ENV] == "1"


def test_runner_run_without_a_runner_change_just_ends(in_repo, monkeypatch):
    monkeypatch.setattr(
        cli, "run_session", lambda cfg, **kw: SessionReport(started=datetime.now(UTC))
    )
    monkeypatch.setattr(os, "execve", lambda *a: pytest.fail("restarted"))
    assert cli.main(["run", "--here"]) == 0


@pytest.mark.parametrize("argv", [["run", "--here"], ["run"]])
def test_runner_run_sweeps_what_dead_runners_left_in_tmp(in_repo, monkeypatch, argv):
    """f175 D3: a runner killed by a reboot or a SIGKILL never removed its temp folders."""
    swept: list[int] = []
    monkeypatch.setattr(procs, "sweep_tmp", lambda: swept.append(1))
    monkeypatch.setattr(cli, "_project_configs", lambda: [])
    monkeypatch.setattr(
        cli, "run_session", lambda cfg, **kw: SessionReport(started=datetime.now(UTC))
    )
    cli.main(argv)
    assert swept == [1]


def test_runner_run_goes_on_after_an_idle_session_ended_at_midnight(in_repo, monkeypatch):
    """F101 D3: the idle run closed its session to report the day; the command stays up."""
    sessions = [
        SessionReport(started=datetime.now(UTC), idle=True),
        SessionReport(started=datetime.now(UTC)),
    ]
    monkeypatch.setattr(cli, "run_session", lambda cfg, **kw: sessions.pop(0))
    monkeypatch.setattr(os, "execve", lambda *a: pytest.fail("restarted"))
    assert cli.main(["run", "--here"]) == 0
    assert sessions == []


def test_runner_run_reviews_a_finished_milestone_then_goes_on(in_repo, monkeypatch, capsys):
    """f4-20: F9's last ticket merges while F10 still has tickets. The run reviews F9 as
    `runner milestone` would, records its verdict, then runs F10's next ticket."""
    from tests.runner.test_loop import _config, _merge_any, _two_milestones

    _two_milestones(in_repo)
    cfg = _config(in_repo)
    events: list[str] = []
    ran: list[str] = []
    merge = _merge_any(in_repo, ran)

    def run_task(s, task):
        events.append(task.id)
        return merge(s, task)

    def review(cfg_, key):
        events.append(f"review {key}")
        state = load_state(cfg_.runs_dir / "state.json")
        state.review_stop[key] = "clean"  # as review_milestone records its stop
        save_state(state, cfg_.runs_dir / "state.json")
        return "clean"

    record = owner.record_verdict

    def record_verdict(repo, text):
        events.append("verdict")
        return record(repo, text)

    monkeypatch.setattr(cli, "load_config", lambda repo: cfg)
    monkeypatch.setattr(loop, "fresh_reading", lambda s: None)
    monkeypatch.setattr(loop, "run_task", run_task)
    monkeypatch.setattr(cli, "run_due_review", review)
    monkeypatch.setattr(owner, "record_verdict", record_verdict)
    monkeypatch.setattr(os, "execve", lambda *a: pytest.fail("restarted"))
    assert cli.main(["run", "--here"]) == 0
    assert events == [
        "f9-02-last", "review f9", "verdict", "f10-01-next", "review f10", "verdict"
    ]  # fmt: skip
    assert "✅ READY FOR SIGN-OFF" in capsys.readouterr().out
    reports = sorted((in_repo / ".softfield" / "sessions").glob("*.md"))
    assert any("## Verdict" in r.read_text() for r in reports)
    assert git(in_repo, "status", "--porcelain") == ""


def test_a_review_that_changes_the_runner_restarts_runner_run(in_repo, monkeypatch):
    from tests.runner.test_loop import _config

    reviews = iter(["f9", None])
    monkeypatch.setattr(cli, "load_config", lambda repo: _config(in_repo))

    def run_session(cfg, *, once, dry_run, escalate):
        return SessionReport(started=datetime.now(UTC), review=next(reviews))

    monkeypatch.setattr(cli, "run_session", run_session)
    monkeypatch.setattr(cli, "run_due_review", lambda cfg, key: RESTART)
    monkeypatch.setattr(owner, "verdict", lambda *a, **kw: pytest.fail("a verdict mid-review"))
    monkeypatch.setattr(os, "execve", lambda *a: (_ for _ in ()).throw(Restarted()))
    monkeypatch.setattr(sys, "argv", ["runner", "run"])
    with pytest.raises(Restarted):
        cli.main(["run", "--here"])


def test_a_ctrl_c_or_a_crash_ends_the_commands_runs(in_repo, monkeypatch):
    """f2-03: a Ctrl-C left run 20261002-055804 alive and on the reserve."""
    ended: list[str] = []
    monkeypatch.setattr(loop, "end_open_runs", lambda: ended.append("ended"))

    def ctrl_c(cfg, key, base):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "run_milestone", ctrl_c)
    with pytest.raises(KeyboardInterrupt):
        cli.main(["milestone", "1"])
    assert ended == ["ended"]
    monkeypatch.setattr(cli, "run_session", lambda cfg, **kw: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        cli.main(["run", "--here"])
    assert ended == ["ended", "ended"]


def test_runner_pause_and_resume_write_the_dashboards_requests(in_repo, monkeypatch, capsys):
    """f5-18: the console's pause goes by the request, as `runner reserve` does; with no run
    live, the command applies it at once, so the next run starts paused."""
    at = datetime(2026, 10, 7, 21, 30, tzinfo=UTC)
    monkeypatch.setattr(loop, "now", lambda: at)
    state_path = in_repo / ".softfield" / "var" / "runs" / "state.json"
    assert cli.main(["pause"]) == 0
    assert load_state(state_path).owner_pause == at.isoformat()
    assert "pause: paused: the runner finishes its job, then holds" in capsys.readouterr().out
    assert cli.main(["resume"]) == 0
    assert load_state(state_path).owner_pause is None
    conn = metrics.open_db(in_repo / "var" / "factory-metrics.sqlite")
    try:
        rows = conn.execute("SELECT kind, subject, value, done FROM owner_requests ORDER BY id")
        assert [tuple(r) for r in rows] == [
            ("pause", None, None, at.isoformat()),
            ("resume", None, None, at.isoformat()),
        ]
    finally:
        conn.close()


def test_runner_pause_during_a_live_run_leaves_it_to_the_run(in_repo, monkeypatch, capsys):
    at = datetime(2026, 10, 7, 21, 30, tzinfo=UTC)
    monkeypatch.setattr(loop, "now", lambda: at)
    conn = metrics.open_db(in_repo / "var" / "factory-metrics.sqlite")
    project = metrics.upsert_project(conn, in_repo.name)
    beat = (at - timedelta(seconds=30)).isoformat()
    metrics.upsert_run(conn, project, "20261007-212900", started=beat, heartbeat=beat)
    conn.close()
    assert cli.main(["pause"]) == 0
    assert load_state(in_repo / ".softfield" / "var" / "runs" / "state.json").owner_pause is None
    assert "a run is live: it pauses after the job it is on" in capsys.readouterr().out


@pytest.mark.parametrize(("argv", "score"), [(["--score", "7"], 7), ([], None)])
def test_signoff_passes_the_owners_score_on(in_repo, monkeypatch, argv, score):
    seen: list[object] = []
    monkeypatch.setattr(
        owner, "signoff", lambda repo, key, today, force, db, score: seen.append((key, score))
    )
    assert cli.main(["signoff", "f1", *argv]) == 0
    assert seen == [("f1", score)]


def test_signoff_refuses_a_score_of_11(in_repo, capsys):
    assert cli.main(["signoff", "f1", "--score", "11"]) == 1
    assert "1 to 10" in capsys.readouterr().err


def _later(repo, *ids):
    for task_id in ids:
        write_task(repo / ".softfield" / "tasks" / "later", task_id)
    git(repo, "add", ".softfield/tasks")
    git(repo, "commit", "-q", "-m", "set aside")
    return git(repo, "rev-parse", "HEAD")


def test_queue_puts_a_later_ticket_back_in_ready_and_commits(in_repo, capsys):
    """ADR 17 item 3: a unique prefix will do; the commit holds the move alone."""
    _later(in_repo, "m4-12-send-recovers", "f3-01-other")
    assert cli.main(["queue", "m4-12"]) == 0
    assert (in_repo / ".softfield" / "tasks" / "ready" / "m4-12-send-recovers.md").is_file()
    assert not (in_repo / ".softfield" / "tasks" / "later" / "m4-12-send-recovers.md").exists()
    assert git(in_repo, "log", "-1", "--format=%s").strip() == (
        "queue m4-12-send-recovers (by the owner)"
    )
    changed = git(in_repo, "show", "--name-only", "--no-renames", "--format=", "HEAD").split()
    assert sorted(changed) == [
        ".softfield/tasks/later/m4-12-send-recovers.md",
        ".softfield/tasks/ready/m4-12-send-recovers.md",
    ]
    assert ".softfield/project.toml" in git(in_repo, "status", "--porcelain")  # left alone
    assert "m4-12-send-recovers" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("arg", "shown"), [("m9", ["m4-12-a", "m4-13-b"]), ("m4-1", ["m4-12-a", "m4-13-b"])]
)
def test_queue_with_an_unknown_or_ambiguous_id_shows_the_choices(in_repo, capsys, arg, shown):
    head = _later(in_repo, "m4-12-a", "m4-13-b")
    assert cli.main(["queue", arg]) == 1
    err = capsys.readouterr().err
    assert all(choice in err for choice in shown)
    assert git(in_repo, "rev-parse", "HEAD") == head
    assert sorted(p.name for p in (in_repo / ".softfield" / "tasks" / "later").glob("*.md")) == [
        "m4-12-a.md",
        "m4-13-b.md",
    ]


def test_queue_refuses_a_ticket_that_isnt_in_later(in_repo, capsys):
    write_task(in_repo / ".softfield" / "tasks" / "ready", "m4-14-ready")
    git(in_repo, "add", ".softfield/tasks")
    git(in_repo, "commit", "-q", "-m", "ready")
    head = git(in_repo, "rev-parse", "HEAD")
    assert cli.main(["queue", "m4-14"]) == 1
    assert ".softfield/tasks/ready/" in capsys.readouterr().err
    assert git(in_repo, "rev-parse", "HEAD") == head


@pytest.mark.parametrize(
    ("age", "refused"), [(timedelta(seconds=30), True), (timedelta(minutes=5), False)]
)
def test_queue_refuses_while_a_run_is_live(in_repo, capsys, age, refused):
    """A heartbeat under 2 minutes is a live run; an older one is a dead one."""
    head = _later(in_repo, "m4-12-a")
    conn = metrics.open_db(in_repo / "var" / "factory-metrics.sqlite")
    project = metrics.upsert_project(conn, in_repo.name)
    beat = (datetime.now(UTC) - age).isoformat()
    metrics.upsert_run(
        conn, project, "20261003-120000", command="run", started=beat, heartbeat=beat
    )
    conn.close()
    assert cli.main(["queue", "m4-12"]) == (1 if refused else 0)
    if refused:
        assert "running" in capsys.readouterr().err
        assert git(in_repo, "rev-parse", "HEAD") == head
    else:
        assert (in_repo / ".softfield" / "tasks" / "ready" / "m4-12-a.md").is_file()


def test_a_bad_milestone_name_is_an_error(in_repo, capsys):
    assert cli.main(["milestone", "F 1"]) == 1
    assert "milestone" in capsys.readouterr().err


def test_backfill_writes_to_the_db_given(in_repo, tmp_path, capsys):
    db = tmp_path / "elsewhere.sqlite"
    assert cli.main(["backfill", "--db", str(db)]) == 0
    assert db.is_file()
    assert not (in_repo / "var" / "factory-metrics.sqlite").exists()
    assert "Written" in capsys.readouterr().out


def test_backfill_defaults_to_the_configured_db(in_repo):
    assert cli.main(["backfill"]) == 0
    assert (in_repo / "var" / "factory-metrics.sqlite").is_file()


def test_ratings_replay_twice_gives_the_same_ratings(in_repo, capsys):
    db = in_repo / "var" / "factory-metrics.sqlite"
    conn = metrics.open_db(db)
    project = metrics.upsert_project(conn, in_repo.name)
    run = metrics.upsert_run(conn, project, "run-1")
    for n, (outcome, merged_by) in enumerate([("passed", "x"), ("failed", "claude-opus")]):
        ticket = f"m{n + 1}-01-thing"
        ticket_id = metrics.upsert_ticket(
            conn,
            project,
            ticket,
            milestone_id=metrics.upsert_milestone(conn, project, f"m{n + 1}"),
            difficulty=4,
            merged_by=merged_by,
        )
        job = metrics.start_job(
            conn,
            run,
            ticket_id=ticket_id,
            milestone_id=None,
            role="developer",
            agent="local-qwen3.6-35b-a3b",
            attempt=1,
            started=f"2026-0{n + 1}-01T10:00:00+00:00",
        )
        metrics.finish_job(conn, job, ended=f"2026-0{n + 1}-01T11:00:00+00:00", outcome=outcome)
        start = loop.starting_ratings(load_config(in_repo))
        loop.rate_ticket(conn, project, ticket, start, datetime(2026, n + 1, 2, tzinfo=UTC))
    for k in range(2):  # the old rules: a penalty per finding on m1-01's code
        metrics.add_rating_change(
            conn,
            "local-qwen3.6-35b-a3b",
            "coding",
            2.0,
            1.0,
            at=f"2026-03-0{k + 1}T10:00:00+00:00",
            ticket_id=metrics.upsert_ticket(conn, project, "m1-01-thing"),
            result=f"finding F{k}",
        )
    conn.close()

    assert cli.main(["ratings", "--replay"]) == 0
    first = capsys.readouterr().out
    assert cli.main(["ratings", "--replay"]) == 0
    second = capsys.readouterr().out
    assert first.split("\n\n")[1] == second.split("\n\n")[1]  # the same standings
    assert "Replayed under ADR 24" in first
    assert "→" in first and "→" not in second  # the second wrote nothing
    conn = metrics.open_db(db)
    replayed = conn.execute(
        "SELECT count(*) FROM rating_changes WHERE result LIKE 'replay ADR 24%'"
    ).fetchone()[0]
    conn.close()
    assert replayed > 0


@pytest.fixture
def served(in_repo, monkeypatch) -> list[dict[str, object]]:
    """`runner dashboard` with uvicorn faked: what it would have served, on which host."""
    from factory_dashboard import app

    metrics.open_db(in_repo / "var" / "factory-metrics.sqlite").close()
    seen: list[dict[str, object]] = []
    monkeypatch.setattr(
        app, "serve", lambda db, project, port, host: seen.append({"host": host, "port": port})
    )
    return seen


def test_dashboard_lan_serves_on_the_home_network_address_and_prints_it(
    served, monkeypatch, capsys
):
    """f5-03: the owner typed `--host <their LAN IP>` to reach the dashboard from the phone."""
    monkeypatch.setattr(cli, "_lan_address", lambda: "192.168.1.42")
    assert cli.main(["dashboard", "--lan"]) == 0
    assert served == [{"host": "192.168.1.42", "port": 8765}]
    assert "http://192.168.1.42:8765/" in capsys.readouterr().out


def test_dashboard_stays_on_loopback_without_lan(served, monkeypatch):
    monkeypatch.setattr(cli, "_lan_address", lambda: pytest.fail("looked for the LAN address"))
    assert cli.main(["dashboard"]) == 0
    assert cli.main(["dashboard", "--host", "10.0.0.5"]) == 0
    assert served == [{"host": "127.0.0.1", "port": 8765}, {"host": "10.0.0.5", "port": 8765}]


def test_dashboard_refuses_lan_and_host_together(served, capsys):
    with pytest.raises(SystemExit) as exit_:
        cli.main(["dashboard", "--lan", "--host", "10.0.0.5"])
    assert exit_.value.code == 2
    assert "--lan or --host, not both" in capsys.readouterr().err
    assert served == []


class _FakeUdp:
    """A UDP socket: `connect` only picks the route, so no packet may leave."""

    def __init__(self, family, kind, fail=False):
        import socket

        assert (family, kind) == (socket.AF_INET, socket.SOCK_DGRAM)
        self.fail = fail
        self.connected: list[tuple[str, int]] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def connect(self, address):
        if self.fail:
            raise OSError("Network is unreachable")
        self.connected.append(address)

    def getsockname(self):
        return ("192.168.1.42", 54321)


def test_lan_address_is_the_source_of_a_udp_route_that_sends_nothing(monkeypatch):
    import socket

    made: list[_FakeUdp] = []

    def make(family, kind):
        made.append(_FakeUdp(family, kind))
        return made[-1]

    monkeypatch.setattr(socket, "socket", make)
    assert cli._lan_address() == "192.168.1.42"
    assert len(made[0].connected) == 1  # and _FakeUdp has no send: nothing was sent


def test_dashboard_lan_without_a_network_says_so(served, monkeypatch, capsys):
    import socket

    monkeypatch.setattr(socket, "socket", lambda f, k: _FakeUdp(f, k, fail=True))
    assert cli.main(["dashboard", "--lan"]) == 1
    assert "no home-network address" in capsys.readouterr().err
    assert served == []


def _fake_subprocess(monkeypatch) -> list[list[str]]:
    import subprocess

    ran: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        ran.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="answer\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return ran


def test_copilot_review_runs_read_only(in_repo, monkeypatch, capsys):
    ran = _fake_subprocess(monkeypatch)
    assert cli.main(["copilot-review", "--model", "gpt-5-mini", "Review runner/loop.py"]) == 0
    assert ran[0][:2] == ["copilot", "--prompt=Review runner/loop.py"]
    assert "--deny-tool" in ran[0]
    assert "answer" in capsys.readouterr().out


def test_copilot_help_is_the_only_other_copilot_call(in_repo, monkeypatch):
    ran = _fake_subprocess(monkeypatch)
    assert cli.main(["copilot-review", "--copilot-help"]) == 0
    assert ran == [["copilot", "--help"]]


def test_github_get_refuses_a_write(in_repo, monkeypatch, capsys):
    ran = _fake_subprocess(monkeypatch)
    assert cli.main(["github-get", "/repos/x/y -X DELETE"]) == 1
    assert ran == []
    assert cli.main(["github-get", "/user"]) == 0
    assert ran == [["gh", "api", "--method", "GET", "/user"]]


def test_check_tickets_says_what_approve_would_refuse(in_repo, capsys):
    """The planner's check of its drafts (2026-10-12): the same problems Approve finds, read
    from the files, changing nothing."""
    good = write_task(in_repo / ".softfield" / "tasks" / "later", "m4-12-a")
    bad = write_task(in_repo / ".softfield" / "tasks" / "later", "m4-13-b")
    bad.write_text(
        bad.read_text().replace("### Context\n", "### Context\nRead `templates/gone.html`.\n")
    )
    before = git(in_repo, "status", "--porcelain")
    assert cli.main(["check-tickets", good.relative_to(in_repo).as_posix()]) == 0
    assert "tickets OK" in capsys.readouterr().out
    assert cli.main(["check-tickets"]) == 1  # every ticket in .softfield/tasks/later/
    out = capsys.readouterr().out
    assert "m4-13-b: referenced path does not exist: templates/gone.html" in out
    assert "m4-12-a" not in out
    assert cli.main(["check-tickets", ".softfield/tasks/later/none.md"]) == 1
    assert git(in_repo, "status", "--porcelain") == before


def test_softfield_alone_is_a_guide_not_a_run(tmp_path, monkeypatch, capsys):
    """The owner, 2026-10-14: a bare `softfield` says what runs and what to type; it starts
    nothing."""
    db = tmp_path / "m.sqlite"
    machine = tmp_path / "factory.toml"
    machine.write_text(f'[metrics]\ndb = "{db}"\n')
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("runner.loop.run_projects", lambda *a, **k: pytest.fail("it ran"))
    assert cli.main([]) == 0
    out = capsys.readouterr().out
    assert "No project yet" in out and "softfield run " in out and "softfield init" in out
    conn = metrics.open_db(db)
    try:
        metrics.upsert_project(conn, "ducks", repo="/r/ducks")
        metrics.set_project_paused(conn, "ducks", metrics.SETTING_UP)
    finally:
        conn.close()
    assert cli.main([]) == 0
    out = capsys.readouterr().out
    assert "Runner: not running" in out and "1. ducks  /r/ducks  (setting up)" in out
