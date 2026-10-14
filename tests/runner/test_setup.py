import subprocess
from pathlib import Path

import pytest

from runner import cli, config, metrics, setup
from runner.config import load_config
from tests.runner.conftest import git


def _projects(db: Path) -> list[tuple[str, str | None, int]]:
    conn = metrics.open_db(db)
    try:
        return [(p.name, p.repo, p.priority) for p in metrics.projects_in_order(conn)]
    finally:
        conn.close()


def test_init_sets_up_an_empty_folder_as_a_new_project_on_main(tmp_path, machine):
    """ADR 30 item 7: the factory's files, committed on main, the hook on, the project
    registered last in the owner's order."""
    db = tmp_path / "m.sqlite"
    conn = metrics.open_db(db)
    try:
        metrics.upsert_project(conn, "softfield", repo="/r/softfield")
        metrics.set_project_order(conn, ["softfield"])
    finally:
        conn.close()
    folder = tmp_path / "ducks"
    folder.mkdir()
    origin, written = setup.init(folder, db)
    assert origin == "new"
    for rel in (".factory/project.toml", "AGENTS.md", "CLAUDE.md", "opencode.json", ".gitignore"):
        assert rel in written and (folder / rel).is_file()
    assert (folder / ".factory/tasks/ready").is_dir() and (folder / ".factory/cards").is_dir()
    assert 'name = "ducks"' in (folder / ".factory/project.toml").read_text()
    assert 'origin = "new"' in (folder / ".factory/project.toml").read_text()
    assert load_config(folder).project_name == "ducks"  # it loads, caps and timeouts included
    assert git(folder, "branch", "--show-current").strip() == "main"
    assert git(folder, "status", "--porcelain") == ""
    assert git(folder, "config", "core.hooksPath").strip() == ".factory/hooks"
    assert (folder / ".factory/hooks/pre-commit").stat().st_mode & 0o111
    assert _projects(db) == [("softfield", "/r/softfield", 1), ("ducks", str(folder), 2)]


def test_init_keeps_what_an_existing_repo_has_and_says_existing(tmp_path):
    folder = tmp_path / "shop"
    folder.mkdir()
    git(folder, "init", "-q", "-b", "main")
    git(folder, "config", "user.email", "t@example.com")
    git(folder, "config", "user.name", "Test")
    (folder / "AGENTS.md").write_text("our own rules\n")
    (folder / "app.py").write_text("X = 1\n")
    (folder / ".gitignore").write_text("node_modules/\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "init")
    origin, written = setup.init(folder, tmp_path / "m.sqlite")
    assert origin == "existing" and "AGENTS.md" not in written
    assert (folder / "AGENTS.md").read_text() == "our own rules\n"
    assert (folder / ".gitignore").read_text() == "node_modules/\n.factory/var/\nBLOCKED.md\n"
    assert git(folder, "log", "--format=%an", "-1").strip() == "Softfield runner"


def test_init_after_a_fresh_git_init_on_master_works_on_main(tmp_path):
    folder = tmp_path / "fresh"
    folder.mkdir()
    git(folder, "init", "-q", "-b", "master")
    assert setup.init(folder, tmp_path / "m.sqlite")[0] == "new"
    assert git(folder, "branch", "--show-current").strip() == "main"


@pytest.mark.parametrize("why", ["a project already", "check out main", "commit or stash"])
def test_init_refuses_what_it_would_get_wrong(tmp_path, why):
    folder = tmp_path / "busy"
    folder.mkdir()
    git(folder, "init", "-q", "-b", "main")
    git(folder, "config", "user.email", "t@example.com")
    git(folder, "config", "user.name", "Test")
    (folder / "a.py").write_text("A = 1\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "init")
    if why == "a project already":
        setup.init(folder, tmp_path / "m.sqlite")
    elif why == "check out main":
        git(folder, "checkout", "-q", "-b", "feature")
    else:
        (folder / "a.py").write_text("A = 2\n")
    with pytest.raises(setup.SetupError, match=why):
        setup.init(folder, tmp_path / "m.sqlite")


def test_doctor_says_what_the_web_still_needs_then_passes(tmp_path, machine):
    """ADR 30 item 8, with the owner's ADR 00 accepted in the setup session."""
    db = tmp_path / "m.sqlite"
    folder = tmp_path / "ducks"
    folder.mkdir()
    setup.init(folder, db)
    missing = [f.what for f in setup.doctor(folder, db, run_checks=False) if not f.ok]
    assert missing == [
        "a one-line description in [project]",
        "the idea in .factory/seed.md",
        "ADR 00 accepted: none in .factory/adr/",
        "a first card in .factory/cards/",
    ]
    toml = folder / ".factory/project.toml"
    toml.write_text(toml.read_text().replace('description = ""', 'description = "Ducks."'))
    (folder / ".factory/seed.md").write_text("# Seed\n\nA duck counter.\n")
    adr = "# ADR 00: Initial decisions\n\n- **Status:** Accepted (by the owner, 2026-10-14)\n"
    (folder / ".factory/adr/00-initial.md").write_text(adr)
    (folder / ".factory/cards/m1-count.md").write_text("# Milestone M1: Count\n")
    assert [f.what for f in setup.doctor(folder, db, run_checks=False) if not f.ok] == [
        "everything committed, on main"
    ]
    git(folder, "add", "-A")
    git(
        folder,
        "-c",
        "user.name=T",
        "-c",
        "user.email=t@e",
        "commit",
        "-q",
        "--no-verify",
        "-m",
        "x",
    )
    assert all(f.ok for f in setup.doctor(folder, db, run_checks=False))


def test_the_setup_session_reads_the_shared_bootstrap():
    command = setup.claude_command(Path("/r/ducks"), "new")
    assert command[:3] == ["claude", "--add-dir", str(config.HOME / "docs")]
    assert str(setup.bootstrap()) in command[-1] and "idea" in command[-1]
    assert (Path(setup.__file__).parents[1] / "docs" / "bootstrap.md").is_file()


def test_the_units_run_softfield_with_the_installers_path(tmp_path):
    """ADR 30 item 5: a service doesn't get the shell's PATH, and the runner needs claude,
    opencode, uv and git from it."""
    written = setup.install_units(tmp_path, Path("/home/me"), path="/home/me/.local/bin:/usr/bin")
    assert sorted(p.name for p in written) == [
        "softfield-dashboard.service",
        "softfield-runner.service",
    ]
    runner = (tmp_path / "softfield-runner.service").read_text()
    assert "ExecStart=" in runner and runner.split("ExecStart=")[1].split("\n")[0].endswith(" run")
    assert "Environment=PATH=/home/me/.local/bin:/usr/bin" in runner
    assert "Restart=on-failure" in runner and "WantedBy=default.target" in runner
    assert "dashboard --lan" in (tmp_path / "softfield-dashboard.service").read_text()


def test_softfield_init_without_claude_from_the_folder(tmp_path, monkeypatch, capsys):
    machine = tmp_path / "factory.toml"
    machine.write_text(f'[metrics]\ndb = "{tmp_path / "m.sqlite"}"\n')
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    folder = tmp_path / "ducks"
    folder.mkdir()
    monkeypatch.chdir(folder)
    assert cli.main(["init", "--no-claude"]) == 0
    assert "ducks: set up as a new project" in capsys.readouterr().out
    assert _projects(tmp_path / "m.sqlite") == [("ducks", str(folder), 1)]
    assert subprocess.run(["git", "status", "--porcelain"], cwd=folder, capture_output=True,
                          text=True).stdout == ""  # fmt: skip
