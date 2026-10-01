"""Runner settings from workflow/runner.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_METRICS_DB = "~/.local/share/software-factory/factory-metrics.sqlite"


@dataclass(frozen=True)
class Config:
    repo: Path
    max_attempts: int
    directions_per_task: int
    escalations_per_task: int
    checkpoint_every: int
    review_rounds: int
    default_max_diff: int
    warmup_timeout: int
    opencode_timeout: int
    claude_timeout: int
    gate_timeout: int
    lm_base_url: str
    lm_model: str
    opencode_model: str
    backoff_min: int
    backoff_max: int
    narrative: bool
    metrics_db: Path  # outside the repo, shared by every project (ADR 13 item 1)
    checkpoint_model: str = ""
    project_description: str = ""  # the metrics database's project row (f1 D2)
    claude_reserve: float = 0.3  # the share of Claude's week kept for support roles (ADR 15)

    @property
    def runs_dir(self) -> Path:
        return self.repo / "var" / "runs"


def load_config(repo: Path) -> Config:
    data = tomllib.loads((repo / "workflow" / "runner.toml").read_text(encoding="utf-8"))
    caps, timeouts, lm = data["caps"], data["timeouts"], data["local_model"]
    report = data.get("report", {})
    return Config(
        repo=repo,
        max_attempts=caps["max_attempts"],
        directions_per_task=caps["directions_per_task"],
        escalations_per_task=caps["escalations_per_task"],
        checkpoint_every=caps["checkpoint_every"],
        review_rounds=caps["review_rounds"],
        default_max_diff=caps["default_max_diff"],
        warmup_timeout=timeouts["warmup"],
        opencode_timeout=timeouts["opencode"],
        claude_timeout=timeouts["claude"],
        gate_timeout=timeouts["gate"],
        lm_base_url=lm["base_url"],
        lm_model=lm["model"],
        opencode_model=lm["opencode_model"],
        backoff_min=data["claude"]["usage_limit_backoff_min"],
        backoff_max=data["claude"]["usage_limit_backoff_max"],
        narrative=report.get("narrative", False),
        metrics_db=Path(data.get("metrics", {}).get("db", DEFAULT_METRICS_DB)).expanduser(),
        checkpoint_model=data["claude"].get("checkpoint_model", ""),
        project_description=data.get("project", {}).get("description", ""),
        claude_reserve=data["claude"]["reserve"],
    )


def read_protected(repo: Path) -> list[str]:
    lines = (repo / "workflow" / "protected-paths.txt").read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]
