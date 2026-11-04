"""Agents, roles and the neutral job spec (ADR 14 items 2–4; ADR 15 items 2, 9 and 12).

An agent is a harness plus a model, declared in the machine's factory.toml with its id
(`<harness>-<model>`, D6) and one rating. A role names the agents that may do it. A job is
a `JobSpec`; the adapter for its agent's harness translates the spec into that harness's
tools, runs it, and returns a `JobResult` whose error is a limit, transient or a failure.
The loop owns waiting, parking and retrying.
"""

import importlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol, cast

ANY = "**"  # an edit glob for the whole repo
# Command prefixes a job may run; never the owner's commands (signoff, accept).
CHECK_COMMANDS = ("uv run pytest", "uv run ruff", "uv run mypy", "softfield check-all")
GIT_READ_COMMANDS = ("git diff", "git log", "git show")  # the runner commits, never a job

# ADR 15 item 12's error classes
LIMIT, TRANSIENT, FAILURE = "limit", "transient", "failure"
LOGIN = "login"  # the harness's login has expired: only the owner can end it (bug-59)


@dataclass(frozen=True)
class WindowSeed:
    """A starting guess at one of an agent's allowance windows; learned after (ADR 15 item 2)."""

    name: str  # "five_hour", "seven_day", "month", …
    capacity: float | None = None  # None: unknown, used until refused


@dataclass(frozen=True)
class Agent:
    id: str  # `<harness>-<model>` (D6)
    harness: str  # "claude", "opencode", "copilot"
    model: str  # as the harness names it
    rating: int  # 1–10, the lead's estimate until results move it (ADR 15 item 9)
    windows: tuple[WindowSeed, ...] = ()


@dataclass(frozen=True)
class JobSpec:
    role: str  # an ADR 14 role: "direction", "checkpoint", "lead-ticket", …
    prompt: str
    timeout: int  # seconds
    edit: tuple[str, ...] = ()  # globs it may write, ANY for anywhere; none: read-only
    commands: tuple[str, ...] = ()  # command prefixes it may run
    resume: str | None = None  # a session to carry on, where the harness keeps them
    title: str = ""  # the session's name, where the harness shows one
    # Sandboxed: it may write only under these folders (runner/sandbox.py; the bench's copy).
    # OpenCode only for now; empty: no sandbox.
    writable: tuple[Path, ...] = ()
    # The factory's context (ADR 41 item 2): the system prompt where the harness has one
    system: str = ""

    @property
    def read_only(self) -> bool:
        return not self.edit

    @property
    def whole_prompt(self) -> str:
        """For a harness with no system prompt of its own."""
        return self.system + self.prompt


@dataclass(frozen=True)
class Reading:
    """One of an agent's allowance windows as its harness reported it (ADR 15 item 3)."""

    window: str  # "five_hour" | "seven_day" (Claude) | "month" (Copilot)
    utilization: float  # the share used, 0–1
    resets_at: datetime


@dataclass(frozen=True)
class Refusal:
    """A job stopped by a limit. ``certain`` is False when the error only looks like one."""

    window: str | None
    resets_at: datetime | None
    certain: bool = True


@dataclass(frozen=True)
class JobResult:
    ok: bool
    text: str
    duration_s: float
    usage: dict[str, int] = field(default_factory=dict)  # tokens, by kind
    requests: float = 0.0  # for a harness metered in requests
    cost_usd: float | None = None  # the harness's API-equivalent price (f1 D7)
    refusal: Refusal | None = None
    transient: bool = False  # a lost connection, an overload, a server error
    login_expired: bool = False
    num_turns: int = 0
    session_id: str | None = None
    readings: tuple[Reading, ...] = ()  # every window reading, in order
    model: str = ""  # the exact model it ran on, as its harness reported it (f2-04)
    # What a developer's attempt did, where the harness streams it (ADR 12 items 4, 6 and 7)
    peak_context: int = 0  # the largest context one step sent
    edit_streak: int = 0  # the longest run of edits without running a command
    refused_commands: int = 0
    edits: int = 0
    timed_out: bool = False

    @property
    def error(self) -> str | None:
        if self.ok:
            return None
        if self.refusal is not None:
            return LIMIT
        if self.login_expired:
            return LOGIN
        return TRANSIENT if self.transient else FAILURE


class Adapter(Protocol):
    def run(
        self, agent: Agent, spec: JobSpec, repo: Path, log_path: Path, now: datetime
    ) -> JobResult: ...


class UnknownHarness(KeyError):
    pass


# A harness's adapter is its module's ``ADAPTER``, imported when first asked for.
HARNESSES = {
    "claude": "runner.claude",
    "opencode": "runner.local_model",
    "copilot": "runner.copilot",
}


def adapter_for(harness: str) -> Adapter:
    if harness not in HARNESSES:
        raise UnknownHarness(f"no adapter for the harness {harness!r}")
    return cast(Adapter, importlib.import_module(HARNESSES[harness]).ADAPTER)
