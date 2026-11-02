"""F20 D1: the metrics database's daily copy into a Dropbox folder."""

import os
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner import backup, loop
from runner.config import Backup, Config, ConfigError, load_config
from runner.report import TaskRecord
from tests.runner.conftest import git, write_task
from tests.runner.test_config import MINIMAL_TOML, REPO

# `_config` reads this repo's project.toml over the machine file (ADR 30 item 3)
pytestmark = pytest.mark.usefixtures("machine")

THURSDAY = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def _name(at: datetime) -> str:
    return f"factory-metrics-{at.astimezone():%Y%m%d-%H%M}.sqlite"


def _source(path: Path) -> Path:
    """A database in WAL mode, as the live one is, with a few rows."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("CREATE TABLE threads (id INTEGER PRIMARY KEY, text TEXT)")
    conn.executemany("INSERT INTO threads (text) VALUES (?)", [("coucou",), ("Mum",)])
    conn.commit()
    conn.close()
    return path


def _dump(path: Path) -> list[tuple[object, ...]]:
    conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    try:
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        query = 'SELECT * FROM "{}"'  # the database's own table names
        return [(name, *row) for name in names for row in conn.execute(query.format(name))]
    finally:
        conn.close()


def _backups(tmp_path: Path, keep: int = 14, every_hours: float = 24) -> backup.Backups:
    db = _source(tmp_path / "live.sqlite")
    return backup.Backups(db, Backup(tmp_path / "Dropbox" / "backups", keep, every_hours))


# --- the copy, when it is due, and the pruning ---------------------------------------------


def test_with_no_copy_one_is_written_with_the_same_tables_and_rows(tmp_path):
    backups = _backups(tmp_path)
    path = backups.check(THURSDAY)
    assert path is not None
    assert path == tmp_path / "Dropbox" / "backups" / _name(THURSDAY)
    # only the finished copy: no temporary file, no -wal or -shm, live or the copy's own
    assert [p.name for p in path.parent.iterdir()] == [path.name]
    assert _dump(path) == _dump(tmp_path / "live.sqlite") != []
    conn = sqlite3.connect(path)
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    conn.close()


def test_a_copy_newer_than_every_hours_means_none_then_one_once_older(tmp_path):
    backups = _backups(tmp_path)
    first = backups.check(THURSDAY)
    assert backups.check(THURSDAY + timedelta(hours=23, minutes=59)) is None
    later = THURSDAY + timedelta(hours=24)
    second = backups.check(later)
    assert second is not None and second != first
    assert sorted(p.name for p in second.parent.iterdir()) == [_name(THURSDAY), _name(later)]


def test_a_copy_already_in_the_folder_counts(tmp_path):
    backups = _backups(tmp_path)
    folder = tmp_path / "Dropbox" / "backups"
    folder.mkdir(parents=True)
    (folder / _name(THURSDAY - timedelta(hours=2))).write_bytes(b"")
    assert backups.check(THURSDAY) is None
    assert backups.check(THURSDAY + timedelta(hours=23)) is not None


def test_past_keep_the_oldest_copies_go_and_nothing_else_in_the_folder(tmp_path):
    backups = _backups(tmp_path, keep=2)
    folder = tmp_path / "Dropbox" / "backups"
    folder.mkdir(parents=True)
    old = [_name(THURSDAY - timedelta(days=d)) for d in (3, 2)]
    others = ["notes.txt", "factory-metrics-old.sqlite", ".dropbox"]
    for name in old + others:
        (folder / name).write_bytes(b"x")
    newest = backups.check(THURSDAY)
    assert newest is not None
    assert sorted(p.name for p in folder.iterdir()) == sorted([old[1], newest.name, *others])


def test_a_missing_folder_is_created(tmp_path):
    backups = _backups(tmp_path)
    assert not (tmp_path / "Dropbox").exists()
    assert backups.check(THURSDAY) is not None


@pytest.mark.skipif(os.geteuid() == 0, reason="root writes anywhere")
def test_a_folder_not_writable_raises_and_leaves_nothing_behind(tmp_path):
    backups = _backups(tmp_path)
    folder = tmp_path / "Dropbox" / "backups"
    folder.mkdir(parents=True)
    folder.chmod(0o500)
    try:
        with pytest.raises((OSError, sqlite3.Error)):
            backups.check(THURSDAY)
        assert list(folder.iterdir()) == []
        # tried again, but not at every second's poll
        assert backups.check(THURSDAY + timedelta(seconds=5)) is None
        folder.chmod(0o700)
        assert backups.check(THURSDAY + backup.RETRY_AFTER) is not None
    finally:
        folder.chmod(0o700)


def test_while_none_is_due_a_check_does_not_list_the_folder(tmp_path, monkeypatch):
    backups = _backups(tmp_path)
    backups.check(THURSDAY)
    listed: list[Path] = []
    real = backup.copies

    def copies(folder: Path) -> list[Path]:
        listed.append(folder)
        return real(folder)

    monkeypatch.setattr(backup, "copies", copies)
    for minutes in range(1, 4):
        assert backups.check(THURSDAY + timedelta(minutes=minutes)) is None
    assert listed == []


# --- the config ----------------------------------------------------------------------------


def _toml(tmp_path: Path, extra: str = "") -> Path:
    (tmp_path / ".softfield").mkdir()
    (tmp_path / ".softfield" / "project.toml").write_text(MINIMAL_TOML + extra, encoding="utf-8")
    return tmp_path


def test_the_machines_toml_has_d1s_backup_section():
    expected = Backup(Path.home() / "Dropbox" / "software-factory-backups", 14, 24)
    assert load_config(REPO).backup == expected


def test_a_config_without_backup_uses_d1s_defaults(tmp_path):
    expected = Backup(Path.home() / "Dropbox" / "software-factory-backups", 14, 24)
    assert load_config(_toml(tmp_path)).backup == expected


def test_backup_is_read_from_the_toml(tmp_path):
    repo = _toml(tmp_path, '[backup]\ndir = "~/elsewhere"\nkeep = 3\nevery_hours = 6\n')
    assert load_config(repo).backup == Backup(Path.home() / "elsewhere", 3, 6)


@pytest.mark.parametrize("extra", ["keep = 0", "every_hours = 0", 'keep = "many"'])
def test_a_backup_that_keeps_nothing_or_never_waits_is_a_config_error(tmp_path, extra):
    with pytest.raises(ConfigError, match="backup"):
        load_config(_toml(tmp_path, f"[backup]\n{extra}\n"))


# --- the run: at its start, at each pick and while it waits ---------------------------------


@pytest.fixture(autouse=True)
def _quiet_run(monkeypatch):
    monkeypatch.setattr(loop, "OPEN_RUNS", [])
    monkeypatch.setattr(loop, "fresh_reading", lambda s: None)  # no real `claude -p`


@pytest.fixture
def fake_clock(monkeypatch) -> list[datetime]:
    clock = [THURSDAY]

    def sleep(seconds: float) -> None:
        clock[0] += timedelta(seconds=seconds)

    monkeypatch.setattr(loop, "now", lambda: clock[0])
    monkeypatch.setattr("time.sleep", sleep)
    return clock


def _config(repo: Path, folder: Path) -> Config:
    cfg = load_config(REPO)
    return replace(
        cfg,
        repo=repo,
        metrics_db=repo / "var" / "factory-metrics.sqlite",  # never the real one
        backup=Backup(folder, 14, 24),
        backoff_min=1,
    )


def _copies(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []


def test_a_runs_start_writes_a_copy_of_the_metrics_database(repo, tmp_path, fake_clock):
    folder = tmp_path / "Dropbox"
    loop.run_session(_config(repo, folder), once=False, dry_run=False, escalate=False)
    assert _copies(folder) == [_name(THURSDAY)]
    copied = {row[0] for row in _dump(folder / _name(THURSDAY))}  # tables with rows
    assert {"projects", "runs"} <= copied


def test_a_config_with_no_backup_writes_none(repo, tmp_path, fake_clock):
    cfg = replace(_config(repo, tmp_path / "Dropbox"), backup=None)
    loop.run_session(cfg, once=False, dry_run=False, escalate=False)
    assert not (tmp_path / "Dropbox").exists()


def _ticket_runs(monkeypatch, then=None) -> list[str]:
    ran: list[str] = []

    def run_task(s, task, directing=None):
        ran.append(task.id)
        if then is not None:
            then()
        return TaskRecord(task.id, task.milestone, result="blocked", note="faked")

    monkeypatch.setattr(loop, "run_task", run_task)
    return ran


def test_once_the_copy_is_old_the_next_pick_writes_one(repo, tmp_path, fake_clock, monkeypatch):
    write_task(repo / ".softfield" / "tasks" / "ready", "m1-01-thing")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "ticket")
    folder = tmp_path / "Dropbox"

    def a_day_passes() -> None:
        fake_clock[0] += timedelta(hours=25)

    ran = _ticket_runs(monkeypatch, a_day_passes)
    loop.run_session(_config(repo, folder), once=True, dry_run=False, escalate=False)
    assert ran == ["m1-01-thing"]
    later = THURSDAY + timedelta(hours=25)
    assert _copies(folder) == [_name(THURSDAY), _name(later)]


@pytest.mark.skipif(os.geteuid() == 0, reason="root writes anywhere")
def test_a_folder_not_writable_is_one_note_and_the_run_goes_on(
    repo, tmp_path, fake_clock, monkeypatch, capsys
):
    write_task(repo / ".softfield" / "tasks" / "ready", "m1-01-thing")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "ticket")
    folder = tmp_path / "Dropbox"
    folder.mkdir()
    folder.chmod(0o500)
    ran = _ticket_runs(monkeypatch)
    try:
        report = loop.run_session(_config(repo, folder), once=True, dry_run=False, escalate=False)
    finally:
        folder.chmod(0o700)
    assert ran == ["m1-01-thing"]
    assert report is not None
    notes = [n for n in report.notes if "backup" in n]
    assert len(notes) == 1 and "failed" in notes[0]
    assert "backup failed" in capsys.readouterr().out
    assert _copies(folder) == []


def test_a_long_wait_writes_a_copy_without_a_pick(repo, tmp_path, fake_clock):
    folder = tmp_path / "Dropbox"
    s = loop.open_session(_config(repo, folder))
    loop.check_backup(s)
    assert _copies(folder) == [_name(THURSDAY)]
    resumes = THURSDAY + timedelta(hours=30)
    loop.wait_for_claude(s, 30 * 3600, resumes, "m1-01-lead", limit=False)
    assert len(_copies(folder)) == 2
    loop.close_session(s)


def test_a_wait_watching_a_switch_writes_a_copy_too(repo, tmp_path, fake_clock):
    folder = tmp_path / "Dropbox"
    s = loop.open_session(_config(repo, folder))
    loop.check_backup(s)
    resumes = THURSDAY + timedelta(hours=30)
    loop.wait_for_claude(s, 30 * 3600, resumes, "m1-01-lead", limit=False, until=lambda: False)
    assert len(_copies(folder)) == 2
    loop.close_session(s)


def test_the_owners_pause_writes_a_copy_while_it_holds(repo, tmp_path, fake_clock, monkeypatch):
    folder = tmp_path / "Dropbox"
    s = loop.open_session(_config(repo, folder))
    loop.check_backup(s)
    s.state.owner_pause = THURSDAY.isoformat()
    polls = [0]

    def apply(s_: loop.Session) -> None:
        fake_clock[0] += timedelta(hours=13)
        polls[0] += 1
        if polls[0] == 2:
            s_.state.owner_pause = None

    monkeypatch.setattr(loop, "apply_owner_requests", apply)
    monkeypatch.setattr(loop, "_planning_goes", lambda s_: False)
    assert loop._hold_for_the_owner(s)
    assert len(_copies(folder)) == 2
    loop.close_session(s)
