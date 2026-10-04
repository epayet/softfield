"""``POST /requests`` (f5 D3, ADR 18 items 2 and 3): the dashboard's only write, a request row
for the runner, from the dashboard's own page only."""

import re

import pytest

from factory_dashboard.queries import connect
from runner import metrics
from tests.factory_dashboard.conftest import NOW, PROJECT

SAME = "http://127.0.0.1:8765"  # the test client's own origin
HTMX = {"HX-Request": "true", "Origin": SAME}
FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def _rows(db_path):
    conn = connect(db_path)
    try:
        return [dict(row) for row in conn.execute("SELECT * FROM owner_requests ORDER BY id")]
    finally:
        conn.close()


def _project_id(db_path, name):
    conn = connect(db_path)
    try:
        return conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()[0]
    finally:
        conn.close()


def _post(client, body, headers):
    return client.post("/requests", content=body, headers={**FORM, **headers})


def test_a_post_from_the_dashboards_page_writes_one_row_and_answers_asked(client, db_path):
    response = _post(client, "kind=signoff&subject=f1", HTMX)
    assert response.status_code == 200
    [row] = _rows(db_path)
    assert row == {
        "id": row["id"],
        "project_id": _project_id(db_path, PROJECT),
        "kind": "signoff",
        "subject": "f1",
        "value": None,
        "created": NOW.isoformat(),
        "done": None,
        "result": None,
    }
    assert "Asked: the runner will do it." in response.text
    # it asks for the request's status every 5 s, in its own place
    poll = re.search(r"<[^>]*hx-get=\"/requests/(\d+)\"[^>]*>", response.text)
    assert poll and int(poll[1]) == row["id"]
    assert 'hx-trigger="every 5s"' in poll[0] and 'hx-swap="outerHTML"' in poll[0]


def test_each_kind_keeps_its_subject_or_value(client, db_path):
    for body in ("kind=five_hour&value=yes", "kind=queue&subject=f5-09-queue-button"):
        assert _post(client, body, HTMX).status_code == 200
    assert [(r["kind"], r["subject"], r["value"]) for r in _rows(db_path)] == [
        ("five_hour", None, "yes"),
        ("queue", "f5-09-queue-button", None),
    ]


def test_a_referer_from_the_same_host_will_do_without_an_origin(client, db_path):
    headers = {"HX-Request": "true", "Referer": f"{SAME}/milestones/f1?project=coucou"}
    assert _post(client, "kind=signoff&subject=f1", headers).status_code == 200
    assert len(_rows(db_path)) == 1


def test_the_project_is_the_one_asked_for(client, db_path):
    assert (
        _post(client, "kind=queue&subject=m1-01-elsewhere&project=other", HTMX).status_code == 200
    )
    assert [r["project_id"] for r in _rows(db_path)] == [_project_id(db_path, "other")]


@pytest.mark.parametrize(
    "headers",
    [
        {},  # a plain form post from anywhere
        {"Origin": SAME},  # no htmx header
        {"HX-Request": "true"},  # neither Origin nor Referer
        {"HX-Request": "true", "Origin": "http://attacker.example"},
        {"HX-Request": "true", "Origin": "http://127.0.0.1:9999"},  # another port, another site
        {"HX-Request": "true", "Origin": "null"},  # a sandboxed frame or a file
        {"HX-Request": "true", "Referer": "http://attacker.example/page"},
        # Origin wins over a Referer that would pass
        {"HX-Request": "true", "Origin": "http://attacker.example", "Referer": f"{SAME}/"},
        {"HX-Request": "false", "Origin": SAME},
    ],
)
def test_a_post_not_from_the_dashboards_page_gets_403_and_writes_nothing(client, db_path, headers):
    response = _post(client, "kind=signoff&subject=f1", headers)
    assert response.status_code == 403
    assert _rows(db_path) == []


def test_a_refused_post_never_opens_the_database_for_writing(client, monkeypatch):
    from factory_dashboard import requests

    monkeypatch.setattr(requests, "writable", lambda request: pytest.fail("opened for writing"))
    assert _post(client, "kind=signoff&subject=f1", {"Origin": SAME}).status_code == 403


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ("kind=rm&subject=f1", 400),  # not a request the runner knows
        ("subject=f1", 400),
        ("kind=signoff&subject=f1&project=nowhere", 404),  # the dashboard makes no project
    ],
)
def test_a_request_the_runner_cant_take_writes_nothing(client, db_path, body, status):
    assert _post(client, body, HTMX).status_code == status
    assert _rows(db_path) == []
    conn = connect(db_path)
    try:
        assert (
            conn.execute("SELECT count(*) FROM projects WHERE name = 'nowhere'").fetchone()[0] == 0
        )
    finally:
        conn.close()


def test_the_status_shows_the_result_once_the_request_is_done_and_stops_polling(client, db_path):
    _post(client, "kind=signoff&subject=f1", HTMX)
    [row] = _rows(db_path)
    waiting = client.get(f"/requests/{row['id']}")
    assert waiting.status_code == 200
    assert "Asked: the runner will do it." in waiting.text
    assert f'hx-get="/requests/{row["id"]}"' in waiting.text

    conn = metrics.open_db(db_path)
    metrics.finish_request(conn, row["id"], NOW.isoformat(), "signed off <f1> & tagged")
    conn.close()
    done = client.get(f"/requests/{row['id']}")
    assert "signed off &lt;f1&gt; &amp; tagged" in done.text  # the runner's text, escaped
    assert "hx-get" not in done.text and "hx-trigger" not in done.text
    assert "Asked" not in done.text


def test_the_status_of_an_unknown_request_is_404(client):
    assert client.get("/requests/999").status_code == 404


def test_reading_a_status_writes_nothing_and_needs_no_guard(client, db_path):
    _post(client, "kind=five_hour&value=no", HTMX)
    before = _rows(db_path)
    assert client.get(f"/requests/{before[0]['id']}").status_code == 200
    assert _rows(db_path) == before
