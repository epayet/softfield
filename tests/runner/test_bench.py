"""`runner bench` (ADR 14 item 8) on a real temporary git repo, with the agents faked."""

import os
import sqlite3
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from factory_dashboard import queries
from runner import bench, gates, loop, metrics
from runner.agents import Agent, JobResult, JobSpec, Refusal
from runner.config import Config
from runner.gitops import Git, with_trailers
from runner.review import Finding
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


def _history(repo: Path, trailer: bool = True) -> str:
    """A ticket merged like the runner merges one, then today's workflow files changed after.
    Without ``trailer``, merged as an escalation that implemented it (no `Task:`). Returns the
    merge's parent."""
    (repo / "AGENTS.md").write_text("old rules\n")
    (repo / "docs" / "agents").mkdir(parents=True)
    (repo / "docs" / "agents" / "developer.md").write_text("old notes\n")
    write_task(repo / "tasks" / "ready", TICKET)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"add {TICKET}")
    parent = git(repo, "rev-parse", "HEAD").strip()
    (repo / "coucou" / "thing.py").write_text("def thing() -> int:\n    return 42\n")
    message = f"escalation {TICKET}: implemented (by Claude)"
    git(
        repo,
        "commit",
        "-q",
        "-am",
        with_trailers(f"{TICKET}: done", task=TICKET) if trailer else message,
    )
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
        seen["tree"] = git(work, "rev-parse", "HEAD~1^{tree}").strip()
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
    assert seen["tree"] == git(repo, "rev-parse", f"{parent}^{{tree}}").strip()
    assert "raise NotImplementedError" in seen["thing"]
    assert (seen["agents"], seen["notes"]) == ("today's rules\n", "today's notes\n")
    assert "Make the thing work." in seen["ticket"] and "# --- runner ---" not in seen["ticket"]
    assert seen["branch"] == "HEAD"  # detached: no branch of the repo moves
    assert seen["remotes"] == ""  # no remote leads back to the repo


def test_a_copy_has_its_own_root_commit_and_the_gates_diff_against_its_base(repo, copies):
    """OpenCode keys a project by the repo's root commit (`rev-list --max-parents=0 --all`):
    a copy sharing it was given the main checkout as its directory (f4-19)."""
    parent = _history(repo)
    git(repo, "tag", "v1", parent)  # no ref of the repo's may survive in the copy
    work = copies / "copy"
    base = bench.make_copy(_config(repo, copies), work, parent, TICKET, "the ticket\n")
    repo_roots = set(git(repo, "rev-list", "--max-parents=0", "--all").split())
    [root] = git(work, "rev-list", "--max-parents=0", "--all").split()
    assert root not in repo_roots
    other = copies / "other"  # the next agent on the same ticket, within the same second
    bench.make_copy(_config(repo, copies), other, parent, TICKET, "the ticket\n")
    assert git(other, "rev-list", "--max-parents=0", "HEAD").split() != [root]
    assert git(work, "rev-list", "--count", "--all").strip() == "2"  # the root, then the base
    assert git(work, "rev-parse", f"{root}^{{tree}}") == git(
        repo, "rev-parse", f"{parent}^{{tree}}"
    )
    _implement(work, None)  # type: ignore[arg-type]
    work_git = Git(work)
    work_git.commit_all("attempt 1")
    assert work_git.changed_files(base) == ["coucou/thing.py"]
    assert work_git.diff_size(base) > 0


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


def test_each_replay_is_a_rating_game_for_its_agent(repo, copies, fake_agents):
    """ADR 24 item 3: a new model earns its rating on the bench."""
    _history(repo)
    cfg = _config(repo, copies)
    conn = metrics.open_db(cfg.metrics_db)
    metrics.upsert_ticket(conn, metrics.upsert_project(conn, repo.name), TICKET, difficulty=5)
    conn.close()
    fake_agents["fake-a"].append(_implement)
    fake_agents["fake-b"].extend([_stray, _stray, _stray])
    bench.run_bench(cfg, [TICKET], ["fake-a", "fake-b"])
    conn = sqlite3.connect(cfg.metrics_db)
    try:
        changes = conn.execute(
            "SELECT agent, before, after, result FROM rating_changes ORDER BY at"
        ).fetchall()
    finally:
        conn.close()
    assert [(agent, result) for agent, _, _, result in changes] == [
        ("fake-a", "bench passed at the first attempt"),
        ("fake-b", "bench not passed"),
    ]
    assert changes[0][2] > changes[0][1] and changes[1][2] < changes[1][1]


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


def test_a_review_finding_matches_by_file_and_nearby_line_or_by_summary():
    known = bench.Known("k", "nit", "coucou/thing.py", 10, "Magic number")
    found = [
        Finding("1", "nit", "backlog", "other words", file="coucou/thing.py", line=14),
        Finding("2", "nit", "backlog", "other words", file="coucou/thing.py", line=30),
        Finding("3", "nit", "backlog", "  magic   NUMBER ", file="coucou/else.py", line=1),
        Finding("4", "nit", "backlog", "other words", file="coucou/thing.py"),
        Finding("5", "nit", "backlog", "other words", file="coucou/else.py", line=10),
    ]
    assert [bench.matches(known, f) for f in found] == [True, False, True, True, False]


# --- review replays (ADR 16 item 10) --------------------------------------------------------

ANSWER = """Here is what I found.
```json
{"findings": [
  {"severity": "should-fix", "file": "coucou/thing.py", "line": 3, "summary": "a constant",
   "detail": "42 is unexplained", "route": "backlog", "ticket": "m1-01-thing"},
  {"severity": "nit", "file": "coucou/new.py", "line": null, "summary": "nobody saw this",
   "detail": "", "route": "backlog", "ticket": "m1-01-thing"}
]}
```"""


def _metrics(repo: Path) -> sqlite3.Connection:
    return metrics.open_db(repo / "var" / "factory-metrics.sqlite")


def _checkpointed(repo: Path, trailer: bool = True) -> int:
    """`_history`'s merge, reviewed by a checkpoint with two known findings: a should-fix in
    coucou/thing.py and a blocking one in the test. Returns the checkpoint's job."""
    _history(repo, trailer)
    merge = git(repo, "rev-parse", "HEAD~2").strip()
    conn = _metrics(repo)
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        m1 = metrics.upsert_milestone(conn, project, "m1")
        run = metrics.upsert_run(conn, project, "20260930-100000", command="run")
        ticket = metrics.upsert_ticket(
            conn, project, TICKET, milestone_id=m1, kind="developer", commit=merge, difficulty=3
        )
        for role, ticket_id, agent, started in (
            ("developer", ticket, "fake-a", "2026-09-30T10:00:00+02:00"),
            ("checkpoint", None, "claude-opus", "2026-09-30T11:00:00+02:00"),
        ):
            job = metrics.start_job(
                conn,
                run,
                ticket_id=ticket_id,
                milestone_id=m1,
                role=role,
                agent=agent,
                attempt=1,
                started=started,
            )
            metrics.finish_job(conn, job, ended=started, outcome="passed")
        checkpoint = job
        for n, severity, file, line, summary in (
            (1, "should-fix", "coucou/thing.py", 2, "thing returns a magic number"),
            (2, "blocking", "tests/unit/test_thing.py", 2, "the test checks nothing"),
        ):
            metrics.add_finding(
                conn,
                m1,
                f"m1-C{checkpoint}-{n}",
                job_id=checkpoint,
                ticket_id=ticket,
                severity=severity,
                file=file,
                line=line,
                summary=summary,
                agent="claude-opus",
            )
    finally:
        conn.close()
    return checkpoint


def _answer(text: str) -> Act:
    def act(work: Path, spec: JobSpec) -> JobResult:
        assert spec.read_only
        assert TICKET in spec.prompt and "coucou/thing.py" in spec.prompt
        # the copy as the checkpoint saw it: the merge, with the ticket in done/
        assert "return 42" in (work / "coucou" / "thing.py").read_text()
        assert (work / "tasks" / "done" / f"{TICKET}.md").is_file()
        (work / "coucou" / "thing.py").write_text("edited\n")  # only ever the copy
        return JobResult(ok=True, text=text, duration_s=1.0, num_turns=2)

    return act


def test_a_review_replay_scores_a_hit_a_miss_and_lists_the_new_finding(repo, copies, fake_agents):
    checkpoint = _checkpointed(repo)
    before = _snapshot(repo)
    fake_agents["fake-a"].append(_answer(ANSWER))
    report = bench.run_review_bench(_config(repo, copies), ["m1"], ["fake-a"])
    assert report.stopped is None
    [result] = report.reviews
    assert (result.checkpoint, result.agent, result.outcome) == (checkpoint, "fake-a", "passed")
    score = result.score
    assert score is not None
    assert score.hits == (f"m1-C{checkpoint}-1",)
    assert score.misses == (f"m1-C{checkpoint}-2",)
    assert score.missed_blocking == 1
    assert [f.summary for f in score.unscored] == ["nobody saw this"]
    [job] = [j for j in _jobs(repo) if j["command"] == "bench"]
    assert (job["role"], job["agent"], job["ticket"], job["outcome"]) == (
        "bench",
        "fake-a",
        None,
        "passed",
    )
    assert queries.parse_review_note(job["note"]) == (1, 1, 1, 1)
    # the new finding is listed for the lead, never recorded as a finding
    conn = _metrics(repo)
    try:
        assert conn.execute("SELECT count(*) FROM findings").fetchone()[0] == 2
    finally:
        conn.close()
    [listed] = (repo / "var" / "bench").glob(f"*/checkpoint-{checkpoint}-fake-a/new-findings.json")
    assert "nobody saw this" in listed.read_text()
    assert _snapshot(repo) == before
    assert not list(copies.iterdir())


def test_a_review_replay_finds_a_merge_without_its_task_trailer(repo, copies, fake_agents):
    # f4-24: an escalation that implemented the ticket committed no `Task:` trailer; the
    # ticket's recorded commit stands in for it
    checkpoint = _checkpointed(repo, trailer=False)
    fake_agents["fake-a"].append(_answer(ANSWER))
    [result] = bench.run_review_bench(_config(repo, copies), ["m1"], ["fake-a"]).reviews
    assert (result.checkpoint, result.outcome) == (checkpoint, "passed")


def test_later_findings_on_the_tickets_are_known_but_rejected_ones_are_not(
    repo, copies, fake_agents
):
    checkpoint = _checkpointed(repo)
    conn = _metrics(repo)
    try:
        project = metrics.upsert_project(conn, repo.name)
        m1 = metrics.upsert_milestone(conn, project, "m1")
        ticket = metrics.upsert_ticket(conn, project, TICKET)
        run = metrics.upsert_run(conn, project, "review-20261001-100000", command="review")
        review = metrics.start_job(
            conn,
            run,
            ticket_id=None,
            milestone_id=m1,
            role="review",
            agent="claude-opus",
            attempt=1,
            started="2026-10-01T10:00:00+02:00",
        )
        metrics.finish_job(conn, review, ended="2026-10-01T10:30:00+02:00", outcome="passed")
        metrics.add_finding(
            conn,
            m1,
            "F1",
            job_id=review,
            ticket_id=ticket,
            severity="blocking",
            summary="nobody saw this",
        )
        # the review judged the checkpoint's first finding wrong
        metrics.add_finding(conn, m1, f"m1-C{checkpoint}-1", verdict="rejected")
    finally:
        conn.close()
    fake_agents["fake-a"].append(_answer(ANSWER))
    [result] = bench.run_review_bench(_config(repo, copies), ["m1"], ["fake-a"]).reviews
    assert result.score is not None
    assert result.score.hits == ("F1",)
    assert result.score.misses == (f"m1-C{checkpoint}-2",)
    assert [f.summary for f in result.score.unscored] == ["a constant"]


def test_a_review_bench_skips_the_agents_own_checkpoints(repo, copies, fake_agents):
    _checkpointed(repo)
    with pytest.raises(loop.RunnerError, match="no checkpoint of m1"):
        bench.run_review_bench(_config(repo, copies), ["m1"], ["claude-opus"])


def test_a_refused_review_replay_stops_the_bench(repo, copies, fake_agents):
    _checkpointed(repo)

    def refuse(work: Path, spec: JobSpec) -> JobResult:
        return JobResult(ok=False, text="quota", duration_s=0.5, refusal=Refusal("month", RESETS))

    fake_agents["fake-a"].append(refuse)
    fake_agents["fake-b"].append(_answer(ANSWER))
    report = bench.run_review_bench(_config(repo, copies), ["m1"], ["fake-a", "fake-b"])
    assert report.stopped is not None and "fake-a" in report.stopped
    assert [(r.agent, r.outcome, r.score) for r in report.reviews] == [("fake-a", "refused", None)]
    assert fake_agents["fake-b"]  # never ran
    [job] = [j for j in _jobs(repo) if j["command"] == "bench"]
    assert (job["outcome"], queries.parse_review_note(job["note"])) == ("refused", None)


def test_an_unusable_answer_fails_its_replay_and_the_bench_goes_on(repo, copies, fake_agents):
    _checkpointed(repo)
    fake_agents["fake-a"].append(_answer("no JSON here"))
    fake_agents["fake-b"].append(_answer(ANSWER))
    report = bench.run_review_bench(_config(repo, copies), ["m1"], ["fake-a", "fake-b"])
    assert [(r.agent, r.outcome) for r in report.reviews] == [
        ("fake-a", "failed"),
        ("fake-b", "passed"),
    ]


def test_unknown_tickets_and_agents_fail_before_anything_runs(repo, copies, fake_agents):
    _history(repo)
    with pytest.raises(loop.RunnerError, match="no-such-agent"):
        bench.run_bench(_config(repo, copies), [TICKET], ["no-such-agent"])
    with pytest.raises(loop.RunnerError, match="m1-99-none"):
        bench.run_bench(_config(repo, copies), ["m1-99-none"], ["fake-a"])
    assert not (repo / "var" / "factory-metrics.sqlite").exists()
