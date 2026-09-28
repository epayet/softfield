"""The local executor: LM Studio warm-up and headless OpenCode runs."""

import json
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


def run_opencode(
    repo: Path, model: str, title: str, prompt: str, timeout: int, log_path: Path
) -> OpencodeRun:
    cmd = ["opencode", "run", "--format", "json", "-m", model, "--title", title, prompt]
    started = time.monotonic()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            cmd, cwd=repo, capture_output=True, text=True, timeout=timeout, check=False
        )
        stdout, exit_code = proc.stdout, proc.returncode
        log_path.write_text(stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout
        stdout = raw.decode() if isinstance(raw, bytes) else (raw or "")
        exit_code = None
        log_path.write_text(stdout + "\n--- timed out ---\n", encoding="utf-8")
    return OpencodeRun(
        exit_code=exit_code,
        duration_s=time.monotonic() - started,
        tokens=parse_events(stdout.splitlines()),
    )
