import hashlib
import json
import os
import re
import sqlite3
from datetime import timedelta
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient

from factory_dashboard import app as app_module
from factory_dashboard.app import HOST, PORT, Db, ago, create_app
from factory_dashboard.queries import connect
from runner import cli, metrics
from tests.factory_dashboard.conftest import LOCAL, NOW, OPUS, OTHER, PROJECT, write_allowance
from tests.factory_dashboard.test_overview import REFRESH, lead_replies, open_overview
from tests.layout import DISPLAY, PHONE, layout_problems

STATIC = Path(app_module.__file__).parent / "static"
VENDOR = STATIC / "vendor"

TABS = [
    "/projects",  # every project, first (ADR 30 item 6)
    "/",
    "/planning",
    "/board",
    "/tickets",
    "/jobs",
    "/runs",
    "/timeline",
    "/agents",
    "/bench",
]
PAGES = [*TABS, "/milestones"]  # the list has no tab since the board (f5-17), and still answers


def test_the_app_refuses_to_write(db_path):
    app = create_app(db_path, PROJECT)

    @app.post("/try-to-write")
    def try_to_write(conn: Db) -> None:
        conn.execute("DELETE FROM jobs")

    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        TestClient(app, base_url="http://127.0.0.1").post("/try-to-write")
    conn = connect(db_path)
    assert conn.execute("SELECT count(*) FROM jobs").fetchone()[0] > 0
    conn.close()


def test_the_top_bar_has_a_tab_per_page_that_keeps_the_project(client):
    html = client.get(f"/?project={OTHER}").text
    tabs = re.findall(r'<nav class="tabs"[^>]*>(.*?)</nav>', html, re.S)[0]
    assert re.findall(r'href="([^"?]*)\?project=other"', tabs) == TABS
    assert 'href="/?project=other" aria-current="page"' in tabs
    # the filter lists every project, the one shown selected
    assert re.search(r'<option value="other" selected>', html)
    assert '<option value="coucou">' in html


def test_the_project_defaults_to_the_repos(client):
    html = client.get("/").text
    assert '<option value="coucou" selected>' in html
    assert re.search(r'<nav class="crumbs"[^>]*>.*coucou', html, re.S)


def test_the_page_loads_its_scripts_and_styles_from_the_app(client):
    html = client.get("/").text
    for path in (
        "/static/vendor/htmx.min.js",
        "/static/vendor/echarts.min.js",
        "/static/charts.js",
        "/static/dashboard.css",
    ):
        assert re.search(re.escape(path) + r"\?v=[0-9a-f]", html), f"{path} missing ?v="
        assert client.get(path).status_code == 200
    assert "https://" not in html  # vendored: no CDN


def test_no_page_or_stylesheet_names_a_third_party_host(client):
    """AGENTS.md rule 7: no CDN at run time, fonts included (f5-14)."""
    for path in [*PAGES, "/static/dashboard.css"]:
        text = client.get(path).text
        assert re.findall(r"(?:https?:)?//[a-z0-9.-]+\.[a-z]{2,}", text) == [], path
        assert "@import" not in text, path


def test_no_template_has_a_bare_static_link():
    """Every /static/ link in a template, the partials too, goes through ``static`` (F48 D4)."""
    bare = re.compile(r'/static/[^"\'>]')
    found = sorted((STATIC.parent / "templates").rglob("*.html"))
    assert len(found) > 5
    for template in found:
        html = template.read_text()
        assert bare.search(html) is None, f"{template.name} has a bare /static/ link"


def test_a_static_links_version_follows_the_files_content(tmp_path, monkeypatch, client):
    """F48 D4: the version is the content's hash, so a file rewritten while the server runs is
    a new URL and an unchanged one keeps its own; a path that isn't a file fails the render."""
    link = app_module.static("dashboard.css")
    assert re.fullmatch(r"/static/dashboard\.css\?v=[0-9a-f]{10}", link)
    assert client.get(link).content == (STATIC / "dashboard.css").read_bytes()
    monkeypatch.setattr(app_module, "HERE", tmp_path)
    monkeypatch.setattr(app_module, "_static_cache", {})
    (tmp_path / "static").mkdir()
    one, other = tmp_path / "static" / "one.css", tmp_path / "static" / "other.css"
    one.write_text("a")
    other.write_text("b")
    first = app_module.static("one.css")
    assert first == f"/static/one.css?v={hashlib.sha256(b'a').hexdigest()[:10]}"
    assert app_module.static("one.css") == first
    assert app_module.static("other.css").partition("?")[2] != first.partition("?")[2]
    one.write_text("changed")
    os.utime(one, (1, one.stat().st_mtime + 1))  # a later write, whatever the clock's grain
    assert app_module.static("one.css") == (
        f"/static/one.css?v={hashlib.sha256(b'changed').hexdigest()[:10]}"
    )
    with pytest.raises(FileNotFoundError):
        app_module.static("missing.css")


FONTS = {  # family -> the weights the mock-ups use (f5-14)
    "Chakra Petch": ("500", "600", "700"),
    "Barlow": ("400", "500", "600"),
    "JetBrains Mono": ("400", "600"),
}


def test_the_fonts_load_from_the_app(client):
    css = client.get("/static/dashboard.css").text
    faces = re.findall(r"@font-face\s*\{(.*?)\}", css, re.S)
    found: dict[tuple[str, str], str] = {}
    for face in faces:
        family = re.search(r'font-family:\s*"([^"]+)"', face)
        weight = re.search(r"font-weight:\s*(\d+)", face)
        url = re.search(r'src:\s*url\("([^"]+)"\)\s*format\("woff2"\)', face)
        assert family and weight and url, face
        assert "font-display: swap" in face
        found[family[1], weight[1]] = url[1]
    assert sorted(found) == sorted((f, w) for f, ws in FONTS.items() for w in ws)
    for path in found.values():
        assert path.startswith("/static/vendor/fonts/") and path.endswith(".woff2")
        response = client.get(path)
        assert response.status_code == 200 and response.content[:4] == b"wOF2"
    # each family in use: display, body, ids and numbers
    assert re.search(r'--display:\s*"Chakra Petch"', css)
    assert re.search(r'--body:\s*"Barlow"', css)
    assert re.search(r'--mono:\s*"JetBrains Mono"', css)


def test_every_vendored_file_is_recorded_with_its_sha256():
    """README.md's table pins each file (ADR 13); fonts carry their OFL licence beside them."""
    readme = (VENDOR / "README.md").read_text()
    recorded = dict(re.findall(r"^\| `([^`]+)` \|.*\| `([0-9a-f]{64})` \|$", readme, re.M))
    shipped = {
        p.relative_to(VENDOR).as_posix() for p in VENDOR.rglob("*") if p.suffix in {".js", ".woff2"}
    }
    actual = {name: hashlib.sha256((VENDOR / name).read_bytes()).hexdigest() for name in shipped}
    assert recorded == actual
    for family in ("chakra-petch", "barlow", "jetbrains-mono"):
        assert "SIL OPEN FONT LICENSE" in (VENDOR / "fonts" / f"{family}.LICENSE").read_text()


def _block(css: str, opener: str) -> dict[str, str]:
    """The custom properties in the block that starts with ``opener``."""
    start = css.index(opener)
    body = css[start : css.index("}", start)]
    return dict(re.findall(r"(--[\w-]+):\s*([^;]+);", body))


def _resolve(tokens: dict[str, str], name: str) -> str:
    value = tokens[name].strip()
    ref = re.fullmatch(r"var\((--[\w-]+)\)", value)
    return _resolve(tokens, ref[1]) if ref else value


def _luminance(hex_colour: str) -> float:
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast(a: str, b: str) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


MOCKUP = {  # .factory/cards/f1-factory-mockup.html's :root, and the board's area colours
    "--floor": "#12161b",
    "--bay": "#181e25",
    "--plate": "#1f2730",
    "--rule": "#303b47",
    "--hazard": "#f2b10a",
    "--fail": "#ec5458",
    "--clog": "#ec5458",
    "--opus": "#ff9640",
    "--sonnet": "#ffc48a",
    "--qwen": "#8ccf62",
    "--oss": "#4fd1a5",
    "--nemo": "#c3e06a",
    "--copilot": "#7aa7ff",
    "--factory": "#f2b10a",
    "--product": "#4fd1a5",
}


def test_dark_is_the_default_and_light_follows_the_system():
    css = (STATIC / "dashboard.css").read_text()
    dark = _block(css, ":root {")
    light = {**dark, **_block(css, "@media (prefers-color-scheme: light) { :root {")}
    assert "prefers-color-scheme: dark" not in css
    assert {name: _resolve(dark, name) for name in MOCKUP} == MOCKUP
    # light: a pale floor, the same hazard yellow and orange
    assert _luminance(_resolve(light, "--floor")) > 0.8
    assert _resolve(light, "--hazard") == "#f2b10a" and _resolve(light, "--opus") == "#ff9640"
    # the old names follow the new ones, so templates and charts.js keep working
    for old, new in {"--bg": "--floor", "--surface": "--bay", "--ink": "--fg"}.items():
        assert dark[old].strip() == f"var({new})"
    # ink reads at 4.5:1 or better on every plate, in both themes
    for theme in (dark, light):
        for ink in ("--ink", "--ink-2", "--muted"):
            for plate in ("--floor", "--bay", "--plate"):
                pair = (_resolve(theme, ink), _resolve(theme, plate))
                assert _contrast(*pair) >= 4.5, (ink, plate, pair)


def test_the_top_bar_has_the_mockups_title_hazard_stripe_and_tab_segment(client):
    html = client.get("/").text
    header = re.search(r'<header class="bar">(.*?)</header>', html, re.S)
    assert header
    assert '<span class="brand">' in header[1]
    assert '<div class="hazard"' in header[1]
    assert '<nav class="tabs" aria-label="Pages">' in header[1]
    css = (STATIC / "dashboard.css").read_text()
    assert re.search(r"\.brand \{[^}]*var\(--display\)[^}]*text-transform: uppercase", css)
    # the segment: the current tab is a hazard-yellow plate, as in the mock-up
    assert re.search(r'nav\.tabs a\[aria-current="page"\] \{[^}]*background: var\(--hazard\)', css)
    assert re.search(r"\.hazard \{[^}]*repeating-linear-gradient\(-45deg, var\(--hazard\)", css)


def test_phone_title_and_filter_share_one_line_at_390px(page, client):
    """f9-30: at 390 px the brand's box and the project select's box overlap vertically
    (same line) and the select sits to the right of the brand. This fails when .bar-top
    is not a grid on the phone (the CSS-regex lines that once checked this are gone)."""
    page.set_viewport_size({"width": 390, "height": 844})

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_selector(".brand", state="visible", timeout=REFRESH)
    brand, project = page.locator(".brand"), page.locator(".filters select")
    brand_box = brand.bounding_box()
    project_box = project.bounding_box()
    assert abs(brand_box["y"] - project_box["y"]) < 5, (
        f"title and filter not on same line: "
        f"title y={brand_box['y']:.1f}, select y={project_box['y']:.1f}"
    )
    assert project_box["x"] > brand_box["x"], (
        f"select not right of brand: brand x={brand_box['x']:.1f}, select x={project_box['x']:.1f}"
    )


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_phone_top_bar_is_compact_and_tabs_scroll(page, client, tmp_path, scheme):
    """f3-30: under 640 px the bar is short lines, tabs scroll sideways, current tab visible. The
    title, the factory's status (its dot and sign, f17) and the project share a line, and "Turn
    on notifications" takes one more while it shows."""
    page.emulate_media(color_scheme=scheme)
    page.set_viewport_size(PHONE)
    open_overview(page, client)
    page.evaluate("() => document.fonts.ready")
    header = page.locator("header.bar")
    height = header.evaluate("el => el.getBoundingClientRect().height")
    assert height <= 140, f"header {height}px > 140px"
    title, project = page.locator(".brand"), page.locator(".filters select")
    assert title.bounding_box()["y"] == pytest.approx(project.bounding_box()["y"], abs=8)
    assert title.bounding_box()["height"] < 30, "the title wraps"
    tabs = page.locator("nav.tabs")
    assert tabs.evaluate("el => el.scrollWidth > el.clientWidth"), "tabs not scrollable"
    # Each tab keeps its word's width: shrunk, they overlapped (the owner, 2026-10-06)
    squeezed = page.evaluate(
        """() => [...document.querySelectorAll('nav.tabs a')]
            .filter((a) => a.scrollWidth > a.clientWidth + 1).map((a) => a.textContent)"""
    )
    assert squeezed == [], f"tabs narrower than their words: {squeezed}"
    assert page.evaluate(
        "() => document.documentElement.clientWidth === document.documentElement.scrollWidth"
    ), "page scrolls sideways"
    active = page.locator("nav.tabs a[aria-current='page']")
    if active.count() > 0:
        active.evaluate("el => el.scrollIntoView({inline: 'center', block: 'nearest'})")
        page.wait_for_timeout(100)
        container_bcr = tabs.evaluate("el => el.getBoundingClientRect()")
        tab_bcr = active.evaluate("el => el.getBoundingClientRect()")
        assert tab_bcr["left"] >= container_bcr["left"] - 1
        assert tab_bcr["right"] <= container_bcr["right"] + 1
    page.screenshot(path=tmp_path / f"phone-top-bar-{scheme}.png", full_page=False)
    page.evaluate("() => document.querySelector('.replay')?.setAttribute('data-layout', 'overlay')")
    assert layout_problems(page) == []


def test_desktop_bar_unchanged_at_1440(client):
    """f3-30: at 1440 px the bar is as today (host visible, tabs fit without scrolling)."""
    html = client.get("/").text
    assert re.search(r'<span class="brand">.*?<small>', html, re.S), (
        "host address hidden on desktop"
    )
    assert re.search(r'<nav class="tabs"[^>]*>.*?href="/\?', html, re.S)
    assert re.search(r'href="/board\?', html)
    assert re.search(r'href="/tickets\?', html)
    assert re.search(r'href="/jobs\?', html)
    assert re.search(r'href="/runs\?', html)
    assert re.search(r'href="/timeline\?', html)
    assert re.search(r'href="/agents\?', html)
    assert re.search(r'href="/bench\?', html)


@pytest.mark.parametrize(
    ("scheme", "floor"), [("dark", "rgb(18, 22, 27)"), ("light", "rgb(236, 238, 233)")]
)
@pytest.mark.parametrize("size", [PHONE, DISPLAY], ids=["phone", "display"])
def test_the_overview_wears_the_factory_look_in_both_themes(
    page, client, tmp_path, scheme, floor, size
):
    """Dark unless the system asks for light, the fonts from the app, nothing overlapping.
    The screenshot lands in ``tmp_path`` (``--basetemp`` keeps it, for the job's notes)."""
    page.emulate_media(color_scheme=scheme)
    page.set_viewport_size(size)
    open_overview(page, client)
    page.evaluate("() => document.fonts.ready")
    assert page.evaluate("() => getComputedStyle(document.body).backgroundColor") == floor
    for face in ('700 22px "Chakra Petch"', '400 15px "Barlow"', '400 12px "JetBrains Mono"'):
        assert page.evaluate("f => document.fonts.check(f)", face), face
    page.screenshot(path=tmp_path / f"overview-{scheme}-{size['width']}.png", full_page=True)
    # on a phone the replay bar sticks to the bottom and floats over the page by design (f3-07)
    page.evaluate("() => document.querySelector('.replay')?.setAttribute('data-layout', 'overlay')")
    assert layout_problems(page) == []


def test_templates_use_the_tokens_never_raw_colours():
    """docs/agents/developer.md: a raw colour skips the light theme (f5-14)."""
    raw = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")
    for template in (STATIC.parent / "templates").rglob("*.html"):
        html = template.read_text()
        styles = re.findall(r'style="([^"]*)"', html) + re.findall(
            r"<style>(.*?)</style>", html, re.S
        )
        assert [s for s in styles if raw.search(s)] == [], template.name


def _meter_fills(client: TestClient) -> dict[str, str]:
    panel = re.search(
        r'<section[^>]*\bid="allowance"[^>]*>(.*?)</section>', client.get("/").text, re.S
    )
    assert panel
    # Read from meter span class (works at all sizes)
    return dict(
        re.findall(
            r'<div id="allow-([a-z_-]+)">.*?<div class="meter">\s*<span class="([a-z-]+)"',
            panel[1],
            re.S,
        )
    )


def test_an_allowance_meter_says_how_close_it_is(allowance_client):
    # 5-hour at 80% is past its 75% mark; the week at 20% and Copilot at 2% are under
    assert _meter_fills(allowance_client) == {
        "claude-five_hour": "past-mark",
        "claude-seven_day": "under-mark",
        "copilot-month": "under-mark",
    }
    panel = re.search(r'id="allowance".*?</section>', allowance_client.get("/").text, re.S)
    assert panel
    legend = " ".join(re.sub(r"<[^>]+>", " ", panel[0]).split())
    assert "green: under the mark" in legend
    assert "yellow: past the mark" in legend
    assert "red: above 95%" in legend
    css = (STATIC / "dashboard.css").read_text()
    assert re.search(r"\.meter > \.under-mark \{[^}]*var\(--good\)", css)
    assert re.search(r"\.meter > \.past-mark \{[^}]*var\(--hazard\)", css)
    assert re.search(r"\.meter > \.nearly-out \{[^}]*var\(--fail\)", css)


def test_an_allowance_meter_above_95_percent_is_red(db_path):
    conn = metrics.open_db(db_path)
    try:
        write_allowance(conn)
        conn.execute("DELETE FROM usage_events WHERE agent = 'copilot-auto'")
        metrics.add_usage_event(
            conn,
            "copilot-auto",
            NOW.isoformat(),
            "reading",
            window="month",
            value=0.96,
            resets_at=(NOW + timedelta(days=30)).isoformat(),
        )
        conn.execute("UPDATE usage_events SET value = 0.97 WHERE \"window\" = 'five_hour'")
        conn.commit()
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[app_module.get_now] = lambda: NOW
    fills = _meter_fills(TestClient(app, base_url="http://127.0.0.1:8765"))
    assert fills["claude-five_hour"] == fills["copilot-month"] == "nearly-out"


def test_only_a_loopback_host_is_served(client):
    # a page elsewhere that rebinds its own name to 127.0.0.1 can't read the dashboard
    assert client.get("/", headers={"Host": "attacker.example"}).status_code == 400
    assert client.get("/", headers={"Host": "localhost:8765"}).status_code == 200


def test_runner_dashboard_serves_on_loopback_only(db_path, monkeypatch, capsys):
    served: dict[str, object] = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **options: served.update(options, app=app))
    assert cli.main(["dashboard", "--db", str(db_path), "--port", "9000"]) == 0
    assert (served["host"], served["port"]) == ("127.0.0.1", 9000)
    assert "http://127.0.0.1:9000/" in capsys.readouterr().out
    assert cli.main(["dashboard", "--db", str(db_path)]) == 0
    assert (served["host"], served["port"]) == (HOST, PORT) == ("127.0.0.1", 8765)


def test_runner_dashboard_serves_on_a_lan_address_when_asked(db_path, monkeypatch, capsys):
    # the owner reads it from another machine (owner, 2026-10-01): that address, and no other name
    served: dict[str, object] = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **options: served.update(options, app=app))
    assert cli.main(["dashboard", "--db", str(db_path), "--host", "192.168.178.34"]) == 0
    assert served["host"] == "192.168.178.34"
    assert "http://192.168.178.34:8765/" in capsys.readouterr().out
    client = TestClient(create_app(db_path, PROJECT, "192.168.178.34"))
    assert client.get("/", headers={"Host": "192.168.178.34:8765"}).status_code == 200
    assert client.get("/", headers={"Host": "attacker.example"}).status_code == 400


def test_runner_dashboard_refuses_a_missing_database(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(uvicorn, "run", lambda *a, **k: pytest.fail("served"))
    assert cli.main(["dashboard", "--db", str(tmp_path / "none.sqlite")]) == 1
    assert "softfield backfill" in capsys.readouterr().err


def test_runner_dashboard_reloads_when_its_code_changes(db_path, monkeypatch):
    served: dict[str, object] = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **options: served.update(options, app=app))
    for name in ("DB", "PROJECT", "HOST"):  # serve sets these for the reloaded process
        monkeypatch.setenv(f"FACTORY_DASHBOARD_{name}", "")
    assert cli.main(["dashboard", "--db", str(db_path)]) == 0
    assert served["app"] == "factory_dashboard.app:from_env"
    assert served["factory"] is True and served["reload"] is True
    assert isinstance(app_module.from_env(), FastAPI)


def test_a_page_says_when_a_new_version_is_available(client, tmp_path, monkeypatch):
    html = client.get("/").text
    version = re.search(r"/version\?seen=(\w+)", html)
    assert version is not None
    assert "New version" not in client.get(f"/version?seen={version[1]}").text
    monkeypatch.setattr(app_module, "code_version", lambda: "changed")
    assert "New version" in client.get(f"/version?seen={version[1]}").text


# --- notifications (f5-12, ADR 18 item 4) ---------------------------------------------------


def _facts(html: str) -> tuple[dict[str, str], str]:
    """What ``notify.js`` compares: the open Needs-you items (id -> text), and "all done"."""
    tag = re.search(r'<div id="live-facts"[^>]*>', html)
    assert tag, "no #live-facts"
    needs = re.search(r"data-needs='([^']*)'", tag[0])
    done = re.search(r'data-all-done="(true|false)"', tag[0])
    assert needs and done, tag[0]
    return json.loads(unescape(needs[1])), done[1]


def _owner_item_ids(db_path: Path) -> dict[str, int]:
    conn = connect(db_path)
    try:
        rows = conn.execute("SELECT subject, id FROM owner_items").fetchall()
    finally:
        conn.close()
    return {row["subject"]: row["id"] for row in rows}


def test_the_live_partial_carries_the_open_items_and_whether_work_is_running(serve, db_path):
    needs, done = _facts(serve().get("/live").text)
    ids = _owner_item_ids(db_path)
    # only the open item: the resolved "ollama" one is not there
    assert needs == {f"owner-{ids['ADR 15']}": "Should reactions be editable once sent?"}
    assert done == "false"  # a job runs and two tickets wait


def test_what_the_dashboard_sees_itself_has_an_id_too(serve, db_path):
    needs, done = _facts(serve(heartbeat_age=timedelta(minutes=3)).get("/live").text)
    ids = _owner_item_ids(db_path)
    assert set(needs) == {f"owner-{ids['ADR 15']}", "runner-20261002-113500", "queue"}
    assert "heartbeat stopped 3 min ago" in needs["runner-20261002-113500"]
    assert needs["queue"] == "2 tickets waiting and the runner is idle."
    assert done == "false"  # a job stopped mid-way isn't done


def test_all_done_when_nothing_waits_or_runs(serve_between, db_path):
    client = serve_between(activity="check-all on main")
    assert _facts(client.get("/live").text) == ({}, "true")
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.queue_job(conn, project, "checkpoint", "f1", "A checkpoint", NOW.isoformat())
        conn.commit()
    finally:
        conn.close()
    assert _facts(client.get("/live").text) == ({}, "false")  # a queued job is work left


def test_a_ready_ticket_is_work_left(serve_between, db_path):
    client = serve_between(activity="check-all on main")
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(conn, project, "f1-20-next", milestone_id=f1, state="ready")
    finally:
        conn.close()
    assert _facts(client.get("/live").text) == ({}, "false")


def test_every_page_has_the_notify_bar_and_polls_live_whether_or_not_allowed(client):
    for path in PAGES:
        html = client.get(path).text
        assert re.search(r'<script src="/static/notify\.js\?v=[0-9a-f]+" defer></script>', html), (
            path
        )
        # no #notify-me button
        assert re.search(r'<button[^>]*id="notify-me"', html) is None, path
        # notification bar is present (hidden)
        assert re.search(r'<div id="notify-bar"[^>]*hidden', html), path
        # the top bar's status and Planning count refresh on every page (f6-16), so the poll no
        # longer waits for notifications; notify.js compares the facts only once they're on
        # the Overview has its own single poller (f19-02), not #live-poll
        if path != "/":
            poll = re.search(r'<div id="live-poll"[^>]*>', html)
            assert poll, path
            assert 'hx-get="/live?project=coucou"' in poll[0] and "hidden" in poll[0]
            assert 'hx-trigger="every 5s"' in poll[0]
            assert 'hx-select="#live-facts"' in poll[0]
    assert re.search(r"/static/notify\.js\?v=[0-9a-f]", html)
    assert client.get("/static/notify.js").status_code == 200
    assert client.get("/static/sw.js").status_code == 200


# A stand-in for the browser's Notification: it records what the page asks and shows.
FAKE_NOTIFICATION = """
window.shown = []; window.asked = 0;
class FakeNotification {
  constructor(title, options) { window.shown.push({ title, body: options && options.body }); }
}
FakeNotification.permission = "default";
FakeNotification.requestPermission = async () => {
  window.asked += 1; FakeNotification.permission = "granted"; return "granted";
};
window.Notification = FakeNotification;
"""


def test_the_page_notifies_once_per_new_item_and_once_when_all_is_done(
    page, serve_between, db_path
):
    page.add_init_script(FAKE_NOTIFICATION)
    open_overview(page, serve_between(activity="check-all on main"))
    bar = page.locator("#notify-bar")
    bar.wait_for(state="visible", timeout=REFRESH)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    page.wait_for_timeout(6_000)  # another poll: nothing asked, nothing shown before it's on
    assert page.evaluate("window.asked") == 0
    assert page.evaluate("window.shown") == []
    assert page.evaluate("localStorage.getItem('notify:coucou')") is None  # nothing compared
    page.locator('[data-action="yes"]').click()
    bar.wait_for(state="hidden", timeout=REFRESH)
    assert page.evaluate("window.asked") == 1
    page.wait_for_function("localStorage.getItem('notify:coucou') !== null", timeout=REFRESH)
    assert page.evaluate("window.shown") == []  # what was there before isn't news

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR 30",
            text="A question that came later.",
            created=NOW.isoformat(),
        )
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(conn, project, "f1-20-next", milestone_id=f1, state="ready")
    finally:
        conn.close()
    page.wait_for_function("window.shown.length > 0", timeout=REFRESH)
    page.wait_for_selector('#live-facts[data-all-done="false"]', state="attached", timeout=REFRESH)
    page.wait_for_timeout(6_000)  # the next poll sees the same item: no second notification
    shown = page.evaluate("window.shown")
    assert len(shown) == 1 and "A question that came later." in shown[0]["body"]

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(conn, project, "f1-20-next", milestone_id=f1, state="done")
    finally:
        conn.close()
    page.wait_for_function("window.shown.length > 1", timeout=REFRESH)
    page.wait_for_timeout(6_000)
    shown = page.evaluate("window.shown")
    assert len(shown) == 2 and "done" in shown[1]["title"].lower()


# --- service worker path (f12-05) ----------------------------------------------------------

FAKE_SERVICE_WORKER = """
window.sw_registered = null; window.sw_notifications = [];
Object.defineProperty(navigator, "serviceWorker", {
  value: {
    register: async (url) => {
      window.sw_registered = url;
      return {
        showNotification: async (title, options) => {
          window.sw_notifications.push({
            title, body: options && options.body,
            tag: options && options.tag
          });
        }
      };
    }
  },
  configurable: true,
  writable: true
});
"""

FAKE_SERVICE_WORKER_REJECTS = """
window.sw_registered = null; window.sw_notifications = [];
Object.defineProperty(navigator, "serviceWorker", {
  value: {
    register: async (url) => {
      window.sw_registered = url;
      return {
        showNotification: async (title, options) => {
          throw new Error("no");
        }
      };
    }
  },
  configurable: true,
  writable: true
});
"""


def test_notifications_go_through_service_worker_on_android(page, serve_between, db_path):
    """With a service worker registered the dashboard shows through it (the Android path).
    register is called once with /static/sw.js, the notification lands in the stand-in's list,
    and window.shown stays empty."""
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, serve_between(activity="check-all on main"))
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    # compare only runs when #live-facts is swapped (not on initial load),
    # so wait for the baseline to be established by the first poll
    page.wait_for_function("localStorage.getItem('notify:coucou') !== null", timeout=REFRESH)

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR 31",
            text="A follow-up question.",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)

    assert page.evaluate("window.sw_registered") == "/static/sw.js"
    assert page.evaluate("window.sw_notifications.length") == 1
    entry = page.evaluate("window.sw_notifications[0]")
    assert entry["title"] == "Needs you"
    assert entry["body"] == "A follow-up question."
    assert entry["tag"] and entry["tag"] != ""
    assert page.evaluate("window.shown") == []


def test_fallback_to_direct_notification_when_showNotification_rejects(
    page, serve_between, db_path
):
    """When showNotification rejects the item falls back to new Notification."""
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER_REJECTS)
    open_overview(page, serve_between(activity="check-all on main"))
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    page.wait_for_function("localStorage.getItem('notify:coucou') !== null", timeout=REFRESH)

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR 32",
            text="A fallback question.",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    page.wait_for_function("window.shown.length > 0", timeout=REFRESH)

    shown = page.evaluate("window.shown")
    assert len(shown) == 1 and "A fallback question." in shown[0]["body"]


# --- notification bar (f12-01, ADR 26 item 2) ----------------------------------------------

# A stand-in for the browser's Notification: it records what the page asks and shows.
FAKE_NOTIFICATION_GRANTED = """
window.shown = []; window.asked = 0;
class FakeNotification {
  constructor(title, options) { window.shown.push({ title, body: options && options.body }); }
}
FakeNotification.permission = "granted";
FakeNotification.requestPermission = async () => {
  window.asked += 1; FakeNotification.permission = "granted"; return "granted";
};
window.Notification = FakeNotification;
"""

FAKE_NOTIFICATION_DENIED = """
window.shown = []; window.asked = 0;
class FakeNotification {
  constructor(title, options) { window.shown.push({ title, body: options && options.body }); }
}
FakeNotification.permission = "denied";
FakeNotification.requestPermission = async () => {
  window.asked += 1; FakeNotification.permission = "denied"; return "denied";
};
window.Notification = FakeNotification;
"""


def test_notification_bar_shows_when_permission_is_default(page, client):
    """With permission 'default' and nothing stored, the bar shows."""
    page.add_init_script(FAKE_NOTIFICATION)
    page.set_viewport_size(DISPLAY)

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    bar = page.locator("#notify-bar")
    bar.wait_for(state="visible", timeout=REFRESH)
    assert page.evaluate("localStorage.getItem('notify:asked')") is None


def test_notification_bar_no_thanks_hides_it_and_stays_hidden(page, client):
    """No thanks hides the bar and it stays hidden after a reload."""
    page.add_init_script(FAKE_NOTIFICATION)
    page.set_viewport_size(DISPLAY)

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    bar = page.locator("#notify-bar")
    bar.wait_for(state="visible", timeout=REFRESH)
    page.locator('[data-action="no"]').click()
    bar.wait_for(state="hidden", timeout=REFRESH)
    assert page.evaluate("localStorage.getItem('notify:asked')") == "1"
    # reload: bar should stay hidden
    page.reload()
    bar.wait_for(state="hidden", timeout=REFRESH)


def test_notification_bar_yes_calls_request_permission_once(page, client):
    """Yes calls requestPermission once."""
    page.add_init_script(FAKE_NOTIFICATION)
    page.set_viewport_size(DISPLAY)

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    bar = page.locator("#notify-bar")
    bar.wait_for(state="visible", timeout=REFRESH)
    page.locator('[data-action="yes"]').click()
    assert page.evaluate("window.asked") == 1
    assert page.evaluate("localStorage.getItem('notify:asked')") == "1"
    bar.wait_for(state="hidden", timeout=REFRESH)


LAN = "http://192.168.1.20:8765"  # how the owner opens the dashboard: plain http, not trusted


def _open_at(page, client, origin: str) -> None:
    """The overview at ``origin``, answered by the test client."""

    def route(r) -> None:
        url = r.request.url.removeprefix(origin)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.set_viewport_size(DISPLAY)
    page.route(f"{origin}/**", route)
    page.goto(origin + "/")


def test_notification_bar_shows_steps_on_insecure_origin(page, client):
    """On the LAN address, with Chrome's own Notification (no stand-in: there it answers
    "denied", not "default"), the bar gives the steps with the page's address, and Got it
    hides them for good without answering the question (f12 review, F1 to F3)."""
    _open_at(page, client, LAN)
    assert page.evaluate("[window.isSecureContext, Notification.permission]") == [False, "denied"]
    bar = page.locator("#notify-bar")
    bar.wait_for(state="visible", timeout=REFRESH)
    body = bar.locator("[role=body]").text_content()
    assert "can't show notifications yet" in body
    assert "1. open chrome://flags/#unsafely-treat-insecure-origin-as-secure" in body
    assert f"2. paste this address in its box: {LAN}" in body
    assert "3. set it to Enabled and tap Relaunch" in body
    assert bar.locator(".copy-link").count() == 2
    # the question's buttons answer nothing here, so only Got it shows;
    # the two Copy buttons are also visible
    visible = bar.locator("button:visible").all_text_contents()
    assert visible.count("Got it") == 1
    assert visible.count("Copy") == 2
    page.locator('[data-action="got-it"]').click()
    bar.wait_for(state="hidden", timeout=REFRESH)
    assert page.evaluate("localStorage.getItem('notify:steps')") == "1"
    assert page.evaluate("localStorage.getItem('notify:asked')") is None
    page.reload()
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    assert bar.is_hidden()


FAKE_CLIPBOARD = """
window.clipboard_received = [];
window.navigator.clipboard = {
  writeText: async (text) => { window.clipboard_received.push(text); }
};
"""


def test_notification_bar_copy_buttons_are_buttons_and_say_copied(page, client):
    """On the LAN address the Copy controls are real buttons that say "Copied"
    after tapping (F6)."""
    page.add_init_script(FAKE_CLIPBOARD)
    _open_at(page, client, LAN)
    bar = page.locator("#notify-bar")
    bar.wait_for(state="visible", timeout=REFRESH)
    buttons = bar.locator("button.copy-link")
    assert buttons.count() == 2
    assert buttons.nth(0).text_content() == "Copy"
    assert buttons.nth(1).text_content() == "Copy"
    buttons.nth(0).click()
    page.wait_for_function(
        "document.querySelectorAll('button.copy-link')[0].textContent === 'Copied'", timeout=REFRESH
    )
    assert buttons.nth(0).text_content() == "Copied"
    assert buttons.nth(1).text_content() == "Copy"
    assert page.evaluate("window.clipboard_received") == [
        "chrome://flags/#unsafely-treat-insecure-origin-as-secure"
    ]
    buttons.nth(1).click()
    page.wait_for_function(
        "document.querySelectorAll('button.copy-link')[1].textContent === 'Copied'", timeout=REFRESH
    )
    assert buttons.nth(1).text_content() == "Copied"
    assert page.evaluate("window.clipboard_received") == [
        "chrome://flags/#unsafely-treat-insecure-origin-as-secure",
        LAN,
    ]


def test_notification_bar_asks_after_got_it_once_the_address_is_trusted(page, client):
    """Got it on the steps doesn't answer the question: on a secure address it is still asked."""
    page.add_init_script(FAKE_NOTIFICATION)
    page.add_init_script("localStorage.setItem('notify:steps', '1')")
    _open_at(page, client, ORIGIN)
    bar = page.locator("#notify-bar")
    bar.wait_for(state="visible", timeout=REFRESH)
    assert bar.locator("button:visible").all_text_contents() == ["Yes", "No thanks"]


def test_notification_bar_asks_again_when_the_browser_prompt_was_closed(page, client):
    """Yes, then Chrome's prompt closed without an answer: the bar goes, and comes back on the
    next page, since nothing else can turn notifications on."""
    page.add_init_script(
        FAKE_NOTIFICATION.replace(
            'FakeNotification.permission = "granted"; return "granted"', 'return "default"'
        )
    )
    _open_at(page, client, ORIGIN)
    bar = page.locator("#notify-bar")
    bar.wait_for(state="visible", timeout=REFRESH)
    page.locator('[data-action="yes"]').click()
    bar.wait_for(state="hidden", timeout=REFRESH)
    assert page.evaluate("[window.asked, Notification.permission]") == [1, "default"]
    assert page.evaluate("localStorage.getItem('notify:asked')") is None
    page.reload()
    bar.wait_for(state="visible", timeout=REFRESH)


def test_sw_finds_open_dashboard_tab_on_notification_tap():
    """sw.js uses includeUncontrolled so a tap focuses an open dashboard page."""
    sw = (STATIC / "sw.js").read_text()
    assert "includeUncontrolled" in sw
    assert "event.notification.close()" in sw  # Android keeps a tapped notification otherwise


def test_notification_bar_never_shows_when_permission_granted(page, client):
    """With permission 'granted' the bar never shows."""
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.set_viewport_size(DISPLAY)

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    bar = page.locator("#notify-bar")
    bar.wait_for(state="hidden", timeout=REFRESH)


def test_notification_bar_never_shows_when_permission_denied(page, client):
    """With permission 'denied' the bar never shows."""
    page.add_init_script(FAKE_NOTIFICATION_DENIED)
    page.set_viewport_size(DISPLAY)

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    bar = page.locator("#notify-bar")
    bar.wait_for(state="hidden", timeout=REFRESH)


# --- the top bar's status, its button and the Planning count (f6-16) -------------------------

ORIGIN = "http://127.0.0.1:8765"  # the test client's own origin
ASK = {"Content-Type": "application/x-www-form-urlencoded", "HX-Request": "true", "Origin": ORIGIN}


SIGNS = {"Pause after this job": "⏸", "Resume": "▶"}  # a sign's name for a screen reader


def _status(html: str) -> tuple[str, str, dict[str, str]]:
    """The top bar's status: its words, its dot, and its sign's name (``aria-label``) -> the
    request it posts. The dot's button names the same words; the sign shows only ⏸ or ▶."""
    block = re.search(r'<div id="factory-status"[^>]*>(.*?)</div>', html, re.S)
    assert block, "no #factory-status"
    words = re.search(r'<span class="words" role="status">([^<]*)</span>', block[1])
    assert words, block[1]
    dot = re.fullmatch(
        r'\s*<button type="button" class="dot-btn" aria-label="([^"]*)" title="\1">'
        r'<i class="dot (\w+)"></i></button>.*',
        block[1],
        re.S,
    )
    assert dot and dot[1] == words[1], block[1]
    buttons = {}
    for attrs, text in re.findall(
        r'<button type="button" class="sign"([^>]*)>([^<]*)</button>', block[1]
    ):
        assert 'hx-post="/requests"' in attrs, attrs
        kind = re.search(r'"kind": "(\w+)"', attrs)
        name = re.search(r'aria-label="([^"]*)"', attrs)
        assert kind and name, attrs
        assert text == SIGNS[name[1]], text
        buttons[name[1]] = kind[1]
    assert len(re.findall(r"<button", block[1])) == 1 + len(buttons), block[1]
    return words[1], dot[2], buttons


def _ask(client: TestClient, kind: str) -> None:
    assert client.post("/requests", content=f"kind={kind}", headers=ASK).status_code == 200


def _pause_held(db_path: Path) -> None:
    conn = metrics.open_db(db_path)
    try:
        metrics.add_usage_event(conn, "runner", "2026-10-02T11:40:00+00:00", "pause")
    finally:
        conn.close()


def _running(serve, serve_between, db_path):
    return serve()


def _idle(serve, serve_between, db_path):
    return serve_between(activity="picking the next ticket")


def _pause_asked(serve, serve_between, db_path):
    client = serve()
    _ask(client, "pause")
    return client


def _pause_held_client(serve, serve_between, db_path):
    client = serve()
    _pause_held(db_path)
    return client


def _resume_asked(serve, serve_between, db_path):
    client = _pause_held_client(serve, serve_between, db_path)
    _ask(client, "resume")
    return client


def _waiting(serve, serve_between, db_path):
    return serve_between(
        activity="waiting for Claude · f1-20-next until 12:40",
        waiting_until="2026-10-02T12:40:00+00:00",
    )


def _stopped(serve, serve_between, db_path):
    return serve(live=False)


def _idle_with_queue(serve, serve_between, db_path):
    client = serve_between(
        activity="Idle: 2 tickets wait for Claude's reserve · the week resets Mon 16:00",
    )
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        for ticket, goal in (("f1-20-idle", "Idle first."), ("f1-21-idle", "Idle second.")):
            metrics.upsert_ticket(
                conn, project, ticket, milestone_id=f1, kind="developer", state="ready", title=goal
            )
    finally:
        conn.close()
    return client


def _pause_held_planner(serve, serve_between, db_path):
    client = serve()
    _pause_held(db_path)
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        run = metrics.upsert_run(
            conn,
            project,
            "20261002-120000",
            command="milestone f1",
            started=(NOW - timedelta(minutes=25)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=30)).isoformat(),
        )
        metrics.upsert_ticket(
            conn,
            project,
            "f1-04-live",
            milestone_id=metrics.upsert_milestone(conn, project, "f1"),
            kind="developer",
            state="running",
            difficulty=5,
            title="Running now.",
        )
        job = metrics.start_job(
            conn,
            run,
            ticket_id=None,
            milestone_id=metrics.upsert_milestone(conn, project, "f1"),
            role="planner",
            agent=LOCAL,
            attempt=1,
            started=(NOW - timedelta(minutes=12)).isoformat(),
        )
        metrics.update_running_job(conn, job, tokens_in=42_000, steps=17)
    finally:
        conn.close()
    return client


def _lead_ticket(serve, serve_between, db_path):
    """A lead ticket, the only live job: on a run of its own beside a run between jobs."""
    client = serve_between(activity="picking the next ticket")
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        ticket = metrics.upsert_ticket(
            conn, project, "f1-30-lead", milestone_id=f1, kind="lead", state="running"
        )
        run = metrics.upsert_run(
            conn,
            project,
            "20261002-120000",
            command="milestone f1",
            started=(NOW - timedelta(minutes=25)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=30)).isoformat(),
        )
        metrics.start_job(
            conn,
            run,
            ticket_id=ticket,
            milestone_id=f1,
            role="lead-ticket",
            agent=OPUS,
            attempt=1,
            started=(NOW - timedelta(minutes=12)).isoformat(),
        )
    finally:
        conn.close()
    return client


PAUSE, RESUME = {"Pause after this job": "pause"}, {"Resume": "resume"}


@pytest.mark.parametrize(
    ("setup", "words", "dot", "buttons"),
    [
        # the fixture has more than one project: the status names whose run it is (ADR 30)
        (_running, "Running: coucou · f1-04-live", "developer", PAUSE),  # its only live job
        (_lead_ticket, "Running: f1-30-lead", "lead", PAUSE),  # its only live job
        (_idle, "Idle: nothing to do", "idle", PAUSE),  # this setup has one project
        (
            _idle_with_queue,
            "Idle: 2 tickets wait for Claude&#39;s reserve · the week resets Mon 16:00",
            "idle",
            PAUSE,
        ),
        # the job goes on: its dot stays until it ends
        (_pause_asked, "Pausing after f1-04-live · coucou", "developer", RESUME),
        (_pause_held_client, "Paused by you since 11:40 · coucou", "idle", RESUME),
        (
            _pause_held_planner,
            "Paused by you since 11:40 · the lead is answering you · coucou",
            "lead",  # only the planner runs while paused
            RESUME,
        ),
        (_resume_asked, "Resuming… · coucou", "idle", {}),  # on its way: nothing to press
        (_waiting, "Waiting for Claude until 12:40", "waiting", PAUSE),  # one project
        (_stopped, "Stopped", "stopped", {}),
    ],
    ids=[
        "running",
        "lead-ticket",
        "idle",
        "idle-with-queue",
        "pause-asked",
        "paused",
        "paused-planner",
        "resume-asked",
        "waiting",
        "stopped",
    ],
)
def test_the_top_bar_says_what_the_factory_does_with_pause_or_resume(
    serve, serve_between, db_path, setup, words, dot, buttons
):
    client = setup(serve, serve_between, db_path)
    for path in ("/", "/planning", "/tickets", "/live"):
        assert _status(client.get(path).text) == (words, dot, buttons), path
    # /live carries it out of band, for every page's poll to swap into its top bar
    assert re.search(
        r'<div id="factory-status"[^>]*hx-swap-oob="outerHTML"', client.get("/live").text
    )


def test_the_status_dot_wears_the_floors_colours_from_the_tokens(serve):
    css = (STATIC / "dashboard.css").read_text()

    def rule(selector: str) -> str:
        """The declarations of the top-level rule for exactly ``selector``."""
        found = re.search(rf"^{re.escape(selector)} \{{([^}}]*)\}}", css, re.M)
        assert found, selector
        return found[1]

    assert "background: var(--opus)" in rule(".factory-status .dot.lead")
    assert "background: var(--dev)" in rule(".factory-status .dot.developer")  # the floor's
    assert "background: var(--muted)" in rule(".factory-status .dot")
    assert "var(--opus)" in rule(".factory-status .dot.waiting, .factory-status .dot.stopped")
    assert "var(--muted)" in rule(".factory-status .dot.stopped")
    # only a running job breathes, and never under reduced motion
    breathing = re.findall(
        r"@media \(prefers-reduced-motion: no-preference\) \{\s*([^{]*)\{ animation: breathe", css
    )
    assert breathing == [".factory-status .dot.lead, .factory-status .dot.developer "]
    assert "rgba" not in rule(".factory-status .dot.lead") + rule(".factory-status .dot.developer")
    # what the owner asked shows on its way: a dashed orange edge (lead.md, 2026-10-07)
    assert "dashed var(--opus)" in rule("#factory-status.asked")
    assert '<div id="factory-status" class="factory-status asked"' in (
        _pause_asked(serve, None, None).get("/").text
    )


def _tab(html: str) -> str:
    tab = re.search(r'<a [^>]*id="planning-tab"[^>]*>([^<]*)</a>', html)
    assert tab, "no Planning tab"
    return tab[1]


def test_every_page_shows_the_planning_count_on_first_paint(serve, db_path):
    client = serve()
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        for key in ("f8", "f9"):  # two ideas no thread is about: two seeds on the desk
            metrics.upsert_milestone(conn, project, key, title=f"Idea {key}", state="idea")
    finally:
        conn.close()
    counted = _tab(client.get("/live").text)
    assert re.fullmatch(r"Planning · \d+", counted), counted
    # the Planning page itself too: the count went missing there (the owner, 2026-10-07)
    for path in ("/", "/planning", "/tickets", "/jobs"):
        assert _tab(client.get(path).text) == counted, path


def test_the_top_bar_refreshes_on_any_page_without_notifications(page, serve, db_path):
    client = serve()

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        if url.startswith("/static/"):
            r.fulfill(path=str(STATIC / url.split("?", 1)[0].removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/planning")
    tab = page.locator("#planning-tab")
    assert tab.text_content() == "Planning · 1"
    _pause_held(db_path)
    lead_replies(db_path, "f7")
    page.wait_for_function(
        "document.querySelector('#factory-status [role=status]').textContent"
        " === 'Paused by you since 11:40 · coucou'",
        timeout=REFRESH,
    )
    page.wait_for_function("document.querySelector('#planning-tab').textContent === 'Planning · 2'")
    assert tab.get_attribute("aria-current") == "page"  # still the page shown
    assert page.get_by_role("button", name="Resume", exact=True).text_content() == "▶"


def test_pause_in_the_top_bar_shows_pausing_at_once_and_posts_a_pause(page, serve, db_path):
    client = serve()
    posted: list[str] = []

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path == "/live":
            r.abort()  # no poll: only the click can change the bar
        elif path == "/requests":
            posted.append(r.request.post_data or "")
            answer = client.post("/requests", content=r.request.post_data, headers=ASK)
            r.fulfill(status=answer.status_code, body=answer.text, content_type="text/html")
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/tickets")
    words = page.locator("#factory-status [role=status]")
    assert words.text_content() == "Running: coucou · f1-04-live"
    page.get_by_role("button", name="Pause after this job", exact=True).click()
    page.wait_for_function(
        "document.querySelector('#factory-status [role=status]').textContent"
        " === 'Pausing after f1-04-live · coucou'"
        " && document.getElementById('factory-status').classList.contains('asked')",
        timeout=1_000,
    )
    edge = page.locator("#factory-status").evaluate("e => getComputedStyle(e).borderTopStyle")
    assert edge == "dashed"
    page.wait_for_function("document.querySelector('#factory-status .sign') === null")
    for _ in range(50):
        if posted:
            break
        page.wait_for_timeout(100)
    assert [parse_qs(body)["kind"] for body in posted] == [["pause"]]
    conn = connect(db_path)
    try:
        kinds = [row["kind"] for row in conn.execute("SELECT kind FROM owner_requests")]
    finally:
        conn.close()
    assert kinds == ["pause"]


def _bar(words: str, tone: str, button: str | None, dot: str) -> str:
    """A /live answer's top bar, drawn by the real partial."""
    status = app_module.Status(words, tone, button, dot=dot)
    partial = app_module.templates.get_template("_partials/bar_status.html")
    return partial.render(bar_status=status, project=PROJECT)


def test_pause_survives_a_stale_live_poll(page, serve, db_path):
    """A /live answer still showing Running and Pause leaves Pausing after this job and no button;
    a later /live with Pausing after this job and Resume is swapped in (f28-01 D1)."""
    client = serve()
    live_count = [0]
    posted = []
    # A stale /live fragment showing Running and Pause (kind: pause).
    stale_fragment = _bar("Running: f1-04-live", "good", "pause", "developer")
    # Fresh /live fragment showing Pausing and Resume.
    fresh_fragment = _bar("Pausing after this job", "warn asked", "resume", "developer")

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path == "/live":
            if live_count[0] == 0:
                r.fulfill(body=stale_fragment, content_type="text/html; charset=utf-8")
            else:
                r.fulfill(body=fresh_fragment, content_type="text/html; charset=utf-8")
            live_count[0] += 1
        elif path == "/requests":
            posted.append(r.request.post_data or "")
            answer = client.post("/requests", content=r.request.post_data, headers=ASK)
            r.fulfill(status=answer.status_code, body=answer.text, content_type="text/html")
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/tickets")
    words = page.locator("#factory-status [role=status]")
    assert words.text_content() == "Running: coucou · f1-04-live"
    page.get_by_role("button", name="Pause after this job", exact=True).click()
    page.wait_for_function(
        "document.querySelector('#factory-status [role=status]').textContent"
        " === 'Pausing after f1-04-live · coucou'",
        timeout=1_000,
    )
    page.wait_for_function("document.querySelector('#factory-status .sign') === null")
    for _ in range(50):
        if posted:
            break
        page.wait_for_timeout(100)
    assert [parse_qs(body)["kind"] for body in posted] == [["pause"]]

    # Wait for the fresh /live poll to arrive with Pausing and Resume.
    page.wait_for_function(
        "document.querySelector('#factory-status [role=status]').textContent"
        " === 'Pausing after this job'",
        timeout=REFRESH,
    )
    assert page.get_by_role("button", name="Resume", exact=True).text_content() == "▶"


def test_resume_survives_a_stale_live_poll(page, serve, db_path):
    """A stale Paused by you bar doesn't replace Resuming…; a fresh Running bar is swapped in
    (f28-01 D1)."""
    client = _pause_held_client(serve, serve_between=lambda **k: None, db_path=db_path)
    live_count = [0]
    posted = []
    # A stale /live fragment showing Paused by you and Resume (kind: resume).
    stale_fragment = _bar("Paused by you since 11:40", "warn", "resume", "idle")
    # Fresh /live fragment showing Running and Pause.
    fresh_fragment = _bar("Running: f1-04-live", "good", "pause", "developer")

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path == "/live":
            if live_count[0] == 0:
                r.fulfill(body=stale_fragment, content_type="text/html; charset=utf-8")
            else:
                r.fulfill(body=fresh_fragment, content_type="text/html; charset=utf-8")
            live_count[0] += 1
        elif path == "/requests":
            posted.append(r.request.post_data or "")
            answer = client.post("/requests", content=r.request.post_data, headers=ASK)
            r.fulfill(status=answer.status_code, body=answer.text, content_type="text/html")
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/tickets")
    words = page.locator("#factory-status [role=status]")
    assert words.text_content() == "Paused by you since 11:40 · coucou"
    page.get_by_role("button", name="Resume", exact=True).click()
    page.wait_for_function(
        "document.querySelector('#factory-status [role=status]').textContent === 'Resuming…'"
        " && document.getElementById('factory-status').classList.contains('asked')",
        timeout=1_000,
    )
    page.wait_for_function("document.querySelector('#factory-status .sign') === null")
    for _ in range(50):
        if posted:
            break
        page.wait_for_timeout(100)
    assert [parse_qs(body)["kind"] for body in posted] == [["resume"]]

    # Wait for the fresh /live poll to arrive with Running and Pause.
    page.wait_for_function(
        "document.querySelector('#factory-status [role=status]').textContent"
        " === 'Running: f1-04-live'",
        timeout=REFRESH,
    )
    pause = page.get_by_role("button", name="Pause after this job", exact=True)
    assert pause.text_content() == "⏸"


def test_refused_post_shows_error_and_restores_button(page, serve, db_path):
    """A refused post (500) shows Didn't reach the factory: try again, and the next /live
    puts the Pause button back (f28-01 D2)."""
    client = serve()
    live_count = [0]

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path == "/requests":
            r.fulfill(status=500, body="Internal Server Error")
        elif path == "/live":
            r.fulfill(
                body=client.get("/live").text,
                content_type="text/html; charset=utf-8",
            )
            live_count[0] += 1
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/tickets")
    words = page.locator("#factory-status [role=status]")
    assert words.text_content() == "Running: coucou · f1-04-live"
    page.get_by_role("button", name="Pause after this job", exact=True).click()
    # Wait for the error words first, with no dashed edge, then for the Pause sign to come back.
    page.wait_for_function(
        "document.querySelector('#factory-status [role=status]').textContent"
        ' === "Didn\'t reach the factory: try again"'
        " && !document.getElementById('factory-status').classList.contains('asked')",
        timeout=REFRESH,
    )
    page.wait_for_function(
        "document.querySelector('#factory-status .sign') !== null",
        timeout=REFRESH,
    )
    pause = page.get_by_role("button", name="Pause after this job", exact=True)
    assert pause.text_content() == "⏸"


def test_the_top_bar_says_what_the_factory_does_whichever_project_is_shown(serve):
    """The owner, 2026-10-14: picking a project is for planning and the board; the top bar
    says what the factory does, and its Pause goes to the project whose run it is."""
    html = serve().get("/planning?project=other").text
    assert _status(html) == ("Running: coucou · f1-04-live", "developer", PAUSE)
    assert '"kind": "pause", "project": "coucou"' in html


def _open_tickets(page, client: TestClient, size: dict[str, int]) -> None:
    page.set_viewport_size(size)

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/tickets")
    page.evaluate("() => document.fonts.ready")


def test_on_a_phone_the_dot_and_sign_join_the_brands_row_and_a_tap_shows_the_words(page, serve):
    """f17: at 390 px the brand, the dot, the sign and the project share one row (their middles
    agree: they differ in height), the dot and the sign are 44 px thumb targets, and the words
    show only once the dot is tapped, and stay through the next poll."""
    _open_tickets(page, serve(), PHONE)
    parts = {
        "brand": page.locator(".brand"),
        "dot": page.locator("#factory-status .dot-btn"),
        "sign": page.get_by_role("button", name="Pause after this job", exact=True),
        "project": page.locator(".filters select"),
    }
    boxes = {name: part.bounding_box() for name, part in parts.items()}
    middles = {name: box["y"] + box["height"] / 2 for name, box in boxes.items()}
    assert max(middles.values()) - min(middles.values()) <= 3, middles
    lefts = [boxes[name]["x"] for name in ("brand", "dot", "sign", "project")]
    assert lefts == sorted(lefts), boxes
    for name in ("dot", "sign"):
        assert (boxes[name]["width"], boxes[name]["height"]) == (44, 44), (name, boxes[name])
    words = page.locator("#factory-status [role=status]")
    assert not words.is_visible()
    parts["dot"].click()
    assert words.is_visible()
    assert words.text_content() == "Running: coucou · f1-04-live"
    assert layout_problems(page) == []  # on screen, over nothing it shouldn't cover
    # the next poll swaps the bar in again: the words stay
    page.evaluate("() => { window.shown = document.querySelector('#factory-status .words'); }")
    page.wait_for_function(
        "document.querySelector('#factory-status .words') !== window.shown", timeout=REFRESH
    )
    assert words.is_visible()
    parts["dot"].click()
    assert not words.is_visible()


def test_on_a_wide_screen_the_words_show_beside_the_dot(page, serve):
    """f17: from 640 px the words show beside the dot, on its row, the sign after them."""
    _open_tickets(page, serve(), {"width": 1024, "height": 768})
    dot = page.locator("#factory-status .dot-btn").bounding_box()
    words = page.locator("#factory-status [role=status]")
    assert words.is_visible()
    box = words.bounding_box()
    sign = page.get_by_role("button", name="Pause after this job", exact=True).bounding_box()
    assert dot["x"] + dot["width"] <= box["x"] <= dot["x"] + dot["width"] + 12, (dot, box)
    assert sign["x"] >= box["x"] + box["width"], (box, sign)
    middle = lambda b: b["y"] + b["height"] / 2  # noqa: E731
    assert abs(middle(dot) - middle(box)) <= 3 and abs(middle(sign) - middle(box)) <= 3


# --- ago (f94-02) --------------------------------------------------------------------------------


def test_ago_shows_days_from_48_hours_on():
    """F94: >= 48 h writes days with one decimal; < 48 h is unchanged."""
    assert ago(timedelta(hours=142.2)) == "5.9 days"
    assert ago(timedelta(hours=48)) == "2 days"
    assert ago(timedelta(hours=47)) == "47 h"
    assert ago(timedelta(minutes=58)) == "58 min"
    assert ago(timedelta(hours=120)) == "5 days"
    assert ago(timedelta(hours=48.1)) == "2 days"
    assert ago(timedelta(hours=0)) == "0 s"
