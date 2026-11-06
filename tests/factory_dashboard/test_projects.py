import json
import re

import pytest

from runner import metrics
from tests.factory_dashboard.conftest import NOW, PROJECT
from tests.factory_dashboard.test_planning import _open as open_page
from tests.layout import DISPLAY, PHONE, layout_problems


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
    # Title: ``coucou · Project · SoftField``.
    assert "coucou · Project · SoftField" in html
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


# --- the Projects page (ADR 30 item 6) ------------------------------------------------------


@pytest.fixture
def projects_client(serve, db_path, tmp_path):
    """The fixture's project, a second one first in the order with two ready tickets in its
    repo, and the fixture's live job running in the first."""
    repo = tmp_path / "softfield"
    (repo / ".softfield" / "tasks" / "ready").mkdir(parents=True)
    for name in ("f1-01-a.md", "f1-02-b.md"):
        (repo / ".softfield" / "tasks" / "ready" / name).write_text("x")
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, "softfield", repo=str(repo), description="The factory.")
        metrics.set_project_order(conn, ["softfield", PROJECT])
    finally:
        conn.close()
    return serve()


def test_the_projects_come_in_the_owners_order_with_what_waits_in_each(projects_client):
    html = projects_client.get("/projects").text
    order = section(html, "projects-order")
    assert order.index("softfield") < order.index(PROJECT)
    assert "The factory. 2 ready" in order
    assert 'href="/board?project=softfield"' in html
    assert 'aria-current="page">Projects' in html  # the first tab, lit
    assert "Send new order" in order and "On its way" not in order


def test_now_names_the_job_running_in_any_project(projects_client):
    now = section(projects_client.get("/projects").text, "projects-now")
    assert now.startswith(f"Now {PROJECT} ·")


def test_an_order_not_taken_yet_shows_as_sent_and_cant_be_edited(projects_client, db_path):
    """When a project_order waits, rows show the sent order and each reads "on its way · at the
    runner's next pick"; no input is disabled."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.find_project(conn, PROJECT)
        assert project is not None
        value = json.dumps([PROJECT, "softfield"])
        metrics.add_request(conn, project, "project_order", None, value, NOW.isoformat())
    finally:
        conn.close()
    html = projects_client.get("/projects").text
    order = section(html, "projects-order")
    assert order.index(PROJECT) < order.index("softfield")  # as sent
    assert "on its way · at the runner's next pick" in order
    rows = re.findall(r'<li class="proj"[^>]*data-key="([^"]*)"', html)
    assert set(rows) == {"coucou", "softfield", "other"}


def test_no_order_waiting_shows_no_on_its_way(projects_client):
    """Without a project_order waiting, no row says "on its way"."""
    html = projects_client.get("/projects").text
    order = section(html, "projects-order")
    assert "on its way" not in order


@pytest.mark.parametrize("size", [PHONE, DISPLAY], ids=["phone", "display"])
def test_the_projects_page_lays_out_at_phone_and_display_sizes(page, projects_client, size):
    page.set_viewport_size(size)
    open_page(page, projects_client, "/projects")
    page.evaluate("() => document.fonts.ready")
    page.evaluate("() => document.querySelector('nav.tabs').setAttribute('data-layout', 'overlay')")
    assert layout_problems(page) == []


def test_send_lights_up_only_for_another_order_and_sends_the_names(page, projects_client, db_path):
    open_page(page, projects_client, "/projects")
    send = page.locator(".send-order")
    assert send.is_disabled()
    page.get_by_label(f"{PROJECT}'s place").fill("1")
    page.get_by_label("softfield's place").fill("2")
    assert send.is_enabled()
    send.click()
    page.locator("#order-sent").get_by_text("On its way").wait_for()
    assert page.get_by_label("softfield's place").is_disabled()
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT value FROM owner_requests WHERE kind = 'project_order'")
        assert [json.loads(r[0]) for r in rows] == [[PROJECT, "softfield", "other"]]
    finally:
        conn.close()


def test_a_project_being_set_up_says_so(projects_client, db_path):
    """ADR 30: `softfield init` registers a project paused until `softfield doctor` passes."""
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, "ducks", repo="/r/ducks")
        metrics.set_project_paused(conn, "ducks", metrics.SETTING_UP)
    finally:
        conn.close()
    order = section(projects_client.get("/projects").text, "projects-order")
    assert "ducks Being set up on its computer; the runner takes it once that's done." in order
