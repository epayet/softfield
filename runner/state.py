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
    directions: dict[str, int] = field(default_factory=dict)  # task id -> directions given
    escalations: dict[str, int] = field(default_factory=dict)  # task id -> escalations
    unchecked: list[str] = field(default_factory=list)  # junior merges since the last checkpoint
    # task id -> {"adr": path, "question": one line}: decisions a job left for the owner
    owner: dict[str, dict[str, str]] = field(default_factory=dict)

    def runs_used(self, milestone: int) -> int:
        return self.headless_runs.get(str(milestone), 0)

    def count_run(self, milestone: int) -> None:
        self.headless_runs[str(milestone)] = self.runs_used(milestone) + 1


def load_state(path: Path) -> State:
    if not path.is_file():
        return State()
    data = json.loads(path.read_text(encoding="utf-8"))
    return State(**{k: v for k, v in data.items() if k in State.__dataclass_fields__})


def save_state(state: State, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2, sort_keys=True), encoding="utf-8")
