"""The Agents page's eligibility panel (f1-31, f2-11): who earned a role from its review
replays (`runner bench --review`, ADR 16 item 10), and why not."""

import sqlite3
from collections import Counter
from dataclasses import dataclass

from factory_dashboard.queries import eligibility, review_replays


@dataclass(frozen=True)
class EligibilityRow:
    agent: str
    role: str
    eligible: bool
    reason: str
    replays: int


def eligibility_rows(conn: sqlite3.Connection, project: str) -> list[EligibilityRow]:
    """Each agent that replayed checkpoints: whether it qualifies, why not, and its scored
    replays."""
    counts = Counter(r.agent for r in review_replays(conn, project))
    return [
        EligibilityRow(e.agent, e.role, e.eligible, e.reason, counts[e.agent])
        for e in eligibility(conn, project)
    ]
