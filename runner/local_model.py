"""The local executor: LM Studio warm-up and headless OpenCode runs."""

import contextlib
import json
import os
import signal
import subprocess
import time
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TokenTotals:
    input: int = 0
    output: int = 0
    reasoning: int = 0
    steps: int = 0


@dataclass(frozen=True)
class OpencodeRun:
    exit_code: int | None  # None when it timed out
    duration_s: float
    tokens: TokenTotals

    @property
    def timed_out(self) -> bool:
        return self.exit_code is None


def parse_events(lines: Iterable[str]) -> TokenTotals:
    """Sum token usage over OpenCode's ``--format json`` step_finish events."""
    inp = out = reasoning = steps = 0
    for line in lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "step_finish":
            continue
        tokens = (event.get("part") or {}).get("tokens") or {}
        inp += int(tokens.get("input", 0))
        out += int(tokens.get("output", 0))
        reasoning += int(tokens.get("reasoning", 0))
        steps += 1
    return TokenTotals(input=inp, output=out, reasoning=reasoning, steps=steps)


def warmup(base_url: str, model: str, timeout: int) -> float:
    """One sequential tiny request so LM Studio JIT-loads the model with the owner's settings."""
    body = json.dumps(
        {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}
    ).encode()
    request = urllib.request.Request(  # noqa: S310 - base_url is our localhost config
        f"{base_url}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - localhost
        response.read()
    return time.monotonic() - started


def loaded_context_length(base_url: str, model: str) -> int | None:
    try:
        with urllib.request.urlopen(f"{base_url}/api/v0/models/{model}", timeout=10) as r:  # noqa: S310
            data = json.load(r)
    except OSError:
        return None
    value = data.get("loaded_context_length")
    return int(value) if value else None


def run_killing_group(cmd: list[str], cwd: Path, timeout: int) -> tuple[str, str, int | None]:
    """Run ``cmd`` in its own process group; on timeout kill the whole group.

    OpenCode starts shell commands of its own (pytest, ruff…). Killing only OpenCode would
    leave a hung child running after the attempt. Returns (stdout, stderr, exit code or None).
    """
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return stdout, stderr, proc.returncode
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
        return stdout or "", stderr or "", None


def run_opencode(
    repo: Path, model: str, title: str, prompt: str, timeout: int, log_path: Path
) -> OpencodeRun:
    cmd = ["opencode", "run", "--format", "json", "-m", model, "--title", title, prompt]
    started = time.monotonic()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stdout, stderr, exit_code = run_killing_group(cmd, repo, timeout)
    marker = "\n--- timed out ---\n" if exit_code is None else "\n--- stderr ---\n" + stderr
    log_path.write_text(stdout + marker, encoding="utf-8")
    return OpencodeRun(
        exit_code=exit_code,
        duration_s=time.monotonic() - started,
        tokens=parse_events(stdout.splitlines()),
    )
