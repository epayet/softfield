"""Small persistent runner state in var/runs/state.json (gitignored)."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class State:
    paused_until: str | None = None
    headless_runs: dict[str, int] = field(default_factory=dict)  # milestone -> runs (metrics)
    finding_seen: dict[str, int] = field(default_factory=dict)  # finding id -> rounds seen open
    review_counts: dict[str, list[int]] = field(default_factory=dict)  # milestone -> per round
    review_stop: dict[str, str] = field(default_factory=dict)  # milestone -> why the loop stopped
    directions: dict[str, int] = field(default_factory=dict)  # task id -> directions given
    escalations: dict[str, int] = field(default_factory=dict)  # task id -> escalations
    unchecked: list[str] = field(default_factory=list)  # developer merges since the last checkpoint
    # task id -> {"adr": path, "question": one line}: decisions a job left for the owner
    owner: dict[str, dict[str, str]] = field(default_factory=dict)

    def runs_used(self, milestone: str) -> int:
        return self.headless_runs.get(milestone, 0)

    def count_run(self, milestone: str) -> None:
        self.headless_runs[milestone] = self.runs_used(milestone) + 1


# Fields keyed by milestone: older state files used the bare number ("4" for m4).
_BY_MILESTONE = ("headless_runs", "review_counts", "review_stop")


def load_state(path: Path) -> State:
    if not path.is_file():
        return State()
    data = json.loads(path.read_text(encoding="utf-8"))
    for name in _BY_MILESTONE:
        if isinstance(data.get(name), dict):
            data[name] = {(f"m{k}" if k.isdigit() else k): v for k, v in data[name].items()}
    return State(**{k: v for k, v in data.items() if k in State.__dataclass_fields__})


def save_state(state: State, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2, sort_keys=True), encoding="utf-8")
