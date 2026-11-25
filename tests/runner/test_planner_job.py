"""The planner's and the setup's jobs (`runner/planner_job.py`): where the work stands, a
merged ticket's minutes, and a plan's clash both sides added. Planner jobs the queue runs are
in `test_loop.py`."""

import re
import sqlite3
from datetime import timedelta
from pathlib import Path

from runner import metrics, planner_job
from runner.state import State
from tests.runner.conftest import THURSDAY, git, write_task
from tests.runner.test_loop import _config, _milestone_doc


def _work_in_two_cards(repo: Path) -> None:
    """M1 (building, second in the queue) with three ready tickets, one waiting on another; M2
    (ready, first) with a lead ticket; M3 an idea with none, not on the list; M4 building,
    last."""
    _milestone_doc(repo, "m1-first", "> **State:** building")
    _milestone_doc(repo, "m2", "> **State:** ready")
    _milestone_doc(repo, "m3", "> **State:** idea")
    _milestone_doc(repo, "m4", "> **State:** building")
    (repo / ".softfield" / "order.txt").write_text("m2\nm4\nm1\n")
    ready = repo / ".softfield" / "tasks" / "ready"
    write_task(ready, "m1-01-a")
    write_task(ready, "m1-02-b", "[m1-01-a]")
    write_task(ready, "m1-03-d")
    path = write_task(ready, "m2-01-c")
    path.write_text(path.read_text().replace("milestone: 1\n", "milestone: 2\nagent: lead\n"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "two cards")


def test_where_the_work_stands_is_the_runners_own_order_and_reading_it_changes_nothing(repo):
    """F21 D1: the ticket in flight, then the others as `run_order` sorts them (the card's
    place first), each with its milestone and who does it; every card in the queue's order,
    without a number (F222 D7); nothing written."""
    _work_in_two_cards(repo)
    cfg = _config(repo)
    state = State(in_flight={"kind": "local", "ticket": "m1-01-a", "agent": "local-qwen"})
    block = planner_job.work_stands(cfg, state, [12.0, 20.0, 31.0])
    lines = block.splitlines()
    flying = "In flight: m1-01-a (m1-first, developer), now with local-qwen."
    listed = [
        "1. m2-01-c (m2, lead)",
        "2. m1-02-b (m1-first, developer): waits for m1-01-a",
        "3. m1-03-d (m1-first, developer)",
    ]
    assert [line for line in lines if re.match(r"\d+\. ", line)] == listed
    assert lines.index(flying) < lines.index(listed[0])
    assert {"- building: M4, M1", "- ready: M2", "- idea: M3"} <= set(lines)
    assert "priority" not in block
    assert any("about 20 minutes" in line for line in lines)
    assert git(repo, "status", "--porcelain", "--ignored") == ""  # no state.json, no database
    assert state == State(in_flight={"kind": "local", "ticket": "m1-01-a", "agent": "local-qwen"})


def test_a_ticket_behind_its_direction_says_so_where_the_work_stands(repo):
    _work_in_two_cards(repo)
    behind = {"m1-03-d": "waits for its direction"}
    block = planner_job.work_stands(_config(repo), State(), [], behind)
    assert "In flight: nothing." in block and "No ticket has merged yet" in block
    assert "m1-03-d (m1-first, developer): waits for its direction" in block
    assert "2. m1-01-a (m1-first, developer)\n" in block  # not in flight: listed


def _merged_ticket(
    conn: sqlite3.Connection, project: int, run: int, n: int, minutes: list[int], state: str
) -> None:
    """A ticket whose jobs each took ``minutes``, the last ending ``n`` hours after THURSDAY."""
    ticket = metrics.upsert_ticket(conn, project, f"m1-{n:02}-t", state=state)
    end = THURSDAY + timedelta(hours=n)
    for attempt, took in enumerate(minutes, 1):
        job = metrics.start_job(
            conn,
            run,
            ticket_id=ticket,
            milestone_id=None,
            role="developer",
            agent="local-qwen",
            attempt=attempt,
            started=(end - timedelta(minutes=took)).isoformat(),
        )
        metrics.finish_job(conn, job, ended=end.isoformat(), outcome="passed")


def test_a_merged_tickets_minutes_are_its_jobs_added_up_for_the_last_twenty(repo):
    """F21 D1: the duration behind the median: every job of a done ticket (attempts, a
    direction), latest merged first; a ticket not merged, or a job still running, counts
    for nothing."""
    conn = metrics.open_db(_config(repo).metrics_db)
    project = metrics.upsert_project(conn, repo.name, repo=str(repo))
    assert planner_job.ticket_minutes(conn, project) == []
    run = metrics.upsert_run(conn, project, "earlier")
    _merged_ticket(conn, project, run, 1, [10, 20], "done")
    _merged_ticket(conn, project, run, 2, [500], "ready")
    _merged_ticket(conn, project, run, 3, [7], "done")
    running = metrics.upsert_ticket(conn, project, "m1-04-t", state="done")
    metrics.start_job(
        conn,
        run,
        ticket_id=running,
        milestone_id=None,
        role="developer",
        agent="local-qwen",
        attempt=1,
        started=THURSDAY.isoformat(),
    )
    other = metrics.upsert_project(conn, "another")
    _merged_ticket(conn, other, metrics.upsert_run(conn, other, "its"), 9, [99], "done")
    assert planner_job.ticket_minutes(conn, project) == [7.0, 30.0]
    for n in range(10, 31):
        _merged_ticket(conn, project, run, n, [n], "done")
    assert planner_job.ticket_minutes(conn, project) == [float(n) for n in range(30, 10, -1)]
    conn.close()


def test_both_added_keeps_each_sides_added_lines_ours_first():
    text = "a\n<<<<<<< ours\nnote\n||||||| base\n=======\nplan\n>>>>>>> theirs\nb\n"
    assert planner_job.both_added(text) == "a\nnote\nplan\nb\n"


def test_both_added_refuses_a_conflict_on_a_line_the_base_held():
    text = "<<<<<<< ours\na queue\n||||||| base\none queue\n=======\ntwo queues\n>>>>>>> theirs\n"
    assert planner_job.both_added(text) is None


def test_both_added_refuses_an_unfinished_conflict():
    assert planner_job.both_added("<<<<<<< ours\nnote\n||||||| base\n=======\nplan\n") is None


def test_both_added_puts_theirs_first_when_asked():
    text = "<<<<<<< plan\nplan\n||||||| base\n=======\nnote\n>>>>>>> main\n"
    assert planner_job.both_added(text, theirs_first=True) == "note\nplan\n"
