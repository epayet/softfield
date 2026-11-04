"""What the runner prints as it works (f1-42, ADR 15 item 14): pure formatters.

Every line names its agent in brackets (`[claude-opus]`, `[local-…]`, `[runner]`); a ticket
that merges at the first attempt takes about six lines. `Session.log` adds the time."""

from datetime import datetime


def duration(seconds: float) -> str:
    total = round(seconds / 60)
    return f"{total} min" if total < 60 else f"{total // 60} h {total % 60:02d}"


def tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def ticket_header(task_id: str, role: str, difficulty: int | None) -> str:
    parts = [task_id, role, *([f"d{difficulty}"] if difficulty is not None else [])]
    return "── " + " · ".join(parts) + " ──"


def start(agent: str, what: str) -> str:
    return f"▶ [{agent}] {what}"


def local_end(
    agent: str, what: str, outcome: str, seconds: float, total_tokens: int, steps: int
) -> str:
    return (
        f"■ [{agent}] {what} {outcome} · {duration(seconds)}"
        f" · {tokens(total_tokens)} tokens · {steps} steps"
    )


def claude_end(
    agent: str, what: str, ok: bool, seconds: float, cost: float | None, timed_out: bool = False
) -> str:
    parts = [duration(seconds), *([f"${cost:.2f}"] if cost is not None else [])]
    outcome = "done" if ok else "cut off at its time limit" if timed_out else "failed"
    return f"■ [{agent}] {what} {outcome} · " + " · ".join(parts)


def first_line(text: str) -> str:
    """The first line with words in it, without its heading marks."""
    for line in text.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line
    return ""


def summary(agent: str, text: str) -> str | None:
    """What a Claude job did, under its end line, whole (the owner read cut ones, f1-51);
    None when there's nothing to say."""
    line = first_line(text)
    return f"  ↳ [{agent}] {line}" if line else None


def local_progress(
    agent: str, what: str, seconds: float, total_tokens: int, steps: int, edit_streak: int
) -> str:
    return (
        f"… [{agent}] {what} · {duration(seconds)} · {tokens(total_tokens)} tokens"
        f" · {steps} steps · edit streak {edit_streak}"
    )


def running(agent: str, what: str, seconds: float) -> str:
    return f"… [{agent}] {what} still running · {duration(seconds)}"


def merged(agent: str, task_id: str, attempts: int, lines: int | None, seconds: float) -> str:
    parts = [_plural(attempts, "attempt"), *([f"{lines} lines"] if lines is not None else [])]
    return f"✔ [{agent}] {task_id} merged · " + " · ".join([*parts, duration(seconds)])


def stopped(task_id: str, state: str, reason: str, where: str, waiting: int) -> str:
    behind = (
        "nothing waits"
        if not waiting
        else f"{_plural(waiting, 'ticket')} {'waits' if waiting == 1 else 'wait'} behind it"
    )
    return f"⚠ [runner] {task_id} {state}: {reason} · {where} · {behind}"


def paused(agent: str, why: str, resumes: datetime, now: datetime) -> str:
    shown = resumes.astimezone()
    same_day = shown.date() == now.astimezone().date()
    at = f"{shown:%H:%M}" if same_day else f"{shown:%a %H:%M}"
    return f"⏸ [{agent}] {why} · resumes {at} (in {duration((resumes - now).total_seconds())})"


def resumed(agent: str, what: str) -> str:
    return f"▶ [{agent}] {what} resumed"
