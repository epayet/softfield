import json

import pytest

from runner.review import (
    Finding,
    ReviewFileError,
    ReviewRound,
    parse_checkpoint,
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


def test_a_review_with_locations_verdicts_and_a_score(tmp_path):
    """f1-23 (ADR 14 item 13): the last round judges the checkpoints and scores the milestone."""
    path = tmp_path / "r.json"
    finding = {
        "id": "m1-F1",
        "severity": "blocking",
        "route": "local",
        "summary": "bug",
        "file": "coucou/a.py",
        "line": 12,
        "detail": "It leaks.",
        "ticket": "m1-02-photos",
    }
    verdicts = {"m1-C7-1": "confirmed", "m1-C7-2": "rejected", "m1-F1": "missed"}
    path.write_text(
        json.dumps({"findings": [finding], "checkpoint_verdicts": verdicts, "score": 7})
    )
    round_ = parse_review(path)
    assert round_.findings == (
        Finding(
            "m1-F1",
            "blocking",
            "local",
            "bug",
            file="coucou/a.py",
            line=12,
            detail="It leaks.",
            ticket="m1-02-photos",
        ),
    )
    assert round_.checkpoint_verdicts == verdicts and round_.score == 7


def test_an_old_review_has_no_verdicts_or_score(tmp_path):
    path = tmp_path / "r.json"
    path.write_text(json.dumps({"findings": [{"id": "m1-F1", "severity": "nit"}], "stop": None}))
    round_ = parse_review(path)
    assert (round_.checkpoint_verdicts, round_.score) == ({}, None)
    assert (round_.findings[0].file, round_.findings[0].line) == ("", None)


@pytest.mark.parametrize(
    "extra",
    [
        {"score": 11},
        {"score": 0},
        {"score": True},
        {"score": "7"},
        {"checkpoint_verdicts": {"m1-C1-1": "maybe"}},
        {"checkpoint_verdicts": ["m1-C1-1"]},
        {"findings": [{"id": "x", "severity": "nit", "line": "twelve"}]},
    ],
)
def test_bad_verdicts_scores_and_lines_are_refused(tmp_path, extra):
    path = tmp_path / "r.json"
    path.write_text(json.dumps({"findings": [], **extra}))
    with pytest.raises(ReviewFileError):
        parse_review(path)


def test_a_checkpoints_findings_are_numbered_in_order(tmp_path):
    path = tmp_path / "checkpoint-3.json"
    raw = {"severity": "should-fix", "file": "a.py", "line": 3, "summary": "s", "detail": "d"}
    path.write_text(json.dumps({"findings": [raw, {**raw, "route": "local", "ticket": "m1-09"}]}))
    first, second = parse_checkpoint(path)
    assert (first.id, first.route, first.file, first.line, first.detail) == (
        "1",
        "report",
        "a.py",
        3,
        "d",
    )
    assert (second.id, second.route, second.ticket) == ("2", "local", "m1-09")


def test_a_checkpoint_finding_says_its_kind_of_fix(tmp_path):
    """f8-09: `test` when the code is right and its test weak; anything else is `code`."""
    path = tmp_path / "checkpoint-3.json"
    raw = {"severity": "should-fix", "summary": "s"}
    kinds = [{**raw, "kind": "test"}, {**raw, "kind": "code"}, raw, {**raw, "kind": "tests"}]
    path.write_text(json.dumps({"findings": kinds}))
    assert [f.kind for f in parse_checkpoint(path)] == ["test", "code", "code", "code"]


@pytest.mark.parametrize("text", ["not json", '{"findings": [{"severity": "meh"}]}', "[]"])
def test_a_malformed_checkpoint_file_is_an_error(tmp_path, text):
    path = tmp_path / "checkpoint-1.json"
    path.write_text(text)
    with pytest.raises(ReviewFileError):
        parse_checkpoint(path)


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
