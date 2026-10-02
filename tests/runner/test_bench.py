"""`runner bench` (ADR 14 item 8) on a real temporary git repo, with the agents faked."""

import os
import sqlite3
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from runner import bench, gates, loop
from runner.agents import Agent, JobResult, JobSpec, Refusal
from runner.config import Config
from runner.gitops import with_trailers
from runner.tasks import append_footer
from tests.runner.conftest import git, write_task

TICKET = "m1-01-thing"
AGENTS = (
    Agent("fake-a", "fake", "a", 5),
    Agent("fake-b", "fake", "b", 5),
    Agent("claude-opus", "claude", "opus", 9),
    Agent("ollama-x", "opencode", "ollama/x", 5),  # the real OpenCode adapter, a fake binary
)
RESETS = datetime(2026, 10, 3, 4, 0, tzinfo=UTC)


@pytest.fixture
def copies(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The `[bench] dir`: outside the repo, as in real use."""
    return tmp_path_factory.mktemp("bench-copies")


def _config(repo: Path, copies: Path) -> Config:
    return Config(
        repo=repo,
        bench_copies=copies,
        max_attempts=3,
        directions_per_task=1,
        escalations_per_task=2,
        checkpoint_every=2,
        review_rounds=3,
        default_max_diff=150,
        warmup_timeout=1,
        opencode_timeout=1,
        claude_timeout=1,
        gate_timeout=60,
        lm_base_url="http://x",
        lm_model="m",
        backoff_min=1,
        backoff_max=2,
        narrative=False,
        metrics_db=repo / "var" / "factory-metrics.sqlite",  # never the real one
        agents={a.id: a for a in AGENTS},
        roles={"developer": ("fake-a",), "escalation": ("claude-opus",)},
    )


def _history(repo: Path) -> str:
    """A ticket merged like the runner merges one, then today's workflow files changed after.
    Returns the merge's parent."""
    (repo / "AGENTS.md").write_text("old rules\n")
    (repo / "docs" / "agents").mkdir(parents=True)
    (repo / "docs" / "agents" / "developer.md").write_text("old notes\n")
    write_task(repo / "tasks" / "ready", TICKET)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"add {TICKET}")
    parent = git(repo, "rev-parse", "HEAD").strip()
    (repo / "coucou" / "thing.py").write_text("def thing() -> int:\n    return 42\n")
    git(repo, "commit", "-q", "-am", with_trailers(f"{TICKET}: done", task=TICKET))
    git(repo, "mv", f"tasks/ready/{TICKET}.md", f"tasks/done/{TICKET}.md")
    append_footer(repo / "tasks" / "done" / f"{TICKET}.md", {"result": "done", "attempts": 1})
    git(repo, "commit", "-q", "-am", f"runner: {TICKET} done")
    (repo / "AGENTS.md").write_text("today's rules\n")
    (repo / "docs" / "agents" / "developer.md").write_text("today's notes\n")
    git(repo, "commit", "-q", "-am", "today's workflow")
    return parent


Act = Callable[[Path, JobSpec], JobResult | None]


@pytest.fixture
def fake_agents(monkeypatch) -> dict[str, list[Act]]:
    """Each fake agent's scripted runs, in order; Claude must never be called."""
    script: dict[str, list[Act]] = {"fake-a": [], "fake-b": []}

    class Fake:
        def run(self, agent, spec, repo, log_path, now):
            log_path.write_text(spec.prompt)
            result = script[agent.id].pop(0)(repo, spec)
            return result or JobResult(ok=True, text="done", duration_s=1.0, num_turns=3)

    def adapter_for(harness: str):
        if harness != "fake":
            pytest.fail(f"bench called the {harness} harness")
        return Fake()

    def no_claude(*args, **kwargs):
        pytest.fail("bench called Claude")

    monkeypatch.setattr(bench, "adapter_for", adapter_for)
    monkeypatch.setattr(loop, "call_claude", no_claude)
    file_gates = tuple(
        g
        for g in gates.GATES
        if g.__name__
        in {"gate_protected", "gate_no_new_skips", "gate_dependencies", "gate_diff_size"}
    )
    monkeypatch.setattr(gates, "GATES", file_gates)
    return script


def _implement(repo: Path, spec: JobSpec) -> None:
    (repo / "coucou" / "thing.py").write_text("def thing() -> int:\n    return 42\n")


def _stray(repo: Path, spec: JobSpec) -> None:
    (repo / "coucou" / "secret.py").write_text("X = 1\n")


def _fix(repo: Path, spec: JobSpec) -> None:
    """A retry: it builds on the attempt before, told what failed."""
    assert "protected-paths" in spec.prompt
    (repo / "coucou" / "secret.py").unlink()
    _implement(repo, spec)


def _jobs(repo: Path) -> list[sqlite3.Row]:
    conn = sqlite3.connect(repo / "var" / "factory-metrics.sqlite")
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(
            "SELECT j.*, t.ticket, r.command FROM jobs j JOIN runs r ON r.id = j.run_id"
            " LEFT JOIN tickets t ON t.id = j.ticket_id ORDER BY j.id"
        ).fetchall()
    finally:
        conn.close()


def _snapshot(repo: Path) -> tuple[str | int, ...]:
    return (
        git(repo, "rev-parse", "main"),
        git(repo, "branch", "--list"),
        git(repo, "status", "--porcelain"),
        git(repo, "worktree", "list", "--porcelain").count("worktree "),
    )


def test_two_agents_get_their_own_bench_jobs_and_main_is_untouched(repo, copies, fake_agents):
    _history(repo)
    before = _snapshot(repo)
    fake_agents["fake-a"].append(_implement)
    fake_agents["fake-b"].extend([_stray, _fix])
    report = bench.run_bench(_config(repo, copies), [TICKET], ["fake-a", "fake-b"])
    assert report.stopped is None
    assert [(r.ticket, r.agent, r.outcome, r.attempts) for r in report.results] == [
        (TICKET, "fake-a", "passed", 1),
        (TICKET, "fake-b", "passed", 2),
    ]
    jobs = _jobs(repo)
    assert {(j["command"], j["role"], j["ticket"]) for j in jobs} == {("bench", "bench", TICKET)}
    assert [(j["agent"], j["outcome"]) for j in jobs] == [
        ("fake-a", "passed"),
        ("fake-b", "failed"),
        ("fake-b", "passed"),
    ]
    assert len({j["attempt"] for j in jobs}) == 3  # one row each: two agents never share a key
    assert '"name": "protected-paths", "ok": false' in jobs[1]["gates"]
    # main, the branches, the tree and tasks/ are as they were; the copies are gone
    assert _snapshot(repo) == before
    assert not (repo / "coucou" / "secret.py").exists()
    assert "raise NotImplementedError" not in (repo / "coucou" / "thing.py").read_text()
    assert not list(copies.iterdir())


def test_the_copy_starts_at_the_merges_parent_with_todays_workflow(repo, copies, fake_agents):
    parent = _history(repo)
    seen: dict[str, str] = {}

    def look(work: Path, spec: JobSpec) -> None:
        seen["parent"] = git(work, "rev-parse", "HEAD~1").strip()
        seen["thing"] = (work / "coucou" / "thing.py").read_text()
        seen["agents"] = (work / "AGENTS.md").read_text()
        seen["notes"] = (work / "docs" / "agents" / "developer.md").read_text()
        seen["ticket"] = (work / "tasks" / "ready" / f"{TICKET}.md").read_text()
        seen["branch"] = git(work, "rev-parse", "--abbrev-ref", "HEAD").strip()
        seen["remotes"] = git(work, "remote")
        # its own clone: its own .git, under [bench] dir, nothing shared with the repo's
        assert work.is_relative_to(copies) and not work.is_relative_to(repo)
        common = git(work, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
        assert Path(common) == work / ".git"
        _implement(work, spec)

    fake_agents["fake-a"].append(look)
    bench.run_bench(_config(repo, copies), [TICKET], ["fake-a"])
    assert seen["parent"] == parent
    assert "raise NotImplementedError" in seen["thing"]
    assert (seen["agents"], seen["notes"]) == ("today's rules\n", "today's notes\n")
    assert "Make the thing work." in seen["ticket"] and "# --- runner ---" not in seen["ticket"]
    assert seen["branch"] == "HEAD"  # detached: no branch of the repo moves
    assert seen["remotes"] == ""  # no remote leads back to the repo


# Resolves its project the way OpenCode does: the worktree, then the repository it belongs
# to (the common dir's parent), and edits there. In a `git worktree` that's the main checkout.
FAKE_OPENCODE = """\
#!/bin/sh
top=$(git rev-parse --show-toplevel)
common=$(git rev-parse --path-format=absolute --git-common-dir)
project=$(dirname "$common")
echo "worktree: $top"
echo "project: $project"
echo "X = 1" > "$project/coucou/opencode_was_here.py"
"""


def test_an_opencode_agent_edits_its_copy_never_the_main_checkout(
    repo, copies, tmp_path_factory, monkeypatch
):
    _history(repo)
    bin_dir = tmp_path_factory.mktemp("bin")
    fake = bin_dir / "opencode"
    fake.write_text(FAKE_OPENCODE)
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(loop, "call_claude", lambda *a, **k: pytest.fail("bench called Claude"))
    file_gates = tuple(g for g in gates.GATES if g.__name__ in {"gate_protected", "gate_diff_size"})
    monkeypatch.setattr(gates, "GATES", file_gates)
    cfg = replace(_config(repo, copies), opencode_timeout=60)
    before = _snapshot(repo)
    report = bench.run_bench(cfg, [TICKET], ["ollama-x"])
    assert _snapshot(repo) == before
    assert not (repo / "coucou" / "opencode_was_here.py").exists()
    [result] = report.results
    assert (result.outcome, result.attempts) == ("passed", 1)  # the edit landed in the copy
    [log] = (repo / "var" / "bench").glob(f"*/{TICKET}-ollama-x/opencode-1.jsonl")
    project = Path(log.read_text().split("project: ")[1].splitlines()[0])
    assert project.is_relative_to(copies)
    assert not list(copies.iterdir())  # removed afterwards


def test_a_bench_dir_inside_the_repo_is_refused(repo, fake_agents):
    _history(repo)
    with pytest.raises(loop.RunnerError, match=r"\[bench\] dir"):
        bench.run_bench(_config(repo, repo / "var" / "copies"), [TICKET], ["fake-a"])
    assert not (repo / "var" / "copies").exists()


def test_a_failing_agent_would_escalate_without_calling_claude(repo, copies, fake_agents):
    _history(repo)
    fake_agents["fake-a"].extend([_stray, _stray, _stray])  # the file stays: each one fails
    report = bench.run_bench(_config(repo, copies), [TICKET], ["fake-a"])
    [result] = report.results
    assert (result.outcome, result.attempts) == ("would escalate", 3)
    jobs = _jobs(repo)
    assert [j["outcome"] for j in jobs] == ["failed"] * 3
    assert jobs[-1]["note"] == "would escalate"
    assert not fake_agents["fake-a"]


def test_a_refusal_stops_the_bench_and_says_who_and_when_it_resets(repo, copies, fake_agents):
    _history(repo)

    def refuse(work: Path, spec: JobSpec) -> JobResult:
        _implement(work, spec)
        return JobResult(
            ok=False, text="quota", duration_s=0.5, refusal=Refusal("five_hour", RESETS)
        )

    fake_agents["fake-a"].append(refuse)
    fake_agents["fake-b"].append(_implement)
    before = _snapshot(repo)
    report = bench.run_bench(_config(repo, copies), [TICKET], ["fake-a", "fake-b"])
    assert report.stopped is not None
    assert "fake-a" in report.stopped and RESETS.astimezone().strftime("%H:%M") in report.stopped
    assert [(r.agent, r.outcome) for r in report.results] == [("fake-a", "refused")]
    assert fake_agents["fake-b"] == [_implement]  # never ran
    assert [(j["agent"], j["outcome"]) for j in _jobs(repo)] == [("fake-a", "refused")]
    assert _snapshot(repo) == before


def test_unknown_tickets_and_agents_fail_before_anything_runs(repo, copies, fake_agents):
    _history(repo)
    with pytest.raises(loop.RunnerError, match="no-such-agent"):
        bench.run_bench(_config(repo, copies), [TICKET], ["no-such-agent"])
    with pytest.raises(loop.RunnerError, match="m1-99-none"):
        bench.run_bench(_config(repo, copies), ["m1-99-none"], ["fake-a"])
    assert not (repo / "var" / "factory-metrics.sqlite").exists()
