"""The owner's commands exit 0 when ready, 2 when something needs them, 1 on an error."""

import pytest

from runner import cli, owner


@pytest.fixture
def in_repo(repo, monkeypatch):
    (repo / "workflow" / "runner.toml").write_text(
        (cli._repo() / "workflow" / "runner.toml").read_text()
    )
    monkeypatch.chdir(repo)
    return repo


@pytest.mark.parametrize(("code", "expected"), [(0, 0), (2, 2)])
def test_milestone_exits_with_the_verdicts_code(in_repo, monkeypatch, capsys, code, expected):
    monkeypatch.setattr(cli, "run_milestone", lambda cfg, n, base: "clean")
    monkeypatch.setattr(owner, "verdict", lambda repo, n, state, stop: (code, "VERDICT\n"))
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
    monkeypatch.setattr(owner, "verdict", lambda repo, k, state, stop: (0, "V\n"))
    monkeypatch.setattr(owner, "record_verdict", lambda repo, text: None)
    assert cli.main(["milestone", arg]) == 0
    assert seen == [(key, f"{key}-start")]


def test_a_bad_milestone_name_is_an_error(in_repo, capsys):
    assert cli.main(["milestone", "F 1"]) == 1
    assert "milestone" in capsys.readouterr().err
