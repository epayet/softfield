"""runner/sandbox.py: a sandboxed command writes only where it's allowed (Landlock)."""

import subprocess
import sys
from pathlib import Path

import pytest

from runner import sandbox

pytestmark = pytest.mark.skipif(not sandbox.available(), reason="no Landlock on this kernel")


def _run(cmd: list[str], writable: list[Path], monkeypatch) -> subprocess.CompletedProcess[str]:
    monkeypatch.setattr(sandbox, "TOOL_DIRS", (Path("/dev"),))  # /tmp holds the "outside" too
    return subprocess.run(sandbox.wrap(cmd, writable), capture_output=True, text=True, check=False)


WRITER = """\
import os, sys
from pathlib import Path
inside, outside, kept = (Path(p) for p in sys.argv[1:])
(inside / "new.txt").write_text("ok")
for what, act in [
    ("create", lambda: (outside / "leak.txt").write_text("x")),
    ("truncate", lambda: kept.write_text("")),
    ("delete", lambda: kept.unlink()),
    ("mkdir", lambda: (outside / "d").mkdir()),
]:
    try:
        act()
        print(what, "allowed")
    except PermissionError:
        print(what, "denied")
"""


def test_writes_land_only_in_the_allowed_folders(tmp_path, monkeypatch):
    inside, outside = tmp_path / "copy", tmp_path / "main"
    inside.mkdir()
    outside.mkdir()
    kept = outside / "README.md"
    kept.write_text("the owner's file\n")
    script = tmp_path / "writer.py"
    script.write_text(WRITER)
    cmd = [sys.executable, str(script), str(inside), str(outside), str(kept)]
    done = _run(cmd, [inside, tmp_path / "writer.py"], monkeypatch)
    assert done.returncode == 0, done.stderr
    assert done.stdout.split("\n")[:4] == [
        "create denied",
        "truncate denied",
        "delete denied",
        "mkdir denied",
    ]
    assert (inside / "new.txt").read_text() == "ok"
    assert kept.read_text() == "the owner's file\n"
    assert list(outside.iterdir()) == [kept]


def test_the_sandbox_starts_from_a_folder_with_another_runner_package(tmp_path, monkeypatch):
    """A bench copy holds an older `runner/`, maybe without sandbox.py: the launcher is ours."""
    (tmp_path / "runner").mkdir()
    (tmp_path / "runner" / "__init__.py").write_text("raise SystemExit('the copy')\n")
    monkeypatch.chdir(tmp_path)
    done = _run(["sh", "-c", "echo ran"], [tmp_path], monkeypatch)
    assert (done.returncode, done.stdout) == (0, "ran\n"), done.stderr


def test_the_launcher_does_not_need_sandbox_py_on_disk(tmp_path, monkeypatch):
    """The runner checks out older task branches in the main checkout, some without
    runner/sandbox.py: a bench beside it found no file to start (2026-10-06, gemma)."""
    cmd = sandbox.wrap(["true"], [tmp_path])
    assert not any(arg.endswith("sandbox.py") for arg in cmd)
    done = _run(["sh", "-c", "echo ran"], [tmp_path], monkeypatch)
    assert (done.returncode, done.stdout) == (0, "ran\n"), done.stderr
