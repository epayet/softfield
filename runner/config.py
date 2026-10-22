"""Runner settings: the machine's ``~/.config/softfield/factory.toml``, then the project's
``.factory/project.toml`` over it, table by table (ADR 30 item 3)."""

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runner.agents import Agent, WindowSeed

DEFAULT_METRICS_DB = "~/.local/share/software-factory/factory-metrics.sqlite"
# Outside any repo; a copy holds a .venv of a few hundred MB, and /tmp may be RAM (f2-12)
DEFAULT_BENCH_DIR = "~/.cache/software-factory/bench"
DEFAULT_BACKUP_DIR = "~/Dropbox/software-factory-backups"
# The machine's settings: agents, roles, Claude, the local model, metrics, backup, bench
DEFAULT_MACHINE = "~/.config/softfield/factory.toml"
MACHINE_ENV = "SOFTFIELD_CONFIG"  # another machine file; tests point it at none
PROJECT_TOML = Path(".factory") / "project.toml"
PROJECT_MD = Path(".factory") / "project.md"  # the rules that hold for this project only
# The Softfield checkout this code runs from (``live``, ADR 30 item 5) and its shared docs:
# lead.md, owner.md, task-format.md, task-writing.md, workflow.md (item 4)
HOME = Path(__file__).resolve().parents[1]
DOCS = HOME / "docs"
PROTECTED = Path(".factory") / "protected-paths.txt"


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Backup:
    """`[backup]`: where the metrics database's copies go, how many stay, and how often a new
    one is due (F20 D1)."""

    dir: Path = field(default_factory=lambda: Path(DEFAULT_BACKUP_DIR).expanduser())
    keep: int = 14
    every_hours: float = 24


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
    name: str = ""  # `[project] name`; ``project_name`` falls back on the repo's folder
    claude_reserve: float = 0.3  # the share of Claude's week kept for support roles (ADR 15)
    review_timeout: int = 1800  # a milestone review's own limit; Claude's when unset (2026-10-08)
    five_hour_reserve: float = 0.25  # Claude's 5-hour window kept for the owner (ADR 16 item 1)
    developer_five_hour_cap: float = 0.5  # Claude develops only under it (ADR 16 item 2)
    # the hardest lead ticket the first `[roles] lead-ticket` agent takes; 0: none (ADR 32)
    lead_first_up_to: int = 0
    agents: Mapping[str, Agent] = field(default_factory=dict)  # by id (ADR 14 item 3)
    roles: Mapping[str, tuple[str, ...]] = field(default_factory=dict)  # role → agent ids
    # `[bench] dir`: where the bench clones its copies of the repo (f2-12)
    bench_copies: Path = field(default_factory=lambda: Path(DEFAULT_BENCH_DIR).expanduser())
    # `[backup]`, D1's defaults when the toml has none; None (a test's config) copies nothing
    backup: Backup | None = None

    @property
    def project_name(self) -> str:
        """The project's name in the metrics database (ADR 30 item 3)."""
        return self.name or self.repo.name

    @property
    def runs_dir(self) -> Path:
        return self.repo / ".factory" / "var" / "runs"

    def agent_for(self, role: str) -> Agent:
        """The first agent `[roles]` names for ``role`` (f1-25 routes among them)."""
        if not (ids := self.roles.get(role)):
            raise ConfigError(f"[roles] names no agent for {role}")
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


def _lead_first_up_to(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ConfigError("[claude] lead_first_up_to must be a whole difficulty, 0 for none")
    return value


def _backup(table: dict[str, Any]) -> Backup:
    keep, every = table.get("keep", Backup.keep), table.get("every_hours", Backup.every_hours)
    if not isinstance(keep, int) or isinstance(keep, bool) or keep < 1:
        raise ConfigError("[backup] keep must be a whole number of copies, at least 1")
    if not isinstance(every, int | float) or isinstance(every, bool) or every <= 0:
        raise ConfigError("[backup] every_hours must be a number of hours above 0")
    return Backup(Path(table.get("dir", DEFAULT_BACKUP_DIR)).expanduser(), keep, float(every))


def machine_file() -> Path:
    return Path(os.environ.get(MACHINE_ENV) or DEFAULT_MACHINE).expanduser()


def _read(repo: Path) -> dict[str, Any]:
    """The machine's tables, then the project's over them: a table in both is merged, the
    project's keys winning."""
    machine = machine_file()
    data = tomllib.loads(machine.read_text(encoding="utf-8")) if machine.is_file() else {}
    project = tomllib.loads((repo / PROJECT_TOML).read_text(encoding="utf-8"))
    for name, table in project.items():
        both = isinstance(table, dict) and isinstance(data.get(name), dict)
        data[name] = {**data[name], **table} if both else table
    return data


def machine_metrics_db() -> Path:
    """The metrics database the machine's file names, without any project: `softfield run`
    reads the projects there (ADR 30 item 6)."""
    machine = machine_file()
    data = tomllib.loads(machine.read_text(encoding="utf-8")) if machine.is_file() else {}
    return Path(data.get("metrics", {}).get("db", DEFAULT_METRICS_DB)).expanduser()


def project_name(repo: Path) -> str:
    """`[project] name` in the repo's ``.factory/project.toml``, else its folder's name."""
    try:
        data = tomllib.loads((repo / PROJECT_TOML).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return repo.name
    return str(data.get("project", {}).get("name") or repo.name)


def load_config(repo: Path) -> Config:
    data = _read(repo)
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
        name=str(data.get("project", {}).get("name") or ""),
        claude_reserve=data["claude"]["reserve"],
        five_hour_reserve=data["claude"].get("five_hour_reserve", 0.25),
        developer_five_hour_cap=data["claude"].get("developer_five_hour_cap", 0.5),
        lead_first_up_to=_lead_first_up_to(data["claude"].get("lead_first_up_to", 0)),
        agents=agents,
        roles=_roles(data, agents),
        bench_copies=Path(data.get("bench", {}).get("dir", DEFAULT_BENCH_DIR)).expanduser(),
        backup=_backup(data.get("backup", {})),
    )


@dataclass(frozen=True)
class Checks:
    """``[checks]`` in ``.factory/project.toml``: what check-all and the gates run on this
    project (ADR 30 item 3). The defaults suit any uv project with its tests in ``tests/``."""

    test_dirs: tuple[str, ...] = ("tests",)
    # pytest-xdist's workers for the full suite; 0 runs it in one process (F71: Softfield's
    # took 19.5 min alone, 5 on 16 workers). The project's dev dependencies must have it.
    test_workers: int = 0
    mypy: tuple[str, ...] = ()  # mypy's targets; none skips it
    translations: bool = False  # the gettext check of ``runner/i18n.py`` (ADR 00 A2)
    dependency_files: tuple[str, ...] = ("pyproject.toml", "uv.lock")
    dependency_dirs: tuple[str, ...] = ()  # vendored code
    # the end-to-end tests a milestone's review runs first; none skips them (2026-10-15: every
    # review outside Coucou stopped on "end-to-end tests fail" for want of them)
    e2e: tuple[str, ...] = ()
    # test folder -> (module folder, module suffix): one test file per module (ADR 00 A1)
    layouts: Mapping[str, tuple[str, str]] = field(default_factory=dict)


def project_checks(repo: Path) -> Checks:
    """The project's ``[checks]``; the defaults when its project.toml has none."""
    try:
        data = tomllib.loads((repo / PROJECT_TOML).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Checks()
    table, default = data.get("checks", {}), Checks()
    try:
        return Checks(
            test_dirs=tuple(table.get("test_dirs", default.test_dirs)),
            test_workers=int(table.get("test_workers", default.test_workers)),
            mypy=tuple(table.get("mypy", default.mypy)),
            translations=bool(table.get("translations", default.translations)),
            dependency_files=tuple(table.get("dependency_files", default.dependency_files)),
            dependency_dirs=tuple(table.get("dependency_dirs", default.dependency_dirs)),
            e2e=tuple(table.get("e2e", default.e2e)),
            layouts={str(k): (str(v[0]), str(v[1])) for k, v in table.get("layouts", {}).items()},
        )
    except (TypeError, IndexError, ValueError) as exc:
        raise ConfigError(f"[checks] in {PROJECT_TOML}: {exc}") from exc


def suite_args(checks: Checks) -> list[str]:
    """pytest's arguments for the whole suite: its folders, on its workers."""
    workers = ["-n", str(checks.test_workers)] if checks.test_workers > 0 else []
    return [*workers, *checks.test_dirs]


def read_protected(repo: Path) -> list[str]:
    lines = (repo / PROTECTED).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]
