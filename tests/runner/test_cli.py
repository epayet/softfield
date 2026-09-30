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
