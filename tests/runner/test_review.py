import json

import pytest

from runner.review import (
    Finding,
    ReviewFileError,
    ReviewRound,
    parse_review,
    recurring_for_claude,
    stop_reason,
    update_seen,
)


def _round(*findings: Finding, stop=None) -> ReviewRound:
    return ReviewRound(findings=findings, stop=stop)


BLOCKING = Finding("m1-F1", "blocking", "local", "bug")
SHOULD = Finding("m1-F2", "should-fix", "claude", "edge case")
NIT = Finding("m1-F3", "nit", "backlog", "naming")


def test_parse_review(tmp_path):
    path = tmp_path / "r.json"
    path.write_text(
        json.dumps(
            {
                "findings": [
                    {"id": "m1-F1", "severity": "blocking", "route": "local", "summary": "bug"},
                ],
                "stop": None,
            }
        )
    )
    assert parse_review(path) == _round(BLOCKING)


@pytest.mark.parametrize(
    "payload",
    [
        {"findings": [{"id": "x", "severity": "meh", "route": "local"}]},
        {"findings": [], "stop": "bored"},
    ],
)
def test_parse_review_rejects_bad_values(tmp_path, payload):
    path = tmp_path / "r.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ReviewFileError):
        parse_review(path)


def test_nits_and_resolved_findings_never_loop():
    resolved = Finding("m1-F1", "blocking", "local", "bug", resolved=True)
    assert stop_reason(1, _round(NIT, resolved), None, {}, 3) == "clean"


def test_claude_can_stop_the_loop():
    assert stop_reason(1, _round(BLOCKING, stop="adr-needed"), None, {}, 3) == "adr-needed"


def test_findings_must_decrease():
    assert stop_reason(2, _round(BLOCKING, SHOULD), 2, {}, 3) == (
        "findings did not decrease (2 -> 2)"
    )
    assert stop_reason(2, _round(BLOCKING), 2, {}, 3) is None


def test_round_cap():
    assert stop_reason(3, _round(BLOCKING), 2, {}, 3) == "review round cap (3) reached"


def test_recurrence():
    seen = update_seen({}, _round(BLOCKING, NIT))
    assert seen == {"m1-F1": 1}
    seen = update_seen(seen, _round(BLOCKING))
    assert recurring_for_claude(seen) == ["m1-F1"]
    seen = update_seen(seen, _round(BLOCKING))
    assert stop_reason(3, _round(BLOCKING), 5, seen, 9) == "a finding came back a third time"
