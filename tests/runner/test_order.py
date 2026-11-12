"""The queue's order is one list per project (ADR 45, F222 D1, D4, D5): the runner picks from
it, a drag writes it, and the first apply of the owner's requests makes it in today's order."""

import json
from pathlib import Path

from runner import loop, metrics, order, requests
from runner.loop import close_session, open_session
from runner.state import State
from runner.tasks import load_dir, parse_task, pick_next, pulls, run_order, task_priority
from tests.runner.conftest import git, write_task
from tests.runner.test_loop import _config

ORDER = ".softfield/order.txt"
BUG = "bug-07-queue-order"


def _board(repo: Path, cards: dict[str, object], bugs: dict[str, int | None] | None = None) -> str:
    """Each card with its priority and one ready ticket (or a state alone, for one with no
    ticket), and each bug ticket ready with its own ``priority:`` (none for None); main's
    head."""
    docs = repo / ".softfield" / "cards"
    docs.mkdir(parents=True, exist_ok=True)
    ready = repo / ".softfield" / "tasks" / "ready"
    for key, priority in cards.items():
        header = f"**State:** ready · **Priority:** {priority}"
        if isinstance(priority, str):
            header = f"**State:** {priority}"
        else:
            path = write_task(ready, f"{key}-01-a")
            path.write_text(path.read_text().replace("milestone: 1", f"milestone: {key}"))
        (docs / f"{key}-card.md").write_text(
            f"# Milestone {key.upper()}: a card\n\n> {header}\n\n## Outcome\n"
        )
    for bug, priority in (bugs or {}).items():
        path = write_task(ready, bug)
        own = "" if priority is None else f"\npriority: {priority}"
        path.write_text(
            path.read_text().replace("milestone: 1", f"milestone: bugs\narea: factory{own}")
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the board")
    return git(repo, "rev-parse", "HEAD")


def _listed(repo: Path, *keys: str) -> None:
    (repo / ORDER).write_text("".join(f"{key}\n" for key in keys))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the list")


def _pick_order(repo: Path) -> list[str]:
    """The ready tickets in the order the run takes them, as `softfield run --dry-run` and the
    pick read them (`loop._dispatch_tickets`, `loop._cards`)."""
    ready = load_dir(repo / ".softfield" / "tasks" / "ready", 400)
    tickets = loop._dispatch_tickets(repo, ready, set(), set(), {}, loop.now())
    picked, left = [], list(ready)
    cards = loop._cards(repo, ready)
    while (task := pick_next(left, set(), set(), cards)) is not None:
        picked.append(task.id)
        left.remove(task)
    assert picked == [t.id for t in tickets]  # the pick and the dry run agree
    return picked


def _table(repo: Path) -> list[str]:
    conn = metrics.open_db(repo / "var" / "factory-metrics.sqlite")
    try:
        project = metrics.find_project(conn, _config(repo).project_name)  # the run's project
        return [] if project is None else metrics.board_order(conn, project)
    finally:
        conn.close()


# --- the file ---------------------------------------------------------------------------------


def test_no_file_is_no_list(tmp_path):
    assert order.read_order(tmp_path) is None


def test_the_list_reads_each_key_once_in_its_order(tmp_path):
    (tmp_path / ".softfield").mkdir()
    (tmp_path / ORDER).write_text("f9\n\n  bug-07-a  \nf7\nf9\n")
    assert order.read_order(tmp_path) == ["f9", "bug-07-a", "f7"]
    assert order.order_text(["f9", "bug-07-a", "f7"]) == "f9\nbug-07-a\nf7\n"


def test_places_put_what_the_list_doesnt_name_after_all_it_names(repo):
    _board(repo, {"f7": 1, "f8": 1, "f9": 1}, {BUG: 0})
    ready = load_dir(repo / ".softfield" / "tasks" / "ready", 400)
    assert order.places(["f9", "f13", BUG], ready) == {"f9": 0, BUG: 2, "f7": 3, "f8": 3}


# --- the order ------------------------------------------------------------------------------


def test_task_priority_places_a_bug_by_its_id_and_a_ticket_by_its_card(repo):
    _board(repo, {"f7": 1}, {BUG: 0})
    ready = repo / ".softfield" / "tasks" / "ready"
    bug, card = parse_task(ready / f"{BUG}.md", 400), parse_task(ready / "f7-01-a.md", 400)
    places = {"f7": 0, BUG: 1}
    assert (task_priority(card, places), task_priority(bug, places)) == (0, 1)
    assert pick_next([bug, card], set(), set(), places) == card
    pulled = pulls([bug, card], places)
    assert sorted([bug, card], key=lambda t: run_order(t, places, pulled)) == [card, bug]
    # with no place for it, a bug's own number, as before the list
    assert task_priority(bug, {"f7": 0}) == 0


def test_with_a_list_the_pick_and_the_dry_run_follow_it(repo):
    _board(repo, {"f7": 1, "f8": 2, "f9": 3}, {BUG: 0})
    assert _pick_order(repo) == [BUG, "f7-01-a", "f8-01-a", "f9-01-a"]  # the numbers
    _listed(repo, "f9", "f7", BUG, "f8")
    assert _pick_order(repo) == ["f9-01-a", "f7-01-a", BUG, "f8-01-a"]


def test_what_the_list_doesnt_name_comes_after_and_a_done_or_missing_line_is_ignored(repo):
    _board(repo, {"f7": 0, "f8": 0, "f9": 5, "f11": "done"}, {BUG: 0, "bug-08-b": 0})
    _listed(repo, "f11", "f13", "f9", "bug-08-b", "bug-99-gone")
    assert _pick_order(repo) == ["f9-01-a", "bug-08-b", BUG, "f7-01-a", "f8-01-a"]


def test_dry_run_prints_the_tickets_in_the_lists_order(repo, capsys):
    _board(repo, {"f7": 1, "f8": 2}, {BUG: 0})
    _listed(repo, "f8", BUG, "f7")
    loop.dry_run_plan(_config(repo))
    out = capsys.readouterr().out
    assert out.index("f8-01-a") < out.index(BUG) < out.index("f7-01-a")


# --- the move (D4) --------------------------------------------------------------------------


def test_the_move_writes_todays_order_in_a_commit_of_the_list_alone(repo):
    head = _board(repo, {"f7": 100, "f8": 100, "f9": 2, "f10": "idea", "f11": "done"}, {BUG: None})
    before = _pick_order(repo)
    assert before == ["f9-01-a", BUG, "f7-01-a", "f8-01-a"]
    lines = requests.move_to_list(repo)
    assert lines == [f"{requests.MOVED}: 5 cards and bugs in line"]
    # every open card, the idea too, in the order the pick took them
    assert (repo / ORDER).read_text() == f"f9\n{BUG}\nf7\nf8\nf10\n"
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "show", "--name-only", "--format=", "HEAD").split() == [ORDER]
    assert git(repo, "log", "-1", "--format=%an").strip() == "Softfield runner"
    assert git(repo, "status", "--porcelain") == ""
    assert _pick_order(repo) == before
    assert requests.move_to_list(repo) == []  # once
    assert git(repo, "rev-parse", "HEAD~1") == head


def test_the_move_places_a_bug_by_its_own_number(repo):
    _board(repo, {"f7": 100}, {BUG: 5})
    requests.move_to_list(repo)
    assert order.read_order(repo) == [BUG, "f7"]


def test_with_no_open_card_the_move_writes_nothing(repo):
    head = _board(repo, {"f11": "done"}, {BUG: None})
    assert requests.move_to_list(repo) == []
    assert not (repo / ORDER).exists()
    assert git(repo, "rev-parse", "HEAD") == head


def test_the_move_waits_for_main(repo):
    _board(repo, {"f7": 1})
    git(repo, "checkout", "-q", "-b", "elsewhere")
    assert requests.move_to_list(repo) == []
    assert not (repo / ORDER).exists()


def _second_project(root: Path) -> Path:
    """Another project's repo, not Softfield's: like the ``repo`` fixture, on main."""
    repo = root / "other-project"
    (repo / ".softfield" / "tasks" / "ready").mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "Test")
    (repo / ".softfield" / "tasks" / "ready" / ".gitkeep").write_text("")
    (repo / ".gitignore").write_text("var/\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def test_each_projects_first_apply_of_requests_moves_it_and_the_table_follows(
    repo, tmp_path_factory
):
    other = _second_project(tmp_path_factory.mktemp("projects"))
    boards: list[tuple[Path, dict[str, object]]] = [
        (repo, {"f7": 3, "f8": 1}),
        (other, {"f2": 1, "f1": 4}),
    ]
    for project, cards in boards:
        _board(project, cards)
        s = open_session(_config(project))
        try:
            loop.apply_owner_requests(s)
        finally:
            close_session(s)
    assert order.read_order(repo) == ["f8", "f7"]
    assert order.read_order(other) == ["f2", "f1"]
    assert _table(repo) == ["f8", "f7"] and _table(other) == ["f2", "f1"]


# --- a drag and the table (D5) ------------------------------------------------------------


def test_a_drags_list_is_the_order_sent_and_the_table_equals_it(repo):
    _board(repo, {"f7": 1, "f8": 2, "f9": 3, "f11": "done"}, {BUG: 0})
    _listed(repo, "f11", BUG, "f7", "f8", "f9")
    conn = metrics.open_db(repo / "var" / "factory-metrics.sqlite")
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        metrics.add_request(conn, project, "reorder", None, json.dumps(["f9", "f7"]), "2026-11-12")
    finally:
        conn.close()
    requests.apply_requests(repo, repo / "var" / "factory-metrics.sqlite", loop.now(), State())
    # the order sent, then the rest in the list's order; the done card's line dropped
    assert order.read_order(repo) == ["f9", "f7", BUG, "f8"]
    assert _pick_order(repo) == ["f9-01-a", "f7-01-a", BUG, "f8-01-a"]
    assert ORDER in git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert git(repo, "status", "--porcelain") == ""
    assert _table(repo) == ["f9", "f7", BUG, "f8"]


def test_a_sync_makes_the_table_equal_to_the_list(repo):
    _board(repo, {"f7": 1, "f8": 2})
    _listed(repo, "f8", "f7")
    s = open_session(_config(repo))  # its start syncs the cards
    try:
        assert _table(repo) == ["f8", "f7"]
        _listed(repo, "f7", "f8")
        loop.sync_cards(s)
        assert _table(repo) == ["f7", "f8"]
    finally:
        close_session(s)


def test_a_plan_branch_may_not_change_the_list():
    changes = [("100644", ORDER)]
    why = requests._outside("plan/f7", changes, "f7", replan=True, running=None)
    assert why == f"plan/f7 changes {ORDER}, {requests._OUTSIDE}: not approved"
