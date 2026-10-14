import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from factory_dashboard.app import HOST, PORT
from factory_dashboard.queries import connect
from runner import cli, metrics
from runner.config import read_protected
from runner.gates import touching_protected
from runner.report import (
    DASHBOARD_URL,
    REPORT_END,
    REPORT_START,
    ClaudeRunRecord,
    SessionReport,
    TaskRecord,
    milestone_report,
    observations,
    render,
    with_report,
)
from runner.usage import ClaudeUsage
from tests.factory_dashboard.conftest import PROJECT, write_fixture
from tests.factory_dashboard.test_queries import write_sonnet_ticket

T0 = datetime(2026, 9, 27, 14, 0, tzinfo=UTC)


def _report() -> SessionReport:
    report = SessionReport(started=T0, ended=T0 + timedelta(minutes=30))
    report.tasks = [
        TaskRecord(
            "m1-01-a",
            "m1",
            "done",
            attempts=1,
            model_s=300,
            tokens_in=1_000_000,
            tokens_out=100_000,
            steps=40,
            warmup_s=35,
        ),
        TaskRecord(
            "m1-02-b", "m1", "escalated", attempts=3, gate_failures=["mypy", "mypy", "ruff"]
        ),
    ]
    report.claude_runs = [ClaudeRunRecord("escalation", "m1-02-b", 120, 5000, 800, 20000, True)]
    return report


def test_local_and_claude_tokens_are_compared():
    usage = ClaudeUsage(input=0, cache_write=100_000, cache_read=9_000_000, output=40_000, steps=30)
    text = render(_report(), usage)
    assert "processed **1.1M tokens** (1,000,000 in, 100,000 out) on 2 task(s)" in text
    # 125k writes + 900k reads + 200k output = 1.2M; reads are 73% of it
    assert "Claude spent **≈1.2M token-equivalents** over 30 steps (≈41k a step; 73%" in text


def test_a_session_report_is_a_summary_with_the_runs_dashboard_link():
    text = render(_report())
    assert "- **Tasks:** 2 attempted: 1 merged (`m1-01-a`), 1 not (`m1-02-b`: escalated)" in text
    assert "- **Headless Claude runs:** 1" in text
    # the run's folder is named after its start; its page has every task, job and gate
    assert f"{DASHBOARD_URL}/runs/20260927-140000" in text
    assert "`softfield dashboard`" in text
    assert "| Task |" not in text and "## Headless Claude runs" not in text
    assert f"http://{HOST}:{PORT}" == DASHBOARD_URL


def test_observations():
    obs = observations(_report())
    assert "First-attempt pass rate: 1/2." in obs
    assert "Most frequent gate failure: `mypy` (2x)." in obs
    assert any("25,000 tokens" in o for o in obs)
    assert any("cold for 1 task" in o for o in obs)


def test_empty_session():
    assert observations(SessionReport(started=T0)) == ["No tasks ran."]


def test_observations_point_the_review_at_widened_tasks_and_edited_tests():
    report = SessionReport(started=T0)
    report.tasks = [
        TaskRecord(
            "m4-01-a",
            "m4",
            "done",
            attempts=1,
            outside_files=["coucou/helper.py"],
            changed_tests=["tests/unit/test_a.py"],
        )
    ]
    obs = observations(report)
    assert "`m4-01-a` changed files outside `files:`: coucou/helper.py." in obs
    assert "`m4-01-a` edited existing tests (review these): tests/unit/test_a.py." in obs


# --- `runner report <key>`: a milestone review's numbers (f1-05, ADR 14 item 16) ----------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "metrics.sqlite"
    conn = metrics.open_db(path)
    write_fixture(conn)
    conn.close()
    return path


def _numbers(db_path: Path, key: str = "f1") -> str:
    conn = connect(db_path)
    try:
        return milestone_report(conn, PROJECT, key)
    finally:
        conn.close()


def test_the_report_pins_the_milestones_numbers(db_path):
    text = _numbers(db_path)
    assert text.startswith(REPORT_START + "\n") and text.endswith(REPORT_END + "\n")
    assert "| Tickets merged | 3 of 3 |" in text
    assert "| First-attempt pass rate | 1/2 (50%) |" in text
    assert "| Local attempts | 4 |" in text
    assert "| Escalations, directions, checkpoints | 1, 1, 1 |" in text
    assert "| Review rounds | 1 |" in text
    assert "| Findings | 1 blocking, 2 should-fix, 1 nit |" in text
    assert "| Local model | 525k tokens (500,000 in, 25,000 out) |" in text
    assert "| Claude | $7.80 (150k token-equivalents) |" in text


def test_the_report_shows_savings_in_dollars_with_tokens_underneath(db_path):
    text = _numbers(db_path)
    # doing it itself $1.50 (15k equivalents), supporting $4.20 (100k), net -$2.70
    assert "| **All** | 2 | 100 | $1.50 | $4.20 | **-$2.70** |" in text
    assert "| local-qwen3.6-35b-a3b | 2 | 100 | $1.50 | $4.20 | **-$2.70** |" in text
    assert "doing it itself ≈15k token-equivalents, supporting ≈100k" in text
    assert "| claude-opus | 4 | 120k | $7.50 |" in text


def test_the_report_credits_sonnets_lines_and_leaves_removed_tickets_out(db_path):
    write_sonnet_ticket(db_path)
    text = _numbers(db_path)
    assert "| Tickets merged | 4 of 4 |" in text
    # 60 lines at $3 per 200; its own $0.40 job and a fifth of the review and checkpoint
    assert "| claude-sonnet | 1 | 60 | $0.90 | $0.76 | **$0.14** |" in text


def test_the_report_has_the_trend_across_milestones(db_path):
    text = _numbers(db_path)
    trend = text[text.index("### Trends") :]
    assert trend.index("| m4 |") < trend.index("| f1 |")
    assert "| f1 | 3 | 1/2 (50%) | 4 | $7.80 | -$2.70 |" in trend


def test_the_report_replaces_only_the_text_between_the_markers():
    block = f"{REPORT_START}\nnew\n{REPORT_END}\n"
    doc = f"# Review\n\nBefore.\n\n{REPORT_START}\nold\nnumbers\n{REPORT_END}\n\nAfter.\n"
    assert with_report(doc, block) == f"# Review\n\nBefore.\n\n{block}\nAfter.\n"
    assert with_report(with_report(doc, block), block) == with_report(doc, block)


def test_the_report_goes_at_the_end_when_the_markers_are_missing():
    block = f"{REPORT_START}\nnew\n{REPORT_END}\n"
    assert with_report("# Review\n\nText.\n", block) == f"# Review\n\nText.\n\n{block}"
    assert with_report("", block) == block
    # a lone start marker isn't a block: nothing after it is lost
    lone = f"# Review\n{REPORT_START}\nkept\n"
    assert with_report(lone, block) == f"{lone}\n{block}"


@pytest.fixture
def in_repo(repo, monkeypatch, machine):
    toml = (cli._repo() / ".factory" / "project.toml").read_text()
    toml = re.sub(r'^name = ".*"\n', "", toml, count=1, flags=re.M)  # its folder's name
    (repo / ".factory" / "project.toml").write_text(toml)
    monkeypatch.chdir(repo)
    return repo


def test_runner_report_writes_the_review(in_repo, tmp_path, capsys):
    db = tmp_path / "metrics.sqlite"
    conn = metrics.open_db(db)
    write_fixture(conn)
    conn.execute("UPDATE projects SET name = ?", (in_repo.name,))
    conn.close()
    review = in_repo / ".factory" / "reviews" / "f1.md"
    review.parent.mkdir(parents=True)
    review.write_text(f"# F1 review\n\n{REPORT_START}\nstale\n{REPORT_END}\n\n## Findings\n")
    assert cli.main(["report", "f1", "--db", str(db)]) == 0
    text = review.read_text()
    assert text.startswith("# F1 review\n\n" + REPORT_START)
    assert "stale" not in text and "| Tickets merged | 3 of 3 |" in text
    assert text.endswith(f"{REPORT_END}\n\n## Findings\n")
    assert ".factory/reviews/f1.md" in capsys.readouterr().out


def test_the_reports_numbers_are_protected_and_the_queries_are_not():
    protected = read_protected(cli._repo())
    assert touching_protected(
        ["tests/runner/test_report.py", "factory_dashboard/queries.py", "runner/report.py"],
        protected,
    ) == ["runner/report.py", "tests/runner/test_report.py"]


def test_runner_report_refuses_an_unknown_milestone_or_database(in_repo, tmp_path, capsys):
    assert cli.main(["report", "f1", "--db", str(tmp_path / "none.sqlite")]) == 1
    db = tmp_path / "metrics.sqlite"
    metrics.open_db(db).close()
    assert cli.main(["report", "f1", "--db", str(db)]) == 1
    assert "no milestone f1" in capsys.readouterr().err
    assert not (in_repo / ".factory" / "reviews" / "f1.md").exists()
