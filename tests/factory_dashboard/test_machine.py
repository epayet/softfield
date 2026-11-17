"""How long the computer has been on (F251 D1, D2): read from a faked /proc/uptime or a faked
sysctl, never the real machine."""

import subprocess
from datetime import UTC, datetime, timedelta

import pytest

from factory_dashboard import machine

NOW = datetime(2026, 11, 16, 21, 46, tzinfo=UTC)
# conftest's autouse _no_uptime stands booted_at in for the pages; these tests want the real one
booted_at = machine.booted_at


@pytest.fixture
def proc(monkeypatch, tmp_path):
    """A /proc/uptime of the given text, or none when the text is None."""

    def write(text: str | None):
        path = tmp_path / "uptime"
        if text is not None:
            path.write_text(text)
        monkeypatch.setattr(machine, "UPTIME", path)

    return write


@pytest.fixture
def sysctl(monkeypatch):
    """``sysctl -n kern.boottime`` printing the given text, or failing when it is None."""
    calls: list[list[str]] = []

    def write(text: str | None):
        def run(args, **kwargs):
            calls.append(args)
            if text is None:
                raise FileNotFoundError(args[0])
            return subprocess.CompletedProcess(args, 0, stdout=text, stderr="")

        monkeypatch.setattr(subprocess, "run", run)
        return calls

    return write


@pytest.mark.parametrize(
    ("span", "words"),
    [
        (timedelta(minutes=42, seconds=59), "42 min"),
        (timedelta(hours=5, minutes=12), "5 h 12 min"),
        (timedelta(days=6, hours=4, minutes=59), "6 d 4 h"),
        (timedelta(minutes=59, seconds=59), "59 min"),
        (timedelta(hours=23, minutes=59), "23 h 59 min"),
        (timedelta(days=1), "1 d 0 h"),
    ],
)
def test_on_for_says_minutes_then_hours_then_days(span, words):
    assert machine.on_for(NOW - span, NOW) == words


def test_linux_start_is_now_less_proc_uptimes_first_number(proc, sysctl):
    proc("535440.25 1000000.00\n")  # 6 d 4 h 44 min 0.25 s
    calls = sysctl("{ sec = 1, usec = 0 }")
    assert booted_at(NOW) == NOW - timedelta(seconds=535440.25)
    assert calls == []  # Linux answered: macOS's command never runs


def test_macos_start_is_kern_boottimes_sec(proc, sysctl):
    proc(None)
    calls = sysctl("{ sec = 1762731720, usec = 482000 } Mon Nov 10 00:42:00 2025\n")
    assert booted_at(NOW) == datetime(2025, 11, 9, 23, 42, tzinfo=UTC)
    assert calls == [["sysctl", "-n", "kern.boottime"]]


@pytest.mark.parametrize("text", ["", "not a number\n"])
def test_an_unreadable_proc_uptime_falls_back_to_sysctl(proc, sysctl, text):
    proc(text)
    sysctl("{ sec = 1762731720, usec = 0 }")
    assert booted_at(NOW) == datetime(2025, 11, 9, 23, 42, tzinfo=UTC)


@pytest.mark.parametrize("out", [None, "kern.boottime: unknown oid\n"])
def test_neither_source_means_none(proc, sysctl, out):
    proc(None)
    sysctl(out)
    assert booted_at(NOW) is None
