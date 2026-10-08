"""Runner settings from workflow/runner.toml."""

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runner.agents import Agent, WindowSeed

DEFAULT_METRICS_DB = "~/.local/share/software-factory/factory-metrics.sqlite"
# Outside any repo; a copy holds a .venv of a few hundred MB, and /tmp may be RAM (f2-12)
DEFAULT_BENCH_DIR = "~/.cache/software-factory/bench"


class ConfigError(ValueError):
    pass


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
    backoff_min: int
    backoff_max: int
    narrative: bool
    metrics_db: Path  # outside the repo, shared by every project (ADR 13 item 1)
    project_description: str = ""  # the metrics database's project row (f1 D2)
    claude_reserve: float = 0.3  # the share of Claude's week kept for support roles (ADR 15)
    review_timeout: int = 1800  # a milestone review's own limit; Claude's when unset (2026-10-08)
    five_hour_reserve: float = 0.25  # Claude's 5-hour window kept for the owner (ADR 16 item 1)
    developer_five_hour_cap: float = 0.5  # Claude develops only under it (ADR 16 item 2)
    agents: Mapping[str, Agent] = field(default_factory=dict)  # by id (ADR 14 item 3)
    roles: Mapping[str, tuple[str, ...]] = field(default_factory=dict)  # role → agent ids
    # `[bench] dir`: where the bench clones its copies of the repo (f2-12)
    bench_copies: Path = field(default_factory=lambda: Path(DEFAULT_BENCH_DIR).expanduser())

    @property
    def runs_dir(self) -> Path:
        return self.repo / "var" / "runs"

    def agent_for(self, role: str) -> Agent:
        """The first agent `[roles]` names for ``role`` (f1-25 routes among them)."""
        if not (ids := self.roles.get(role)):
            raise ConfigError(f"workflow/runner.toml: [roles] names no agent for {role}")
        return self.agents[ids[0]]


def _agent(agent_id: str, table: dict[str, Any]) -> Agent:
    rating = table.get("rating")
    if not isinstance(rating, int) or isinstance(rating, bool) or not 1 <= rating <= 10:
        raise ConfigError(f"[agents.{agent_id}] rating must be one number from 1 to 10")
    try:
        windows = tuple(
            WindowSeed(str(w["name"]), float(w["capacity"]) if "capacity" in w else None)
            for w in table.get("windows", [])
        )
        return Agent(agent_id, str(table["harness"]), str(table["model"]), rating, windows)
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigError(
            f"[agents.{agent_id}] needs harness and model, and windows of name and capacity ({exc})"
        ) from exc


def _roles(data: dict[str, Any], agents: Mapping[str, Agent]) -> dict[str, tuple[str, ...]]:
    roles = {role: tuple(ids) for role, ids in data.get("roles", {}).items()}
    for role, ids in roles.items():
        if unknown := [i for i in ids if i not in agents]:
            raise ConfigError(f"[roles] {role} names undeclared agents: {', '.join(unknown)}")
    return roles


def load_config(repo: Path) -> Config:
    data = tomllib.loads((repo / "workflow" / "runner.toml").read_text(encoding="utf-8"))
    caps, timeouts, lm = data["caps"], data["timeouts"], data["local_model"]
    report = data.get("report", {})
    agents = {agent_id: _agent(agent_id, t) for agent_id, t in data.get("agents", {}).items()}
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
        review_timeout=timeouts.get("review", timeouts["claude"]),
        gate_timeout=timeouts["gate"],
        lm_base_url=lm["base_url"],
        lm_model=lm["model"],
        backoff_min=data["claude"]["usage_limit_backoff_min"],
        backoff_max=data["claude"]["usage_limit_backoff_max"],
        narrative=report.get("narrative", False),
        metrics_db=Path(data.get("metrics", {}).get("db", DEFAULT_METRICS_DB)).expanduser(),
        project_description=data.get("project", {}).get("description", ""),
        claude_reserve=data["claude"]["reserve"],
        five_hour_reserve=data["claude"].get("five_hour_reserve", 0.25),
        developer_five_hour_cap=data["claude"].get("developer_five_hour_cap", 0.5),
        agents=agents,
        roles=_roles(data, agents),
        bench_copies=Path(data.get("bench", {}).get("dir", DEFAULT_BENCH_DIR)).expanduser(),
    )


def read_protected(repo: Path) -> list[str]:
    lines = (repo / "workflow" / "protected-paths.txt").read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]
