from datetime import UTC, datetime, timedelta

import pytest

from runner.agents import Agent
from runner.allowance import Window
from runner.router import LeadOnly, Ticket, lead_only, route, stand_in

HOUR = timedelta(hours=1)
DAY = timedelta(days=1)
WEEK = timedelta(days=7)

# Claude's week as in test_allowance: Thursday is 3/7 in, plus a day's margin (ADR 25), so
# the pace line is 0.7 × 4/7 = 40%.
WEEK_RESET = datetime(2026, 10, 5, 16, 0, tzinfo=UTC)
WEEK_START = WEEK_RESET - WEEK
THURSDAY = WEEK_START + 3 * DAY
SUNDAY_EVENING = WEEK_RESET - 12 * HOUR  # inside the last 10% of the week: the sweep

LOCAL = Agent("local-qwen", "opencode", "lmstudio/qwen/qwen3.6-35b-a3b", 5)
OLLAMA = Agent("ollama-gpt-oss-120b", "opencode", "ollama/gpt-oss:120b-cloud", 6)
SONNET = Agent("claude-sonnet", "claude", "sonnet", 7)
OPUS = Agent("claude-opus", "claude", "opus", 9)
COPILOT = Agent("copilot-auto", "copilot", "auto", 6)
DEVELOPERS = (LOCAL, SONNET)
LADDER = (LOCAL, SONNET, OPUS)


def week(used: float) -> Window:
    return Window("seven_day", "fixed", WEEK, WEEK_RESET, 1.0, used, 0.3, measured=True)


def five_hour(used: float, now: datetime) -> Window:
    return Window("five_hour", "rolling", 5 * HOUR, now + 2 * HOUR, 1.0, used, measured=True)


def claude(used: float, now: datetime = THURSDAY) -> list[Window]:
    return [five_hour(0.1, now), week(used)]


def unknown(cooldown_until: datetime | None = None) -> list[Window]:
    """An Ollama plan: capacity unknown, used until refused (ADR 15 item 2)."""
    return [Window("plan", "fixed", 30 * DAY, None, None, 0.0, cooldown_until=cooldown_until)]


def developer(
    candidates=DEVELOPERS,
    windows=None,
    *,
    now=THURSDAY,
    difficulty=5,
    attempt=1,
    failed=None,
    refused=(),
    ratings=None,
    **lead_first,
):
    return route(
        "developer",
        Ticket("f1-99-thing", difficulty),
        attempt,
        candidates,
        ratings or {},
        windows or {},
        {},
        now,
        failed=failed,
        refused=refused,
        **lead_first,
    )


@pytest.mark.parametrize(
    ("windows", "now", "difficulty", "agent", "reason"),
    [
        # Cloud first, within its pace: 20% used on Thursday, under the 30% line.
        (
            {SONNET.id: claude(0.20)},
            THURSDAY,
            5,
            SONNET,
            "claude-sonnet (rated 7) covers difficulty 5, the best permitted:"
            " claude-sonnet: week 20% used, under its pace line of 40%",
        ),
        # Its pace spent: 41% used, past Thursday's line of 40%.
        (
            {SONNET.id: claude(0.41)},
            THURSDAY,
            5,
            LOCAL,
            "local-qwen, the floor: claude-sonnet: week 41% used, over its pace line of 40%",
        ),
        # The sweep takes an ordinary ticket a spread week would refuse.
        (
            {SONNET.id: claude(0.66, SUNDAY_EVENING)},
            SUNDAY_EVENING,
            5,
            SONNET,
            "claude-sonnet (rated 7) covers difficulty 5, the best permitted:"
            " claude-sonnet: week 66% used, in its sweep, under 70%",
        ),
        # Nothing covers a difficulty above every rating: local is the floor.
        (
            {SONNET.id: claude(0.0)},
            THURSDAY,
            8,
            LOCAL,
            "local-qwen, the floor: no cloud agent rated 8 or more",
        ),
    ],
)
def test_cloud_first_paced_else_local(windows, now, difficulty, agent, reason):
    assert developer(windows=windows, now=now, difficulty=difficulty) == (agent, reason)


def test_the_best_rated_permitted_agent_takes_the_ticket():
    windows = {SONNET.id: claude(0.1), OPUS.id: claude(0.1)}
    assert developer(LADDER, windows).agent == OPUS
    # A rating moved by results counts, not the config's estimate.
    assert developer(LADDER, windows, ratings={SONNET.id: 9.5}).agent == SONNET


def test_an_unknown_difficulty_still_goes_to_the_cloud():
    assert developer(windows={SONNET.id: claude(0.1)}, difficulty=None).agent == SONNET


def test_a_cloud_agent_that_refused_is_skipped():
    # This attempt's refusal: the same attempt reruns on the next candidate.
    picked = developer((LOCAL, OLLAMA), {OLLAMA.id: unknown()}, refused={OLLAMA.id})
    assert picked == (LOCAL, "local-qwen, the floor: ollama-gpt-oss-120b refused this attempt")
    # An earlier refusal: its window rests until the reset (allowance.learn).
    resting = {OLLAMA.id: unknown(cooldown_until=THURSDAY + HOUR)}
    assert developer((LOCAL, OLLAMA), resting) == (
        LOCAL,
        "local-qwen, the floor: ollama-gpt-oss-120b: plan refused, waiting until Thu 1 Oct 17:00",
    )
    # Unrefused, an unknown capacity is used.
    assert developer((LOCAL, OLLAMA), {OLLAMA.id: unknown()}).agent == OLLAMA


def test_with_every_candidate_refused_there_is_no_one_left():
    with pytest.raises(LookupError):
        developer((OLLAMA,), {OLLAMA.id: unknown()}, refused={OLLAMA.id})


def test_a_read_only_harness_never_develops():
    assert developer((LOCAL, COPILOT), {COPILOT.id: []}).agent == LOCAL


@pytest.mark.parametrize(
    ("failed", "windows", "agent", "reason"),
    [
        # local (5) failed: Sonnet (7) is the cheapest 2 points above it, not Opus.
        (
            LOCAL,
            {SONNET.id: claude(0.1), OPUS.id: claude(0.1)},
            SONNET,
            "step up from local-qwen (rated 5) to claude-sonnet (rated 7):"
            " claude-sonnet: week 10% used, under its pace line of 40%",
        ),
        # Sonnet (7) failed: Opus (9) is 2 above it.
        (
            SONNET,
            {SONNET.id: claude(0.1), OPUS.id: claude(0.1)},
            OPUS,
            "step up from claude-sonnet (rated 7) to claude-opus (rated 9):"
            " claude-opus: week 10% used, under its pace line of 40%",
        ),
        # Sonnet over its pace: no step up, local retries.
        (
            LOCAL,
            {SONNET.id: claude(0.41), OPUS.id: claude(0.41)},
            LOCAL,
            "local-qwen again: no permitted agent rated 7 or more",
        ),
    ],
)
def test_a_failed_attempt_steps_up_two_points(failed, windows, agent, reason):
    picked = developer(LADDER, windows, attempt=2, failed=failed.id)
    assert picked == (agent, reason)


def test_one_point_above_is_no_step_up():
    picked = developer((LOCAL, OLLAMA), {OLLAMA.id: unknown()}, attempt=2, failed=LOCAL.id)
    assert picked == (LOCAL, "local-qwen again: no permitted agent rated 7 or more")


def test_a_failed_cloud_agent_no_longer_permitted_hands_back_to_the_first_pick():
    windows = {SONNET.id: claude(0.41)}
    picked = developer(DEVELOPERS, windows, attempt=2, failed=SONNET.id)
    assert picked.agent == LOCAL
    assert picked.reason.startswith("claude-sonnet may not retry: ")


def test_with_lead_work_ready_a_developer_ticket_never_goes_to_claude():
    """ADR 16 item 2: lead work comes first; the next permitted agent takes the ticket."""
    windows = {SONNET.id: claude(0.1), OPUS.id: claude(0.1), OLLAMA.id: unknown()}
    assert developer((LOCAL, SONNET), windows, lead_ready=True) == (
        LOCAL,
        "local-qwen, the floor: claude-sonnet: lead work is ready, it goes first",
    )
    assert developer((LOCAL, OLLAMA, SONNET), windows, lead_ready=True).agent == OLLAMA
    # Nor as a step up
    stepped = developer(LADDER, windows, attempt=2, failed=LOCAL.id, lead_ready=True)
    assert stepped == (LOCAL, "local-qwen again: no permitted agent rated 7 or more")


@pytest.mark.parametrize(
    ("used", "agent", "reason"),
    [
        (
            0.4,
            SONNET,
            "claude-sonnet (rated 7) covers difficulty 5, the best permitted:"
            " claude-sonnet: week 10% used, under its pace line of 40%",
        ),
        (
            0.5,
            LOCAL,
            "local-qwen, the floor: claude-sonnet: 5-hour window 50% used,"
            " not under the developers' cap of 50%",
        ),
    ],
)
def test_claude_develops_only_under_half_its_5_hour_window(used, agent, reason):
    """ADR 16 item 2: so a lead job that follows has room."""
    windows = {SONNET.id: [five_hour(used, THURSDAY), week(0.1)]}
    assert developer(windows=windows, five_hour_cap=0.5) == (agent, reason)


MONTH = timedelta(days=30)
MONTH_RESET = datetime(2026, 10, 16, tzinfo=UTC)  # THURSDAY is half-way through its month


def copilot_month(used: float, cooldown_until: datetime | None = None) -> list[Window]:
    return [
        Window(
            "month",
            "fixed",
            MONTH,
            MONTH_RESET,
            1.0,
            used,
            measured=True,
            cooldown_until=cooldown_until,
        )
    ]


def test_copilot_stands_in_for_claude_past_its_pace_line_up_to_its_capacity():
    """ADR 16 item 9: emergency use may pass Copilot's monthly pace line, not its capacity."""
    picked = stand_in((COPILOT,), {COPILOT.id: copilot_month(0.8)}, THURSDAY, [LOCAL], "full")
    assert picked == (
        COPILOT,
        "copilot-auto stands in for Claude (full):"
        " copilot-auto: month 80% used, under its cap of 100%",
    )
    resting = copilot_month(0.1, cooldown_until=THURSDAY + HOUR)
    assert stand_in((COPILOT,), {COPILOT.id: resting}, THURSDAY, [LOCAL], "") is None


def test_copilot_never_stands_in_on_a_copilot_developers_merges():
    """Its model is unknown (`auto`), so it may be the author's (ADR 16 item 9)."""
    windows = {COPILOT.id: copilot_month(0.1)}
    assert stand_in((COPILOT,), windows, THURSDAY, [LOCAL, COPILOT], "") is None
    assert stand_in((), windows, THURSDAY, [LOCAL], "") is None


def test_a_lead_ticket_is_never_routed_to_a_developer():
    for role in ("developer", "last-attempt"):
        with pytest.raises(LeadOnly):
            route(role, Ticket("f1-25-router", 8, lead_only=True), 1, LADDER, {}, {}, {}, THURSDAY)


def test_lead_work_is_a_lead_ticket_or_one_touching_protected_paths():
    protected = ["runner/**", "coucou/pairing.py"]
    assert lead_only("lead", ["docs/x.md"], protected)
    assert lead_only("developer", ["coucou/thing.py", "runner/loop.py"], protected)
    assert not lead_only("developer", ["coucou/thing.py"], protected)


@pytest.mark.parametrize(
    ("authors", "agent", "reason"),
    [
        (
            [SONNET],
            OPUS,
            "claude-opus, another model than the authors (claude-sonnet)",
        ),
        (
            [LOCAL],
            SONNET,
            "claude-sonnet, another model than the authors (local-qwen)",
        ),
        (
            [LOCAL, SONNET],
            OPUS,
            "claude-opus, another model than the authors (local-qwen, claude-sonnet)",
        ),
    ],
)
def test_a_checkpoint_goes_to_another_model_than_the_developers(authors, agent, reason):
    picked = route(
        "checkpoint",
        None,
        1,
        (SONNET, OPUS),
        {},
        {},
        {},
        THURSDAY,
        authors=authors,
    )
    assert picked == (agent, reason)


def test_a_checkpoint_with_no_other_model_listed_says_so():
    picked = route("checkpoint", None, 1, (SONNET,), {}, {}, {}, THURSDAY, authors=[SONNET])
    assert picked == (
        SONNET,
        "claude-sonnet, the only checkpoint agent: [roles] checkpoint lists no other model"
        " than the authors (claude-sonnet)",
    )


def test_other_roles_take_their_first_agent():
    assert route("direction", None, 1, (OPUS, SONNET), {}, {}, {}, THURSDAY) == (
        OPUS,
        "claude-opus, the first agent [roles] direction names",
    )


def lead(difficulty, candidates=(SONNET, OPUS), up_to=4):
    ticket = Ticket("f1-98-lead", difficulty, lead_only=True)
    return route("lead-ticket", ticket, 1, candidates, {}, {}, {}, THURSDAY, lead_first_up_to=up_to)


@pytest.mark.parametrize("difficulty", [1, 3, 4])
def test_the_first_lead_agent_takes_a_lead_ticket_up_to_the_limit(difficulty):
    """ADR 32 item 1, F153 D1."""
    assert lead(difficulty) == (
        SONNET,
        f"claude-sonnet, a lead ticket of difficulty {difficulty} (the first agent up to 4)",
    )


@pytest.mark.parametrize("difficulty", [5, 9])
def test_the_second_lead_agent_takes_a_harder_lead_ticket(difficulty):
    assert lead(difficulty) == (
        OPUS,
        f"claude-opus, a lead ticket of difficulty {difficulty} (the second agent above 4)",
    )


def test_the_second_lead_agent_takes_a_lead_ticket_with_no_difficulty():
    assert lead(None) == (
        OPUS,
        "claude-opus, a lead ticket of no difficulty (the first agent only up to 4)",
    )


@pytest.mark.parametrize(("candidates", "up_to"), [((OPUS,), 4), ((OPUS,), 0), ((SONNET, OPUS), 0)])
def test_one_lead_agent_or_no_limit_gives_the_last_listed(candidates, up_to):
    """Today's config, one agent and no setting, behaves as today; the limit 0 goes back."""
    assert lead(3, candidates, up_to) == (
        OPUS,
        "claude-opus, the last agent [roles] lead-ticket names",
    )
