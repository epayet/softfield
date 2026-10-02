"""The owner's commands exit 0 when ready, 2 when something needs them, 1 on an error."""

import os

import pytest

from runner import cli, loop, owner
from runner.milestone import RESTART


@pytest.fixture
def in_repo(repo, monkeypatch):
    toml = (cli._repo() / "workflow" / "runner.toml").read_text()
    real_db = '"~/.local/share/software-factory/factory-metrics.sqlite"'
    assert real_db in toml
    test_db = (repo / "var" / "factory-metrics.sqlite").as_posix()
    (repo / "workflow" / "runner.toml").write_text(toml.replace(real_db, f'"{test_db}"'))
    monkeypatch.chdir(repo)
    return repo


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


class Restarted(Exception):
    pass


def test_a_yes_to_the_reserve_survives_the_self_restart_but_not_a_new_command(in_repo, monkeypatch):
    """The owner, 2026-10-01: a yes lasts for the running command only, restarts included."""
    seen: list[bool] = []
    envs: list[dict[str, str]] = []

    def run(cfg, key, base):
        seen.append(loop.RESERVE.yes)
        if len(seen) == 1:
            loop.RESERVE.yes = True  # the owner answered y, then a lead ticket changed runner/
            return RESTART
        return "clean"

    def execve(path, args, env):
        envs.append(dict(env))
        raise Restarted

    monkeypatch.setattr(cli, "run_milestone", run)
    monkeypatch.setattr(os, "execve", execve)
    monkeypatch.setattr(owner, "verdict", lambda repo, k, state, stop, db: (0, "V\n"))
    monkeypatch.setattr(owner, "record_verdict", lambda repo, text: None)
    monkeypatch.delenv(loop.RESERVE_ENV, raising=False)
    monkeypatch.setattr(loop, "RESERVE", loop.ReserveAnswer())
    with pytest.raises(Restarted):
        cli.main(["milestone", "1"])
    # The restarted process: its modules fresh, the environment the restart gave it.
    monkeypatch.setattr(loop, "RESERVE", loop.ReserveAnswer())
    monkeypatch.setenv(loop.RESERVE_ENV, envs[0][loop.RESERVE_ENV])
    assert cli.main(["milestone", "1"]) == 0
    assert loop.RESERVE_ENV not in os.environ  # its children don't inherit the yes
    # The owner's next command, after a Ctrl-C.
    monkeypatch.setattr(loop, "RESERVE", loop.ReserveAnswer())
    assert cli.main(["milestone", "1"]) == 0
    assert seen == [False, True, False]


def test_a_restart_without_a_yes_passes_none_on(in_repo, monkeypatch):
    envs: list[dict[str, str]] = []

    def execve(path, args, env):
        envs.append(dict(env))
        raise Restarted

    monkeypatch.setattr(cli, "run_milestone", lambda cfg, key, base: RESTART)
    monkeypatch.setattr(os, "execve", execve)
    monkeypatch.setattr(loop, "RESERVE", loop.ReserveAnswer())
    with pytest.raises(Restarted):
        cli.main(["milestone", "1"])
    assert loop.RESERVE_ENV not in envs[0]


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
