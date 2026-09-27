"""Milestone review loop: finding files and the stop rules (docs/workflow.md)."""

import json
from dataclasses import dataclass
from pathlib import Path

SEVERITIES = ("blocking", "should-fix", "nit")
ROUTES = ("local", "claude", "adr", "backlog")
CLAUDE_STOPS = ("adr-needed", "security-unresolved", "unforeseen-cross-milestone")


class ReviewFileError(ValueError):
    pass


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    route: str
    summary: str
    resolved: bool = False
    security: bool = False

    @property
    def actionable(self) -> bool:
        return self.severity != "nit" and not self.resolved


@dataclass(frozen=True)
class ReviewRound:
    findings: tuple[Finding, ...]
    stop: str | None  # a reason Claude asks to stop for, from CLAUDE_STOPS


def parse_review(path: Path) -> ReviewRound:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewFileError(f"cannot read review file {path}: {exc}") from exc
    findings = []
    for raw in data.get("findings", []):
        finding = Finding(
            id=str(raw["id"]),
            severity=str(raw["severity"]),
            route=str(raw.get("route", "backlog")),
            summary=str(raw.get("summary", "")),
            resolved=bool(raw.get("resolved", False)),
            security=bool(raw.get("security", False)),
        )
        if finding.severity not in SEVERITIES or finding.route not in ROUTES:
            raise ReviewFileError(f"bad severity/route in finding {finding.id}")
        findings.append(finding)
    stop = data.get("stop")
    if stop is not None and stop not in CLAUDE_STOPS:
        raise ReviewFileError(f"unknown stop reason {stop!r}")
    return ReviewRound(findings=tuple(findings), stop=stop)


def update_seen(seen: dict[str, int], round_: ReviewRound) -> dict[str, int]:
    """Count how many rounds each actionable finding has been open."""
    updated = dict(seen)
    for finding in round_.findings:
        if finding.actionable:
            updated[finding.id] = updated.get(finding.id, 0) + 1
    return updated


def recurring_for_claude(seen: dict[str, int]) -> list[str]:
    """Findings open for a second round: Claude fixes these, not the local model."""
    return sorted(fid for fid, count in seen.items() if count == 2)


def stop_reason(
    round_no: int,
    round_: ReviewRound,
    previous_count: int | None,
    seen: dict[str, int],
    max_rounds: int,
) -> str | None:
    """Why the loop must stop after this round, or None to continue."""
    if round_.stop:
        return round_.stop
    count = sum(f.actionable for f in round_.findings)
    if count == 0:
        return "clean"
    if any(n >= 3 for n in seen.values()):
        return "a finding came back a third time"
    if previous_count is not None and count >= previous_count:
        return f"findings did not decrease ({previous_count} -> {count})"
    if round_no >= max_rounds:
        return f"review round cap ({max_rounds}) reached"
    return None
