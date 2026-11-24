"""How long the computer the dashboard runs on has been on (F251 D1, D2): its last start, read
from the operating system, sleep included, and the top bar's words for the span."""

from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

UPTIME = Path("/proc/uptime")  # Linux: seconds since the last start, then idle seconds
BOOTTIME = ["sysctl", "-n", "kern.boottime"]  # macOS: "{ sec = 1700000000, usec = 0 } Tue …"


def booted_at(now: datetime) -> datetime | None:
    """When the computer last started, or None when neither Linux's nor macOS's source answers."""
    try:
        return now - timedelta(seconds=float(UPTIME.read_text().split()[0]))
    except (OSError, ValueError, IndexError):
        pass
    try:
        out = subprocess.run(BOOTTIME, capture_output=True, text=True, timeout=2, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    sec = re.search(r"\bsec = (\d+)", out)
    return datetime.fromtimestamp(int(sec[1]), UTC) if sec else None


def on_for(booted: datetime, now: datetime) -> str:
    """The span in the top bar's words: "42 min" under an hour, "5 h 12 min" under a day,
    then "6 d 4 h"."""
    return on_for_delta(now - booted)


def on_for_delta(delta: timedelta) -> str:
    """The span for an elapsed ``timedelta``: "42 min" under an hour, "5 h 12 min" under a day,
    then "6 d 4 h"."""
    total_seconds = max(0, int(delta.total_seconds()))
    minutes = total_seconds // 60
    days, minutes = divmod(minutes, 24 * 60)
    hours, minutes = divmod(minutes, 60)
    if days:
        return f"{days} d {hours} h"
    if hours:
        return f"{hours} h {minutes} min"
    return f"{minutes} min"
