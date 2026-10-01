from pathlib import Path

from runner.config import load_config, read_protected
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
opencode_model = "lmstudio/m"
[claude]
reserve = 0.3
usage_limit_backoff_min = 1
usage_limit_backoff_max = 2
"""


def _repo(tmp_path, extra=""):
    (tmp_path / "workflow").mkdir()
    (tmp_path / "workflow" / "runner.toml").write_text(MINIMAL_TOML + extra, encoding="utf-8")
    return tmp_path


def test_metrics_db_is_read_from_the_toml_with_home_expanded(tmp_path):
    repo = _repo(tmp_path, '[metrics]\ndb = "~/elsewhere/metrics.sqlite"\n')
    assert load_config(repo).metrics_db == Path.home() / "elsewhere" / "metrics.sqlite"


def test_metrics_db_falls_back_to_the_default(tmp_path):
    expected = Path.home() / ".local/share/software-factory/factory-metrics.sqlite"
    assert load_config(_repo(tmp_path)).metrics_db == expected


def test_the_repos_toml_loads_with_an_absolute_metrics_db():
    assert load_config(REPO).metrics_db.is_absolute()


def test_claudes_reserve_is_read_from_the_toml(tmp_path):
    """ADR 15 item 4: 30% of Claude's week is kept for the lead's support roles."""
    assert load_config(REPO).claude_reserve == 0.3
    repo = _repo(tmp_path, "")
    toml = repo / "workflow" / "runner.toml"
    toml.write_text(toml.read_text().replace("reserve = 0.3", "reserve = 0.4"))
    assert load_config(repo).claude_reserve == 0.4


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
        "docs/agents/developer.md",
        "AGENTS.md",
    ]
    assert touching_protected(guarded, read_protected(REPO)) == sorted(guarded)


def test_ordinary_tests_are_not_protected():
    free = ["tests/browser/test_render.py", "tests/integration/test_display_css.py"]
    assert touching_protected(free, read_protected(REPO)) == []
