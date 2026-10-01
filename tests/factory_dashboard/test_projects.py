import re


def section(html: str, name: str) -> str:
    """The text of the page's ``<section id="name">``, tags stripped."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html, re.S)
    assert match, f"no section {name}"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())


def test_project_page_answers_200(project_client):
    resp = project_client.get("/projects/coucou")
    assert resp.status_code == 200


def test_project_shows_description_and_repo(project_client):
    html = project_client.get("/projects/coucou").text
    about = section(html, "about")
    assert "A factory dashboard that measures itself." in about
    assert "https://github.com/example/coucou" in about


def test_project_shows_milestones_newest_first_with_status(project_client):
    html = project_client.get("/projects/coucou").text
    milestones = section(html, "milestones")
    # In-progress milestones sort before done ones, then by started DESC.
    # F2 (in progress) appears before F1 (done).
    f2_pos = milestones.index("F2")
    f1_pos = milestones.index("F1")
    assert f2_pos < f1_pos, "F2 should appear before F1"
    assert 'href="/milestones/f1?project=' in html
    assert 'href="/milestones/f2?project=' in html


def test_project_shows_runs(project_client):
    html = project_client.get("/projects/coucou").text
    assert 'href="/runs/20261001-100000?project=' in html
    assert 'href="/runs/20260930-100000?project=' in html


def test_project_with_no_milestones_says_so(db_path):
    """A project with no milestones yet says so."""
    from datetime import UTC, datetime

    from fastapi.testclient import TestClient

    from factory_dashboard.app import create_app, get_now
    from runner import metrics

    path = db_path
    conn = metrics.open_db(path)
    try:
        project_id = metrics.upsert_project(conn, "empty")
        metrics.upsert_run(conn, project_id, "20261001-000000")
    finally:
        conn.close()

    app = create_app(path, "empty")
    app.dependency_overrides[get_now] = lambda: datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    html = client.get("/projects/empty").text
    milestones = section(html, "milestones")
    assert "No milestones yet" in milestones


def test_unknown_project_is_404(project_client):
    resp = project_client.get("/projects/nonexistent")
    assert resp.status_code == 404
