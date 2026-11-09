"""Tests for ``factory_dashboard.reports`` (f59-01): a week's numbers, by local Monday."""

from datetime import date, datetime, timedelta

import pytest

from factory_dashboard import queries
from factory_dashboard.reports import PLANTING, STEERING, CardTime, owner_time, series, week, weeks
from runner import metrics

FACTORY = "softfield"
TRAVEL = "travel-companion"
BOTH = [FACTORY, TRAVEL]
QWEN = "local-qwen"
OPUS = "claude-opus"
SONNET = "claude-sonnet"
# No lead ticket carries a difficulty, so savings price each line at the seed rate.
SEED = queries.SEED_DOLLARS_PER_LINE


def _at(month: int, day: int, hour: int, minute: int = 0) -> datetime:
    """Local time on that date, with that date's own offset (summer time ends 25 Oct)."""
    return datetime(2026, month, day, hour, minute).astimezone()


def _job(conn, run, ticket, role, agent, start, minutes, outcome="passed", cost=None):
    """One job on ``ticket``; ``minutes=None`` leaves it running, with no ``ended``."""
    job = metrics.start_job(
        conn,
        run,
        ticket_id=ticket,
        milestone_id=None,
        role=role,
        agent=agent,
        attempt=1,
        started=start.isoformat(),
    )
    if minutes is not None:
        ended = (start + timedelta(minutes=minutes)).isoformat()
        metrics.finish_job(conn, job, ended=ended, outcome=outcome, cost_usd=cost)


@pytest.fixture
def db(tmp_path):
    """Two projects over three weeks: 28 Sep (one job), 5 Oct (none), 12 Oct and 19 Oct.

    Week of 12 Oct, softfield: f1-01 qwen passed (30 min, 100 lines, milestone m1, which ends
    15 Oct), f1-02 Opus lead-ticket passed ($3, 60 min), f1-03 qwen timeout (60 min, a cost
    that isn't Claude's), f1-04 qwen passed Sunday 18 Oct 23:30 (15 min).
    Week of 19 Oct, softfield: f1-05 qwen passed Monday 19 Oct 00:10 (10 min), f1-06 Opus
    escalation passed ($2, 30 min), f1-07 qwen still running. travel-companion: t-01 qwen
    passed (60 min, 50 lines, milestone t1, which ends 21 Oct), t-02 Opus lead-ticket passed
    ($1, 30 min). Week of 28 Sep, travel-companion: t-00 qwen failed (20 min).
    """
    path = tmp_path / "factory-metrics.sqlite"
    conn = metrics.open_db(path)
    try:
        factory = metrics.upsert_project(conn, FACTORY)
        travel = metrics.upsert_project(conn, TRAVEL)
        m1 = metrics.upsert_milestone(conn, factory, "m1", ended=_at(10, 15, 12).isoformat())
        t1 = metrics.upsert_milestone(conn, travel, "t1", ended=_at(10, 21, 12).isoformat())
        run = metrics.upsert_run(conn, factory, "20261012-090000")
        trip = metrics.upsert_run(conn, travel, "20260929-090000")

        def ticket(project, key, milestone=None, kind="developer", merged_by=None, lines=None):
            return metrics.upsert_ticket(
                conn,
                project,
                key,
                milestone_id=milestone,
                kind=kind,
                merged_by=merged_by,
                commit="a" * 40 if merged_by else None,
                lines_changed=lines,
            )

        f101 = ticket(factory, "f1-01", m1, merged_by=QWEN, lines=100)
        _job(conn, run, f101, "developer", QWEN, _at(10, 13, 10), 30)
        f102 = ticket(factory, "f1-02", m1, kind="lead", merged_by=OPUS, lines=20)
        _job(conn, run, f102, "lead-ticket", OPUS, _at(10, 13, 11), 60, cost=3.0)
        f103 = ticket(factory, "f1-03")
        _job(conn, run, f103, "developer", QWEN, _at(10, 14, 9), 60, "timeout", cost=5.0)
        f104 = ticket(factory, "f1-04")
        _job(conn, run, f104, "developer", QWEN, _at(10, 18, 23, 30), 15)
        f105 = ticket(factory, "f1-05")
        _job(conn, run, f105, "developer", QWEN, _at(10, 19, 0, 10), 10)
        f106 = ticket(factory, "f1-06")
        _job(conn, run, f106, "escalation", OPUS, _at(10, 20, 10), 30, cost=2.0)
        f107 = ticket(factory, "f1-07")
        _job(conn, run, f107, "developer", QWEN, _at(10, 21, 9), None)

        t00 = ticket(travel, "t-00")
        _job(conn, trip, t00, "developer", QWEN, _at(9, 29, 10), 20, "failed")
        t01 = ticket(travel, "t-01", t1, merged_by=QWEN, lines=50)
        _job(conn, trip, t01, "developer", QWEN, _at(10, 20, 9), 60)
        t02 = ticket(travel, "t-02", t1, kind="lead", merged_by=OPUS, lines=10)
        _job(conn, trip, t02, "lead-ticket", OPUS, _at(10, 20, 11), 30, cost=1.0)
    finally:
        conn.close()
    return queries.connect(path)


def test_a_week_for_two_projects_counts_both(db):
    found = week(db, BOTH, date(2026, 10, 19))
    assert found.monday == date(2026, 10, 19)
    assert found.milestones_done == 1  # t1
    assert found.merged == {QWEN: 2, OPUS: 1}  # f1-05, t-01; t-02 (an escalation isn't one)
    assert found.escalations == 1
    assert found.timeouts == 0


def test_a_week_for_one_project_counts_only_its_own(db):
    found = week(db, [FACTORY], date(2026, 10, 19))
    assert found.milestones_done == 0  # t1 is travel-companion's
    assert found.merged == {QWEN: 1}  # f1-05 only
    assert found.dollars == {"escalation": 2.0}
    assert found.savings == 0
    assert week(db, [TRAVEL], date(2026, 10, 19)).merged == {QWEN: 1, OPUS: 1}


def test_sunday_late_counts_in_its_week_and_monday_early_in_the_next(db):
    # f1-04 starts Sunday 18 Oct 23:30 local, f1-05 Monday 19 Oct 00:10 local: in UTC both
    # fall on Sunday, so a week cut in UTC would put f1-05 in the week of 12 Oct.
    assert week(db, [FACTORY], date(2026, 10, 12)).merged == {QWEN: 2, OPUS: 1}
    assert week(db, [FACTORY], date(2026, 10, 19)).merged == {QWEN: 1}


def test_dollars_are_by_role_and_only_claudes(db):
    found = week(db, BOTH, date(2026, 10, 19))
    assert found.dollars == {"escalation": pytest.approx(2.0), "lead-ticket": pytest.approx(1.0)}
    # f1-03's $5 is a local agent's, so the week of 12 Oct has only the lead ticket's $3.
    assert week(db, BOTH, date(2026, 10, 12)).dollars == {"lead-ticket": pytest.approx(3.0)}


def test_hours_are_by_agent_and_leave_out_a_running_job(db):
    found = week(db, BOTH, date(2026, 10, 19))
    # qwen: f1-05 10 min + t-01 60 min; f1-07 has no ended. Opus: 30 + 30 min.
    assert found.hours == {QWEN: pytest.approx(70 / 60), OPUS: pytest.approx(1.0)}


def test_developer_attempts_and_passed_are_by_agent(db):
    found = week(db, BOTH, date(2026, 10, 12))
    assert found.attempts == {QWEN: 3}  # f1-01, f1-03, f1-04; the lead ticket isn't one
    assert found.passed == {QWEN: 2}
    assert found.rate == pytest.approx(2 / 3)
    later = week(db, BOTH, date(2026, 10, 19))
    assert later.attempts == {QWEN: 3}  # f1-05, f1-07 (running), t-01
    assert later.passed == {QWEN: 2}


def test_a_week_with_no_developer_attempt_has_no_rate(db):
    found = week(db, BOTH, date(2026, 10, 5))
    assert found.attempts == {}
    assert found.rate is None


def test_each_number_has_the_week_before(db):
    found = week(db, BOTH, date(2026, 10, 19))
    before = found.previous
    assert before is not None
    assert before.monday == date(2026, 10, 12)
    assert before.previous is None
    assert before.milestones_done == 1  # m1
    assert before.merged == {QWEN: 2, OPUS: 1}
    assert before.timeouts == 1
    assert before.escalations == 0
    assert before.hours == {QWEN: pytest.approx(1.75), OPUS: pytest.approx(1.0)}
    assert before.savings == pytest.approx(100 * SEED)


def test_savings_sum_the_milestones_that_ended_in_the_week(db):
    assert week(db, BOTH, date(2026, 10, 12)).savings == pytest.approx(100 * SEED)  # m1
    assert week(db, BOTH, date(2026, 10, 19)).savings == pytest.approx(50 * SEED)  # t1
    assert week(db, BOTH, date(2026, 10, 19)).savings == pytest.approx(
        queries.savings(db, TRAVEL, "t1").net
    )


def _mondays_since(first: date) -> list[date]:
    today = datetime.now().astimezone().date()
    monday = today - timedelta(days=today.weekday())
    found = []
    while monday >= first:
        found.append(monday)
        monday -= timedelta(days=7)
    return found


def test_weeks_lists_every_monday_since_the_first_job_newest_first(db):
    found = weeks(db, BOTH)
    assert found == _mondays_since(date(2026, 9, 28))
    assert date(2026, 10, 5) in found  # a week with no job
    assert weeks(db, [FACTORY])[-1] == date(2026, 10, 12)
    assert weeks(db, []) == []


def test_series_is_the_same_weeks_oldest_first(db):
    found = series(db, BOTH)
    assert [w.monday for w in found] == _mondays_since(date(2026, 9, 28))[::-1]
    assert [w.milestones_done for w in found[:4]] == [0, 0, 1, 1]
    assert found[2].previous is not None
    assert found[2].previous.monday == date(2026, 10, 5)


# --- the owner's time (f86-01) ----------------------------------------------------------


def _owner(tmp_path, presses=(), items=(), titles=()):
    """The metrics database at ``tmp_path`` (the ``db`` fixture's, when a test uses both) with
    the owner's ``presses`` (project, kind, subject, created: a datetime or the exact text),
    the desk's ``items`` (project, created, resolved or None) and cards' ``titles``."""
    path = tmp_path / "factory-metrics.sqlite"
    conn = metrics.open_db(path)
    try:
        ids = {name: metrics.upsert_project(conn, name) for name in BOTH}
        for project, kind, subject, at in presses:
            created = at if isinstance(at, str) else at.isoformat()
            metrics.add_request(conn, ids[project], kind, subject, None, created)
        for number, (project, created, resolved) in enumerate(items):
            item = metrics.upsert_owner_item(
                conn, ids[project], "verdict", f"item-{number}", created=created.isoformat()
            )
            if resolved is not None:
                metrics.resolve_owner_item(conn, item, resolved.isoformat())
        for project, key, title in titles:
            metrics.upsert_milestone(conn, ids[project], key, title=title)
    finally:
        conn.close()
    return queries.connect(path)


WEEK = date(2026, 10, 19)


def test_three_actions_make_22_minutes_in_two_sittings(tmp_path):
    at = [_at(10, 20, 10, 0), _at(10, 20, 10, 12), _at(10, 20, 11, 0)]
    db = _owner(tmp_path, presses=[(FACTORY, "message", "f158", t) for t in at])
    found = owner_time(db, [FACTORY], WEEK)
    # 10:00 starts a sitting (5), 10:12 continues it (12), 11:00 is 48 min later (5).
    assert found.hours == pytest.approx(22 / 60)
    assert found.sittings == 2
    assert found.days == 1
    assert found.actions == {"message": 3}


def test_offsets_are_ordered_and_subtracted_as_datetimes(tmp_path):
    later, earlier = "2026-10-20T10:00:00+01:00", "2026-10-20T09:10:00+00:00"
    db = _owner(
        tmp_path, presses=[(FACTORY, "message", "f1", later), (FACTORY, "approve", "f1", earlier)]
    )
    found = owner_time(db, [FACTORY], WEEK)
    # 09:00 UTC, then 09:10 UTC: 5 + 10 minutes. As text, 09:10 would come first and the
    # gap be -10 minutes (-5 minutes in all).
    assert found.hours == pytest.approx(15 / 60)
    assert found.sittings == 1


def test_by_card_has_the_cards_title_planting_and_steering_most_minutes_first(tmp_path):
    db = _owner(
        tmp_path,
        presses=[
            (FACTORY, "message", "f158-milestones-don-t", _at(10, 20, 10, 0)),
            (FACTORY, "approve", "f158-milestones-don-t", _at(10, 20, 10, 12)),
            (FACTORY, "message", "f158", _at(10, 20, 11, 0)),
            # a plant goes to Planting even when its subject looks like a card
            (FACTORY, "plant", "f200-a-new-idea", _at(10, 20, 14, 0)),
            (FACTORY, "pause", None, _at(10, 20, 15, 0)),
            (FACTORY, "reserve", "five_hour", _at(10, 20, 15, 10)),
        ],
        titles=[(FACTORY, "f158-milestones-don-t", "Milestones don't matter")],
    )
    assert owner_time(db, [FACTORY], WEEK).by_card == [
        CardTime("f158", FACTORY, "Milestones don't matter", 22.0),
        CardTime(None, None, STEERING, 15.0),  # 5 for the pause, 10 for the reserve
        CardTime(None, None, PLANTING, 5.0),
    ]


def test_one_card_key_on_two_projects_is_two_cards_each_with_its_project(tmp_path):
    db = _owner(
        tmp_path,
        presses=[
            (FACTORY, "message", "f1", _at(10, 20, 10, 0)),
            (TRAVEL, "message", "f1-first-trip", _at(10, 20, 10, 10)),
        ],
        titles=[(FACTORY, "f1", "Factory line"), (TRAVEL, "f1-first-trip", "First trip")],
    )
    assert owner_time(db, BOTH, WEEK).by_card == [
        CardTime("f1", TRAVEL, "First trip", 10.0),
        CardTime("f1", FACTORY, "Factory line", 5.0),
    ]


def test_one_project_counts_its_own_actions_and_items_and_two_count_both(tmp_path):
    db = _owner(
        tmp_path,
        presses=[
            (FACTORY, "message", "f1", _at(10, 20, 10, 0)),
            (TRAVEL, "message", "f1", _at(10, 20, 10, 10)),
        ],
        items=[
            (FACTORY, _at(10, 20, 8), _at(10, 20, 9)),
            (TRAVEL, _at(10, 20, 8), _at(10, 20, 11)),
        ],
    )
    factory, travel = owner_time(db, [FACTORY], WEEK), owner_time(db, [TRAVEL], WEEK)
    both = owner_time(db, BOTH, WEEK)
    # One sitting over both projects: the switch to travel-companion counts its 10 min gap.
    assert [f.hours for f in (factory, travel, both)] == pytest.approx([5 / 60, 10 / 60, 15 / 60])
    assert [f.sittings for f in (factory, travel, both)] == [1, 1, 1]
    assert [f.waited_items for f in (factory, travel, both)] == [1, 1, 2]
    assert [f.waited_hours for f in (factory, travel, both)] == pytest.approx([1.0, 3.0, 2.0])


def test_waited_is_the_median_over_items_resolved_in_the_week(tmp_path):
    db = _owner(
        tmp_path,
        items=[
            (FACTORY, _at(10, 19, 8), _at(10, 19, 9)),  # 1 h
            (FACTORY, _at(10, 20, 8), _at(10, 20, 10)),  # 2 h
            (FACTORY, _at(10, 21, 8), _at(10, 21, 14)),  # 6 h
            (FACTORY, _at(10, 17, 8), _at(10, 18, 14)),  # 30 h, resolved the week before
            (FACTORY, _at(10, 20, 8), None),  # still open
        ],
    )
    found = owner_time(db, [FACTORY], WEEK)
    assert found.waited_items == 3
    assert found.waited_hours == pytest.approx(2.0)
    empty = owner_time(db, [FACTORY], date(2026, 10, 26))
    assert empty.waited_items == 0
    assert empty.waited_hours is None


def test_week_has_the_owners_time_with_the_week_before(tmp_path):
    db = _owner(
        tmp_path,
        presses=[
            (FACTORY, "message", "f1", _at(10, 13, 10, 0)),
            (FACTORY, "message", "f1", _at(10, 20, 10, 0)),
            (FACTORY, "message", "f1", _at(10, 20, 10, 30)),
        ],
        items=[
            (FACTORY, _at(10, 14, 8), _at(10, 14, 11)),
            (FACTORY, _at(10, 21, 8), _at(10, 21, 9)),
        ],
    )
    owner = week(db, [FACTORY], WEEK).owner
    assert owner is not None
    assert owner.hours == pytest.approx(10 / 60)
    assert owner.hours_before == pytest.approx(5 / 60)
    assert owner.waited_hours == pytest.approx(1.0)
    assert owner.waited_hours_before == pytest.approx(3.0)
    first = week(db, [FACTORY], date(2026, 10, 12)).owner
    assert first is not None
    assert first.hours_before is None  # the week of 5 Oct wasn't recorded
    assert first.waited_hours_before is None
    assert week(db, [FACTORY], date(2026, 10, 5)).owner is None


def test_series_has_the_owners_hours_from_the_first_recorded_week(db, tmp_path):
    # ``db`` writes the jobs (weeks from 28 Sep); ``_owner`` adds to the same file.
    conn = _owner(
        tmp_path,
        presses=[
            (TRAVEL, "message", "f1", _at(10, 13, 10, 0)),
            (FACTORY, "message", "f1", _at(10, 20, 10, 0)),
        ],
    )
    found = series(conn, BOTH)
    assert [w.owner for w in found[:2]] == [None, None]  # 28 Sep, 5 Oct
    assert [w.owner.hours for w in found[2:4] if w.owner] == [
        pytest.approx(5 / 60),
        pytest.approx(5 / 60),
    ]
    assert all(w.owner is not None and w.owner.hours == 0 for w in found[4:])
