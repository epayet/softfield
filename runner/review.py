"""Milestone review loop: finding files and the stop rules (docs/workflow.md).

Checkpoints and reviews write their findings as JSON (ADR 14 item 13); the review's last
round also judges the checkpoints' findings and scores the milestone."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SEVERITIES = ("blocking", "should-fix", "nit")
ROUTES = ("local", "claude", "adr", "backlog")
CLAUDE_STOPS = ("adr-needed", "security-unresolved", "unforeseen-cross-milestone")
# A checkpoint finding the review confirmed or rejected, or a review finding a checkpoint
# should have caught (missed).
VERDICTS = ("confirmed", "rejected", "missed")


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
    file: str = ""
    line: int | None = None
    detail: str = ""
    ticket: str = ""  # the ticket whose work it is about
    kind: str = "code"  # a checkpoint's: "test" when the code is right and its test weak (f8-09)

    @property
    def actionable(self) -> bool:
        return self.severity != "nit" and not self.resolved


@dataclass(frozen=True)
class ReviewRound:
    findings: tuple[Finding, ...]
    stop: str | None  # a reason Claude asks to stop for, from CLAUDE_STOPS
    checkpoint_verdicts: dict[str, str] = field(default_factory=dict)  # finding key: VERDICTS
    score: int | None = None  # the milestone's, 1-10


def _read(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewFileError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ReviewFileError(f"{path} is not a JSON object")
    return data


def _line(value: object, finding: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    raise ReviewFileError(f"bad line {value!r} in finding {finding}")


def _finding(raw: dict[str, Any], finding_id: str) -> Finding:
    finding = Finding(
        id=finding_id,
        severity=str(raw.get("severity")),
        route=str(raw.get("route", "backlog")),
        summary=str(raw.get("summary", "")),
        resolved=bool(raw.get("resolved", False)),
        security=bool(raw.get("security", False)),
        file=str(raw.get("file") or ""),
        line=_line(raw.get("line"), finding_id),
        detail=str(raw.get("detail") or ""),
        ticket=str(raw.get("ticket") or ""),
        kind="test" if raw.get("kind") == "test" else "code",
    )
    if finding.severity not in SEVERITIES or finding.route not in ROUTES:
        raise ReviewFileError(f"bad severity/route in finding {finding.id}")
    return finding


def _findings(data: dict[str, Any]) -> list[dict[str, Any]]:
    raws = data.get("findings", [])
    if not isinstance(raws, list) or not all(isinstance(raw, dict) for raw in raws):
        raise ReviewFileError("findings is not a list of objects")
    return raws


def _verdicts(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict) or any(v not in VERDICTS for v in value.values()):
        raise ReviewFileError(f"bad checkpoint_verdicts {value!r}")
    return {str(key): str(verdict) for key, verdict in value.items()}


def _score(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 10:
        return value
    raise ReviewFileError(f"bad score {value!r}: a score is 1 to 10")


def parse_review(path: Path) -> ReviewRound:
    data = _read(path)
    findings = []
    for raw in _findings(data):
        if "id" not in raw:
            raise ReviewFileError("a finding has no id")
        findings.append(_finding(raw, str(raw["id"])))
    stop = data.get("stop")
    if stop is not None and stop not in CLAUDE_STOPS:
        raise ReviewFileError(f"unknown stop reason {stop!r}")
    return ReviewRound(
        findings=tuple(findings),
        stop=stop,
        checkpoint_verdicts=_verdicts(data.get("checkpoint_verdicts")),
        score=_score(data.get("score")),
    )


def parse_checkpoint(path: Path) -> tuple[Finding, ...]:
    """A checkpoint's findings, numbered from 1 in order: the runner keys them."""
    return tuple(_finding(raw, str(n)) for n, raw in enumerate(_findings(_read(path)), start=1))


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
