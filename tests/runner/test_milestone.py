import pytest

from runner.milestone import footer_fields, milestone_metrics, milestone_summary
from runner.tasks import append_footer
from tests.runner.conftest import write_task


def test_footer_fields_reads_the_last_footer(tmp_path):
    path = write_task(tmp_path, "m1-01-a")
    append_footer(path, {"result": "escalated", "attempts": 3})
    append_footer(path, {"result": "done", "attempts": 1})
    assert footer_fields(path.read_text()) == {"result": "done", "attempts": "1"}


def test_milestone_metrics(repo):
    for folder, tid, attempts in [
        ("done", "m1-01-a", 1),
        ("done", "m1-02-b", 2),
        ("escalated", "m1-03-c", 3),
        ("done", "m2-01-d", 1),
    ]:
        path = write_task(repo / "tasks" / folder, tid)
        append_footer(path, {"attempts": attempts, "tokens": 1000 * attempts})
    append_footer(repo / "tasks" / "done" / "m1-02-b.md", {"attempts": 1, "tokens": 500})
    metrics = milestone_metrics(repo, "m1")
    assert (metrics.done, metrics.escalated, sorted(metrics.attempts)) == (2, 1, [1, 1, 3])
    assert metrics.tasks == ["a", "b"]
    assert metrics.local_tokens == 1000 + 2000 + 500 + 3000  # every footer, requeues included
    assert round(metrics.escalation_rate, 2) == 0.33


def test_milestone_summary_without_a_start_tag(repo):
    assert "there's no `m7-start` yet" in milestone_summary(repo, "m7")


def test_a_milestone_stops_for_a_restart_before_the_review(repo, monkeypatch):
    from runner import milestone
    from tests.runner.test_loop import _config

    monkeypatch.setattr(milestone, "work_queue", lambda s, milestone=None: True)
    monkeypatch.setattr(
        milestone, "review_milestone", lambda *a: pytest.fail("reviewed with stale code")
    )
    assert milestone.run_milestone(_config(repo), "m1", "HEAD") == milestone.RESTART


def test_a_factory_milestones_metrics_and_summary(repo):
    for tid in ("f1-01-a", "m1-01-b"):
        write_task(repo / "tasks" / "done", tid)
    assert milestone_metrics(repo, "f1").tasks == ["a"]
    assert "Who did the work in F1" in milestone_summary(repo, "f1")
    assert "there's no `f1-start` yet" in milestone_summary(repo, "f1")
