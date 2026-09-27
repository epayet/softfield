from runner.milestone import footer_fields, milestone_metrics
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
        append_footer(path, {"attempts": attempts})
    metrics = milestone_metrics(repo, 1)
    assert (metrics.done, metrics.escalated, sorted(metrics.attempts)) == (2, 1, [1, 2, 3])
    assert round(metrics.escalation_rate, 2) == 0.33
