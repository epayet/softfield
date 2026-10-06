"""Small persistent runner state in var/runs/state.json (gitignored)."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


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
    # Merges only a stand-in checkpoint reviewed, for Claude's re-check (f8-08), and the
    # [ticket, file] of each finding it filed: the re-check doesn't file those again.
    recheck: list[str] = field(default_factory=list)
    recheck_filed: list[list[str]] = field(default_factory=list)
    # task id -> {"adr": path, "question": one line}: decisions a job left for the owner
    owner: dict[str, dict[str, str]] = field(default_factory=dict)
    # The job running now (ADR 15 item 11): kind ("local" or a Claude job's), ticket, branch,
    # agent, job_id, session_id, started. A Ctrl-C or a crash leaves it for the next run.
    in_flight: dict[str, Any] | None = None
    # "kind:ticket or subject" -> {"session_id", "branch", "cause"}: a recovered or parked
    # Claude job, resumed on its next run ("" when no session id was known)
    interrupted: dict[str, dict[str, str]] = field(default_factory=dict)
    timed_out: dict[str, int] = field(default_factory=dict)  # task id -> attempts cut off
    # task id -> {"kind", "branch", "session_id", "resets_at", …}: a ticket parked while Claude
    # is limited (its job's kind, resumed first after the reset) or at its reserve ("reserve",
    # with the owner's "text"; asked again by the next command). ADR 15 items 5 and 10. A
    # support job parks as its queue row's `not_before` instead (f8 D3); an older file's
    # support entries become rows at the next start.
    parked: dict[str, dict[str, Any]] = field(default_factory=dict)
    # "kind:subject" -> what a queued support job needs to start or resume (f8 D3): a
    # checkpoint's milestone and note, an escalation's logs and reason, a direction's attempts
    # so far. Dropped when its row is done.
    queued: dict[str, dict[str, Any]] = field(default_factory=dict)
    # The owner's reserve switches (ADR 22 item 4, f8 D4): "week" or "five_hour" -> when it
    # was turned on. Off is absent; on lasts 24 hours (`loop.switch_on`).
    switches: dict[str, str] = field(default_factory=dict)
    # The owner paused the factory (f5-18), and when it took: the run finishes the job it is
    # on, then picks nothing until they resume. Not `paused_until`, which is a limit's.
    owner_pause: str | None = None

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
