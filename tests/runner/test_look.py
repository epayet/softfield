"""`softfield look` (ADR 28): a planner or review job reads the metrics database and the
dashboard's pages, and can change neither."""

import importlib
import json
import pkgutil
import re
from pathlib import Path

import pytest

from runner import claude, cli, look, metrics, milestone, planner
from runner.agents import JobResult
from runner.gates import GateResult
from runner.state import load_state
from tests.factory_dashboard.conftest import PROJECT, write_fixture, write_planning
from tests.runner.conftest import git
from tests.runner.test_loop import _config
from tests.runner.test_milestone import REVIEW_DOC, _milestone_repo


@pytest.fixture
def db(tmp_path: Path) -> Path:
    """The dashboard's fixture database with the planning room's rows (``write_planning``)."""
    path = tmp_path / "db" / "factory-metrics.sqlite"
    path.parent.mkdir()
    conn = metrics.open_db(path)
    try:
        write_fixture(conn)
        write_planning(conn)
    finally:
        conn.close()
    return path


# --- look sql ---------------------------------------------------------------------------------


def test_sql_prints_a_selects_rows_under_their_column_names(db):
    out = look.sql(db, "SELECT ticket, state FROM tickets WHERE ticket LIKE 'f1-0%' ORDER BY 1")
    assert out.splitlines() == [
        "ticket\tstate",
        "f1-01-first\tdone",
        "f1-02-escalated\tdone",
        "f1-03-lead\tdone",
    ]


def test_sql_can_list_the_tables_and_a_tables_columns(db):
    """What a job needs to write its SELECT: the schema, with no list kept anywhere."""
    assert "owner_requests" in look.sql(db, "SELECT name FROM sqlite_master WHERE type = 'table'")
    assert "difficulty" in look.sql(db, "PRAGMA table_info(tickets)")


def test_sql_shows_an_empty_cell_and_keeps_a_row_on_one_line(db):
    out = look.sql(db, "SELECT NULL AS empty, 'a' || char(10) || 'b' AS two_lines")
    assert out.splitlines() == ["empty\ttwo_lines", "NULL\ta\\nb"]


@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO projects (name) VALUES ('made')",
        "UPDATE tickets SET state = 'ready'",
        "DELETE FROM jobs",
        "DROP TABLE jobs",
        "CREATE TABLE made (x)",
        "ATTACH DATABASE '{made}' AS made",
        "VACUUM INTO '{made}'",
        "PRAGMA user_version = 5",
        "PRAGMA journal_mode = DELETE",
        "PRAGMA wal_checkpoint(TRUNCATE)",
        "SELECT 1; SELECT 2",
        "SELECT 1; DELETE FROM jobs",
        "BEGIN",
    ],
)
def test_sql_refuses_everything_but_one_read_and_the_file_is_unchanged(db, tmp_path, query):
    """ADR 28 item 1: SQLite refuses it (its authorizer), whatever the text looks like. An
    ATTACH would make a file even on a read-only connection."""
    made = tmp_path / "made.sqlite"
    before = db.read_bytes()
    jobs = look.sql(db, "SELECT count(*) AS n FROM jobs")
    with pytest.raises(look.LookError) as refused:
        look.sql(db, query.format(made=made))
    assert len(str(refused.value).splitlines()) == 1
    assert db.read_bytes() == before
    assert look.sql(db, "SELECT count(*) AS n FROM jobs") == jobs
    assert not made.exists()


def test_sql_refuses_a_write_hidden_in_a_read(db):
    """Not by matching the text: this one starts with SELECT's own keyword."""
    before = db.read_bytes()
    with pytest.raises(look.LookError):
        look.sql(db, "WITH gone AS (SELECT 1) DELETE FROM jobs")
    assert db.read_bytes() == before


def test_sql_prints_the_cap_and_says_it_cut_the_rows(db):
    numbers = (
        "WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 250)"
        " SELECT i FROM n"
    )
    lines = look.sql(db, numbers).splitlines()
    assert lines[: look.MAX_ROWS + 1] == ["i", *(str(i) for i in range(1, look.MAX_ROWS + 1))]
    assert lines[look.MAX_ROWS + 1 :] == ["(cut: the first 200 rows; there are more)"]
    whole = look.sql(db, numbers + " LIMIT 200").splitlines()
    assert len(whole) == 201 and "cut" not in whole[-1]


def test_sql_cuts_a_long_cell_and_says_so(db):
    header, row, note = look.sql(db, "SELECT hex(zeroblob(2000)) AS long").splitlines()
    assert header == "long" and row == "0" * look.MAX_CELL + "…"
    assert note == f"(cut: 1 cell longer than {look.MAX_CELL} characters, ending in …)"


def test_sql_on_a_missing_database_or_a_bad_query_is_one_plain_line(db, tmp_path):
    with pytest.raises(look.LookError, match="no metrics database at"):
        look.sql(tmp_path / "none.sqlite", "SELECT 1")
    assert not (tmp_path / "none.sqlite").exists()
    with pytest.raises(look.LookError, match="no such table: unknown_table"):
        look.sql(db, "SELECT * FROM unknown_table")


# --- look page --------------------------------------------------------------------------------


def test_text_keeps_a_pages_words_and_drops_its_tags_scripts_and_styles():
    html = (
        "<html><head><title>Desk</title><style>p { color: red }</style>"
        "<script>var hidden = 1 < 2;</script></head>"
        "<body><h1>Your   desk</h1>\n\n\n\n<p>One <b>bold</b>\n word &amp; more</p>"
        "<template><p>unseen</p></template><ul><li>a</li><li>b</li></ul></body></html>"
    )
    assert look.text(html) == "Desk\nYour desk\nOne bold word & more\na\nb"


def test_page_prints_the_desks_words_with_no_tag_or_script(db):
    out = look.page(db, PROJECT, "/planning")
    assert "Seeds, not asked about yet" in out and "Parallel developers" in out
    assert not re.search(r"<[a-zA-Z/!]", out)
    assert "htmx" not in out and "function" not in out and "{" not in out
    assert "\n\n" not in out and not [line for line in out.splitlines() if line != line.strip()]


def test_page_prints_the_floors_data_as_json(db):
    floor = json.loads(look.page(db, PROJECT, "/line/live"))
    assert isinstance(floor, dict) and floor
    assert isinstance(json.loads(look.page(db, PROJECT, "/line/replay")), dict)


def test_page_follows_a_pages_own_redirect(db):
    assert look.page(db, PROJECT, "/line") == look.page(db, PROJECT, "/")


def test_page_cuts_a_long_page_and_says_so(db, monkeypatch):
    whole = look.page(db, PROJECT, "/planning")
    monkeypatch.setattr(look, "MAX_PAGE", 100)
    out = look.page(db, PROJECT, "/planning")
    assert out == f"{whole[:100]}\n(cut: the first 100 of {len(whole)} characters)"


@pytest.mark.parametrize(
    "address", ["/nowhere", "planning", "//example.com/planning", "http://example.com/"]
)
def test_page_on_an_unknown_address_is_one_plain_line(db, address):
    with pytest.raises(look.LookError) as refused:
        look.page(db, PROJECT, address)
    assert len(str(refused.value).splitlines()) == 1


def test_page_on_a_missing_database_says_so(tmp_path):
    with pytest.raises(look.LookError, match="no metrics database at"):
        look.page(tmp_path / "none.sqlite", PROJECT, "/")


def _routes() -> list[tuple[str, set[str]]]:
    """Every route of the dashboard as (path, methods): the app's own and each page module's
    router's, so a page added later is here without being listed."""
    import factory_dashboard
    from factory_dashboard.app import create_app

    found = list(create_app(Path("unused"), PROJECT).routes)
    for info in pkgutil.iter_modules(factory_dashboard.__path__):
        module = importlib.import_module(f"factory_dashboard.{info.name}")
        found += getattr(getattr(module, "router", None), "routes", [])
    return [
        (route.path, set(route.methods))  # type: ignore[attr-defined]
        for route in found
        if getattr(route, "methods", None)
    ]


def _get_addresses() -> list[str]:
    """Every GET route of the dashboard, a ``{parameter}`` filled with a value of the fixture."""
    values = {
        "run_dir": "20260930-100000",
        "ticket_id": "f1-01-first",
        "name": PROJECT,
        "job_id": "1",
        "thread": "f6",
        "path:path": ".factory/cards/f6-mockup/desk.html",
        "id": "adr-20",
        "request_id": "1",
        "key": "f1",
    }
    return [
        re.sub(r"\{([^}]+)\}", lambda m: values[m[1]], path)
        for path, methods in _routes()
        if "GET" in methods
    ]


def test_only_the_request_route_is_not_a_get():
    """`look page` only ever sends a GET, and the dashboard's one write is a POST."""
    others = {(path, method) for path, methods in _routes() for method in methods - {"GET", "HEAD"}}
    assert others == {("/requests", "POST")}


def test_no_get_route_of_the_dashboard_writes(db, tmp_path):
    """ADR 28 item 1: opening any page changes nothing, in the database or beside it."""
    conn = metrics.open_db(db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.add_request(conn, project, "pause", None, None, "2026-10-02T12:00:00+00:00")
    finally:
        conn.close()
    addresses = _get_addresses()
    assert {"/", "/planning", "/planning/f6", "/requests/1", "/line/live"} <= set(addresses)
    before = db.read_bytes()
    opened = 0
    for address in addresses:
        try:
            look.page(db, PROJECT, address)
            opened += 1
        except look.LookError:
            pass  # a page the fixture doesn't hold: its answer wrote nothing either
        assert db.read_bytes() == before, address
    assert opened >= 15
    assert sorted(p.name for p in tmp_path.iterdir()) == ["db"]


# --- look disk --------------------------------------------------------------------------------


def _fill(path: Path, nbytes: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * nbytes)
    return path


def test_disk_sizes_each_place_and_the_factorys_parts_of_tmp(tmp_path):
    tmp = tmp_path / "tmp"
    _fill(tmp / "softfield-1000" / "1-1" / "a", 2_000_000)
    _fill(tmp / "pytest-of-sam" / "pytest-3" / "b", 1_000_000)
    _fill(tmp / "org.chromium.Chromium.x" / "c", 500_000)
    _fill(tmp / "tmpabc.sqlite", 300_000)
    _fill(tmp / "someone-elses" / "d", 4_000_000)
    _fill(tmp_path / "bench" / "e", 10_000)
    _fill(tmp_path / "runs" / "f", 20_000)
    db = _fill(tmp_path / "m.sqlite", 30_000)
    _fill(tmp_path / "m.sqlite-wal", 40_000)
    out = look.disk(
        db, tmp_path / "bench", tmp_path / "runs", tmp=tmp, proc=tmp_path / "noproc",
        uid=1000, user="sam",
    )  # fmt: skip
    lines = {line[:32].strip(): line for line in out.splitlines()}
    assert "7.8 MB, 5 files" in lines[look.TMP_LABEL]
    assert "2.0 MB, 1 files" in lines["softfield-1000"]
    assert "1.0 MB, 1 files" in lines["pytest-of-sam"]
    assert "0.5 MB, 1 files" in lines["Chromium temp folders"]
    assert "0.3 MB, 1 files" in lines["tmp*.sqlite databases"]
    assert "0.0 MB, 0 files" in lines["Playwright folders"]
    assert "someone-elses" not in out
    assert "0.0 MB, 1 files" in lines["the bench folder"]
    assert "0.0 MB, 1 files" in lines[".factory/var/runs/"]
    assert "0.0 MB, 1 files" in lines["the metrics database"]
    assert "0.0 MB, 1 files" in lines["its write-ahead log (-wal)"]
    assert "none" in out.splitlines()[-1]


def test_disk_reads_a_missing_folder_as_zero_and_skips_what_it_cannot_read(tmp_path):
    tmp = tmp_path / "tmp"
    _fill(tmp / "pytest-of-sam" / "ok", 1000)
    locked = tmp / "pytest-of-sam" / "locked"
    _fill(locked / "hidden", 1000)
    locked.chmod(0)
    try:
        out = look.disk(
            tmp_path / "none.sqlite", tmp_path / "nobench", tmp_path / "noruns", tmp=tmp,
            proc=tmp_path / "noproc", uid=1000, user="sam",
        )  # fmt: skip
    finally:
        locked.chmod(0o700)
    lines = {line[:32].strip(): line for line in out.splitlines()}
    for place in ("the bench folder", ".factory/var/runs/", "the metrics database"):
        assert lines[place].endswith("0.0 MB, 0 files")
    assert lines["pytest-of-sam"].endswith("0.0 MB, 1 files")  # the locked folder is skipped


def test_disk_lists_deleted_files_held_open_largest_first(tmp_path):
    proc = tmp_path / "proc"
    for pid, command, nbytes in ((11, "small", 100), (22, "big", 5_000_000)):
        (proc / str(pid) / "fd").mkdir(parents=True)
        (proc / str(pid) / "comm").write_text(command + "\n")
        gone = _fill(tmp_path / f"{command} (deleted)", nbytes)
        (proc / str(pid) / "fd" / "3").symlink_to(gone)
        (proc / str(pid) / "fd" / "4").symlink_to(tmp_path)  # not deleted
    (proc / "self").mkdir()  # not a pid
    out = look.disk(
        tmp_path / "m.sqlite", tmp_path / "b", tmp_path / "r", tmp=tmp_path / "t", proc=proc,
        uid=Path(proc).stat().st_uid, user="sam",
    )  # fmt: skip
    held = out.splitlines()[-3:]
    assert "2 " in held[0] or "held open: 2" in held[0]
    assert "pid 22  big" in held[1] and "5.0 MB" in held[1]
    assert "pid 11  small" in held[2]


def test_disk_caps_the_deleted_files_listed_and_counts_the_rest(tmp_path, monkeypatch):
    monkeypatch.setattr(look, "MAX_HELD", 1)
    proc = tmp_path / "proc"
    for pid, nbytes in ((11, 100), (22, 5_000_000), (33, 2_000_000)):
        (proc / str(pid) / "fd").mkdir(parents=True)
        gone = _fill(tmp_path / f"g{pid} (deleted)", nbytes)
        (proc / str(pid) / "fd" / "3").symlink_to(gone)
    out = look.disk(
        tmp_path / "m", tmp_path / "b", tmp_path / "r", tmp=tmp_path / "t", proc=proc,
        uid=proc.stat().st_uid, user="sam",
    )  # fmt: skip
    assert out.splitlines()[-3:] == [
        "deleted files still held open: 3, largest first",
        "      5.0 MB  pid 22  ?",
        "  (and 2 more, 2.0 MB)",
    ]


def test_disk_writes_nothing(tmp_path):
    _fill(tmp_path / "tmp" / "pytest-of-sam" / "a", 10)
    before = sorted(p.as_posix() for p in tmp_path.rglob("*"))
    look.disk(
        tmp_path / "m", tmp_path / "b", tmp_path / "r", tmp=tmp_path / "tmp", uid=1, user="sam"
    )
    assert sorted(p.as_posix() for p in tmp_path.rglob("*")) == before


# --- the command ------------------------------------------------------------------------------


@pytest.fixture
def in_repo(repo, monkeypatch, machine):
    """The temporary repo as the command's, its metrics database under its ``var/``."""
    toml = (cli._repo() / ".factory" / "project.toml").read_text()
    test_db = (repo / "var" / "factory-metrics.sqlite").as_posix()
    metrics_db = f'\n[metrics]\ndb = "{test_db}"\n'  # over the machine's real one
    # the project is its folder's name
    toml = re.sub(r'^name = ".*"\n', "", toml, count=1, flags=re.M)
    (repo / ".factory" / "project.toml").write_text(toml + metrics_db)
    monkeypatch.chdir(repo)
    conn = metrics.open_db(repo / "var" / "factory-metrics.sqlite")
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        metrics.upsert_milestone(conn, project, "f9-parallel", title="Parallel work", state="idea")
        metrics.add_request(conn, project, "pause", None, None, "2026-10-02T12:00:00+00:00")
    finally:
        conn.close()
    return repo


def test_the_command_prints_a_select_and_a_page(in_repo, capsys):
    assert cli.main(["look", "sql", "SELECT key, title FROM milestones"]) == 0
    assert capsys.readouterr().out == "key\ttitle\nf9-parallel\tParallel work\n"
    assert cli.main(["look", "page", "/planning"]) == 0
    out = capsys.readouterr().out
    assert "Parallel work" in out and "<" not in out


@pytest.mark.parametrize(
    ("argv", "said"),
    [
        (["sql", "DELETE FROM milestones"], "not authorized"),
        (["sql", "SELECT * FROM unknown_table"], "no such table"),
        (["page", "/nowhere"], "no page at /nowhere"),
    ],
)
def test_the_command_fails_with_one_plain_line(in_repo, capsys, argv, said):
    assert cli.main(["look", *argv]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert said in captured.err and len(captured.err.splitlines()) == 1


def test_the_command_has_only_its_two_forms(in_repo, capsys):
    for argv in (
        ["look"],
        ["look", "post", "/requests"],
        ["look", "page", "/", "--method", "POST"],
    ):
        with pytest.raises(SystemExit) as exit_:
            cli.main(argv)
        assert exit_.value.code == 2


def test_looking_applies_no_owner_request_and_changes_nothing(in_repo, capsys):
    """ADR 28 item 3: every other command applies the owner's requests first (here, a pause
    made from the dashboard). A look runs inside a job, and leaves them to the runner."""
    db = in_repo / "var" / "factory-metrics.sqlite"
    state_path = in_repo / ".factory" / "var" / "runs" / "state.json"
    before, status = db.read_bytes(), git(in_repo, "status", "--porcelain")
    head = git(in_repo, "rev-parse", "HEAD")
    assert cli.main(["look", "sql", "SELECT kind, done FROM owner_requests"]) == 0
    assert capsys.readouterr().out == "kind\tdone\npause\tNULL\n"
    assert cli.main(["look", "page", "/"]) == 0
    assert cli.main(["look", "sql", "DELETE FROM owner_requests"]) == 1
    capsys.readouterr()
    assert db.read_bytes() == before
    assert not state_path.exists()
    assert git(in_repo, "status", "--porcelain") == status
    assert git(in_repo, "rev-parse", "HEAD") == head
    # the same request, at the next command that isn't a look
    assert cli.main(["queue", "none"]) == 1
    assert load_state(state_path).owner_pause is not None


# --- who may look (ADR 28 items 4 and 5) ------------------------------------------------------

LOOK = "Bash(softfield look:*)"


def test_the_review_job_may_look_and_is_told_so(repo, monkeypatch):
    """Allowed since f95-02, but its prompt never said so: F19's, F28's and F135's reviews
    wrote that they couldn't read the metrics database (2026-10-21)."""
    _milestone_repo(repo)
    tools: list[tuple[str, ...]] = []
    prompts: list[str] = []

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        tools.append(job.allowed_tools)
        prompts.append(job.prompt)
        out = re.search(r"Write (\S+) as:", job.prompt)
        assert out
        (repo_ / out[1]).write_text(json.dumps({"findings": [], "stop": None}))
        (repo_ / ".factory" / "reviews").mkdir(parents=True, exist_ok=True)
        (repo_ / ".factory" / "reviews" / "m1.md").write_text(REVIEW_DOC)
        return JobResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    monkeypatch.setattr(milestone, "run_e2e", lambda *a: GateResult("e2e", True, ""))
    assert milestone.review_milestone(_config(repo), "m1", "m1-start") == "clean"
    assert tools and all(LOOK in job for job in tools)
    assert all('`softfield look sql "<one SELECT>"`' in prompt for prompt in prompts)


@pytest.mark.parametrize("thread", ["f7", "general"])
def test_the_planners_prompt_says_it_can_look_in_one_line(thread):
    prompt = planner.prompt(thread, "What is on my desk?", {})
    [line] = [line for line in prompt.splitlines() if "softfield look" in line]
    assert '`softfield look sql "<one SELECT>"`' in line
    assert "`softfield look page <address>`" in line
    assert "look before answering what the owner sees" in line
    assert prompt.index(line) < prompt.index("What is on my desk?")
