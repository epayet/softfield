"""The Agents page's eligibility panel (f1-31): who earned a role by shadowing, and why not."""

import sqlite3
from dataclasses import dataclass

from factory_dashboard.queries import SHADOW_SUFFIX, eligibility


@dataclass(frozen=True)
class ShadowRow:
    agent: str
    role: str
    eligible: bool
    reason: str
    jobs: int


def shadow_rows(conn: sqlite3.Connection, project: str) -> list[ShadowRow]:
    """Each agent that shadowed a role: whether it qualifies, why not, and its shadow jobs."""
    counts = {
        (row["agent"], row["role"]): row["n"]
        for row in conn.execute(
            "SELECT j.agent, j.role, count(*) AS n FROM jobs j JOIN runs r ON r.id = j.run_id"
            " JOIN projects p ON p.id = r.project_id WHERE p.name = ? AND j.role LIKE ?"
            " GROUP BY j.agent, j.role",
            (project, "%" + SHADOW_SUFFIX),
        )
    }
    return [
        ShadowRow(
            e.agent,
            e.role,
            e.eligible,
            e.reason,
            counts.get((e.agent, e.role + SHADOW_SUFFIX), 0),
        )
        for e in eligibility(conn, project)
    ]
