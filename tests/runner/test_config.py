from pathlib import Path

import pytest

from runner.agents import Agent, WindowSeed
from runner.config import ConfigError, load_config, read_protected
from runner.gates import touching_protected

REPO = Path(__file__).resolve().parents[2]


MINIMAL_TOML = """
[caps]
max_attempts = 3
directions_per_task = 1
escalations_per_task = 2
checkpoint_every = 2
review_rounds = 3
default_max_diff = 1000
[timeouts]
warmup = 1
opencode = 1
claude = 1
gate = 1
[local_model]
base_url = "http://x"
model = "m"
[claude]
reserve = 0.3
usage_limit_backoff_min = 1
usage_limit_backoff_max = 2
"""


def _repo(tmp_path, extra=""):
    (tmp_path / ".factory").mkdir()
    (tmp_path / ".factory" / "project.toml").write_text(MINIMAL_TOML + extra, encoding="utf-8")
    return tmp_path


def test_metrics_db_is_read_from_the_toml_with_home_expanded(tmp_path):
    repo = _repo(tmp_path, '[metrics]\ndb = "~/elsewhere/metrics.sqlite"\n')
    assert load_config(repo).metrics_db == Path.home() / "elsewhere" / "metrics.sqlite"


def test_metrics_db_falls_back_to_the_default(tmp_path):
    expected = Path.home() / ".local/share/software-factory/factory-metrics.sqlite"
    assert load_config(_repo(tmp_path)).metrics_db == expected


def test_the_bench_dir_is_read_from_the_toml_or_defaults_outside_the_repo(tmp_path):
    repo = _repo(tmp_path, '[bench]\ndir = "~/elsewhere/bench"\n')
    assert load_config(repo).bench_copies == Path.home() / "elsewhere" / "bench"
    expected = Path.home() / ".cache/software-factory/bench"
    (tmp_path / "default").mkdir()
    assert load_config(_repo(tmp_path / "default")).bench_copies == expected


def test_a_review_has_its_own_timeout_or_claudes(tmp_path, machine):
    """F6's review hit Claude's 30 minutes twice on 2026-10-08: a milestone review gets its
    own limit; without one it keeps Claude's."""
    repo = _repo(tmp_path)
    assert load_config(repo).review_timeout == 1
    toml = repo / ".factory" / "project.toml"
    toml.write_text(MINIMAL_TOML.replace("gate = 1", "gate = 1\nreview = 7"), encoding="utf-8")
    assert (load_config(repo).claude_timeout, load_config(repo).review_timeout) == (1, 7)
    assert load_config(REPO).review_timeout == 3600


def test_the_repos_toml_loads_with_an_absolute_metrics_db(machine):
    assert load_config(REPO).metrics_db.is_absolute()


def test_claudes_reserve_is_read_from_the_toml(tmp_path, machine):
    """ADR 15 item 4: 30% of Claude's week is kept for the lead's support roles."""
    assert load_config(REPO).claude_reserve == 0.3
    repo = _repo(tmp_path, "")
    toml = repo / ".factory" / "project.toml"
    toml.write_text(toml.read_text().replace("reserve = 0.3", "reserve = 0.4"))
    assert load_config(repo).claude_reserve == 0.4


def test_the_owners_share_of_the_5_hour_window_and_the_developers_cap_are_read(tmp_path, machine):
    """ADR 16 items 1–2 (f2 D1): unattended jobs keep 25% of Claude's 5-hour window for the
    owner, and Claude takes developer tickets only under 50% of it."""
    cfg = load_config(REPO)
    assert (cfg.five_hour_reserve, cfg.developer_five_hour_cap) == (0.25, 0.5)
    extra = "five_hour_reserve = 0.2\ndeveloper_five_hour_cap = 0.4\n"
    repo = _repo(tmp_path, "")
    toml = repo / ".factory" / "project.toml"
    toml.write_text(toml.read_text().replace("[claude]\n", "[claude]\n" + extra))
    cfg = load_config(repo)
    assert (cfg.five_hour_reserve, cfg.developer_five_hour_cap) == (0.2, 0.4)


def test_the_repos_toml_declares_f1s_agents_and_roles(machine):
    """ADR 14 item 3, D6; f1-25 turns on Sonnet as a developer after local (ADR 15 item 6),
    with Opus to check Sonnet's merges (item 9); f1-26 shadows the checkpoint with Copilot."""
    cfg = load_config(REPO)
    local, opus, sonnet = "local-qwen3.6-35b-a3b", "claude-opus", "claude-sonnet"
    assert cfg.agents[local] == Agent(local, "opencode", "lmstudio/qwen/qwen3.6-35b-a3b", 5)
    assert (cfg.agents[opus].harness, cfg.agents[opus].model) == ("claude", "opus")
    assert (cfg.agents[sonnet].harness, cfg.agents[sonnet].model) == ("claude", "sonnet")
    assert all(1 <= agent.rating <= 10 for agent in cfg.agents.values())
    assert dict(cfg.roles) == {
        # f2-09: from their F2 jobs; Sonnet off first attempts (ADR 17 item 1, until f4-13)
        "developer": (local,),  # cloud developers off until a clean bench (owner, 2026-10-04)
        "last-attempt": (local,),
        "direction": (opus,),
        "escalation": (opus,),
        "lead-ticket": (opus,),
        "review": (opus,),
        "narrative": (opus,),
        "planner": (opus,),  # the planning room (ADR 20 item 1)
        "checkpoint": (sonnet, opus),
        "checkpoint-shadow": (),  # off: the bench replaces shadowing (ADR 16 item 10)
        "checkpoint-stand-in": ("copilot-auto",),  # when Claude can't (ADR 16 item 9)
    }
    assert cfg.agents["copilot-auto"].harness == "copilot"
    assert cfg.agent_for("checkpoint").id == sonnet
    assert not hasattr(cfg, "checkpoint_model")


def test_the_cloud_developers_ratings_follow_their_f2_results(machine):
    """f2-09: gpt-oss-120b merged f2-13 at its first attempt and lost f2-06, so it stays a
    developer at its results' rating (5.1); nemotron-3-super blocked twice on f2-07 (4.3)."""
    cfg = load_config(REPO)
    assert cfg.agents["ollama-gpt-oss-120b"].rating == 5
    assert cfg.agents["ollama-nemotron-3-super"].rating == 4
    assert "ollama-nemotron-3-super" not in cfg.roles["developer"]


AGENTS_TOML = """
[agents.claude-opus]
harness = "claude"
model = "opus"
rating = 10

[agents.copilot-auto]
harness = "copilot"
model = "auto"
rating = 6
windows = [{ name = "month", capacity = 200 }]
"""


def test_an_agents_windows_are_seeds(tmp_path):
    """ADR 15 item 2: config values only seed a new agent's windows."""
    cfg = load_config(_repo(tmp_path, AGENTS_TOML + '[roles]\nreview = ["claude-opus"]\n'))
    assert cfg.agents["copilot-auto"].windows == (WindowSeed("month", 200.0),)
    assert cfg.agents["claude-opus"].windows == ()


def test_a_role_naming_an_undeclared_agent_is_a_config_error(tmp_path):
    repo = _repo(tmp_path, AGENTS_TOML + '[roles]\nreview = ["claude-opus", "claude-haiku"]\n')
    with pytest.raises(ConfigError, match=r"review.*claude-haiku"):
        load_config(repo)


@pytest.mark.parametrize("rating", ["0", "11", '"high"', "{ coding = 6 }"])
def test_an_agent_has_one_rating_from_1_to_10(tmp_path, rating):
    """ADR 15 item 9: one rating per agent, no longer coding and reviewing."""
    toml = AGENTS_TOML.replace("rating = 10", f"rating = {rating}")
    with pytest.raises(ConfigError, match="claude-opus"):
        load_config(_repo(tmp_path, toml))


def test_a_role_with_no_agent_is_a_config_error_when_asked_for(tmp_path):
    cfg = load_config(_repo(tmp_path, AGENTS_TOML))
    with pytest.raises(ConfigError, match="checkpoint"):
        cfg.agent_for("checkpoint")


def test_security_tests_and_the_leads_docs_are_protected():
    """ADR 07 items 4 and 14: developers may change tests, but not the ones guarding protected
    code, and not the lead's instructions or their own notes."""
    guarded = [
        "tests/integration/test_scoping_isolation.py",
        "tests/integration/test_revocation.py",
        "tests/unit/test_deviceauth.py",
        "tests/browser/test_outbox.py",
        "tests/e2e/test_display.py",
        "docs/agents/lead.md",
        "docs/agents/owner.md",
        "docs/agents/developer.md",
        "AGENTS.md",
    ]
    assert touching_protected(guarded, read_protected(REPO)) == sorted(guarded)


def test_ordinary_tests_are_not_protected():
    free = ["tests/browser/test_render.py", "tests/integration/test_display_css.py"]
    assert touching_protected(free, read_protected(REPO)) == []
