from datetime import UTC, datetime, timedelta

from runner.claude import STRIPPED_ENV, backoff_seconds, claude_env, usage_limit_reset

NOW = datetime(2026, 9, 27, 14, 0, tzinfo=UTC)


def test_env_never_carries_api_credentials():
    env = {k: "x" for k in STRIPPED_ENV} | {"PATH": "/bin", "HOME": "/home/me"}
    assert claude_env(env) == {"PATH": "/bin", "HOME": "/home/me"}


def test_not_a_limit():
    assert usage_limit_reset("Error: file not found", NOW) == (False, None)


def test_epoch_reset():
    stamp = int((NOW + timedelta(hours=2)).timestamp())
    assert usage_limit_reset(f"Claude AI usage limit reached|{stamp}", NOW) == (
        True,
        NOW + timedelta(hours=2),
    )


def test_clock_reset_later_today_and_tomorrow():
    assert usage_limit_reset("You've hit your limit · resets 5pm", NOW) == (
        True,
        NOW.replace(hour=17),
    )
    assert usage_limit_reset("usage limit reached, resets at 9:30am", NOW) == (
        True,
        (NOW + timedelta(days=1)).replace(hour=9, minute=30),
    )


def test_limit_without_time():
    assert usage_limit_reset("rate limit exceeded", NOW) == (True, None)


def test_backoff_grows_and_caps():
    assert [backoff_seconds(n, 900, 18000) for n in range(6)] == [
        900,
        1800,
        3600,
        7200,
        14400,
        18000,
    ]
