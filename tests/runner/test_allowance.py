import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner.allowance import (
    PastJob,
    Refusal,
    Window,
    answer,
    expected_cost,
    learn,
    reserve_only,
    window_shape,
)

PROBE = Path(__file__).parent / "fixtures" / "probes" / "claude-stream.jsonl"

HOUR = timedelta(hours=1)
DAY = timedelta(days=1)
WEEK = timedelta(days=7)
MONTH = timedelta(days=30)

# Claude's week in the 2026-10-01 probe: Monday 28 September to Monday 5 October, 16:00 UTC.
WEEK_RESET = datetime(2026, 10, 5, 16, 0, tzinfo=UTC)
WEEK_START = WEEK_RESET - WEEK
THURSDAY = WEEK_START + 3 * DAY  # 3/7 of the week: the pace line is 0.7 × 3/7 = 30%


def claude_week(used, reserve=0.3):
    return Window("seven_day", "fixed", WEEK, WEEK_RESET, 1.0, used, reserve, measured=True)


def claude_five_hour(used, now, reserve=0.0):
    return Window(
        "five_hour", "rolling", 5 * HOUR, now + 2 * HOUR, 1.0, used, reserve, measured=True
    )


@pytest.mark.parametrize(
    ("now", "used", "cost", "ok", "reason"),
    [
        (THURSDAY, 0.20, 0.02, True, "claude-sonnet: week 20% used, under its pace line of 30%"),
        (THURSDAY, 0.29, 0.02, False, "claude-sonnet: week 29% used, over its pace line of 30%"),
        # Monday evening: little of the week has gone, so little may be spent.
        (
            WEEK_START + 12 * HOUR,
            0.04,
            0.02,
            False,
            "claude-sonnet: week 4% used, over its pace line of 5%",
        ),
        # 17 h before the reset is just outside the sweep; spread refuses what the sweep allows.
        (
            WEEK_RESET - 17 * HOUR,
            0.66,
            0.02,
            False,
            "claude-sonnet: week 66% used, over its pace line of 63%",
        ),
        (
            WEEK_RESET - 16 * HOUR,
            0.66,
            0.02,
            True,
            "claude-sonnet: week 66% used, in its sweep, under 70%",
        ),
        # The sweep keeps the reserve.
        (
            WEEK_RESET - 16 * HOUR,
            0.69,
            0.02,
            False,
            "claude-sonnet: week 69% used, in its sweep, over 70%",
        ),
    ],
)
def test_a_fixed_window_is_paced(now, used, cost, ok, reason):
    got = answer("claude-sonnet", [claude_week(used)], cost, now)
    assert (got.ok, got.reason) == (ok, reason)


@pytest.mark.parametrize(
    ("used", "cost", "ok", "reason"),
    [
        (0.95, 0.03, True, "claude-sonnet: 5-hour window 95% used, under its cap of 100%"),
        (0.95, 0.06, False, "claude-sonnet: 5-hour window 95% used, over its cap of 100%"),
    ],
)
def test_a_rolling_window_is_a_cap_not_a_pace(used, cost, ok, reason):
    now = WEEK_START + HOUR  # a fixed window this early would refuse almost anything
    got = answer("claude-sonnet", [claude_five_hour(used, now)], cost, now)
    assert (got.ok, got.reason) == (ok, reason)


def test_every_window_must_agree_and_the_tightest_gives_the_reason():
    week = claude_week(0.10)
    assert answer("claude-sonnet", [claude_five_hour(0.50, THURSDAY), week], 0.02, THURSDAY) == (
        True,
        "claude-sonnet: week 10% used, under its pace line of 30%",
    )
    assert answer("claude-sonnet", [week, claude_five_hour(0.99, THURSDAY)], 0.02, THURSDAY) == (
        False,
        "claude-sonnet: 5-hour window 99% used, over its cap of 100%",
    )


def test_a_local_agent_has_no_window_and_always_passes():
    assert answer("local-qwen3.6-35b-a3b", [], 1e9, THURSDAY) == (
        True,
        "local-qwen3.6-35b-a3b: no allowance window, always allowed",
    )


# Copilot's month: a seeded capacity of 50 requests, reset on the 1st.
MONTH_RESET = datetime(2026, 11, 1, tzinfo=UTC)
MONTH_START = MONTH_RESET - MONTH
MID_MONTH = MONTH_START + MONTH / 2
IN_MONTH_SWEEP = MONTH_RESET - 2 * DAY


def copilot_month(used, capacity=50.0):
    return Window("month", "fixed", MONTH, MONTH_RESET, capacity, used)


def test_a_refusal_sets_the_capacity_at_its_usage_and_cools_down_until_the_reset():
    refused = Refusal(at=MID_MONTH, used=30)
    window = learn(copilot_month(30), [refused], MID_MONTH + HOUR)
    assert window.capacity == 30
    assert window.cooldown_until == MONTH_RESET
    assert answer("copilot-auto", [window], 1, MID_MONTH + HOUR) == (
        False,
        "copilot-auto: month refused, waiting until Sun 1 Nov 00:00",
    )


def test_a_learned_capacity_paces_the_next_window():
    last_month = Refusal(at=MONTH_START - 3 * DAY, used=30, resets_at=MONTH_START)
    learned = learn(copilot_month(16), [last_month], MID_MONTH)
    assert learned.cooldown_until is None
    # Half the month: the line is 15 of the learned 30, where the seed's 50 gave 25.
    assert answer("copilot-auto", [learned], 1, MID_MONTH) == (
        False,
        "copilot-auto: month 53% used, over its pace line of 50%",
    )
    assert answer("copilot-auto", [copilot_month(16)], 1, MID_MONTH).ok


def test_the_sweep_may_pass_a_learned_capacity():
    last_month = Refusal(at=MONTH_START - 3 * DAY, used=30, resets_at=MONTH_START)
    learned = learn(copilot_month(30), [last_month], IN_MONTH_SWEEP)
    assert answer("copilot-auto", [learned], 1, IN_MONTH_SWEEP) == (
        True,
        "copilot-auto: month 100% used, in its sweep, past its learned capacity until refused",
    )
    before = IN_MONTH_SWEEP - 2 * DAY
    assert not answer(
        "copilot-auto", [learn(copilot_month(30), [last_month], before)], 1, before
    ).ok


def test_the_sweep_never_passes_a_measured_capacity_or_a_reserve():
    week = claude_week(0.99, reserve=0.0)
    assert not answer("claude-sonnet", [week], 0.02, WEEK_RESET - HOUR).ok


def ollama_day(used, resets_at=None):
    return Window("day", "rolling", DAY, resets_at, None, used)


def test_an_unknown_capacity_is_used_until_refused_then_cools_down():
    now = THURSDAY
    assert answer("ollama-gpt-oss-120b", [ollama_day(5e6)], 1e5, now) == (
        True,
        "ollama-gpt-oss-120b: day capacity unknown, used until refused",
    )
    # No reset given: an hour off, then the next window, still of unknown capacity.
    refused = Refusal(at=now, used=5e6)
    later = learn(ollama_day(5e6), [refused], now + 30 * timedelta(minutes=1))
    assert later.capacity is None
    assert later.cooldown_until == now + HOUR
    assert not answer("ollama-gpt-oss-120b", [later], 1e5, now + timedelta(minutes=30)).ok
    after = learn(ollama_day(0), [refused], now + 61 * timedelta(minutes=1))
    assert after.cooldown_until is None
    assert answer("ollama-gpt-oss-120b", [after], 1e5, now + 61 * timedelta(minutes=1)).ok


def test_an_unknown_capacity_with_a_reset_waits_for_it_and_learns():
    reset = THURSDAY + 5 * HOUR
    refused = Refusal(at=THURSDAY, used=5e6, resets_at=reset)
    window = learn(ollama_day(5e6, reset), [refused], THURSDAY + HOUR)
    assert window.capacity == 5e6
    assert window.cooldown_until == reset
    assert not answer("ollama-gpt-oss-120b", [window], 1e5, THURSDAY + HOUR).ok


@pytest.mark.parametrize(
    ("windows", "now", "only"),
    [
        # 79% of the week on Thursday: only the reserve stands in the way.
        ([claude_week(0.79)], THURSDAY, True),
        # Monday's pace refuses, but the reserve is untouched.
        ([claude_week(0.10)], WEEK_START + 6 * HOUR, False),
        # At the reserve, but the 5-hour window is full too.
        ([claude_week(0.79), claude_five_hour(0.99, THURSDAY)], THURSDAY, False),
        # Allowed: nothing to ask.
        ([claude_week(0.10)], THURSDAY, False),
        # The whole week is spent: the reserve can't help.
        ([claude_week(0.99)], THURSDAY, False),
    ],
)
def test_reserve_only_says_when_the_reserve_alone_refuses(windows, now, only):
    assert reserve_only("claude-opus", windows, 0.03, now) is only


def test_the_reserve_lets_support_roles_take_the_rest_of_the_window():
    got = answer("claude-opus", [claude_week(0.79)], 0.03, THURSDAY, use_reserve=True)
    assert got == (True, "claude-opus: week 79% used, under its cap of 100% (using the reserve)")


@pytest.mark.parametrize(
    ("used", "ok", "reason"),
    [
        (0.70, True, "claude-opus: 5-hour window 70% used, under its cap of 75%"),
        (0.80, False, "claude-opus: 5-hour window 80% used, over its cap of 75%"),
    ],
)
def test_a_rolling_window_with_a_reserve_caps_short_of_it(used, ok, reason):
    """ADR 16 item 1: the last 25% of Claude's 5-hour window is the owner's."""
    got = answer("claude-opus", [claude_five_hour(used, THURSDAY, 0.25)], 0.0, THURSDAY)
    assert (got.ok, got.reason) == (ok, reason)


def test_each_windows_reserve_is_used_only_when_named():
    """ADR 16 item 3: a yes to the week's reserve doesn't lift the 5-hour window's."""
    windows = [claude_week(0.79), claude_five_hour(0.80, THURSDAY, 0.25)]
    week_only = answer("claude-opus", windows, 0.0, THURSDAY, use_reserve={"seven_day"})
    assert week_only == (False, "claude-opus: 5-hour window 80% used, over its cap of 75%")
    five_only = answer("claude-opus", windows, 0.0, THURSDAY, use_reserve={"five_hour"})
    assert five_only == (False, "claude-opus: week 79% used, over its pace line of 30%")
    both = answer("claude-opus", windows, 0.0, THURSDAY, use_reserve={"seven_day", "five_hour"})
    assert both.ok
    assert answer("claude-opus", windows, 0.0, THURSDAY, use_reserve=True).ok


@pytest.mark.parametrize(
    ("week", "five_hour", "asked"),
    [
        (0.10, 0.80, {"five_hour"}),
        (0.79, 0.07, {"seven_day"}),
        (0.79, 0.80, {"seven_day", "five_hour"}),
        (0.10, 0.70, set()),
        (0.10, 0.99, set()),  # past even the owner's share: the reserve can't help
    ],
)
def test_reserve_only_names_the_window_whose_reserve_alone_refuses(week, five_hour, asked):
    windows = [claude_week(week), claude_five_hour(five_hour, THURSDAY, 0.25)]
    got = {
        name
        for name in ("seven_day", "five_hour")
        if reserve_only("claude-opus", windows, 0.02, THURSDAY, name)
    }
    assert got == asked


def probe_windows(now):
    shapes = {}
    for line in PROBE.read_text().splitlines():
        event = json.loads(line)
        if event.get("type") == "rate_limit_event":
            for name, reading in event["rate_limit_info"]["unifiedWindows"].items():
                resets_at = datetime.fromtimestamp(reading["resetsAt"], UTC)
                kind, length = window_shape(name, [resets_at - now])
                shapes[name] = Window(
                    name,
                    kind,
                    length,
                    resets_at,
                    1.0,
                    reading["utilization"],
                    0.3 if name == "seven_day" else 0.0,
                    measured=True,
                )
    return list(shapes.values())


def test_the_probe_refuses_a_developer_job_on_thursday_and_allows_a_review():
    now = datetime(2026, 10, 1, 11, 0, tzinfo=UTC)  # Thursday, noon in London
    windows = probe_windows(now)
    assert {w.name: w.used for w in windows} == {"five_hour": 0.07, "seven_day": 0.79}
    assert {w.name: w.resets_at for w in windows}["seven_day"] == WEEK_RESET
    developer = answer("claude-sonnet", windows, 0.03, now)
    assert developer == (False, "claude-sonnet: week 79% used, over its pace line of 28%")
    assert reserve_only("claude-sonnet", windows, 0.03, now)
    assert answer("claude-opus", windows, 0.02, now, use_reserve=True).ok


@pytest.mark.parametrize(
    ("name", "ahead", "shape"),
    [
        ("five_hour", [2 * HOUR], ("rolling", 5 * HOUR)),
        ("seven_day", [6 * HOUR], ("fixed", WEEK)),  # Claude names its windows
        ("day", [3 * HOUR, 4 * HOUR + 50 * timedelta(minutes=1)], ("rolling", 5 * HOUR)),
        ("plan", [2 * HOUR, 6 * DAY], ("fixed", WEEK)),
        ("plan", [20 * DAY], ("fixed", MONTH)),
    ],
)
def test_a_window_shape_comes_from_its_name_or_how_far_ahead_its_resets_are(name, ahead, shape):
    assert window_shape(name, ahead) == shape


JOBS = [
    PastJob("claude-sonnet", 4, 0.02),
    PastJob("claude-sonnet", 4, 0.04),
    PastJob("claude-sonnet", 4, 0.03),
    PastJob("claude-sonnet", 7, 0.10),
    PastJob("claude-opus", 5, 0.50),
]


@pytest.mark.parametrize(
    ("agent", "difficulty", "cost"),
    [
        ("claude-sonnet", 4, 0.03),  # the median at that difficulty
        ("claude-sonnet", 5, 0.035),  # none at 5: all of its jobs
        ("ollama-gpt-oss-120b", 5, 0.01),  # none at all: the seed
    ],
)
def test_expected_cost_is_the_median_of_past_jobs_with_fallbacks(agent, difficulty, cost):
    assert expected_cost(agent, difficulty, JOBS, seed=0.01) == pytest.approx(cost)
