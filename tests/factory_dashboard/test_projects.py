import json
import re
from html import unescape
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from factory_dashboard import stacks_routes
from factory_dashboard.projects import taken_names
from runner import config, metrics, stacks
from runner.requests import home_path
from runner.stacks import Result
from tests.factory_dashboard import test_stacks_routes
from tests.factory_dashboard.conftest import NOW, PROJECT
from tests.factory_dashboard.test_planning import _open as open_page
from tests.factory_dashboard.test_stacks_routes import (
    APP,
    HTMX,
    _crashed,
    _register,
    _repo,
    _running,
)
from tests.layout import DISPLAY, PHONE, layout_problems

# The app's fixtures: Docker replaced, and coaster-ranker registered with a `[run]`
docker = test_stacks_routes.docker
app_repo = test_stacks_routes.app_repo


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
    assert 'aria-current="page"><b>Projects</b>' in html  # lit in the sub menu (F194)
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
    assert layout_problems(page) == []


def test_send_lights_up_only_for_another_order_and_sends_the_names(page, projects_client, db_path):
    open_page(page, projects_client, "/projects")
    send = page.locator(".send-order")
    assert send.is_disabled()
    page.get_by_label(f"{PROJECT}'s place").fill("1")
    page.get_by_label("softfield's place").fill("2")
    assert send.is_enabled()
    send.click()
    # "On its way" shows only until /requests answers, which then replaces it: wait for the
    # answer, which stays (it raced the click and failed about one run in three)
    page.locator("#order-sent").get_by_text("Asked").wait_for()
    assert page.get_by_label("softfield's place").is_disabled()
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT value FROM owner_requests WHERE kind = 'project_order'")
        assert [json.loads(r[0]) for r in rows] == [[PROJECT, "softfield", "other"]]
    finally:
        conn.close()


# --- starting a project from the page (F122 D6, .softfield/cards/f122-mockup/projects-new.html) --


def _setting_up(db_path, tmp_path, name="ducks") -> int:
    """A project the runner registered from a `new_project` request: paused `setting up`."""
    (tmp_path / name).mkdir()
    conn = metrics.open_db(db_path)
    try:
        project_id = metrics.upsert_project(conn, name, repo=str(tmp_path / name))
        metrics.set_project_paused(conn, name, metrics.SETTING_UP)
        conn.commit()
    finally:
        conn.close()
    return project_id


def lit(row: str) -> list[str]:
    """The stations lit (``here``) in a plate's line of four."""
    return re.findall(r'<span class="st here">([^<]*)</span>', row)


def test_the_start_panel_asks_the_idea_name_built_with_and_app_and_says_where(
    projects_client, db_path
):
    html = projects_client.get("/projects").text
    start = re.search(r'<section id="projects-start".*?</section>', html, re.S)
    assert start, "no Start a project panel"
    panel = start.group(0)
    assert 'hx-post="/requests"' in panel
    assert '<input type="hidden" name="kind" value="new_project">' in panel
    assert f'<input type="hidden" name="project" value="{PROJECT}">' in panel
    assert '<textarea name="idea"' in panel
    assert '<input type="text" name="name"' in panel
    assert '<input type="text" name="built_with"' in panel
    assert '<input type="checkbox" name="app" checked>' in panel
    root = home_path(config.projects_root(db_path))  # `~/…` for a folder in the home
    assert f'data-root="{root}" data-taken="' in panel and f'">{root}/</span>' in panel
    assert home_path(Path.home() / "code" / "x") == "~/code/x"
    assert "A new project is set up on its computer" not in html


def test_a_waiting_new_project_draws_its_plate_on_its_way_until_the_runner_takes_it(
    projects_client, db_path
):
    idea = "Note the birds from the balcony, with the date and a photo."
    conn = metrics.open_db(db_path)
    try:
        project = metrics.find_project(conn, PROJECT)
        assert project is not None
        value = json.dumps({"name": "bird-log", "idea": idea, "built_with": "", "app": True})
        request = metrics.add_request(conn, project, "new_project", None, value, NOW.isoformat())
        conn.commit()
    finally:
        conn.close()
    html = projects_client.get("/projects").text
    match = re.search(r'<li class="proj-asked">(.*?)</li>', html, re.S)
    assert match, "no waiting plate"
    row = match.group(1)
    assert "way-plate" in row
    assert words(row) == (
        f"bird-log {idea} Asked Set up by the lead ADR 00 for you In the factory"
        " On its way: the runner makes its folder at its next pick"
    )
    assert lit(row) == ["Asked"]
    assert "<input" not in row  # no place to change
    assert html.index('<li class="proj-asked">') < html.index(
        '<li class="proj"'
    )  # before the first
    assert "bird-log" in section(html, "projects-order")
    conn = metrics.open_db(db_path)
    try:
        conn.execute("UPDATE owner_requests SET done = ? WHERE id = ?", (NOW.isoformat(), request))
        conn.commit()
    finally:
        conn.close()
    after = section(projects_client.get("/projects").text, "projects-order")
    assert "bird-log" not in after and "On its way" not in after


def test_a_project_set_up_by_the_lead_lights_that_station_and_links_to_m1(
    projects_client, db_path, tmp_path
):
    project_id = _setting_up(db_path, tmp_path)
    conn = metrics.open_db(db_path)
    try:
        metrics.queue_job(conn, project_id, "setup", "m1", "new project", NOW.isoformat())
        conn.commit()
    finally:
        conn.close()
    row = plate(projects_client.get("/projects").text, "ducks")
    assert lit(row) == ["Set up by the lead"]
    assert '<span class="st past">Asked</span>' in row
    assert 'href="/planning/m1?project=ducks">Answer on its first card →</a>' in row
    assert "/board?project=ducks" not in row and 'href="/?project=ducks"' not in row


def test_a_project_whose_adr_00_waits_lights_adr_00_for_you(
    projects_client, db_path, tmp_path, monkeypatch
):
    """After the setup job's reply its row is done, and M1's thread with ADR 00 waits on the
    desk (one item, as `test_a_crashed_app_and_desk_items_are_two_lines_counted_once` stands
    it in)."""
    from factory_dashboard import planning

    project_id = _setting_up(db_path, tmp_path)
    conn = metrics.open_db(db_path)
    try:
        job = metrics.queue_job(conn, project_id, "setup", "m1", "new project", NOW.isoformat())
        metrics.finish_queued(conn, job, NOW.isoformat())
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setattr(planning, "desk", lambda conn, name, now: ["m1"] if name == "ducks" else [])
    monkeypatch.setattr(planning, "waiting_for_you", lambda items: items)
    row = plate(projects_client.get("/projects").text, "ducks")
    assert lit(row) == ["ADR 00 for you"]
    past = re.findall(r'<span class="st past">([^<]*)</span>', row)
    assert past == ["Asked", "Set up by the lead"]
    assert 'href="/planning/m1?project=ducks"' in row


def _strip(html: str) -> str:
    match = re.search(r'<section id="setup-strip".*?</section>', html, re.S)
    return match.group(0) if match else ""


def test_a_project_being_set_up_says_so_on_its_other_pages_with_what_is_next(
    projects_client, db_path, tmp_path, monkeypatch
):
    """bug-67: Planning and M1's thread carry the plate's line at the top, the same station lit,
    and one line on what's next; the Projects page keeps it on the plate only."""
    from factory_dashboard import planning

    project_id = _setting_up(db_path, tmp_path)
    conn = metrics.open_db(db_path)
    try:
        job = metrics.queue_job(conn, project_id, "setup", "m1", "new project", NOW.isoformat())
        conn.commit()
    finally:
        conn.close()
    for path in ("/planning?project=ducks", "/planning/m1?project=ducks"):
        strip = _strip(projects_client.get(path).text)
        assert lit(strip) == ["Set up by the lead"], path
        assert "The lead is setting it up. Its answer comes on M1" in words(strip)
        assert 'href="/planning/m1?project=ducks"' in strip
    assert not _strip(projects_client.get("/projects").text)
    conn = metrics.open_db(db_path)
    try:
        metrics.finish_queued(conn, job, NOW.isoformat())
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setattr(planning, "desk", lambda conn, name, now: ["m1"] if name == "ducks" else [])
    monkeypatch.setattr(planning, "waiting_for_you", lambda items: items)
    strip = _strip(projects_client.get("/planning?project=ducks").text)
    assert lit(strip) == ["ADR 00 for you"]
    assert "Next: read ADR 00 on M1 and approve it. Then the lead plans M1" in words(strip)


def test_a_project_in_the_factory_has_no_setup_strip(projects_client):
    assert not _strip(projects_client.get("/planning?project=softfield").text)


def test_a_live_projects_plate_has_no_stations_and_keeps_board_and_overview(projects_client):
    row = plate(projects_client.get("/projects").text, "softfield")
    assert "stations" not in row and "Answer on its first card" not in row
    assert 'href="/board?project=softfield">Board</a>' in row
    assert 'href="/?project=softfield">Overview</a>' in row


def test_taken_names_are_the_roots_folders_the_live_projects_and_those_on_their_way(
    db_path, tmp_path
):
    """bug-68: what Start it refuses before it is pressed (`_free_folder` in runner/setup.py
    would quietly make ``name-2``)."""
    root = tmp_path / "root"
    (root / "old-thing").mkdir(parents=True)
    (root / ".hidden").mkdir()
    conn = metrics.open_db(db_path)
    try:
        project = metrics.find_project(conn, PROJECT)
        assert project is not None
        value = json.dumps({"name": "Bird Log", "idea": "Birds.", "built_with": "", "app": True})
        metrics.add_request(conn, project, "new_project", None, value, NOW.isoformat())
        taken = taken_names(conn, root)
    finally:
        conn.close()
    assert "old-thing" in taken and "bird-log" in taken
    assert PROJECT in taken
    assert ".hidden" not in taken and "Bird Log" not in taken


def test_start_it_is_off_for_a_name_whose_folder_exists_and_says_why(page, projects_client):
    """bug-68 (the owner, 2026-11-19): Start it makes new projects only. A name whose folder
    is taken (here a live project's) turns it off with a line, before it is pressed."""
    open_page(page, projects_client, "/projects")
    root = page.locator("#goes-in").get_attribute("data-root")
    start = page.get_by_role("button", name="Start it")
    warning = page.locator("#name-taken")
    page.get_by_label("The idea").fill("Another factory.")
    page.get_by_label("Name").fill("SoftField")
    assert page.locator("#goes-in").inner_text() == f"{root}/softfield"
    assert start.is_disabled()
    assert warning.inner_text() == (
        f"{root}/softfield already exists. Start it makes new projects only: pick another name."
    )
    page.get_by_label("Name").fill("softfield two")
    assert page.locator("#goes-in").inner_text() == f"{root}/softfield-two"
    assert start.is_enabled() and warning.is_hidden()


def test_start_it_sends_the_forms_json_and_shows_the_plate_at_once(page, projects_client, db_path):
    open_page(page, projects_client, "/projects")
    root = page.locator("#goes-in").get_attribute("data-root")
    page.get_by_label("The idea").fill("A tiny app for the birds on the balcony.")
    page.get_by_label("Name").fill("bird-log")
    assert page.locator("#goes-in").inner_text() == f"{root}/bird-log"
    page.get_by_role("button", name="Start it").click()
    plate_ = page.locator("#order-form .proj-asked")
    plate_.get_by_text("On its way: the runner makes its folder at its next pick").wait_for()
    assert plate_.count() == 1, "expected exactly one plate"
    assert plate_.locator(".name").inner_text() == "bird-log"
    assert page.get_by_label("The idea").is_disabled()
    page.locator("#start-sent").get_by_text("Asked").wait_for()
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT kind, value FROM owner_requests").fetchall()
    finally:
        conn.close()
    assert [(r[0], json.loads(r[1])) for r in rows] == [
        (
            "new_project",
            {
                "name": "bird-log",
                "idea": "A tiny app for the birds on the balcony.",
                "built_with": "",
                "app": True,
            },
        )
    ]


def test_the_start_form_htmx_listeners_guard_on_their_own_target(projects_client):
    """bug-68 (2026-11-19): the start form's htmx listeners must act only on the form's
    own request, so polling from the request partial inside #start-sent doesn't bubble up
    and append duplicate plates (the order form's listeners already have this guard)."""
    html = projects_client.get("/projects").text
    # Find the start form's script block (the second IIFE)
    start_script_match = re.search(r"// Start a project.*?\(\(\) => \{(.*?)\}\)\(\)", html, re.S)
    assert start_script_match, "no start project script"
    script = start_script_match.group(1)
    # Both listeners must carry the guard
    config_lines = re.findall(r'form\.addEventListener\("htmx:configRequest".*?\}\);', script, re.S)
    assert len(config_lines) >= 1
    assert "if (event.target !== form) return;" in config_lines[0]
    before_lines = re.findall(r'form\.addEventListener\("htmx:beforeRequest".*?\}\);', script, re.S)
    assert len(before_lines) >= 1
    assert "if (event.target !== form) return;" in before_lines[0]


# --- each plate's app (F239 D6, f239-05) -----------------------------------------------------


def plate(html: str, name: str) -> str:
    """The HTML of project ``name``'s plate on the Projects page."""
    key = re.escape(name)
    match = re.search(rf'<li class="proj"[^>]*data-key="{key}"[^>]*>(.*?)</li>', html, re.S)
    assert match, f"no plate for {name}"
    return match.group(1)


def words(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


def plant_of(html: str, button: str) -> dict[str, str]:
    """The ``hx-vals`` of the plant button whose text is ``button``, read as htmx reads it."""
    match = re.search(rf"hx-vals='([^']*)'[^>]*>{re.escape(button)}</button>", html)
    assert match, f"no button {button!r}"
    found: dict[str, str] = json.loads(match.group(1))
    return found


def test_a_running_app_shows_running_stop_open_and_logs(projects_client, docker, app_repo):
    docker.ps = _running()
    row = plate(projects_client.get("/projects").text, APP)
    assert "App Running" in words(row)
    assert f'hx-post="/projects/{APP}/stop"' in row
    assert f'hx-post="/projects/{APP}/run"' not in row
    # the page's host, the main service's published port, `[run]`'s path ("/" by default)
    assert '<a class="btn go" href="http://127.0.0.1:8123/" target="_blank" rel="noopener">' in row
    assert f'href="/projects/{APP}/logs">Logs</a>' in row
    assert "Plant a card" not in row


def test_open_follows_the_run_tables_path(projects_client, docker, app_repo):
    toml = app_repo / ".softfield" / "project.toml"
    toml.write_text(toml.read_text() + 'path = "/app/"\n', encoding="utf-8")
    docker.ps = _running()
    row = plate(projects_client.get("/projects").text, APP)
    assert 'href="http://127.0.0.1:8123/app/"' in row


def test_a_stopped_app_shows_stopped_and_run_without_open(projects_client, docker, app_repo):
    docker.ps = ""  # no containers
    row = plate(projects_client.get("/projects").text, APP)
    assert "App Stopped" in words(row)
    assert f'hx-post="/projects/{APP}/run"' in row
    assert f'hx-post="/projects/{APP}/stop"' not in row
    assert "Open" not in row
    assert "Plant a card" not in row


def test_a_crashed_app_shows_why_run_logs_and_a_fix_plant(projects_client, docker, app_repo):
    docker.ps = _crashed()
    row = plate(projects_client.get("/projects").text, APP)
    text = words(row)
    assert "App Crashed" in text
    assert f"{APP}-web-1: Exited (1) 3 minutes ago" in text  # `state`'s detail
    assert 'class="app-row broken"' in row
    assert f'hx-post="/projects/{APP}/run"' in row
    assert f'hx-post="/projects/{APP}/stop"' not in row
    assert "Open" not in row
    assert "Logs" in text
    plant = plant_of(row, "Plant a card to fix it")
    assert plant["kind"] == "plant" and plant["project"] == APP
    assert json.loads(plant["value"])["text"].startswith(f"{APP}'s app crashed")


@pytest.fixture
def crashed_project(projects_client, docker, app_repo, db_path, tmp_path, monkeypatch):
    """A project with a stack whose app is crashed."""
    _register(db_path, APP, app_repo)
    docker.ps = _crashed()
    return projects_client


def test_a_crashed_project_adds_its_line_to_needs_you(crashed_project):
    """A crashed project adds its line to the Needs you panel."""
    html = crashed_project.get("/projects").text
    needs_you = section(html, "projects-needs-you")
    assert "coaster-ranker" in needs_you
    assert "app crashed" in needs_you
    assert "Logs" in needs_you
    # The count includes both desk items and the crashed project.
    assert "in all" in needs_you


def test_a_crashed_app_and_desk_items_are_two_lines_counted_once(crashed_project, monkeypatch):
    """A project with desk items and a crashed app shows both lines, once each; the first draft
    drew its desk line twice and hid the crash."""
    from factory_dashboard import planning

    monkeypatch.setattr(planning, "desk", lambda conn, name, now: ["a", "b"] if name == APP else [])
    monkeypatch.setattr(planning, "waiting_for_you", lambda items: items)
    needs_you = section(crashed_project.get("/projects").text, "projects-needs-you")
    assert needs_you.count(f"{APP} 's app crashed") == 1  # `section` spaces out the link
    assert needs_you.count(f"{APP} · 2 items on the Planning desk") == 1
    assert "3 in all" in needs_you


def test_needs_you_shows_even_with_no_desk_items(crashed_project, db_path):
    """The Needs you panel shows when there are no items on any desk, only a crashed app."""
    conn = metrics.open_db(db_path)
    try:
        conn.execute("DELETE FROM owner_requests")
        conn.commit()
    finally:
        conn.close()
    html = crashed_project.get("/projects").text
    needs_you = section(html, "projects-needs-you")
    assert "coaster-ranker" in needs_you
    assert "app crashed" in needs_you


def test_running_or_stopped_adds_no_needs_you_line(projects_client, docker, app_repo, db_path):
    """A running or stopped project adds no line to Needs you."""
    _register(db_path, APP, app_repo)
    docker.ps = _running()
    html = projects_client.get("/projects").text
    needs_you = section(html, "projects-needs-you")
    assert "coaster-ranker" not in needs_you
    docker.ps = ""  # stopped
    html = projects_client.get("/projects").text
    needs_you = section(html, "projects-needs-you")
    assert "coaster-ranker" not in needs_you


@pytest.fixture
def update_failed(docker, monkeypatch):
    """`state` as it reads a failed update's result file (runner/stacks.py's tests cover that)."""
    tail = "Step 4/9 : RUN pip install\nERROR: no matching distribution for nope==9"
    failed = stacks.StackState(
        stacks.UPDATE_FAILED, 8123, "2026-11-12T14:02:00+00:00", tail, "a8c3fae1d2b4c5e6"
    )
    monkeypatch.setattr(stacks, "state", lambda stack: failed)
    docker.logs = "".join(f"web-1  | line {n}\n" for n in range(1, 31))
    return failed


def test_a_failed_update_shows_its_commit_and_the_fix_plant(
    projects_client, docker, app_repo, update_failed
):
    row = plate(projects_client.get("/projects").text, APP)
    text = words(row)
    assert "App Update failed" in text
    assert "ERROR: no matching distribution for nope==9 · main a8c3fae" in text
    assert "Step 4/9" not in text  # only the build output's last line on the row
    assert "Plant a card to fix it" in text


def test_the_fix_plant_holds_the_project_the_commit_and_the_last_30_log_lines(
    projects_client, docker, app_repo, update_failed, db_path
):
    plant = plant_of(plate(projects_client.get("/projects").text, APP), "Plant a card to fix it")
    value = json.loads(plant["value"])
    assert value["ask"] is False
    head, detail, logs = value["text"].split("\n\n")
    assert head == (
        f"{APP}'s app didn't update at 2026-11-12T14:02:00+00:00 on main a8c3fae1d2b4c5e6:"
        " find out why and fix it"
    )
    assert detail == update_failed.detail
    assert logs.splitlines()[0] == logs.splitlines()[-1] == "```"
    assert logs.splitlines()[1:-1] == [f"web-1  | line {n}" for n in range(1, 31)]
    assert next(c for c in docker.calls if "logs" in c)[-2:] == ["--tail", "30"]
    # posted as the button posts it, it is the Plant box's request
    response = projects_client.post("/requests", data=plant, headers=HTMX)
    assert response.status_code == 200
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT kind, value FROM owner_requests").fetchall()
    finally:
        conn.close()
    assert [(r[0], json.loads(r[1])) for r in rows] == [("plant", value)]


def test_a_project_without_run_offers_a_stack_plant_and_no_run(
    projects_client, docker, db_path, tmp_path
):
    _register(db_path, APP, _repo(tmp_path / "Coaster Ranker", run=False))
    row = plate(projects_client.get("/projects").text, APP)
    assert "No stack yet: the factory can't run it." in words(row)
    assert f'/projects/{APP}/run"' not in row and "Logs" not in row
    plant = plant_of(row, "Plant a card for a stack")
    assert plant["kind"] == "plant" and plant["project"] == APP
    assert json.loads(plant["value"]) == {
        "text": f"Give {APP} a Docker Compose stack the Projects page can run"
        " (ADR 46; what it needs: runner/instructions/run-stack.md)",
        "ask": False,
    }
    assert docker.calls == []  # no stack, no Docker


def test_a_plant_press_is_its_own_request_not_the_orders(page, projects_client, db_path, tmp_path):
    """The plate's buttons sit inside the order form: a plant sends a plant, says so, and leaves
    the places editable."""
    _register(db_path, APP, _repo(tmp_path / "Coaster Ranker", run=False))
    open_page(page, projects_client, "/projects")
    row = page.locator(f'.proj[data-key="{APP}"]')
    row.get_by_role("button", name="Plant a card for a stack").click()
    row.locator(".app-sent").get_by_text("Asked: the runner will do it.").wait_for()
    assert row.get_by_role("button", name="Plant a card for a stack").is_hidden()
    assert page.get_by_label("softfield's place").is_enabled()
    assert page.locator("#order-sent").inner_text() == ""
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT kind, value FROM owner_requests").fetchall()
    finally:
        conn.close()
    assert [(r[0], json.loads(r[1])["text"]) for r in rows] == [
        ("plant", stacks_routes.STACK_PLANT.format(name=APP))
    ]


def test_softfields_plate_has_neither_run_nor_a_plant(
    projects_client, docker, tmp_path, monkeypatch
):
    home = _repo(tmp_path / "softfield")  # Softfield's repo, with a `[run]` even
    monkeypatch.setattr(config, "HOME", home)
    row = plate(projects_client.get("/projects").text, "softfield")
    assert "app-row" not in row
    assert "Plant a card" not in row and '/projects/softfield/run"' not in row
    assert docker.calls == []


def test_docker_missing_shows_its_reason_and_the_page_still_draws(
    projects_client, docker, app_repo, monkeypatch
):
    def missing(args, cwd, env) -> Result:
        return Result(127, "", "docker is not installed on this machine")

    monkeypatch.setattr(stacks, "_docker", missing)
    response = projects_client.get("/projects")
    assert response.status_code == 200
    text = words(plate(response.text, APP))
    assert "App Docker isn't available docker is not installed on this machine" in text
    assert "Run" not in text and "Stop" not in text and "starting" not in text
    assert "Plant a card" not in text


# --- savings on the project page (f132-04) ---------------------------------------------------


def test_project_page_shows_savings_heading_with_project_name(project_client):
    """The heading reads "Savings from delegating on <project>, so far"."""
    html = project_client.get("/projects/coucou").text
    savings = section(html, "savings")
    assert "Savings from delegating on coucou, so far" in savings


def test_project_page_shows_savings_sums_over_all_delegated_tickets(project_client):
    """The sums cover all of the project's delegated tickets, not just one milestone."""
    html = project_client.get("/projects/coucou").text
    savings = section(html, "savings")
    # All milestones summed: 3 delegated tickets, net is negative
    assert "3 delegated tickets" in savings
    assert "-$4.13" in savings


def test_project_page_no_chart_in_savings_section(project_client):
    """The savings section has no chart, only the three figures."""
    html = project_client.get("/projects/coucou").text
    savings_section = re.search(r'<section[^>]*\bid="savings"[^>]*>(.*?)</section>', html, re.S)
    assert savings_section
    assert "data-chart" not in savings_section[1]


def test_project_with_no_delegated_tickets_says_so(db_path):
    """A project with no delegated tickets says the message."""
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
    savings = section(html, "savings")
    assert "No delegated tickets yet." in savings


def test_a_running_ticketless_review_names_the_card_on_projects_page(serve, db_path):
    """A running review on f158-… names the card: "review F158" with its title, the key
    linked to its planning page (F62 D1)."""
    from datetime import timedelta

    from factory_dashboard.app import create_app, get_now
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project_id = metrics.find_project(conn, PROJECT)
        assert project_id is not None
        m = metrics.upsert_milestone(
            conn,
            project_id,
            "f158-milestones-don-t-show-me-their",
            title="Milestones show their reviews",
        )
        run = metrics.upsert_run(
            conn,
            project_id,
            "20261002-120000",
            command="milestone f158",
            started=(NOW - timedelta(minutes=25)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=30)).isoformat(),
        )
        metrics.start_job(
            conn,
            run,
            ticket_id=None,
            milestone_id=m,
            role="review",
            agent="claude-opus",
            attempt=1,
            started=(NOW - timedelta(minutes=12)).isoformat(),
        )
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    html = client.get("/projects").text
    now_section = section(html, "projects-now")
    assert "review F158" in now_section
    assert "Milestones show their reviews" in now_section
    assert 'href="/planning/f158?project=' in html
    # The role "review" does not appear as bare text where the card name should be
    assert "review F158" in now_section
