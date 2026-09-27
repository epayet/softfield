"""Runner settings from workflow/runner.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Price:
    input: float
    output: float


@dataclass(frozen=True)
class Config:
    repo: Path
    max_attempts: int
    headless_runs_per_milestone: int
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
    prices: dict[str, Price]

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
        headless_runs_per_milestone=caps["headless_claude_runs_per_milestone"],
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
        prices={
            name: Price(input=p["input"], output=p["output"])
            for name, p in report.get("prices", {}).items()
        },
    )


def read_protected(repo: Path) -> list[str]:
    lines = (repo / "workflow" / "protected-paths.txt").read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]
