"""The picker (ADR 22 item 2, f8 D2): which job runs next and why. It is pure, so no repo."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from runner import allowance
from runner.dispatch import Pick, Queued, Ticket, Windows, pick, plan

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
OPEN = Windows()  # nothing holds Claude back


def _row(kind: str, subject: str, *, minutes_ago: int = 10, not_before: datetime | None = None):
    created = (NOW - timedelta(minutes=minutes_ago)).isoformat()
    until = None if not_before is None else not_before.isoformat()
    return Queued(kind, subject, f"why {kind} {subject}", created, until)


def _lead(task_id: str, priority: int = 100, **kw) -> Ticket:
    return Ticket(task_id, lead=True, priority=priority, **kw)


def _dev(task_id: str, priority: int = 100, **kw) -> Ticket:
    return Ticket(task_id, lead=False, priority=priority, **kw)


def _week(used: float) -> allowance.Window:
    """Claude's week, a day before its reset, with 30% kept back for support roles."""
    resets = NOW + timedelta(days=1)
    return allowance.Window(
        "seven_day", "fixed", allowance.WEEK, resets, 1.0, used, reserve=0.3, measured=True
    )


def _order(lines) -> list[tuple[str, str]]:
    return [(line.pick.kind, line.pick.subject) for line in lines]


# --- today's order, first (ADR 22, Risk) ------------------------------------------------


def test_a_parked_escalation_past_its_reset_goes_before_a_ticket():
    """`_resume_support` runs before `_next_task`."""
    parked = _row("escalation", "f1-21", not_before=NOW - timedelta(minutes=1))
    got = pick([parked], [_lead("f1-22", 1)], OPEN, NOW)
    assert got == Pick("escalation", "f1-21", "why escalation f1-21")


def test_a_due_review_goes_before_the_next_ticket():
    """`work_queue` stops for `_due_review` before loading the ready tickets (f4-20)."""
    got = pick([_row("review", "f9")], [_dev("f10-01", 1), _lead("f10-02", 1)], OPEN, NOW)
    assert got is not None and (got.kind, got.subject) == ("review", "f9")


def test_lead_work_goes_before_a_developer_ticket():
    """ADR 16 item 2: lead work first, even past a developer ticket of higher priority."""
    got = pick([], [_dev("f8-07", 1), _lead("f8-02", 2)], OPEN, NOW)
    assert got == Pick("ticket", "f8-02", "priority 2, lead ticket")


def test_developers_run_meanwhile_while_claude_is_limited():
    """`_next_task`: while a job is parked for a limit, only developer tickets run."""
    limited = Windows(limited_until=NOW + timedelta(hours=2))
    lines = plan([], [_lead("f8-02", 1), _dev("f8-07", 2)], limited, NOW)
    assert _order(lines) == [("ticket", "f8-02"), ("ticket", "f8-07")]
    assert lines[0].waits == "Claude is limited until Mon 5 Oct 14:00"
    assert lines[1].waits is None
    assert pick([], [_lead("f8-02", 1), _dev("f8-07", 2)], limited, NOW) == Pick(
        "ticket", "f8-07", "priority 2, developer ticket"
    )


def test_at_the_weeks_reserve_a_lead_ticket_waits_and_support_jobs_may_use_it():
    """ADR 15 items 4 and 5: the reserve is the support roles'; a lead ticket waits for the
    owner, and developer tickets go first."""
    windows = Windows(claude=(_week(0.75),))
    lines = plan([_row("checkpoint", "f8")], [_lead("f8-02"), _dev("f8-07")], windows, NOW)
    waits = {line.pick.subject: line.waits for line in lines}
    assert waits["f8"] is None
    assert waits["f8-02"] is not None and "week 75% used" in waits["f8-02"]
    assert waits["f8-07"] is None


def _week_at_33(used: float) -> allowance.Window:
    """Claude's week with its pace line at 33% now (0.7 × (2.3/7 + 1/7))."""
    resets = NOW + 4.7 * timedelta(days=1)
    return replace(_week(used), resets_at=resets)


def test_over_its_pace_line_a_lead_ticket_waits_and_names_the_line():
    """ADR 44 item 1: 65% is short of the reserve, and the line holds it all the same."""
    lines = plan([], [_lead("f8-02"), _dev("f8-07")], Windows(claude=(_week_at_33(0.65),)), NOW)
    waits = {line.pick.subject: line.waits for line in lines}
    assert waits == {"f8-02": "claude: week 65% used, over its pace line of 33%", "f8-07": None}


def test_in_the_weeks_last_10_percent_a_lead_ticket_may_use_the_whole_reserve():
    """ADR 44 item 2: the last 17 hours or so."""
    last = replace(_week(0.72), resets_at=NOW + timedelta(hours=16))
    assert pick([], [_lead("f8-02")], Windows(claude=(last,)), NOW) is not None
    full = replace(last, used=1.0)
    assert pick([], [_lead("f8-02")], Windows(claude=(full,)), NOW) is None


def test_over_the_line_a_planner_job_a_review_and_a_checkpoint_still_run():
    """ADR 44 items 4 and 5."""
    queued = [_row("planner", "f9"), _row("review", "f7"), _row("checkpoint", "f8")]
    lines = plan(queued, [_lead("f8-02")], Windows(claude=(_week_at_33(0.65),)), NOW)
    waits = {line.pick.subject: line.waits for line in lines}
    assert (waits["f9"], waits["f7"], waits["f8"]) == (None, None, None)
    assert waits["f8-02"] is not None


def test_over_the_line_a_ticket_parked_mid_work_goes_at_its_reset():
    """ADR 44 item 7: work already begun goes on, whatever the pace."""
    parked = _lead("f8-02", not_before=NOW - timedelta(minutes=1))
    assert pick([], [parked], Windows(claude=(_week_at_33(0.65),)), NOW) == Pick(
        "ticket", "f8-02", "priority 100, lead ticket, its reset has passed"
    )


def test_the_owners_switch_lets_a_lead_ticket_use_the_reserve():
    windows = Windows(claude=(_week(0.75),), reserves=frozenset({"seven_day"}))
    got = pick([], [_lead("f8-02"), _dev("f8-07")], windows, NOW)
    assert got is not None and got.subject == "f8-02"


def test_support_jobs_wait_while_claude_is_limited_too():
    limited = Windows(limited_until=NOW + timedelta(hours=2))
    lines = plan([_row("escalation", "f1-21")], [], limited, NOW)
    assert lines[0].waits == "Claude is limited until Mon 5 Oct 14:00"
    assert pick([_row("escalation", "f1-21")], [], limited, NOW) is None


def test_a_parked_ticket_past_its_reset_goes_before_other_tickets():
    """`_next_task`: due parked tickets go first."""
    parked = _dev("f8-07", 5, not_before=NOW - timedelta(minutes=1))
    got = pick([], [_lead("f8-02", 1), parked], OPEN, NOW)
    assert got == Pick("ticket", "f8-07", "priority 5, developer ticket, its reset has passed")


# --- D2's order --------------------------------------------------------------------------


def test_every_kind_queued_comes_out_in_d2s_order():
    queued = [
        _row("review", "f7", minutes_ago=50),
        _row("checkpoint", "f8", minutes_ago=40),
        _row("direction", "f8-05", minutes_ago=30),
        _row("escalation", "f8-04", minutes_ago=20),
        _row("planner", "f9", minutes_ago=10),
    ]
    tickets = [_dev("f8-07", 1), _lead("f8-02", 2)]
    lines = plan(queued, tickets, OPEN, NOW)
    assert _order(lines) == [
        ("planner", "f9"),
        ("escalation", "f8-04"),
        ("direction", "f8-05"),
        ("checkpoint", "f8"),
        ("review", "f7"),
        ("ticket", "f8-02"),
        ("ticket", "f8-07"),
    ]
    assert all(line.waits is None for line in lines)
    assert lines[0].pick.reason == "why planner f9"
    assert pick(queued, tickets, OPEN, NOW) == lines[0].pick


def test_the_same_kind_goes_by_age():
    queued = [_row("checkpoint", "new", minutes_ago=1), _row("checkpoint", "old", minutes_ago=9)]
    assert _order(plan(queued, [], OPEN, NOW)) == [("checkpoint", "old"), ("checkpoint", "new")]


def test_tickets_keep_the_run_order_they_are_given_within_lead_and_developer():
    """The caller orders them as `pick_next` does (priority, milestone, id)."""
    tickets = [_dev("f8-07", 1), _lead("f8-03", 1), _dev("f8-06", 2), _lead("f8-02", 2)]
    assert [line.pick.subject for line in plan([], tickets, OPEN, NOW)] == [
        "f8-03",
        "f8-02",
        "f8-07",
        "f8-06",
    ]


def test_a_row_not_before_a_future_time_is_skipped_and_says_until_when():
    parked = _row("escalation", "f1-21", not_before=NOW + timedelta(hours=3))
    lines = plan([parked], [_dev("f8-07")], OPEN, NOW)
    assert _order(lines) == [("escalation", "f1-21"), ("ticket", "f8-07")]
    assert lines[0].waits == "waits until Mon 5 Oct 15:00"
    assert pick([parked], [_dev("f8-07")], OPEN, NOW) == Pick(
        "ticket", "f8-07", "priority 100, developer ticket"
    )


def test_a_parked_ticket_before_its_reset_is_skipped_and_says_until_when():
    parked = _lead("f8-02", 1, not_before=NOW + timedelta(hours=3))
    lines = plan([], [parked], OPEN, NOW)
    assert lines[0].waits == "waits until Mon 5 Oct 15:00"
    assert pick([], [parked], OPEN, NOW) is None


def test_a_ticket_that_waits_is_never_picked_and_keeps_its_reason():
    waiting = _dev("f8-07", 1, waits="waiting on f8-06")
    lines = plan([], [waiting, _dev("f8-08", 2)], OPEN, NOW)
    assert [line.waits for line in lines] == ["waiting on f8-06", None]
    got = pick([], [waiting, _dev("f8-08", 2)], OPEN, NOW)
    assert got is not None and got.subject == "f8-08"


def test_an_unknown_kind_is_listed_last_and_never_picked():
    lines = plan([_row("mystery", "x"), _row("review", "f7")], [_dev("f8-07")], OPEN, NOW)
    assert _order(lines)[-1] == ("mystery", "x")
    assert lines[-1].waits == "unknown kind of job"


def test_nothing_queued_and_no_ticket_picks_nothing():
    assert plan([], [], OPEN, NOW) == []
    assert pick([], [], OPEN, NOW) is None


def test_while_the_owner_pauses_every_line_waits_and_nothing_is_picked():
    """ADR 22 item 5 (f5-18): pause is a state of the pick, whatever each job waited for."""
    queued = [_row("checkpoint", "f8"), _row("escalation", "f8-04"), _row("mystery", "x")]
    tickets = [_lead("f8-02", 1), _dev("f8-07", 2), _dev("f8-08", 3, waits="waiting on f8-06")]
    limited = Windows(limited_until=NOW + timedelta(hours=2))
    for windows in (OPEN, limited):
        lines = plan(queued, tickets, windows, NOW, paused=True)
        assert _order(lines) == _order(plan(queued, tickets, windows, NOW))  # the same order
        assert [line.waits for line in lines] == ["paused by you"] * 6
        assert pick(queued, tickets, windows, NOW, paused=True) is None
    assert pick(queued, tickets, OPEN, NOW, paused=False) is not None


def test_a_ticket_waiting_for_its_gates_goes_right_after_the_planner_jobs():
    """bug-04: its gates take about 5 minutes and no model, and main moving on throws its
    finished work away."""
    queued = [_row("review", "f7"), _row("escalation", "f8-04"), _row("planner", "f9")]
    tickets = [_lead("f8-02", 1), _dev("f8-07", 5, regate=True)]
    lines = plan(queued, tickets, OPEN, NOW)
    assert _order(lines) == [
        ("planner", "f9"),
        ("ticket", "f8-07"),
        ("escalation", "f8-04"),
        ("review", "f7"),
        ("ticket", "f8-02"),
    ]
    assert lines[1].pick.reason == "its gates wait, developer ticket"
    assert pick(queued[:2], tickets, OPEN, NOW) == lines[1].pick


def test_a_regate_ticket_never_waits_for_claude_but_waits_for_what_holds_it():
    limited = Windows(limited_until=NOW + timedelta(hours=2))
    held = _lead("f8-02", 1, regate=True)
    assert pick([], [held], limited, NOW) == Pick("ticket", "f8-02", "its gates wait, lead ticket")
    assert pick([], [replace(held, waits="paused")], limited, NOW) is None
    assert pick([], [held], OPEN, NOW, paused=True) is None


def test_while_the_owner_pauses_a_planner_job_still_goes_and_keeps_its_own_wait():
    """ADR 22 item 5's ⚑ (f6-14): the owner pauses to talk a change through on /planning, so
    their messages still reach the lead; a ticket, a checkpoint and an escalation wait."""
    queued = [_row("checkpoint", "f8"), _row("escalation", "f8-04"), _row("planner", "f6/1")]
    tickets = [_lead("f8-02", 1), _dev("f8-07", 2)]
    lines = plan(queued, tickets, OPEN, NOW, paused=True)
    waits = {line.pick.subject: line.waits for line in lines}
    assert waits == {
        "f6/1": None,
        "f8-04": "paused by you",
        "f8": "paused by you",
        "f8-02": "paused by you",
        "f8-07": "paused by you",
    }
    assert pick(queued, tickets, OPEN, NOW, paused=True) == Pick(
        "planner", "f6/1", "why planner f6/1"
    )
    # Its own wait still holds it: a row parked for a limit, or Claude limited
    parked = _row("planner", "f6/2", not_before=NOW + timedelta(hours=3))
    [line] = plan([parked], [], OPEN, NOW, paused=True)
    assert line.waits == "waits until Mon 5 Oct 15:00"
    limited = Windows(limited_until=NOW + timedelta(hours=2))
    [line] = plan([_row("planner", "f6/1")], [], limited, NOW, paused=True)
    assert line.waits == "Claude is limited until Mon 5 Oct 14:00"
    assert pick([parked], tickets, OPEN, NOW, paused=True) is None


# --- The fast lane (ADR 35) --------------------------------------------------------------

LANE_QUEUE = [
    _row("review", "f7", minutes_ago=50),
    _row("checkpoint", "f8", minutes_ago=40),
    _row("direction", "f8-05", minutes_ago=30),
    _row("escalation", "f8-04", minutes_ago=20),
    _row("planner", "f9", minutes_ago=10),
]


def test_a_fast_lane_ticket_goes_before_the_planner_a_checkpoint_and_a_review():
    """ADR 35 item 2: before everything, a parked ticket whose reset has passed included."""
    parked = _dev("f8-07", 1, not_before=NOW - timedelta(minutes=1))
    tickets = [parked, _lead("f8-02", 2), _dev("f172-01", 50)]
    got = pick(LANE_QUEUE, tickets, OPEN, NOW, first={"f172-01"})
    assert got == Pick("ticket", "f172-01", "fast lane, priority 50, developer ticket")
    lines = plan(LANE_QUEUE, tickets, OPEN, NOW, first={"f172-01"})
    assert _order(lines)[0] == ("ticket", "f172-01")
    assert len(lines) == 8


def test_a_direction_or_escalation_for_a_lane_ticket_goes_with_it():
    """ADR 35 item 2: it is that ticket's own work; one for another ticket keeps its place."""
    lines = plan(LANE_QUEUE, [_lead("f8-02", 2)], OPEN, NOW, first={"f8-05", "f8-02"})
    assert _order(lines) == [
        ("direction", "f8-05"),
        ("ticket", "f8-02"),
        ("planner", "f9"),
        ("escalation", "f8-04"),
        ("checkpoint", "f8"),
        ("review", "f7"),
    ]
    got = pick(LANE_QUEUE, [], OPEN, NOW, first={"f8-05"})
    assert got == Pick("direction", "f8-05", "why direction f8-05")


def test_inside_the_lane_the_order_the_caller_gives():
    """ADR 35 item 3: the board's order (`pick_next`'s), not lead before developer."""
    tickets = [_dev("f90-01", 3), _lead("f142-01", 9), _lead("f8-02", 1)]
    lines = plan([], tickets, OPEN, NOW, first={"f90-01", "f142-01"})
    assert [line.pick.subject for line in lines] == ["f90-01", "f142-01", "f8-02"]


def test_without_a_lane_the_lines_are_todays():
    queued = [*LANE_QUEUE, _row("mystery", "x")]
    tickets = [
        _dev("f8-07", 1),
        _lead("f8-02", 2),
        _dev("f8-09", 5, regate=True),
        _dev("f8-08", 4, not_before=NOW - timedelta(minutes=1)),
    ]
    assert plan(queued, tickets, OPEN, NOW, first=()) == plan(queued, tickets, OPEN, NOW)


def test_a_lane_lead_ticket_waits_for_a_real_limit_and_the_line_goes_on():
    """ADR 35 items 4 and 5: both reserves, but not a limit; a developer ticket goes meanwhile."""
    limited = Windows(limited_until=NOW + timedelta(hours=2))
    tickets = [_lead("f172-01", 9), _dev("f8-07", 2)]
    lines = plan([], tickets, limited, NOW, first={"f172-01"})
    assert lines[0].waits == "Claude is limited until Mon 5 Oct 14:00"
    got = pick([], tickets, limited, NOW, first={"f172-01"})
    assert got is not None and got.subject == "f8-07"
    at_reserve = Windows(claude=(_week(0.75),))
    assert pick([], tickets, at_reserve, NOW, first={"f172-01"}) == Pick(
        "ticket", "f172-01", "fast lane, priority 9, lead ticket"
    )


def test_while_the_owner_pauses_the_lane_waits_and_the_planner_goes():
    """ADR 35 item 5: the pause stays the owner's one stop."""
    tickets = [_lead("f172-01", 9)]
    lines = plan(LANE_QUEUE, tickets, OPEN, NOW, paused=True, first={"f172-01", "f8-05"})
    assert {line.pick.subject: line.waits for line in lines}["f172-01"] == "paused by you"
    got = pick(LANE_QUEUE, tickets, OPEN, NOW, paused=True, first={"f172-01", "f8-05"})
    assert got is not None and got.kind == "planner"
