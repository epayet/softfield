"""How the runner waits on Claude's limits (`runner/waits.py`), on a real temporary git repo
with Claude faked: the hold, parking a review and waiting for room."""

from datetime import timedelta

from runner import session, waits
from tests.runner.conftest import THURSDAY
from tests.runner.test_loop import (
    FIVE_RESETS,
    LINE_33,
    _claude_at,
    _config,
    _f9_review_due,
    _switch_on,
    _week_read,
)


def test_over_the_line_a_planner_job_a_review_and_a_checkpoint_may_start(repo, fake_clock):
    """ADR 44 items 4 and 5: `claude_hold` is what holds them as they start."""
    _week_read(repo, 0.65, LINE_33)
    s = session.open_session(_config(repo))
    assert waits.claude_hold(s, THURSDAY) is None
    session.close_session(s)


def test_at_80_percent_claude_holds_no_support_job_but_at_100_or_resting_it_does(repo, fake_clock):
    """ADR 50 items 3 and 4: a review, a direction, an escalation and a checkpoint all start
    through `claude_hold`; the 5-hour mark doesn't hold them, the real limit does."""
    _claude_at(repo, 0.80)
    s = session.open_session(_config(repo))
    assert waits.claude_hold(s, THURSDAY) is None
    session.close_session(s)
    _claude_at(repo, 1.0, age=timedelta(minutes=1))
    s = session.open_session(_config(repo))
    hold = waits.claude_hold(s, THURSDAY)
    assert hold is not None and not hold.five_hour and hold.until >= FIVE_RESETS
    session.close_session(s)


def test_at_the_5_hour_mark_no_cards_review_parks(repo, fake_clock):
    """ADR 50 item 3 (it replaces F242 D3's two reserves for the lane card only)."""
    _claude_at(repo, 0.80)
    _f9_review_due(repo, fast_lane=True)
    s = session.open_session(_config(repo), None)
    assert waits.park_review(s, "f9") is False
    assert waits.park_review(s, "f10") is False
    session.close_session(s)


def test_the_5_hour_switch_lets_the_review_go_at_once(repo, fake_clock, at_the_keyboard):
    _claude_at(repo, 0.80)
    _switch_on(repo, "five_hour")
    waits.wait_for_room(session.open_session(_config(repo)), "the review")
    assert fake_clock[0] == THURSDAY


def test_at_80_percent_a_named_milestones_review_doesnt_wait(repo, fake_clock, at_the_keyboard):
    """ADR 50 item 3: `runner milestone`'s `wait_for_room` returns at once, switch off."""
    _claude_at(repo, 0.80)
    waits.wait_for_room(session.open_session(_config(repo)), "the review")
    assert fake_clock[0] == THURSDAY


def test_a_review_parked_for_a_real_limit_keeps_lead_work_from_claude(repo, fake_clock):
    """A review parked at the window's real limit is a limit, as a parked checkpoint is."""
    _claude_at(repo, 1.0)
    s = session.open_session(_config(repo))
    assert waits.park_review(s, "f9") is True
    assert waits._limits_ahead(s, session.now(), five_hour=False) == [FIVE_RESETS]
    assert waits._limits_ahead(s, session.now()) == [FIVE_RESETS]
    session.park_row(s, "review", "f9", FIVE_RESETS)
    assert waits._limits_ahead(s, session.now(), five_hour=False) == [FIVE_RESETS]
