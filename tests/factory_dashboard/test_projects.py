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
    # Newest first by ``started``: F3 (12 h ago) before F2 (1 d ago) before
    # F1 (2 d ago). Each row has key, title and status.
    f3_pos = milestones.index("F3")
    f2_pos = milestones.index("F2")
    f1_pos = milestones.index("F1")
    assert f3_pos < f2_pos < f1_pos, "milestones not newest first"
    assert "F3" in milestones
    assert "The factory ships itself" in milestones
    assert "in progress" in milestones
    assert "F1" in milestones
    assert "The factory measures itself" in milestones
    assert "done" in milestones
    assert 'href="/milestones/f1?project=' in html
    assert 'href="/milestones/f2?project=' in html


def test_project_shows_runs(project_client):
    html = project_client.get("/projects/coucou").text
    runs = section(html, "runs")
    # Newest first: 20261001 before 20260930.
    r1_pos = runs.index("20261001-100000")
    r2_pos = runs.index("20260930-100000")
    assert r1_pos < r2_pos, "runs not newest first"
    assert 'href="/runs/20261001-100000?project=' in html
    assert 'href="/runs/20260930-100000?project=' in html


def test_project_page_title_and_breadcrumb_and_topbar(project_client):
    """The title, breadcrumb text/href and top-bar option show the project name."""
    html = project_client.get("/projects/coucou").text
    # Title: ``coucou · Project · software-factory``.
    assert "coucou · Project · software-factory" in html
    # Breadcrumb text and href.
    assert 'href="/projects/coucou?project=coucou">coucou</a>' in html
    # Selected top-bar project option.
    assert '<option value="coucou" selected>coucou</option>' in html


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


def test_project_with_more_than_10_runs_shows_only_10(db_path):
    """When a project has more than 10 runs, only the newest 10 are displayed."""
    from datetime import UTC, datetime

    from fastapi.testclient import TestClient

    from factory_dashboard.app import create_app, get_now
    from runner import metrics

    path = db_path
    conn = metrics.open_db(path)
    try:
        project_id = metrics.upsert_project(conn, "coucou")
        metrics.upsert_milestone(conn, project_id, "f1")
        for i in range(15):
            metrics.upsert_run(
                conn,
                project_id,
                f"202609{i + 1:02d}-100000",
                command="milestone f1",
            )
        conn.commit()
    finally:
        conn.close()

    app = create_app(path, "coucou")
    app.dependency_overrides[get_now] = lambda: datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    html = client.get("/projects/coucou").text
    runs = section(html, "runs")
    # Exactly 10 links in the runs section.
    run_links = re.findall(r'href="/runs/\d{8}-\d{6}\?project=', html)
    assert len(run_links) == 10, f"expected 10 run links, got {len(run_links)}"
    # The oldest run (20260901) must not appear.
    assert "20260901-100000" not in runs
    # The newest run (20260915) must appear.
    assert "20260915-100000" in runs


def test_unknown_project_is_404(project_client):
    resp = project_client.get("/projects/nonexistent")
    assert resp.status_code == 404


def test_project_crumb(project_client):
    """The project crumb area holds exactly one element for the project."""
    html = project_client.get("/projects/coucou").text
    crumbs = re.findall(r'<nav[^>]*class="crumbs"[^>]*>(.*?)</nav>', html, re.S)
    assert len(crumbs) == 1
    elements = re.findall(r"<(a|span)[^>]*>", crumbs[0])
    assert len(elements) == 1
