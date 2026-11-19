import json
import subprocess
from datetime import date
from pathlib import Path

import pytest

from runner import cli, config, metrics, owner, setup
from runner.config import load_config
from tests.runner.conftest import MACHINE, git


def _projects(db: Path) -> list[tuple[str, str | None, int]]:
    conn = metrics.open_db(db)
    try:
        return [(p.name, p.repo, p.priority) for p in metrics.projects_in_order(conn)]
    finally:
        conn.close()


def test_init_sets_up_an_empty_folder_as_a_new_project_on_main(tmp_path, machine):
    """ADR 30 item 7: the factory's files, committed on main, the hook on, and no row for the
    project: `softfield create` adds it (F236 D1)."""
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
    for rel in (".softfield/project.toml", ".softfield/README.md", ".softfield/.gitignore"):
        assert rel in written and (folder / rel).is_file()
    for rel in ("AGENTS.md", "CLAUDE.md", "opencode.json", ".gitignore", "docs"):  # ADR 41 item 1
        assert not (folder / rel).exists()
    (folder / ".softfield/var").mkdir()
    (folder / ".softfield/var/x").write_text("x")
    (folder / "BLOCKED.md").write_text("x")
    assert git(folder, "status", "--porcelain") == ""  # neither shows in git
    (folder / ".softfield/var/x").unlink()
    (folder / ".softfield/var").rmdir()
    (folder / "BLOCKED.md").unlink()
    assert (folder / ".softfield/tasks/ready").is_dir() and (folder / ".softfield/cards").is_dir()
    assert 'name = "ducks"' in (folder / ".softfield/project.toml").read_text()
    assert 'origin = "new"' in (folder / ".softfield/project.toml").read_text()
    assert load_config(folder).project_name == "ducks"  # it loads, caps and timeouts included
    assert git(folder, "branch", "--show-current").strip() == "main"
    assert git(folder, "status", "--porcelain") == ""
    assert git(folder, "config", "core.hooksPath").strip() == ".softfield/hooks"
    assert (folder / ".softfield/hooks/pre-commit").stat().st_mode & 0o111
    assert _projects(db) == [("softfield", "/r/softfield", 1)]  # F236: no row until `create`
    assert _row(db, "ducks") is None


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
    assert (folder / ".gitignore").read_text() == "node_modules/\n"
    assert not (folder / "CLAUDE.md").exists() and not (folder / "opencode.json").exists()
    assert git(folder, "log", "--format=%an", "-1").strip() == "Softfield runner"


def test_init_after_a_fresh_git_init_on_master_works_on_main(tmp_path):
    folder = tmp_path / "fresh"
    folder.mkdir()
    git(folder, "init", "-q", "-b", "master")
    assert setup.init(folder, tmp_path / "m.sqlite")[0] == "new"
    assert git(folder, "branch", "--show-current").strip() == "main"


@pytest.mark.parametrize("why", ["a project already", "is on feature", "commit or stash"])
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
    elif why == "is on feature":
        git(folder, "checkout", "-q", "-b", "feature")
    else:
        (folder / "a.py").write_text("A = 2\n")
    with pytest.raises(setup.SetupError, match=why):
        setup.init(folder, tmp_path / "m.sqlite")


def _missing(folder: Path, db: Path) -> list[str]:
    """What the web still needs: the failed checks a project waits for."""
    return [f.what for f in setup.doctor(folder, db, run_checks=False) if f.needed and not f.ok]


def test_doctor_says_what_the_web_still_needs_then_passes(tmp_path, machine):
    """ADR 30 item 8, with the owner's ADR 00 accepted in the setup session."""
    db = tmp_path / "m.sqlite"
    folder = tmp_path / "ducks"
    folder.mkdir()
    setup.init(folder, db)
    assert _missing(folder, db) == [
        "a one-line description in [project]",
        "the idea in .softfield/seed.md",
        "ADR 00 accepted: none in .softfield/adr/",
        "a first card in .softfield/cards/",
    ]
    toml = folder / ".softfield/project.toml"
    toml.write_text(toml.read_text().replace('description = ""', 'description = "Ducks."'))
    (folder / ".softfield/seed.md").write_text("# Seed\n\nA duck counter.\n")
    adr = "# ADR 00: Initial decisions\n\n- **Status:** Accepted (by the owner, 2026-10-14)\n"
    (folder / ".softfield/adr/00-initial.md").write_text(adr)  # written Accepted by hand
    (folder / ".softfield/cards/m1-count.md").write_text("# Milestone M1: Count\n")
    git(folder, "config", "user.email", "t@example.com")
    git(folder, "config", "user.name", "Test")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "--no-verify", "-m", "set up")
    assert _missing(folder, db) == [
        "ADR 00 accepted: only `softfield accept 0` accepts it, on your yes"
    ]
    (folder / ".softfield/adr/00-initial.md").write_text(
        adr.replace("Accepted (by the owner, 2026-10-14)", "Proposed")
    )
    git(folder, "commit", "-qam", "proposed", "--no-verify")
    owner.decide_adr(folder, 0, "Accepted", date(2026, 10, 14))  # the owner's yes
    (folder / "stray.py").write_text("X = 1\n")  # untracked work fails it too
    assert _missing(folder, db) == ["everything committed, on main"]
    (folder / "stray.py").unlink()
    found = setup.doctor(folder, db, run_checks=False)
    assert setup.passes(found)  # the phone's notifications aren't set up: they don't hold it
    assert [f.ok for f in found if not f.needed] == [False]
    assert _row(db, "ducks") is None  # doctor only checks: no row, passing or not


def test_doctor_says_whether_the_phones_notifications_are_set_up(tmp_path, monkeypatch, capsys):
    """ADR 31 item 5, f142-03: read from the machine's `[notify] ntfy`; nothing is sent."""
    db = tmp_path / "m.sqlite"
    folder = tmp_path / "ducks"
    folder.mkdir()
    setup.init(folder, db)
    machine = tmp_path / "factory.toml"
    machine.write_text(MACHINE.read_text())
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))

    def no_request(*args, **kwargs):
        raise AssertionError("doctor sent a request")

    monkeypatch.setattr("runner.notify._post", no_request)
    monkeypatch.setattr("urllib.request.urlopen", no_request)

    def phone() -> setup.Finding:
        (finding,) = [f for f in setup.doctor(folder, db, run_checks=False) if not f.needed]
        return finding

    off = phone()
    assert not off.ok
    assert "softfield notify setup" in off.what
    assert "docs/notifications-on-the-phone.md" in off.what
    toml = folder / ".softfield/project.toml"
    toml.write_text(toml.read_text() + f'\n[metrics]\ndb = "{db}"\n')
    machine.write_text(MACHINE.read_text() + '\n[notify]\nntfy = "https://ntfy.sh/abc123"\n')
    on = phone()
    assert on.ok and "set up" in on.what and "abc123" not in on.what  # the topic is the lock
    monkeypatch.chdir(folder)
    cli.main(["doctor", "--quick"])
    assert f"ok  {on.what}" in capsys.readouterr().out


def test_the_phone_steps_name_the_commands_as_the_cli_has_them():
    steps = (Path(setup.__file__).parents[1] / "docs/notifications-on-the-phone.md").read_text()
    for command in ("softfield notify setup", "softfield notify test"):
        assert f"`{command}`" in steps
    assert "1. " in steps and "Use another server" in steps


def test_the_setup_session_gets_the_guide_as_its_instructions(monkeypatch):
    """The owner, 2026-10-14: told to read the guide, the first try said nothing and then
    built the idea. The guide is its instructions now, and it opens with the steps."""
    monkeypatch.setattr("runner.config.HOME", Path(setup.__file__).parents[1])
    command = setup.claude_command(Path("/r/ducks"), "new")
    assert command[:3] == ["claude", "--add-dir", str(config.INSTRUCTIONS)]
    guide = command[command.index("--append-system-prompt") + 1]
    assert "**Never build the idea.**" in guide and "Your first message" in guide
    assert "Never mark ADR 00 Accepted yourself" in guide
    assert command[-1].startswith("Start the setup of ducks, a new project")


def test_doctor_hands_over_with_where_to_go_next():
    text = setup.hand_over("hello", "m1-hello-world", "192.168.1.5")
    assert text.splitlines() == [
        "Done: hello is in the factory.",
        "  The Projects page: http://192.168.1.5:8765/projects",
        "  Its first card, m1-hello-world, on its Planning desk:",
        "  http://192.168.1.5:8765/planning/m1?project=hello",
        "Write to the card to plan it there; the runner builds it once you approve the plan.",
    ]
    planning = setup.hand_over("hello", "m1-hello-world", "192.168.1.5", planning=True)
    assert planning.splitlines()[-1].startswith("The lead plans it once the runner is running")


def test_the_hand_over_asks_the_lead_to_plan_the_first_card_once(tmp_path):
    """The owner, 2026-10-15: the first card sat unplanned until they wrote to it."""
    db = tmp_path / "m.sqlite"
    at = "2026-10-15T09:00:00+01:00"
    assert not setup.plan_first_card("hello", "m1-hello-world", db, at)  # no such project
    conn = metrics.open_db(db)
    try:
        project = metrics.upsert_project(conn, "hello", repo="/r/hello")
    finally:
        conn.close()
    assert setup.plan_first_card("hello", "m1-hello-world", db, at)
    assert not setup.plan_first_card("hello", "m1-hello-world", db, at)  # one waits already
    conn = metrics.open_db(db)
    try:
        rows = conn.execute("SELECT * FROM owner_requests").fetchall()
        assert [(r["project_id"], r["kind"], r["subject"]) for r in rows] == [
            (project, "plan_message", "m1")
        ]
        assert json.loads(rows[0]["value"]) == {"text": "Plan this card.", "comments": {}}
        conn.execute("UPDATE owner_requests SET done = ?", (at,))
        metrics.planner_thread(conn, project, "m1", at)
        conn.commit()
    finally:
        conn.close()
    assert not setup.plan_first_card("hello", "m1-hello-world", db, at)  # its thread began


def test_forget_takes_a_project_off_every_list_but_keeps_its_rows(tmp_path, monkeypatch, capsys):
    db = tmp_path / "m.sqlite"
    machine = tmp_path / "factory.toml"
    machine.write_text(f'[metrics]\ndb = "{db}"\n')
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    conn = metrics.open_db(db)
    try:
        metrics.upsert_project(conn, "hello", repo="/r/hello")
        metrics.upsert_project(conn, "coucou", repo="/r/coucou")
    finally:
        conn.close()
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert cli.main(["forget", "hello"]) == 1  # not confirmed
    assert cli.main(["forget", "hello", "--yes"]) == 0
    assert "hello: forgotten. Its folder stays: /r/hello" in capsys.readouterr().out
    assert [name for name, *_ in _projects(db)] == ["coucou"]
    conn = metrics.open_db(db)
    try:
        assert metrics.find_project(conn, "hello") is not None  # its history stays
    finally:
        conn.close()
    assert cli.main(["forget", "nope", "--yes"]) == 1


def _row(db: Path, name: str) -> tuple[str | None, str | None] | None:
    conn = metrics.open_db(db)
    try:
        return metrics.project_state(conn, name)
    finally:
        conn.close()


def _old_hello(db: Path, paused: str | None, repo: str = "/r/hello") -> int:
    conn = metrics.open_db(db)
    try:
        project = metrics.upsert_project(conn, "hello", repo=repo)
        metrics.upsert_milestone(conn, project, "m1", title="old")
        metrics.set_project_paused(conn, "hello", paused)
        return project
    finally:
        conn.close()


def _hello_folder(tmp_path: Path) -> Path:
    folder = tmp_path / "hello"
    folder.mkdir()
    return folder


def test_init_asks_about_a_forgotten_project_and_keep_renames_the_old_one(tmp_path):
    """F136 D1, D2: the old row is kept as hello-1, forgotten, with its history."""
    db = tmp_path / "m.sqlite"
    old = _old_hello(db, metrics.FORGOTTEN)
    folder = _hello_folder(tmp_path)
    asked = []

    def ask(said: str, choices: list[str]) -> str:
        asked.append(choices)
        assert not any(folder.iterdir())  # nothing is written before the question
        return "keep"

    setup.init(folder, db, ask=ask)
    assert asked == [["keep", "fresh"]]  # no continue: the folder doesn't hold the old project
    assert _row(db, "hello-1") == ("/r/hello", metrics.FORGOTTEN)
    assert _row(db, "hello") is None  # the new project is registered by `create`
    conn = metrics.open_db(db)
    try:
        assert metrics.find_project(conn, "hello-1") == old
        kept = conn.execute("SELECT key FROM milestones WHERE project_id = ?", (old,)).fetchall()
    finally:
        conn.close()
    assert [k[0] for k in kept] == ["m1"]


def test_keep_takes_the_first_free_number(tmp_path):
    db = tmp_path / "m.sqlite"
    _old_hello(db, metrics.FORGOTTEN)
    conn = metrics.open_db(db)
    try:
        metrics.upsert_project(conn, "hello-1", repo="/r/x")
    finally:
        conn.close()
    setup.init(_hello_folder(tmp_path), db, previous="keep")
    assert _row(db, "hello-2") == ("/r/hello", metrics.FORGOTTEN)


def test_continue_is_offered_when_the_folder_names_the_project_and_writes_nothing(tmp_path):
    db = tmp_path / "m.sqlite"
    old = _old_hello(db, metrics.FORGOTTEN)
    folder = _hello_folder(tmp_path)
    setup.init(folder, tmp_path / "other.sqlite")  # the folder's files, under another database
    head = git(folder, "rev-parse", "HEAD")
    offered = []

    def ask(said: str, choices: list[str]) -> str:
        offered.append(choices)
        return "continue"

    setup.init(folder, db, ask=ask)
    assert offered == [["keep", "continue", "fresh"]]
    assert git(folder, "rev-parse", "HEAD") == head and git(folder, "status", "--porcelain") == ""
    assert _row(db, "hello") == ("/r/hello", metrics.FORGOTTEN)  # `create` brings it back
    conn = metrics.open_db(db)
    try:
        assert metrics.find_project(conn, "hello") == old
    finally:
        conn.close()


def _fat_hello(db: Path) -> int:
    old = _old_hello(db, metrics.FORGOTTEN)
    conn = metrics.open_db(db)
    try:
        run = metrics.upsert_run(conn, old, "r1", command="x", started="2026-01-01T00:00:00+00:00")
        ticket = metrics.upsert_ticket(conn, old, "t1")
        metrics.start_job(
            conn, run, ticket_id=ticket, milestone_id=None, role="developer", agent="a", attempt=1,
            started="2026-01-01T00:00:00+00:00",
        )  # fmt: skip
        thread = metrics.planner_thread(conn, old, "m1", "2026-01-01T00:00:00+00:00")
        metrics.add_planner_message(conn, thread["id"], "owner", "2026-01-01T00:00:00+00:00", "hi")
        metrics.add_rating_change(
            conn, "a", "s", 1, 2, at="2026-01-01T00:00:00+00:00", ticket_id=ticket
        )
    finally:
        conn.close()
    return old


def _count_rows(db: Path, table: str) -> int:
    conn = metrics.open_db(db)
    try:
        return int(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0])  # noqa: S608
    finally:
        conn.close()


def test_start_fresh_deletes_the_old_entry_once_its_name_is_typed(tmp_path):
    db = tmp_path / "m.sqlite"
    old = _fat_hello(db)
    folder = _hello_folder(tmp_path)
    prompts = []

    def confirm(prompt: str) -> str:
        prompts.append(prompt)
        return "hello"

    setup.init(folder, db, ask=lambda said, choices: "fresh", confirm=confirm)
    assert "cards" in prompts[0] and "runs" in prompts[0]
    assert _row(db, "hello") is None
    conn = metrics.open_db(db)
    try:
        for table in ("runs", "tickets", "jobs", "planner_threads", "planner_messages"):
            assert _count_rows(db, table) == 0, table
        assert (
            conn.execute("SELECT count(*) FROM milestones WHERE project_id = ?", (old,)).fetchone()[
                0
            ]
            == 0
        )
        assert conn.execute("SELECT ticket_id FROM rating_changes").fetchone()[0] is None
    finally:
        conn.close()


def test_a_wrong_name_typed_back_cancels_with_nothing_written(tmp_path):
    db = tmp_path / "m.sqlite"
    _fat_hello(db)
    folder = _hello_folder(tmp_path)
    with pytest.raises(setup.SetupError, match="nothing was changed"):
        setup.init(folder, db, ask=lambda said, choices: "fresh", confirm=lambda prompt: "nope")
    assert not any(folder.iterdir())
    assert _row(db, "hello") == ("/r/hello", metrics.FORGOTTEN)
    assert _count_rows(db, "runs") == 1


def test_previous_fresh_needs_yes_before_anything_is_written(tmp_path):
    db = tmp_path / "m.sqlite"
    _fat_hello(db)
    folder = _hello_folder(tmp_path)
    with pytest.raises(setup.SetupError, match="--yes"):
        setup.init(folder, db, previous="fresh")
    assert not any(folder.iterdir()) and _count_rows(db, "runs") == 1
    setup.init(folder, db, previous="fresh", yes=True)
    assert _count_rows(db, "runs") == 0


def test_fresh_is_never_offered_for_a_live_project(tmp_path):
    db = tmp_path / "m.sqlite"
    _old_hello(db, None)
    with pytest.raises(setup.SetupError, match="isn't possible"):
        setup.init(_hello_folder(tmp_path), db, previous="fresh", yes=True)


def test_a_live_project_of_the_name_means_a_new_one_called_name_2(tmp_path, machine):
    db = tmp_path / "m.sqlite"
    _old_hello(db, None)
    folder = _hello_folder(tmp_path)
    with pytest.raises(setup.SetupError, match="continue"):
        setup.init(folder, db, previous="continue")
    setup.init(folder, db, previous="keep")
    assert load_config(folder).project_name == "hello-2"
    assert _row(db, "hello") == ("/r/hello", None)  # the live row is unchanged
    assert _row(db, "hello-2") is None


def test_without_an_old_row_init_asks_nothing(tmp_path):
    def ask(said: str, choices: list[str]) -> str:
        raise AssertionError("no question expected")

    setup.init(_hello_folder(tmp_path), tmp_path / "m.sqlite", ask=ask)


def test_init_without_a_terminal_or_a_flag_writes_nothing_and_exits_1(
    tmp_path, monkeypatch, capsys
):
    db = tmp_path / "m.sqlite"
    machine = tmp_path / "factory.toml"
    machine.write_text(f'[metrics]\ndb = "{db}"\n')
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    _old_hello(db, metrics.FORGOTTEN)
    folder = _hello_folder(tmp_path)
    monkeypatch.chdir(folder)
    assert cli.main(["init", "--no-claude"]) == 1
    assert "--previous keep" in capsys.readouterr().out
    assert not any(folder.iterdir())
    assert _row(db, "hello") == ("/r/hello", metrics.FORGOTTEN)
    assert cli.main(["init", "--no-claude", "--previous", "fresh"]) == 1  # f136-03
    assert not any(folder.iterdir())
    assert cli.main(["init", "--no-claude", "--previous", "keep"]) == 0
    assert _row(db, "hello-1") == ("/r/hello", metrics.FORGOTTEN)


def test_forget_says_a_later_init_will_ask(tmp_path, monkeypatch, capsys):
    db = tmp_path / "m.sqlite"
    machine = tmp_path / "factory.toml"
    machine.write_text(f'[metrics]\ndb = "{db}"\n')
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    _old_hello(db, None)
    assert cli.main(["forget", "hello", "--yes"]) == 0
    assert "later `softfield init` under the name hello will ask" in capsys.readouterr().out


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


def _init_env(tmp_path, monkeypatch):
    db = tmp_path / "m.sqlite"
    machine = tmp_path / "factory.toml"
    machine.write_text(f'[metrics]\ndb = "{db}"\n')
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    folder = tmp_path / "ducks"
    folder.mkdir()
    monkeypatch.chdir(folder)
    return db, folder


def _stub_claude(monkeypatch, ran, effect=None):
    real = subprocess.run

    def run(cmd, **kw):
        if cmd[0] != "claude":  # git and the rest are real
            return real(cmd, **kw)
        ran.append(cmd)
        if effect:
            effect()
        return subprocess.CompletedProcess(cmd, 1)

    monkeypatch.setattr(subprocess, "run", run)


def _head(folder: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=folder, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_init_runs_claude_as_a_child_and_says_how_to_finish_when_left_early(
    tmp_path, monkeypatch, capsys
):
    """F236 D5: Claude exits at once (or fails): no row, and two lines say how to finish."""
    db, _folder = _init_env(tmp_path, monkeypatch)
    ran: list[list[str]] = []
    _stub_claude(monkeypatch, ran)
    assert cli.main(["init"]) == 0
    out = capsys.readouterr().out
    assert ran and ran[0][0] == "claude"
    assert "ducks isn't in the factory yet." in out
    assert "To finish: `softfield init` here again carries on with Claude" in out
    assert "`softfield create` adds it if it's ready." in out
    assert _projects(db) == []


def test_init_says_nothing_more_when_claude_registered_the_project(tmp_path, monkeypatch, capsys):
    db, folder = _init_env(tmp_path, monkeypatch)
    ran: list[list[str]] = []
    _stub_claude(monkeypatch, ran, lambda: setup.register(folder, db, "ducks"))
    assert cli.main(["init"]) == 0
    out = capsys.readouterr().out
    assert "isn't in the factory yet" not in out and "To finish" not in out


def test_a_second_init_in_an_unregistered_folder_carries_on_and_writes_nothing(
    tmp_path, monkeypatch, capsys
):
    """F236 D6."""
    _db, folder = _init_env(tmp_path, monkeypatch)
    assert cli.main(["init", "--no-claude"]) == 0
    before = _head(folder)
    ran: list[list[str]] = []
    _stub_claude(monkeypatch, ran)
    assert cli.main(["init"]) == 0
    assert "Carry on the setup of ducks: run `softfield doctor` first" in ran[0][-1]
    assert _head(folder) == before
    capsys.readouterr()
    ran.clear()
    cli.main(["init", "--no-claude"])  # what doctor finds, and no session
    assert not ran and "project.toml" in capsys.readouterr().out


def test_bootstrap_asks_before_create_and_says_the_owner_can_leave():
    guide = setup.bootstrap().read_text(encoding="utf-8")
    assert "Ready to add" in guide and "softfield create" in guide
    assert "You can leave this session now (/exit)." in guide


def test_softfield_init_without_claude_from_the_folder(tmp_path, monkeypatch, capsys):
    machine = tmp_path / "factory.toml"
    machine.write_text(f'[metrics]\ndb = "{tmp_path / "m.sqlite"}"\n')
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    folder = tmp_path / "ducks"
    folder.mkdir()
    monkeypatch.chdir(folder)
    assert cli.main(["init", "--no-claude"]) == 0
    out = capsys.readouterr().out
    assert "ducks: set up as a new project" in out
    assert "`softfield create` adds ducks to the factory" in out
    assert _projects(tmp_path / "m.sqlite") == []
    assert subprocess.run(["git", "status", "--porcelain"], cwd=folder, capture_output=True,
                          text=True).stdout == ""  # fmt: skip


def test_doctor_offers_to_accept_adr_00_first(tmp_path, monkeypatch, machine, capsys):
    """The owner, 2026-10-14: accepting ADR 00 is part of getting ready, one yes away."""
    db = tmp_path / "m.sqlite"
    folder = tmp_path / "ducks"
    folder.mkdir()
    setup.init(folder, db)
    git(folder, "config", "user.email", "t@example.com")
    git(folder, "config", "user.name", "Test")
    adr = folder / ".softfield/adr/00-initial.md"
    adr.write_text("# ADR 00: Initial decisions\n\n- **Status:** Proposed\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "--no-verify", "-m", "ADR 00")
    assert setup.proposed_adr_00(folder) == adr
    toml = folder / ".softfield/project.toml"
    toml.write_text(toml.read_text() + f'\n[metrics]\ndb = "{db}"\n')
    git(folder, "commit", "-qam", "db", "--no-verify")
    monkeypatch.chdir(folder)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    cli.main(["doctor", "--quick"])
    out = capsys.readouterr().out
    assert "ADR 00 waits for you: .softfield/adr/00-initial.md" in out
    assert "- **Status:** Accepted" in adr.read_text()
    assert setup.proposed_adr_00(folder) is None
    assert "ok  ADR 00 accepted" in out
    assert _row(db, "ducks") is None  # neither the question nor the accept made a row


def _ready_ducks(tmp_path: Path, db: Path) -> Path:
    """A folder everything `doctor` needs passes in, with its database in project.toml."""
    folder = tmp_path / "ducks"
    folder.mkdir()
    setup.init(folder, db)
    toml = folder / ".softfield/project.toml"
    toml.write_text(
        toml.read_text().replace('description = ""', 'description = "Ducks."')
        + f'\n[metrics]\ndb = "{db}"\n'
    )
    (folder / ".softfield/seed.md").write_text("# Seed\n\nA duck counter.\n")
    (folder / ".softfield/adr/00-initial.md").write_text(
        "# ADR 00: Initial decisions\n\n- **Status:** Proposed\n"
    )
    card = "# Milestone M1: Count\n\n> **State:** idea · **Area:** product\n"
    (folder / ".softfield/cards/m1-count.md").write_text(card)
    git(folder, "config", "user.email", "t@example.com")
    git(folder, "config", "user.name", "Test")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "--no-verify", "-m", "set up")
    owner.decide_adr(folder, 0, "Accepted", date(2026, 11, 19))
    return folder


def test_doctor_passing_on_an_unregistered_project_points_to_create(
    tmp_path, monkeypatch, machine, capsys
):
    db = tmp_path / "m.sqlite"
    folder = _ready_ducks(tmp_path, db)
    monkeypatch.chdir(folder)
    assert cli.main(["doctor", "--quick"]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == (
        "Ready: `softfield create` adds ducks to the factory."
    )
    assert _row(db, "ducks") is None


def test_create_registers_the_project_last_and_hands_it_over(
    tmp_path, monkeypatch, machine, capsys
):
    db = tmp_path / "m.sqlite"
    conn = metrics.open_db(db)
    try:
        metrics.upsert_project(conn, "softfield", repo="/r/softfield")
        metrics.set_project_order(conn, ["softfield"])
    finally:
        conn.close()
    folder = _ready_ducks(tmp_path, db)
    monkeypatch.chdir(folder)
    assert cli.main(["create", "--quick"]) == 0
    out = capsys.readouterr().out
    assert "Done: ducks is in the factory." in out
    assert _projects(db) == [("softfield", "/r/softfield", 1), ("ducks", str(folder), 2)]
    assert _row(db, "ducks") == (str(folder), None)  # not paused
    conn = metrics.open_db(db)
    try:
        keys = [r[0] for r in conn.execute("SELECT key FROM milestones").fetchall()]
        asked = conn.execute("SELECT kind, subject FROM owner_requests").fetchall()
    finally:
        conn.close()
    assert keys == ["m1-count"]
    assert [tuple(r) for r in asked] == [("plan_message", "m1")]
    assert cli.main(["create", "--quick"]) == 0  # again: says so, changes nothing
    assert "in the factory already" in capsys.readouterr().out
    assert _count_rows(db, "owner_requests") == 1 and len(_projects(db)) == 2


def test_create_with_a_needed_check_failing_writes_no_row(tmp_path, monkeypatch, machine, capsys):
    db = tmp_path / "m.sqlite"
    folder = _ready_ducks(tmp_path, db)
    (folder / "stray.py").write_text("X = 1\n")  # uncommitted: "everything committed" fails
    monkeypatch.chdir(folder)
    assert cli.main(["create", "--quick"]) == 1
    out = capsys.readouterr().out
    assert "--  everything committed, on main" in out
    assert out.rstrip().endswith("Nothing was added to the factory.")
    assert _row(db, "ducks") is None and _count_rows(db, "milestones") == 0


def test_create_refuses_a_name_another_folder_holds(tmp_path, monkeypatch, machine, capsys):
    db = tmp_path / "m.sqlite"
    folder = _ready_ducks(tmp_path, db)
    conn = metrics.open_db(db)
    try:
        metrics.upsert_project(conn, "ducks", repo="/r/other-ducks")
    finally:
        conn.close()
    monkeypatch.chdir(folder)
    assert cli.main(["create", "--quick"]) == 1
    assert "/r/other-ducks" in capsys.readouterr().out
    assert _row(db, "ducks") == ("/r/other-ducks", None)
    assert _count_rows(db, "milestones") == 0


def test_create_brings_a_forgotten_project_of_this_folder_back(
    tmp_path, monkeypatch, machine, capsys
):
    """F136's "continue": the old row, history included, un-forgotten only by `create`."""
    db = tmp_path / "m.sqlite"
    folder = _ready_ducks(tmp_path, db)
    conn = metrics.open_db(db)
    try:
        old = metrics.upsert_project(conn, "ducks", repo=str(folder))
        metrics.set_project_paused(conn, "ducks", metrics.FORGOTTEN)
    finally:
        conn.close()
    monkeypatch.chdir(folder)
    assert cli.main(["create", "--quick"]) == 0
    assert _row(db, "ducks") == (str(folder), None)
    conn = metrics.open_db(db)
    try:
        assert metrics.find_project(conn, "ducks") == old
    finally:
        conn.close()


def test_doctor_puts_the_first_card_on_the_desk_at_once(tmp_path):
    """2026-10-14: the hand-over said "its first card, on its Planning desk", but the card
    reached the database only at the runner's next round, after a developer's job."""
    db = tmp_path / "m.sqlite"
    folder = tmp_path / "hello"
    folder.mkdir()
    setup.init(folder, db)
    card = "# Milestone M1: Say hi\n\n> **State:** idea · **Priority:** 1 · **Area:** product\n"
    (folder / ".softfield/cards/m1-say-hi.md").write_text(card)
    assert setup.publish_cards(folder, "hello", db) == ["m1-say-hi"]
    conn = metrics.open_db(db)
    try:
        rows = conn.execute(
            "SELECT m.key, m.title, m.state FROM milestones m JOIN projects p"
            " ON p.id = m.project_id WHERE p.name = 'hello'"
        ).fetchall()
    finally:
        conn.close()
    assert [tuple(r) for r in rows] == [("m1-say-hi", "Say hi", "idea")]


IDEA = "A log of the birds I see.\r\n\r\n> From the kitchen window, mostly.  \n"
TODAY = date(2026, 11, 19)


def _start(tmp_path: Path, name: str = "Bird log", idea: str = IDEA) -> tuple[Path, str]:
    return setup.start_project(
        tmp_path / "root", tmp_path / "m.sqlite", name, idea, "Django", True, TODAY
    )


def test_a_project_from_the_page_is_made_committed_and_registered_setting_up(tmp_path):
    """F122 D2, ADR 48 items 1 and 3: the folder, the owner's words byte for byte, the first card,
    one commit on main; then the row, paused "setting up", with the card on its board."""
    folder, name = _start(tmp_path)
    assert (folder, name) == (tmp_path / "root" / "bird-log", "bird-log")
    seed = (folder / ".softfield/seed.md").read_bytes()
    assert seed.startswith(b"# Seed\n\n2026-11-19\n\n")
    assert IDEA.encode() in seed
    card = (folder / ".softfield/cards/m1-first-version.md").read_text(encoding="utf-8")
    assert card.startswith("# Milestone M1: First version of Bird log\n")
    assert "**State:** idea" in card and "**Area:** product" in card
    notes = card.split("## Notes\n", 1)[1]
    assert "A log of the birds I see." in notes and "Built with: Django" in notes
    assert "an app, opened in a browser" in notes
    assert 'name = "bird-log"' in (folder / ".softfield/project.toml").read_text()
    assert 'origin = "new"' in (folder / ".softfield/project.toml").read_text()
    assert git(folder, "rev-list", "--count", "HEAD").strip() == "1"
    assert git(folder, "branch", "--show-current").strip() == "main"
    assert git(folder, "status", "--porcelain") == ""
    assert _row(tmp_path / "m.sqlite", "bird-log") == (str(folder), metrics.SETTING_UP)
    conn = metrics.open_db(tmp_path / "m.sqlite")
    try:
        keys = conn.execute(
            "SELECT m.key, m.state FROM milestones m JOIN projects p ON p.id = m.project_id"
            " WHERE p.name = 'bird-log'"
        ).fetchall()
    finally:
        conn.close()
    assert [tuple(k) for k in keys] == [("m1-first-version", "idea")]


def test_the_setup_reads_the_form_back_from_the_projects_files(tmp_path):
    """F122 D3: the setup job's prompt carries the form's values, read from what
    `start_project` wrote: the idea byte for byte, the name, the stack and whether it's an app."""
    folder, name = _start(tmp_path)
    assert setup.form(folder, name) == setup.Form("Bird log", IDEA, "Django", True)
    other, _ = setup.start_project(
        tmp_path / "root", tmp_path / "m.sqlite", "", "Built with: Rust · an app, opened in a"
        " browser", "", False, TODAY,
    )  # fmt: skip
    assert setup.form(other, "built-with-rust-an") == setup.Form(
        "built-with-rust-an", "Built with: Rust · an app, opened in a browser\n", "", False
    )
    (folder / ".softfield/seed.md").unlink()
    (folder / ".softfield/cards/m1-first-version.md").unlink()
    assert setup.form(folder, name) == setup.Form(name, "", "", False)


def test_a_taken_folder_or_live_name_takes_the_first_free_number(tmp_path):
    """F122 D2: never refused for its name."""
    (tmp_path / "root" / "bird-log").mkdir(parents=True)
    conn = metrics.open_db(tmp_path / "m.sqlite")
    try:
        metrics.upsert_project(conn, "bird-log-2", repo="/r/elsewhere")
    finally:
        conn.close()
    folder, name = _start(tmp_path)
    assert name == "bird-log-3" and folder == tmp_path / "root" / "bird-log-3"
    assert 'name = "bird-log-3"' in (folder / ".softfield/project.toml").read_text()


def test_a_forgotten_project_of_the_name_is_kept_under_another(tmp_path):
    """F122 D2: F136's "keep"."""
    db = tmp_path / "m.sqlite"
    conn = metrics.open_db(db)
    try:
        metrics.upsert_project(conn, "bird-log", repo="/r/old-birds")
        metrics.set_project_paused(conn, "bird-log", metrics.FORGOTTEN)
    finally:
        conn.close()
    folder, name = _start(tmp_path)
    assert name == "bird-log"
    assert _row(db, "bird-log-1") == ("/r/old-birds", metrics.FORGOTTEN)
    assert _row(db, "bird-log") == (str(folder), metrics.SETTING_UP)


@pytest.mark.parametrize(
    ("name", "folder"),
    [
        ("", "a-log-of-the"),  # the idea's first words
        ("  Ça va? Les Oiseaux!! ", "ca-va-les-oiseaux"),
        ("x" * 60, "x" * 40),
        ("🐦", "a-log-of-the"),  # nothing left of the name
        ("../../.ssh", "ssh"),  # a name never leaves the root
    ],
)
def test_the_folder_is_the_name_made_a_slug(tmp_path, name, folder):
    made, project = _start(tmp_path, name=name)
    assert project == folder and made.parent == tmp_path / "root"


def test_an_empty_idea_is_refused_and_nothing_is_written(tmp_path):
    with pytest.raises(setup.SetupError, match="idea"):
        _start(tmp_path, idea=" \n ")
    assert not (tmp_path / "root").exists()
    assert not (tmp_path / "m.sqlite").exists() or _projects(tmp_path / "m.sqlite") == []


def test_removing_the_dot_folder_leaves_the_repo_as_it_was(tmp_path):
    """ADR 41 item 1: the factory's footprint is its folder."""
    folder = tmp_path / "shop"
    folder.mkdir()
    git(folder, "init", "-q", "-b", "main")
    git(folder, "config", "user.email", "t@example.com")
    git(folder, "config", "user.name", "Test")
    (folder / "AGENTS.md").write_text("ours\n")
    (folder / "CLAUDE.md").write_text("ours too\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "init")
    before = git(folder, "rev-parse", "HEAD").strip()
    setup.init(folder, tmp_path / "m.sqlite")
    readme = (folder / ".softfield/README.md").read_text()
    git(folder, "rm", "-rq", ".softfield")
    assert git(folder, "diff", "--stat", before).strip() == ""
    assert (folder / "AGENTS.md").read_text() == "ours\n"
    # The one thing outside the folder, a setting in .git, and the README owns up to it (F3)
    assert git(folder, "config", "core.hooksPath").strip() == ".softfield/hooks"
    assert "git config --unset core.hooksPath" in readme and "softfield check-all" in readme


def test_softfield_lead_starts_claude_with_the_factorys_context(tmp_path, monkeypatch):
    """ADR 41 item 3: a plain `claude` stays plain; this one has the brief."""
    monkeypatch.setattr("runner.config.HOME", Path(setup.__file__).parents[1])
    (tmp_path / ".softfield").mkdir()
    (tmp_path / ".softfield" / "project.md").write_text("# Project rule\n")
    command = setup.lead_command(tmp_path, ["--model", "opus"])
    assert command[0] == "claude" and command[-2:] == ["--model", "opus"]
    system = command[command.index("--append-system-prompt") + 1]
    assert "Low ceremony" in system and "# Project rule" in system
    assert "When the lead is Claude" in system
    assert command[command.index("--add-dir") + 1] == str(config.INSTRUCTIONS)
