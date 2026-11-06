import contextlib
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
from tests.factory_dashboard.test_planning import _open as open_planning_page
from tests.layout import DISPLAY, PHONE, layout_problems

STATIC = Path(app_module.__file__).parent / "static"
VENDOR = STATIC / "vendor"

_CDN_EXEMPTION = "http://www.w3.org/2000/svg"
_CDN_RE = re.compile(r"(?:https?:)?//[a-z0-9.-]+\.[a-z]{2,}(/[^\s\"'<>]*)?")


def _find_third_party_hosts(text: str) -> list[str]:
    """Return every URL-like host in *text* except the SVG namespace exemption."""
    return [m.group() for m in _CDN_RE.finditer(text) if m.group() != _CDN_EXEMPTION]


def _third_party_problems(text: str) -> list[str]:
    """Return every third-party host and ``@import`` found in *text*."""
    problems: list[str] = []
    for host in _find_third_party_hosts(text):
        problems.append(host)
    if "@import" in text:
        problems.append("@import")
    return problems


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


def test_the_picker_follows_the_owner_s_project_order(db_path):
    """F193 D1: the picker lists projects by the owner's order, not by name. A tie goes by
    name. After set_project_order changes the order, the next page shows the new one."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, "other")
        metrics.set_project_order(conn, ["other", "coucou"])
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    client = TestClient(app, base_url="http://127.0.0.1:8765")

    html = client.get("/").text
    select_match = re.search(r'<select[^>]*name="project"[^>]*>(.*?)</select>', html, re.S)
    assert select_match
    options = re.findall(r'<option value="([^"]+)"', select_match.group(1))
    assert options == ["other", "coucou"]


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
        assert _third_party_problems(text) == [], path


def test_a_page_that_names_cdn_example_com_after_the_top_bar_fails(client):
    """f69: a page that names https://cdn.example.com/x.js after the top bar makes the
    third-party host test fail (regression for the exact-namespace exemption)."""
    html = client.get("/").text
    header_close = html.lower().rfind("</header>")
    assert header_close != -1, "no </header> found"
    injected = (
        html[: header_close + len("</header>")]
        + "\n<script src='https://cdn.example.com/x.js'></script>"
        + html[header_close + len("</header>") :]
    )
    problems = _third_party_problems(injected)
    assert "https://cdn.example.com/x.js" in problems, (
        "expected https://cdn.example.com/x.js to be detected as third-party host"
    )


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


def _resolve_tokens(css: str, scheme: str) -> dict[str, str]:
    """Resolve the custom properties for *scheme* (``"dark"`` or ``"light"``)."""
    dark = _block(css, ":root {")
    if scheme == "dark":
        resolved: dict[str, str] = {}
        for k, _v in dark.items():
            resolved[k] = _resolve(dark, k)
        return resolved
    light_start = css.index(':root[data-theme="light"]')
    light_body_start = css.index("{", light_start) + 1
    light_body_end = css.index("}", light_body_start)
    light = dict(re.findall(r"(--[\w-]+):\s*([^;]+);", css[light_start:light_body_end]))
    merged = {**dark, **light}
    resolved = {}
    for k, _v in merged.items():
        resolved[k] = _resolve(merged, k)
    return resolved


def _hex_to_rgb(hex_colour: str) -> str:
    """Convert a hex colour like ``#f2b10a`` to ``rgb(242, 177, 10)``."""
    h = hex_colour.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgb({r}, {g}, {b})"


def _luminance(hex_colour: str) -> float:
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast(a: str, b: str) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


MOCKUP = {  # .softfield/cards/f1-factory-mockup.html's :root, and the board's area colours
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
    light = {**dark, **_block(css, ':root[data-theme="light"] {')}
    assert "prefers-color-scheme: dark" not in css
    assert "prefers-color-scheme: light" not in css
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
    assert '<a class="brand"' in header[1]
    assert '<div class="hazard"' in header[1]
    assert '<nav class="tabs" aria-label="Pages">' in header[1]
    css = (STATIC / "dashboard.css").read_text()
    assert re.search(r"\.brand \{[^}]*var\(--display\)[^}]*display: flex", css)
    # the segment: the current tab is a hazard-yellow plate, as in the mock-up
    assert re.search(r'nav\.tabs a\[aria-current="page"\] \{[^}]*background: var\(--hazard\)', css)
    assert re.search(r"\.hazard \{[^}]*repeating-linear-gradient\(-45deg, var\(--hazard\)", css)


def test_the_brand_shows_logo_and_softfield_name(client):
    """f68: the top bar shows the logo SVG and "SoftField" (Soft in warn-ink, Field in good)."""
    html = client.get("/").text
    assert re.search(r'<a class="brand"[^>]*href="/\?project=', html)
    assert re.search(r'<svg[^>]*aria-hidden="true"', html)
    assert re.search(r'class="brand-soft">Soft</span>', html)
    assert re.search(r'class="brand-field">Field</span>', html)
    assert "software-factory" not in html


def test_the_page_links_the_favicon(client):
    """f68: every page links softfield.svg as its icon, and /static/softfield.svg serves an SVG."""
    html = client.get("/").text
    assert re.search(r'<link rel="icon"[^>]*href="[^"]*softfield\.svg[^"]*"', html)
    resp = client.get("/static/softfield.svg")
    assert resp.status_code == 200
    assert b"<svg" in resp.content


def test_the_brand_link_keeps_the_chosen_project(client):
    """f68: clicking the brand goes to the Overview for the same project, from any page: a bare
    ``?project=`` would reload the page it is on (the review, f68-F1)."""
    for path in ("/planning", "/board", "/projects/other"):
        html = client.get(f"{path}?project=other").text
        brand = re.search(r'<a class="brand"[^>]*href="([^"]*)"', html)
        assert brand, path
        assert brand[1] == "/?project=other", path


def test_every_page_title_says_softfield_once(client):
    """f68: every page's title ends "· SoftField", once (the review, f68-F2: Projects and a
    project's page said it twice)."""
    for path in [*PAGES, f"/projects/{PROJECT}"]:
        title = re.search(r"<title>(.*?)</title>", client.get(path).text, re.S)
        assert title, path
        assert title[1].endswith(" · SoftField"), (path, title[1])
        assert title[1].count("SoftField") == 1, (path, title[1])


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_the_logo_follows_the_theme_tokens(page, client, scheme):
    """f68: the logo's sprout and crate use the theme's token colours."""
    css = (STATIC / "dashboard.css").read_text()
    tokens = _resolve_tokens(css, scheme)
    page.set_viewport_size(DISPLAY)
    page.emulate_media(color_scheme=scheme)

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    # The CSS now uses data-theme instead of prefers-color-scheme
    page.evaluate(f'document.documentElement.setAttribute("data-theme", "{scheme}")')
    svg = page.locator(".brand svg")
    assert svg.is_visible()
    crate = page.locator(".brand svg .crate")
    assert crate.is_visible()
    crate_fill = crate.evaluate("el => getComputedStyle(el).fill")
    assert crate_fill == _hex_to_rgb(tokens["--hazard"]), (
        f"crate fill {crate_fill} != --hazard {tokens['--hazard']} ({scheme})"
    )
    sprout = page.locator(".brand svg .sprout").first
    sprout_stroke = sprout.evaluate("el => getComputedStyle(el).getPropertyValue('stroke').trim()")
    assert sprout_stroke == _hex_to_rgb(tokens["--good"]), (
        f"sprout stroke {sprout_stroke} != --good {tokens['--good']} ({scheme})"
    )
    soft = page.locator(".brand-soft")
    soft_color = soft.evaluate("el => getComputedStyle(el).color")
    assert soft_color == _hex_to_rgb(tokens["--warn-ink"]), (
        f"Soft color {soft_color} != --warn-ink {tokens['--warn-ink']} ({scheme})"
    )


def test_the_logo_themes_differ(page, client):
    """f68: the dark and light themes render the logo with different colours."""
    page.set_viewport_size(DISPLAY)

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)

    page.emulate_media(color_scheme="dark")
    page.goto(ORIGIN + "/")
    page.evaluate("localStorage.removeItem('theme')")
    page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
    crate_dark = page.locator(".brand svg .crate").evaluate("el => getComputedStyle(el).fill")
    sprout_dark = page.locator(".brand svg .sprout").first.evaluate(
        "el => getComputedStyle(el).getPropertyValue('stroke').trim()"
    )
    soft_dark = page.locator(".brand-soft").evaluate("el => getComputedStyle(el).color")

    page.emulate_media(color_scheme="light")
    page.goto(ORIGIN + "/")
    page.evaluate("localStorage.removeItem('theme')")
    page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
    crate_light = page.locator(".brand svg .crate").evaluate("el => getComputedStyle(el).fill")
    sprout_light = page.locator(".brand svg .sprout").first.evaluate(
        "el => getComputedStyle(el).getPropertyValue('stroke').trim()"
    )
    soft_light = page.locator(".brand-soft").evaluate("el => getComputedStyle(el).color")

    assert crate_dark != crate_light or sprout_dark != sprout_light or soft_dark != soft_light, (
        "logo colours should differ between themes"
    )


def test_the_brand_link_is_at_least_44px_tall_at_390px(page, client):
    """f68: the brand link has a target of at least 44 px tall at 390 px."""
    page.set_viewport_size({"width": 390, "height": 844})

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_selector(".brand", state="visible", timeout=REFRESH)
    page.evaluate("() => document.fonts.ready")
    brand = page.locator(".brand")
    height = brand.evaluate("el => el.getBoundingClientRect().height")
    assert height >= 44, f"brand height {height}px < 44px at 390px viewport"


def test_phone_brand_logo_dot_sign_and_select_share_one_row(page, client):
    """f68: at 390 px the logo, the name, F17's dot and sign, and the project select
    still share one row, with no layout problems."""
    page.set_viewport_size({"width": 390, "height": 844})

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_selector(".brand", state="visible", timeout=REFRESH)
    page.evaluate("() => document.fonts.ready")
    assert layout_problems(page) == []


def test_desktop_brand_still_shows_host(client):
    """f68: on desktop the host address still shows beside the brand name."""
    html = client.get("/").text
    header = re.search(r'<header class="bar">(.*?)</header>', html, re.S)
    assert header
    assert re.search(r'<a class="brand"[^>]*>.*?<small>', header[1], re.S)


def test_phone_brand_name_does_not_wrap(page, client):
    """f68: on a phone the brand name does not wrap to a second line."""
    page.set_viewport_size(PHONE)

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_selector(".brand", state="visible", timeout=REFRESH)
    page.evaluate("() => document.fonts.ready")
    # a select is as wide as its longest name: the owner's list has longer ones than the fixture's
    page.evaluate(
        """() => document.querySelector('.filters select')
            .add(new Option('travel-companion', 'travel-companion'))"""
    )
    soft, field = page.locator(".brand-soft"), page.locator(".brand-field")
    soft_box, field_box = soft.bounding_box(), field.bounding_box()
    assert soft_box and field_box
    assert field_box["y"] == pytest.approx(soft_box["y"], abs=2), "Field wrapped below Soft"
    assert field_box["x"] > soft_box["x"]
    # squeezed by the row, the name was cut to "SoftFi" (the review, f68-F3)
    brand = page.locator(".brand").bounding_box()
    assert brand
    assert field_box["x"] + field_box["width"] <= brand["x"] + brand["width"] + 1
    assert brand["height"] >= 44
    assert layout_problems(page) == []


def test_no_page_shows_software_factory(client):
    """f68: no page shows "software-factory" in the owner-facing HTML."""
    for path in PAGES:
        html = client.get(path).text
        assert "software-factory" not in html, f"{path} still shows software-factory"


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
    assert abs(brand_box["y"] - project_box["y"]) < 15, (
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
    assert height <= 150, f"header {height}px > 150px"
    title, project = page.locator(".brand"), page.locator(".filters select")
    assert title.bounding_box()["y"] == pytest.approx(project.bounding_box()["y"], abs=15)
    assert title.bounding_box()["height"] >= 44, "the title should be at least 44px tall"
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


def test_phone_theme_switch_plate_is_40px_tall(page, client):
    """f69-08: the phone-specific knob sizing requires a .phone ancestor, but the app
    does not add that class at mobile widths; the overrides must apply directly."""
    page.set_viewport_size(PHONE)
    page.emulate_media(color_scheme="dark", reduced_motion="reduce")

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_selector(".theme-switch", state="visible", timeout=REFRESH)
    page.evaluate("() => document.fonts.ready")
    plate = page.locator(".theme-switch .plate")
    height = plate.evaluate("el => el.getBoundingClientRect().height")
    assert height == 40, f"plate height {height}px != 40px at 390px viewport"
    knob = page.locator(".theme-switch .knob")
    knob_height = knob.evaluate("el => el.getBoundingClientRect().height")
    assert knob_height == 17, f"knob height {knob_height}px != 17px at 390px viewport"
    # The knob position when aria-checked="false" mirrors the aria-checked="true" position
    plate_bcr = plate.evaluate("el => el.getBoundingClientRect()")
    knob_bcr = knob.evaluate("el => el.getBoundingClientRect()")
    gap_top = knob_bcr["top"] - plate_bcr["top"]
    page.evaluate("document.getElementById('theme-btn').click()")
    assert page.locator("#theme-btn").evaluate("el => el.getAttribute('aria-checked')") == "false"
    knob_bcr = knob.evaluate("el => el.getBoundingClientRect()")
    plate_bcr = plate.evaluate("el => el.getBoundingClientRect()")
    gap_bottom = plate_bcr["bottom"] - knob_bcr["bottom"]
    assert gap_bottom == pytest.approx(gap_top, abs=1), (
        f"knob gap bottom {gap_bottom} != gap top {gap_top}"
    )


def test_phone_top_bar_steps_aside_on_scroll(page, client, tmp_path):
    """f42-02: on a phone the top bar slides away when scrolling down
    and comes back on scroll up."""
    page.set_viewport_size(PHONE)
    open_overview(page, client)
    page.evaluate("() => document.fonts.ready")
    page.evaluate("() => document.body.style.minHeight = '3000px'")
    bar = page.locator("header.bar")

    # At the top of the page the bar is in view
    assert bar.evaluate("el => el.getBoundingClientRect().top") == pytest.approx(0, abs=2)

    # Scroll down 400 px: bar should be out of view
    page.evaluate("() => window.scrollTo(0, 400)")
    page.wait_for_function(
        "() => document.querySelector('header.bar').getBoundingClientRect().bottom <= 0"
    )
    bcr = bar.evaluate("el => el.getBoundingClientRect()")
    assert bcr["bottom"] <= 0, f"bar still visible at bottom={bcr['bottom']:.1f}"

    # Scroll up 50 px: bar should be fully in view at the top
    page.evaluate("() => window.scrollTo(0, 350)")
    page.wait_for_function(
        "() => document.querySelector('header.bar').getBoundingClientRect().top >= 0"
    )
    bcr = bar.evaluate("el => el.getBoundingClientRect()")
    assert bcr["top"] == pytest.approx(0, abs=2), f"bar not at top: top={bcr['top']:.1f}"

    # A jitter of 5 px down leaves it in view; small steps that add up past 8 px hide it (review)
    page.evaluate("() => window.scrollTo(0, 355)")
    page.wait_for_timeout(300)
    assert bar.evaluate("el => el.getBoundingClientRect().top") == pytest.approx(0, abs=2)
    for y in (360, 365):
        page.evaluate(f"() => window.scrollTo(0, {y})")
        page.wait_for_timeout(50)
    page.wait_for_function(
        "() => document.querySelector('header.bar').getBoundingClientRect().bottom <= 0"
    )
    page.evaluate("() => window.scrollTo(0, 350)")
    page.wait_for_function(
        "() => document.querySelector('header.bar').getBoundingClientRect().top >= -2"
    )

    # Back at the top, bar is in view
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_function(
        "() => document.querySelector('header.bar').getBoundingClientRect().top >= 0"
    )
    assert bar.evaluate("el => el.getBoundingClientRect().top") == pytest.approx(0, abs=2)

    # At 1024 px scrolling down leaves the bar in view
    page.set_viewport_size(DISPLAY)
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(100)
    assert bar.evaluate("el => el.getBoundingClientRect().top") == pytest.approx(0, abs=2)
    page.evaluate("() => window.scrollTo(0, 400)")
    page.wait_for_timeout(200)
    bcr = bar.evaluate("el => el.getBoundingClientRect()")
    assert bcr["top"] == pytest.approx(0, abs=2), f"bar moved at desktop: top={bcr['top']:.1f}"


def test_desktop_bar_unchanged_at_1440(client):
    """f3-30: at 1440 px the bar is as today (host visible, tabs fit without scrolling)."""
    html = client.get("/").text
    assert re.search(r'<a class="brand".*?<small>', html, re.S), "host address hidden on desktop"
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
    # Clear any stored theme so the page follows the system preference
    with contextlib.suppress(Exception):
        page.evaluate("localStorage.removeItem('theme')")
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
    """.softfield/developer.md: a raw colour skips the light theme (f5-14)."""
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
    assert client.get(f"/version?seen={version[1]}").text == app_module.VERSION_POLL.format(
        version=version[1]
    )
    monkeypatch.setattr(app_module, "code_version", lambda: "changed")
    tag = client.get(f"/version?seen={version[1]}").text
    # a link to the page itself (href=""), the words, and nothing of the old bar
    assert re.fullmatch(r'<a class="version-tag" href="" role="status"[^>]*>.*New version</a>', tag)
    assert "hx-get" not in tag


def test_the_version_poller_sits_on_the_hazard_stripe_not_in_main(client):
    # f38: the tag replaces the poller where it is; in <main> it pushed the page down
    html = client.get("/").text
    header = html[html.index('<header class="bar">') : html.index("</header>")]
    main = html[html.index("<main>") : html.index("</main>")]
    stripe = re.search(r'<div class="bar-stripe">.*?</div>(.*?)</div>', header, re.S)
    assert stripe and 'hx-get="/version?seen=' in stripe[1]
    assert "/version" not in main


def test_the_old_new_version_bar_is_gone_from_the_stylesheet():
    assert ".new-version" not in (STATIC / "dashboard.css").read_text()


def _open_on_version_poll(page, client, size: dict[str, int], loads: list[str]) -> None:
    """Open ``/`` at ``size``, counting each load of the page in ``loads``."""
    page.set_viewport_size(size)

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            if path == "/":
                loads.append(url)
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_function("window.htmx && document.querySelector(\"span[hx-get^='/version']\")")


# htmx's own swap of the poller, as its 10 s poll does it (with an old ``seen``: the tag comes back)
SWAP_IN_THE_TAG = """() => htmx.ajax('GET', '/version?seen=old',
  {target: document.querySelector("span[hx-get^='/version']"), swap: 'outerHTML'})"""


@pytest.mark.parametrize("size", [{"width": 1024, "height": 768}, PHONE], ids=["wide", "phone"])
def test_the_new_version_tag_moves_nothing_on_the_page(page, client, size):
    loads: list[str] = []
    _open_on_version_poll(page, client, size, loads)
    boxes = """() => ['header.bar', 'main', '.bar-top', 'nav.tabs'].map(s => {
      const b = document.querySelector(s).getBoundingClientRect();
      return [s, b.top, b.height, b.width];
    })"""
    before = page.evaluate(boxes)
    page.evaluate(SWAP_IN_THE_TAG)
    tag = page.locator("header.bar .bar-stripe a.version-tag")
    tag.wait_for()
    assert page.evaluate(boxes) == before
    # on the stripe's right end, a 24 px plate with a 44 px tap, and the page stays as it was
    stripe = page.locator(".bar-stripe").bounding_box()
    box = tag.bounding_box()
    assert stripe and box
    assert abs(box["x"] + box["width"] - (stripe["x"] + stripe["width"])) < 1
    assert box["y"] < stripe["y"] < box["y"] + box["height"]
    assert box["height"] >= 44
    plate = tag.evaluate("el => parseFloat(getComputedStyle(el, '::before').height)")
    assert plate == 24
    hit = page.evaluate(
        "([x, y]) => document.elementFromPoint(x, y).closest('.version-tag') !== null",
        [box["x"] + box["width"] - 4, box["y"] + 2],
    )
    assert hit, "the tap above the plate misses the tag"
    assert len(loads) == 1  # a visible page only shows the tag


def test_a_hidden_page_loads_the_new_version_unless_something_would_be_lost(page, client):
    loads: list[str] = []
    _open_on_version_poll(page, client, DISPLAY, loads)
    page.evaluate(
        """() => {
          Object.defineProperty(document, 'visibilityState', {get: () => 'hidden'});
          const draft = document.createElement('textarea');
          draft.id = 'draft';
          draft.value = 'unsent words';
          document.querySelector('main').append(draft);
        }"""
    )
    page.evaluate(SWAP_IN_THE_TAG)
    page.locator("a.version-tag").wait_for()
    page.wait_for_timeout(300)
    assert len(loads) == 1, "reloaded over unsent text"
    page.evaluate("() => document.getElementById('draft').remove()")
    page.evaluate("() => document.dispatchEvent(new Event('visibilitychange'))")
    page.wait_for_function("!document.querySelector('a.version-tag')")
    assert len(loads) == 2


def test_a_page_coming_back_loads_the_new_version_at_once(page, client, monkeypatch):
    # f38 review: a locked phone runs no poll, so coming back must not wait 10 s for the tag
    loads: list[str] = []
    _open_on_version_poll(page, client, PHONE, loads)
    monkeypatch.setattr(app_module, "code_version", lambda: "changed")
    page.evaluate(
        """() => {
          const draft = document.createElement('textarea');
          draft.id = 'draft';
          draft.value = 'unsent words';
          document.querySelector('main').append(draft);
          document.dispatchEvent(new Event('visibilitychange'));
        }"""
    )
    page.wait_for_timeout(300)
    assert len(loads) == 1, "reloaded over unsent text"
    page.evaluate(
        """() => {
          document.getElementById('draft').remove();
          document.dispatchEvent(new Event('visibilitychange'));
        }"""
    )
    for _ in range(20):
        if len(loads) == 2:
            break
        page.wait_for_timeout(100)
    assert len(loads) == 2


# --- notifications (f5-12, ADR 18 item 4) ---------------------------------------------------


def _facts(html: str) -> tuple[dict[str, dict[str, str]], str]:
    """What ``notify.js`` compares: the open needs (id -> {title, body, link}), and "all done"."""
    tag = re.search(r'<div id="live-facts"[^>]*>', html)
    assert tag, "no #live-facts"
    notices = re.search(r"data-notices='([^']*)'", tag[0])
    done = re.search(r'data-all-done="(true|false)"', tag[0])
    assert notices and done, tag[0]
    return json.loads(unescape(notices[1])), done[1]


def _owner_item_ids(db_path: Path) -> dict[str, int]:
    conn = connect(db_path)
    try:
        rows = conn.execute("SELECT subject, id FROM owner_items").fetchall()
    finally:
        conn.close()
    return {row["subject"]: row["id"] for row in rows}


def test_the_live_partial_carries_the_open_items_and_whether_work_is_running(serve, db_path):
    notices, done = _facts(serve().get("/live").text)
    ids = _owner_item_ids(db_path)
    # only the open item: the resolved "ollama" one is not there
    assert set(notices) == {f"coucou/owner-{ids['ADR 15']}"}
    assert done == "false"  # a job runs and two tickets wait


def test_what_the_dashboard_sees_itself_has_an_id_too(serve, db_path):
    notices, done = _facts(serve(heartbeat_age=timedelta(minutes=3)).get("/live").text)
    ids = _owner_item_ids(db_path)
    assert set(notices) == {
        f"coucou/owner-{ids['ADR 15']}",
        "coucou/runner-20261002-113500",
        "coucou/queue",
    }
    assert notices["coucou/runner-20261002-113500"]["title"] == "The runner stopped"
    assert notices["coucou/queue"]["title"] == "The runner is idle"
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
    assert page.evaluate("localStorage.getItem('notify:seen')") is None  # nothing compared
    page.locator('[data-action="yes"]').click()
    bar.wait_for(state="hidden", timeout=REFRESH)
    assert page.evaluate("window.asked") == 1
    page.wait_for_function("localStorage.getItem('notify:seen') !== null", timeout=REFRESH)
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
    assert len(shown) == 1 and shown[0]["title"] == "A decision for you"
    assert "A question that came later." in shown[0]["body"]

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
    addEventListener: () => {},
    register: async (url) => {
      window.sw_registered = url;
      return {
        showNotification: async (title, options) => {
          window.sw_notifications.push({
            title, body: options && options.body,
            tag: options && options.tag,
            data: options && options.data
          });
        }
      };
    }
  },
  configurable: true,
  writable: true
});
"""


def _seen_first_look(page) -> None:
    """notify.js compared the page's own facts on load: what the next look adds is news."""
    page.wait_for_function("localStorage.getItem('notify:seen') !== null", timeout=REFRESH)


def _next_look(page, client, html: str | None = None) -> None:
    """The next poll at once: ``/live`` (or ``html``) swapped into the Overview's
    ``#live-needs-you`` with the bubbling ``htmx:afterSwap`` htmx sends."""
    page.evaluate(
        "(html) => { const el = document.querySelector('#live-needs-you'); el.innerHTML = html;"
        " el.dispatchEvent(new Event('htmx:afterSwap', { bubbles: true })); }",
        html if html is not None else client.get("/live?project=coucou").text,
    )


FAKE_SERVICE_WORKER_REJECTS = """
window.sw_registered = null; window.sw_notifications = [];
Object.defineProperty(navigator, "serviceWorker", {
  value: {
    addEventListener: () => {},
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
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    _seen_first_look(page)

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
    _next_look(page, client)
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)

    assert page.evaluate("window.sw_registered") == "/static/sw.js"
    assert page.evaluate("window.sw_notifications.length") == 1
    entry = page.evaluate("window.sw_notifications[0]")
    assert entry["title"] == "A decision for you"
    assert entry["body"] == "A follow-up question."
    assert entry["tag"] and entry["tag"] != ""
    assert entry["data"]["link"] == "/?project=coucou"
    assert page.evaluate("window.shown") == []


def test_fallback_to_direct_notification_when_showNotification_rejects(
    page, serve_between, db_path
):
    """When showNotification rejects the item falls back to new Notification."""
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER_REJECTS)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    _seen_first_look(page)

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
    _next_look(page, client)
    page.wait_for_function("window.shown.length > 0", timeout=REFRESH)

    shown = page.evaluate("window.shown")
    assert len(shown) == 1 and "A fallback question." in shown[0]["body"]


def test_bundled_notifications_include_the_project_context(page, serve_between, db_path):
    """f114-05: bundled (multi-item) notifications keep the page's project in their link."""
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    _seen_first_look(page)

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR 33",
            text="First bundled item.",
            created=NOW.isoformat(),
        )
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR 34",
            text="Second bundled item.",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    _next_look(page, client)
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)

    entry = page.evaluate("window.sw_notifications[0]")
    assert entry["title"] == "2 things need you"
    assert entry["data"]["link"] == "/planning?project=coucou"
    assert page.evaluate("window.shown") == []


def test_three_items_become_one_bundle_with_titles_in_body(page, serve_between, db_path):
    """Three new items produce one notification whose title names the count and whose body
    lists each title on its own line (f69). Uses distinct kinds so each notice has a
    different title, verifying the exact ordered body."""
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    _seen_first_look(page)

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        # Use three different kinds so each notice has a distinct title
        metrics.upsert_owner_item(
            conn, project, "signoff", "f1", text="Signoff item.", created=NOW.isoformat()
        )
        metrics.upsert_owner_item(
            conn, project, "planning", "m4", text="Planning item.", created=NOW.isoformat()
        )
        metrics.upsert_owner_item(
            conn, project, "adr", "bundle-c", text="ADR item.", created=NOW.isoformat()
        )
    finally:
        conn.close()
    _next_look(page, client)
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)

    entry = page.evaluate("window.sw_notifications[0]")
    assert entry["title"] == "3 things need you"
    body_lines = entry["body"].split("\n")
    assert len(body_lines) == 3
    # Three distinct notice titles, in the database order (oldest first)
    assert body_lines[0] == "Ready for your sign-off: The factory measures itself"
    assert body_lines[1] == "The lead replied: The web app"
    assert body_lines[2] == "A decision for you"
    # Multi-item bundle links to /planning with the project
    assert entry["data"]["link"] == "/planning?project=coucou"
    assert page.evaluate("window.shown") == []


def test_bundled_notification_silent_on_next_look(page, serve_between, db_path):
    """After a bundled notification fires, the next poll sees the same items and produces
    no second notification."""
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    _seen_first_look(page)

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        for owner_id, _adr, text in [
            ("silent-a", "ADR 50", "Item one."),
            ("silent-b", "ADR 51", "Item two."),
        ]:
            metrics.upsert_owner_item(
                conn,
                project,
                "adr",
                owner_id,
                text=text,
                created=NOW.isoformat(),
            )
    finally:
        conn.close()
    _next_look(page, client)
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)
    initial_count = page.evaluate("window.sw_notifications.length")
    assert initial_count == 1

    # Wait for the next poll cycle: same items, no new notification
    page.wait_for_timeout(6_000)
    final_count = page.evaluate("window.sw_notifications.length")
    assert final_count == initial_count


def test_a_sign_off_in_the_same_look_as_all_done_is_not_lost(page, serve_between, db_path):
    """F114 review F2: the last review's verdict opens a sign-off as the queue empties. Both
    arrive in one look and make one bundle that names each; all done never hides the
    sign-off."""
    client = serve_between(activity="check-all on main")
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(conn, project, "f1-20-next", milestone_id=f1, state="ready")
    finally:
        conn.close()
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector('#live-facts[data-all-done="false"]', state="attached", timeout=REFRESH)
    _seen_first_look(page)

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(conn, project, "f1-20-next", milestone_id=f1, state="done")
        metrics.upsert_owner_item(
            conn, project, "signoff", "f1", text="Signoff item.", created=NOW.isoformat()
        )
    finally:
        conn.close()
    _next_look(page, client)
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)

    entry = page.evaluate("window.sw_notifications[0]")
    assert entry["title"] == "2 things need you"
    assert entry["body"].split("\n") == [
        "Ready for your sign-off: The factory measures itself",
        "All work done",
    ]
    assert entry["data"]["link"] == "/planning?project=coucou"


def test_bundled_link_encodes_special_characters_in_project(page, serve_between, db_path):
    """f69: the bundled link URL-encodes the project so names with & or # are not truncated."""
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    _seen_first_look(page)

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        for owner_id, _adr, text in [
            ("enc-a", "ADR 70", "Encoded item one."),
            ("enc-b", "ADR 71", "Encoded item two."),
        ]:
            metrics.upsert_owner_item(
                conn,
                project,
                "adr",
                owner_id,
                text=text,
                created=NOW.isoformat(),
            )
    finally:
        conn.close()
    # The next look names a project with special characters, whose first look is coucou's,
    # so enc-a and enc-b are news
    html = client.get("/live?project=coucou").text
    _next_look(page, client, html.replace('data-project="coucou"', 'data-project="my&amp;proj#2"'))
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)

    entry = page.evaluate("window.sw_notifications[0]")
    link = entry["data"]["link"]
    assert "?project=my%26proj%232" in link, f"expected encoded project in link, got {link}"


def test_compare_uses_per_project_done(page, serve_between, db_path):
    """Moving between projects' pages never notifies "All work done" again: what a browser
    saw of all the work being done is kept per project, inside the one notify:seen key."""
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    # Wait for the first look to store in notify:seen
    page.wait_for_function("localStorage.getItem('notify:seen') !== null", timeout=REFRESH)

    # Add an item on coucou (project A)
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR cross-A",
            text="Item on A.",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    _next_look(page, client)
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)
    assert page.evaluate("window.sw_notifications.length") == 1

    # Switch to the other project: load /live?project=other with the page's data-project
    # "other" has no open items (data-all-done="true") but has never been seen,
    # so no "All work done" notification fires.
    other_live = client.get("/live?project=other").text
    page.evaluate(
        "(html) => { const el = document.querySelector('#live-needs-you'); el.innerHTML = html;"
        " el.dispatchEvent(new Event('htmx:afterSwap', { bubbles: true })); }",
        other_live,
    )
    page.wait_for_timeout(6_000)  # wait for compare to run
    assert page.evaluate("window.sw_notifications.length") == 1

    # Now switch back to coucou: load /live?project=coucou with the page's data-project
    coucou_live = client.get("/live?project=coucou").text
    page.evaluate(
        "(html) => { const el = document.querySelector('#live-needs-you'); el.innerHTML = html;"
        " el.dispatchEvent(new Event('htmx:afterSwap', { bubbles: true })); }",
        coucou_live,
    )
    page.wait_for_timeout(6_000)  # wait for compare to run
    # No new notification: coucou's item was already seen
    assert page.evaluate("window.sw_notifications.length") == 1


def test_all_done_still_notifies_after_a_look_at_another_project(page, serve_between, db_path):
    """F142 review C1347-1: a look at another project between keeps this project's own
    "not done", so its work ending still says "All work done", once."""
    client = serve_between(activity="check-all on main")
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(conn, project, "f1-20-next", milestone_id=f1, state="ready")
    finally:
        conn.close()
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector('#live-facts[data-all-done="false"]', state="attached", timeout=REFRESH)
    _seen_first_look(page)

    other_live = client.get("/live?project=other").text
    assert 'data-all-done="true"' in other_live
    _next_look(page, client, other_live)
    page.wait_for_timeout(6_000)
    assert page.evaluate("window.sw_notifications.length") == 0

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(conn, project, "f1-20-next", milestone_id=f1, state="done")
    finally:
        conn.close()
    _next_look(page, client)
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)
    page.wait_for_timeout(6_000)
    assert [n["title"] for n in page.evaluate("window.sw_notifications")] == ["All work done"]


def test_compare_ignores_old_plain_boolean_done(page, serve_between, db_path):
    """A stored notify:seen with done: false (the old shape), then a look with all done:
    no notification and no error."""
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    page.wait_for_function("localStorage.getItem('notify:seen') !== null", timeout=REFRESH)

    # Overwrite notify:seen with the old shape (plain boolean done)
    page.evaluate(
        "localStorage.setItem('notify:seen', JSON.stringify({ "
        "ids: [], done: false, at: Date.now() }))"
    )

    # Load a page where all work is done (coucou has no open items after check-all)
    # We need to clear the existing item first
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(conn, project, "f1-20-next", milestone_id=f1, state="done")
    finally:
        conn.close()
    all_done_html = client.get("/live?project=coucou").text
    # Make sure data-all-done is true
    assert 'data-all-done="true"' in all_done_html
    page.evaluate(
        "(html) => { const el = document.querySelector('#live-needs-you'); el.innerHTML = html;"
        " el.dispatchEvent(new Event('htmx:afterSwap', { bubbles: true })); }",
        all_done_html,
    )
    page.wait_for_timeout(6_000)
    # No notification and no error (the old shape is handled gracefully)
    assert page.evaluate("window.sw_notifications.length") == 0


def test_new_item_on_other_project_notifies(page, serve_between, db_path):
    """A new item on project B while a page on A is open: one notification."""
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    # Wait for the first look to store in notify:seen
    page.wait_for_function("localStorage.getItem('notify:seen') !== null", timeout=REFRESH)

    # Add a new item on 'other' project
    conn = metrics.open_db(db_path)
    try:
        other = metrics.upsert_project(conn, "other")
        metrics.upsert_owner_item(
            conn,
            other,
            "adr",
            "ADR new-other",
            text="New item on other.",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    _next_look(page, client)
    page.wait_for_function("window.sw_notifications.length > 0", timeout=REFRESH)
    entry = page.evaluate("window.sw_notifications[0]")
    assert "other:" in entry["title"]
    assert entry["body"] == "New item on other."


def test_fallback_notification_has_onclick_handler(page, serve_between, db_path):
    """f69: when the service worker rejects, the fallback notification has an onclick
    handler so the owner can navigate on tap. Taps the notification notify.js created
    and asserts the page navigates to the item's link."""
    client = serve_between(activity="check-all on main")
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER_REJECTS)
    open_overview(page, client)
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)
    _seen_first_look(page)

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR 80",
            text="Fallback navigation test.",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    _next_look(page, client)
    page.wait_for_function("window.shown.length > 0", timeout=REFRESH)

    assert len(page.evaluate("window.shown")) == 1
    assert "Fallback navigation test." in page.evaluate("window.shown[0].body")
    # Tap the notification notify.js created and verify navigation to the item's link.
    assert page.evaluate("typeof window.shown[0].onclick") == "function"
    page.evaluate("window.shown[0].onclick({})")
    page.wait_for_url(ORIGIN + "/?project=coucou", timeout=REFRESH)  # the decision's link


# --- notification bar (f12-01, ADR 26 item 2) ----------------------------------------------

# A stand-in for the browser's Notification: it records what the page asks and shows.
FAKE_NOTIFICATION_GRANTED = """
window.shown = []; window.asked = 0;
class FakeNotification {
  constructor(title, options) {
    this.title = title;
    this.body = options && options.body;
    this.options = options || {};
    window.shown.push(this);
  }
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
    """sw.js uses includeUncontrolled so a tap focuses an open dashboard page and posts the link.
    Also verifies the worker closes the notification (Android) and falls back to openWindow."""
    sw = (STATIC / "sw.js").read_text()
    # Must find all clients, not just controlled ones (Android / background tabs)
    assert "includeUncontrolled" in sw
    # Android keeps a tapped notification otherwise
    assert "event.notification.close()" in sw
    # With a client: focus it, then post the link
    # The worker iterates clients, calls focus(), then postMessage({ link })
    assert sw.index("focus()") < sw.index("postMessage"), "focus must happen before postMessage"
    # Without a client: openWindow is the fallback
    assert "openWindow" in sw
    # openWindow is called only after the client loop (after the first return)
    client_loop = sw.index("for (const client")
    open_window = sw.index("openWindow")
    first_return = sw.index("return;", client_loop)
    assert first_return < open_window, "openWindow must be after the client loop"


FAKE_SERVICE_WORKER_LISTENER = """
window.sw_messages = [];
Object.defineProperty(navigator, 'serviceWorker', {
  value: {
    addEventListener: function(type, handler) {
      if (type === 'message') {
        window._sw_message_handler = handler;
      }
    }
  },
  configurable: true,
  writable: true
});
"""


def test_service_worker_listener_rejects_external_links(page, client):
    """notify.js only accepts postMessage links starting with / and not // (safe vs external).
    External and null links are rejected; a safe local link navigates."""
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    page.add_init_script(FAKE_SERVICE_WORKER_LISTENER)

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
    page.wait_for_timeout(REFRESH)

    # External link: should be rejected (no navigation)
    before = page.evaluate("window.location.href")
    page.evaluate("() => window._sw_message_handler({ data: { link: '//evil.com' } })")
    after = page.evaluate("window.location.href")
    assert before == after  # no navigation for external links

    # A backslash after the slash is another host to Chrome: rejected too
    page.evaluate("() => window._sw_message_handler({ data: { link: '/\\\\evil.com' } })")
    assert before == page.evaluate("window.location.href")

    # Null link: should be rejected
    page.evaluate("() => window._sw_message_handler({ data: { link: null } })")
    assert before == page.evaluate("window.location.href")

    # Safe local link: should navigate
    page.evaluate("() => window._sw_message_handler({ data: { link: '/planning/f1' } })")
    page.wait_for_url(ORIGIN + "/planning/f1", timeout=REFRESH)


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


def test_direct_notification_click_navigates_to_link(page, client, db_path):
    """When a notification is clicked, the dashboard navigates to the link stored in the
    notification data. Taps the notification notify.js created and fails if its onclick
    is removed (f69)."""
    page.add_init_script(FAKE_NOTIFICATION_GRANTED)
    # Force the direct-notification path: service worker available but rejects.
    page.add_init_script(FAKE_SERVICE_WORKER_REJECTS)

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
    _seen_first_look(page)

    # Seed a new item so compare() produces a notification.
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR 90",
            text="Direct click test.",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    _next_look(page, client)
    page.wait_for_function("window.shown.length > 0", timeout=REFRESH)

    # Tap the notification notify.js created and assert navigation to the item's link.
    assert page.evaluate("typeof window.shown[0].onclick") == "function"
    page.evaluate("window.shown[0].onclick({})")
    page.wait_for_url(ORIGIN + "/?project=coucou", timeout=REFRESH)  # the decision's link


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


def _runner_running(serve, serve_between, db_path):
    return serve_between(activity="check-all · f1-04-live")


def _runner_paused(serve, serve_between, db_path):
    client = serve_between(activity="check-all · f1-04-live")
    _ask(client, "pause")
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
        # the runner's own work: green dot that breathes (f184)
        (_runner_running, "Running: check-all · f1-04-live", "runner", PAUSE),
        (_runner_paused, "Pausing after f1-04-live · check-all", "runner", RESUME),
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
        "runner-running",
        "runner-paused",
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


def test_the_pause_sign_s_data_asked_matches_the_server_words(serve_between, db_path):
    """F184: when the runner runs with an activity, the ⏸ sign's data-asked holds the
    reversed activity parts that the server would say when a pause is processed."""
    client = _runner_running(serve_between, serve_between, db_path)
    html = client.get("/").text
    block = re.search(r'<div id="factory-status"[^>]*>(.*?)</div>', html, re.S)
    assert block, "no #factory-status"
    words = re.search(r'<span class="words" role="status">([^<]*)</span>', block[1])
    assert words
    sign = re.search(r'<button type="button" class="sign"([^>]*)>⏸</button>', block[1])
    assert sign
    data_asked = re.search(r'data-asked="([^"]*)"', sign[1])
    assert data_asked
    # data-asked is "Pausing after {reversed}" while words are "Running: {activity}"
    # they match when the activity has no " · " (single-part activity)
    activity = words[1].removeprefix("Running: ")
    if " · " in activity:
        parts = activity.split(" · ")
        expected = "Pausing after " + " · ".join(reversed(parts))
    else:
        expected = f"Pausing after {activity}"
    assert data_asked[1] == expected, f"{data_asked[1]} != {expected}"


@pytest.mark.parametrize(
    "setup",
    [_pause_asked, _pause_held_client, _pause_held_planner, _resume_asked],
    ids=["pause-asked", "paused", "paused-planner", "resume-asked"],
)
def test_now_says_the_pause_in_the_top_bars_words_without_a_button(
    serve, serve_between, db_path, setup
):
    """F28 D3, with F29 and F34: Now's pause line is the top bar's own words, the lead's answer
    and Resuming… included, and the top bar holds the one Pause/Resume."""
    client = setup(serve, serve_between, db_path)
    html = client.get("/live").text
    start = html.index('<section id="now"')
    now = html[start : html.index("</section>", start)]
    bar = _status(html)[0].removesuffix(f" · {PROJECT}")
    assert re.findall(r'<span class="pill warn">([^<]*)</span>', now) == [bar]
    assert '"kind": "pause"' not in now and '"kind": "resume"' not in now


def test_the_status_dot_wears_the_floors_colours_from_the_tokens(serve):
    css = (STATIC / "dashboard.css").read_text()

    def rule(selector: str) -> str:
        """The declarations of the top-level rule for exactly ``selector``."""
        found = re.search(rf"^{re.escape(selector)} \{{([^}}]*)\}}", css, re.M)
        assert found, selector
        return found[1]

    assert "background: var(--opus)" in rule(".factory-status .dot.lead")
    assert "background: var(--dev)" in rule(".factory-status .dot.developer")  # the floor's
    assert "background: var(--good)" in rule(".factory-status .dot.runner")  # runner: green
    assert "background: var(--muted)" in rule(".factory-status .dot")
    assert "var(--opus)" in rule(".factory-status .dot.waiting, .factory-status .dot.stopped")
    assert "var(--muted)" in rule(".factory-status .dot.stopped")
    # only a running job breathes, and never under reduced motion
    breathing = re.findall(
        r"@media \(prefers-reduced-motion: no-preference\) \{\s*([^{]*)\{ animation: breathe", css
    )
    assert breathing == [
        ".factory-status .dot.lead, .factory-status .dot.developer, .factory-status .dot.runner "
    ]
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
    assert _tab(client.get("/live").text) == "Planning · 1"  # the fixture's ripe card
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        for key in ("f8", "f9"):  # two ideas no thread is about: two seeds on the desk
            metrics.upsert_milestone(conn, project, key, title=f"Idea {key}", state="idea")
    finally:
        conn.close()
    assert _tab(client.get("/live").text) == "Planning · 1"  # F103 D1: seeds wait on no one
    lead_replies(db_path, "f7")  # an answer wanted, which does wait for the owner
    counted = _tab(client.get("/live").text)
    assert counted == "Planning · 2"
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


def _count_bar_polls(page) -> None:
    """Count the polls' bars as they arrive, after base.html's script has judged each one, so a
    test can check the stale one was kept out rather than only the last state (f28-01)."""
    page.evaluate(
        """() => {
          window.barPolls = 0;
          document.addEventListener("htmx:oobBeforeSwap", (event) => {
            if (event.detail.target.id === "factory-status") window.barPolls += 1;
          });
        }"""
    )


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
    _count_bar_polls(page)
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

    # the stale poll came back and was kept out: still the asked words, no sign
    page.wait_for_function("window.barPolls >= 1", timeout=REFRESH)
    assert words.text_content() == "Pausing after f1-04-live · coucou"
    assert page.locator("#factory-status .sign").count() == 0

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
    _count_bar_polls(page)
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

    # the stale poll came back and was kept out: still Resuming…, on its way, no sign
    page.wait_for_function("window.barPolls >= 1", timeout=REFRESH)
    assert words.text_content() == "Resuming…"
    assert page.locator("#factory-status .sign").count() == 0
    assert page.locator("#factory-status.asked").count() == 1

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


def test_factory_wide_status_ranks_live_job_before_between_jobs(db_path):
    """D1: a status whose dot is ``lead`` or ``developer`` (a live job) comes before any
    other ``Running: …``. Order: pause, live job, wait for Claude, between-jobs line, Idle,
    Stopped. Among equals, the owner's project order.

    travel-companion first in the order, its run "picking the next ticket" with 9 ready
    tickets, and softfield running a developer job on f15-10-fix-wait-note-assertions-check:
    the bar says "Running: softfield · f15-10-fix-wait-note-assertions-check" with the
    developer's dot, on a page for any of the three projects."""
    from factory_dashboard.app import PICKING, factory_status, factory_wide_status

    conn = metrics.open_db(db_path)
    try:
        # Seed two more projects: travel-companion and softfield
        tc = metrics.upsert_project(conn, "travel-companion")
        sf = metrics.upsert_project(conn, "softfield")
        # Set order: travel-companion first, coucou second, softfield third
        metrics.set_project_order(conn, ["travel-companion", "coucou", "softfield"])

        # travel-companion: between jobs, "picking the next ticket", with 9 ready tickets
        tc_run = metrics.upsert_run(
            conn,
            tc,
            "20261002-110000",
            command="milestone m1",
            started=(NOW - timedelta(minutes=10)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        metrics.update_run_activity(conn, tc_run, PICKING, None)
        m1 = metrics.upsert_milestone(conn, tc, "m1", started=(NOW - timedelta(days=1)).isoformat())
        for i in range(9):
            metrics.upsert_ticket(
                conn, tc, f"m1-0{i + 1}-ready", milestone_id=m1, kind="developer", state="ready"
            )

        # softfield: running a developer job
        sf_run = metrics.upsert_run(
            conn,
            sf,
            "20261002-113500",
            command="milestone f1",
            started=(NOW - timedelta(minutes=25)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        sf_ticket = metrics.upsert_ticket(
            conn,
            sf,
            "f15-10-fix-wait-note-assertions-check",
            milestone_id=metrics.upsert_milestone(conn, sf, "f15"),
            kind="developer",
            state="running",
        )
        metrics.start_job(
            conn,
            sf_run,
            ticket_id=sf_ticket,
            milestone_id=metrics.upsert_milestone(conn, sf, "f15"),
            role="developer",
            agent=LOCAL,
            attempt=1,
            started=(NOW - timedelta(minutes=12)).isoformat(),
        )

        # coucou: also between jobs (already seeded by db_path fixture)
        cc = metrics.upsert_project(conn, "coucou")
        cc_run = metrics.upsert_run(
            conn,
            cc,
            "20261002-100000",
            command="milestone f1",
            started=(NOW - timedelta(hours=1)).isoformat(),
            heartbeat=(NOW - timedelta(minutes=30)).isoformat(),
        )
        metrics.update_run_activity(conn, cc_run, "Idle: 2 tickets wait", None)

        # softfield's developer job should win, not travel-companion's "picking the next ticket"
        assert factory_status(conn, "travel-companion", NOW).words == f"Running: {PICKING}"
        expected_words = "Running: softfield · f15-10-fix-wait-note-assertions-check"
        for proj in ("travel-companion", "coucou", "softfield"):
            status = factory_wide_status(conn, proj, NOW)
            assert status.words == expected_words, f"for {proj}: {status.words}"
            assert status.dot == "developer"
    finally:
        conn.close()


def test_factory_wide_status_ranks_planner_job(db_path):
    """D1: a planner job shows ``planner, job <id>`` with the lead's dot."""
    from factory_dashboard.app import PICKING, factory_wide_status

    conn = metrics.open_db(db_path)
    try:
        # Seed travel-companion first with "picking the next ticket"
        tc = metrics.upsert_project(conn, "travel-companion")
        sf = metrics.upsert_project(conn, "softfield")
        metrics.set_project_order(conn, ["travel-companion", "softfield"])

        tc_run = metrics.upsert_run(
            conn,
            tc,
            "20261002-110000",
            command="milestone m1",
            started=(NOW - timedelta(minutes=10)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        metrics.update_run_activity(conn, tc_run, PICKING, None)

        # softfield: running a planner job
        sf_run = metrics.upsert_run(
            conn,
            sf,
            "20261002-113500",
            command="milestone f1",
            started=(NOW - timedelta(minutes=25)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        job_id = metrics.start_job(
            conn,
            sf_run,
            ticket_id=None,
            milestone_id=metrics.upsert_milestone(conn, sf, "f1"),
            role="planner",
            agent=LOCAL,
            attempt=1,
            started=(NOW - timedelta(minutes=12)).isoformat(),
        )
        status = factory_wide_status(conn, PROJECT, NOW)
        assert status.words == f"Running: softfield · planner, job {job_id}"
        assert status.dot == "lead"
    finally:
        conn.close()


def test_factory_wide_status_two_projects_between_jobs(db_path):
    """D1: two projects between jobs and none running a job: the first in the order is named."""
    from factory_dashboard.app import PICKING, factory_wide_status

    conn = metrics.open_db(db_path)
    try:
        tc = metrics.upsert_project(conn, "travel-companion")
        cc = metrics.upsert_project(conn, "coucou")
        metrics.set_project_order(conn, ["travel-companion", "coucou"])
        tc_run = metrics.upsert_run(
            conn,
            tc,
            "20261002-110000",
            command="milestone m1",
            started=(NOW - timedelta(minutes=10)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        metrics.update_run_activity(conn, tc_run, PICKING, None)
        cc_run = metrics.upsert_run(
            conn,
            cc,
            "20261002-100000",
            command="milestone f1",
            started=(NOW - timedelta(hours=1)).isoformat(),
            heartbeat=(NOW - timedelta(minutes=30)).isoformat(),
        )
        metrics.update_run_activity(conn, cc_run, "Idle: nothing to do", None)
        status = factory_wide_status(conn, PROJECT, NOW)
        assert status.project == "travel-companion"
        assert "travel-companion" in status.words
    finally:
        conn.close()


def test_factory_wide_status_pause_before_running(db_path):
    """D1: a pause still comes before a running job."""
    from factory_dashboard.app import factory_wide_status

    conn = metrics.open_db(db_path)
    try:
        # coucou: paused
        _pause_held(db_path)
        cc = metrics.upsert_project(conn, "coucou")
        cc_run = metrics.upsert_run(
            conn,
            cc,
            "20261002-113500",
            command="milestone f1",
            started=(NOW - timedelta(minutes=25)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        cc_ticket = metrics.upsert_ticket(
            conn,
            cc,
            "f1-04-live",
            milestone_id=metrics.upsert_milestone(conn, cc, "f1"),
            kind="developer",
            state="running",
        )
        metrics.start_job(
            conn,
            cc_run,
            ticket_id=cc_ticket,
            milestone_id=metrics.upsert_milestone(conn, cc, "f1"),
            role="developer",
            agent=LOCAL,
            attempt=1,
            started=(NOW - timedelta(minutes=12)).isoformat(),
        )
        status = factory_wide_status(conn, PROJECT, NOW)
        assert status.words.startswith("Paused by you since 11:40")
        assert status.button == "resume"
    finally:
        conn.close()


def test_factory_wide_status_waiting_for_claude_before_between_jobs(db_path):
    """D1: ``Waiting for Claude until …`` comes before a between-jobs line."""
    from factory_dashboard.app import PICKING, factory_status, factory_wide_status

    conn = metrics.open_db(db_path)
    try:
        tc = metrics.upsert_project(conn, "travel-companion")
        cc = metrics.upsert_project(conn, "coucou")
        # travel-companion first: only the rank, not the order, puts coucou's wait ahead
        metrics.set_project_order(conn, ["travel-companion", "coucou"])
        # coucou: waiting for Claude
        cc_run = metrics.upsert_run(
            conn,
            cc,
            "20261002-120000",
            command="milestone f1",
            started=(NOW - timedelta(minutes=5)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        metrics.update_run_activity(
            conn,
            cc_run,
            "waiting for Claude · f1-20-next until 15:00",
            "2026-10-02T15:00:00+00:00",
        )
        # travel-companion: between jobs
        tc_run = metrics.upsert_run(
            conn,
            tc,
            "20261002-110000",
            command="milestone m1",
            started=(NOW - timedelta(minutes=10)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        metrics.update_run_activity(conn, tc_run, PICKING, None)
        m1 = metrics.upsert_milestone(conn, tc, "m1", started=(NOW - timedelta(days=1)).isoformat())
        metrics.upsert_ticket(
            conn, tc, "m1-01-ready", milestone_id=m1, kind="developer", state="ready"
        )
        tc_status = factory_status(conn, "travel-companion", NOW)
        assert tc_status.words == f"Running: {PICKING}"  # between jobs, not idle
        status = factory_wide_status(conn, PROJECT, NOW)
        assert status.words == "Waiting for Claude until 15:00 · coucou"
        assert status.dot == "waiting"
    finally:
        conn.close()


def test_factory_wide_status_one_project_names_no_project(db_path):
    """D1: one project only: the words name no project, as today."""
    from factory_dashboard.app import factory_wide_status

    conn = metrics.open_db(db_path)
    try:
        # Only coucou exists
        cc = metrics.upsert_project(conn, "coucou")
        cc_run = metrics.upsert_run(
            conn,
            cc,
            "20261002-113500",
            command="milestone f1",
            started=(NOW - timedelta(minutes=25)).isoformat(),
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        cc_ticket = metrics.upsert_ticket(
            conn,
            cc,
            "f1-04-live",
            milestone_id=metrics.upsert_milestone(conn, cc, "f1"),
            kind="developer",
            state="running",
        )
        metrics.start_job(
            conn,
            cc_run,
            ticket_id=cc_ticket,
            milestone_id=metrics.upsert_milestone(conn, cc, "f1"),
            role="developer",
            agent=LOCAL,
            attempt=1,
            started=(NOW - timedelta(minutes=12)).isoformat(),
        )
        status = factory_wide_status(conn, PROJECT, NOW)
        assert " · coucou" not in status.words
        assert status.words == "Running: f1-04-live"
    finally:
        conn.close()


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


# --- theme switch button (f69-01) ----------------------------------------------------------------


def test_every_page_has_the_theme_button(client):
    """Every page's top bar has the Light/Night button with role, labels, and no text."""
    for path in PAGES:
        html = client.get(path).text
        btn = re.search(r'<button([^>]*)id="theme-btn"([^>]*)>', html)
        assert btn, path
        attrs = btn.group(1) + btn.group(2)
        assert 'role="switch"' in attrs, path
        assert "aria-label=" in attrs, path
        assert "aria-checked=" in attrs, path
        assert "title=" in attrs, path
        assert "theme-switch" in attrs, path
        full = re.search(r'<button[^>]*id="theme-btn"[^>]*>(.*?)</button>', html, re.DOTALL)
        assert full, path
        inner = full.group(1)
        text_only = re.sub(r"<[^>]*>", "", inner).strip()
        assert not text_only, f"Button must have no text content: {path}"


def test_the_theme_button_says_night_when_dark(page, client):
    """By default (dark), the button says "Light" with the right title."""
    page.set_viewport_size(DISPLAY)
    page.emulate_media(color_scheme="dark")

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    btn = page.locator("#theme-btn")
    assert btn.evaluate("el => el.getAttribute('aria-checked')") == "true"
    assert btn.evaluate("el => el.title") == "Switch to the light theme"


def test_pressing_the_button_switches_to_light_at_once(page, client):
    """Pressing the button switches to light immediately, charts included."""
    page.set_viewport_size(DISPLAY)
    page.emulate_media(color_scheme="dark")

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#theme-btn", state="visible", timeout=REFRESH)
    # Verify initial state
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark"
    # Click the button via JavaScript to ensure the event fires
    page.evaluate("document.getElementById('theme-btn').click()")
    # The button aria-checked is now false (night is off, light is on)
    btn = page.locator("#theme-btn")
    assert btn.evaluate("el => el.getAttribute('aria-checked')") == "false"
    assert btn.evaluate("el => el.title") == "Switch to the night theme"
    # The html element has data-theme="light"
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
    # The CSS custom properties the charts and floor read have actually changed
    floor = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--floor').trim()"
    )
    fg = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--fg').trim()")
    assert floor == "#eceee9", f"floor {floor} != light floor"
    assert fg == "#16191d", f"fg {fg} != light fg"
    # The series colour the milestone-esc chart reads from --a1 (== --copilot) has changed
    copilot = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--copilot').trim()"
    )
    assert copilot == "#3f6fd6", f"copilot {copilot} != light copilot"


def test_pressing_the_button_redraws_a_drawn_chart_in_place(page, client):
    """f69 review: a chart already on the page takes the new colours without a reload; the
    milestone-esc chart's first series reads --a1 (== --copilot)."""
    page.set_viewport_size(DISPLAY)
    page.emulate_media(color_scheme="dark")

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/milestones")
    selector = '.chart[data-chart="milestone-esc"] svg'
    page.wait_for_selector(selector, state="visible", timeout=REFRESH)
    first_fill = """() => [...document.querySelectorAll(
            '.chart[data-chart="milestone-esc"] svg path')]
        .map((p) => p.getAttribute('fill')).find((f) => f && f !== 'none') || null"""
    assert page.evaluate(first_fill) == "#7aa7ff"
    page.evaluate("window._sameLoad = true")
    page.evaluate("document.getElementById('theme-btn').click()")
    page.wait_for_function(f"({first_fill})() === '#3f6fd6'", timeout=REFRESH)
    assert page.evaluate("window._sameLoad") is True, "the page reloaded"
    assert page.locator(selector).count() == 1, "the chart was drawn twice"


def test_the_choice_stays_on_reload(page, client):
    """The theme choice persists on reload and across pages."""
    page.set_viewport_size(DISPLAY)
    page.emulate_media(color_scheme="dark")

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#theme-btn", state="visible", timeout=REFRESH)
    # Click the button via JavaScript to ensure the event fires
    page.evaluate("document.getElementById('theme-btn').click()")
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
    # Persist on reload
    page.reload()
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
    # Persist across pages
    page.goto(ORIGIN + "/tickets")
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"


def test_without_stored_value_follows_the_system(page, client):
    """With nothing stored, the page follows the system preference."""
    page.set_viewport_size(DISPLAY)

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    # Intercept matchMedia to capture the system-preference listener callback
    page.add_init_script("""
        var _originalMatchMedia = window.matchMedia;
        window.matchMedia = function(query) {
            var mql = _originalMatchMedia.call(window, query);
            if (query === "(prefers-color-scheme: light)") {
                var origAddEventListener = mql.addEventListener.bind(mql);
                mql.addEventListener = function(event, callback) {
                    if (event === "change") window._themeListener = callback;
                    return origAddEventListener(event, callback);
                };
            }
            return mql;
        };
    """)
    # With no stored value and dark system: data-theme starts as dark
    page.emulate_media(color_scheme="dark")
    page.goto(ORIGIN + "/")
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark"
    # Live system change to light: the button updates and visual properties change
    page.evaluate("window._themeFired = false")
    page.evaluate("""
        document.addEventListener('themechange', function() { window._themeFired = true; });
    """)
    page.evaluate("""
        var mql = matchMedia("(prefers-color-scheme: light)");
        Object.defineProperty(mql, 'matches', { value: true, writable: true, configurable: true });
        window._themeListener({ matches: true });
    """)
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
    assert page.locator("#theme-btn").evaluate("el => el.getAttribute('aria-checked')") == "false"
    floor = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--floor').trim()"
    )
    assert floor == "#eceee9", f"floor {floor} != light floor"
    assert page.evaluate("window._themeFired") is True


def test_at_390px_the_top_bar_is_no_taller(page, client):
    """At 390 px the top bar is no taller than before the button was added."""
    page.set_viewport_size({"width": 390, "height": 844})

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.evaluate("() => document.fonts.ready")
    header = page.locator("header.bar")
    height = "el => el.getBoundingClientRect().height"
    with_button = header.evaluate(height)
    assert page.locator("#theme-btn").evaluate(height) >= 44, "the button is under 44px to tap"
    # The bar as it was before the button: the same page with the button taken out
    page.evaluate("document.getElementById('theme-btn').style.display = 'none'")
    without_button = header.evaluate(height)
    assert with_button <= without_button, (
        f"header {with_button}px with the button > {without_button}px without it at 390px"
    )
    page.evaluate("document.getElementById('theme-btn').style.display = ''")
    page.evaluate("document.getElementById('theme-btn').click()")
    assert header.evaluate(height) == with_button, "the light theme changes the bar's height"
    assert page.locator("#theme-btn").evaluate("el => el.getAttribute('aria-checked')") == "true"


def test_a_system_change_leaves_a_stored_choice_alone(page, client):
    """f69 review: once the button was pressed, a later system change on the same page doesn't
    undo the owner's choice."""
    page.set_viewport_size(DISPLAY)

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.emulate_media(color_scheme="dark")
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#theme-btn", state="visible", timeout=REFRESH)
    page.evaluate("document.getElementById('theme-btn').click()")
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
    # The system goes light then dark: the listener registered at load must not follow it
    page.emulate_media(color_scheme="light")
    page.emulate_media(color_scheme="dark")
    page.wait_for_timeout(100)
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
    assert page.locator("#theme-btn").evaluate("el => el.getAttribute('aria-checked')") == "false"


def test_every_light_rule_is_scoped_to_the_light_theme():
    """f69 review: a light rule with a comma names the theme on each selector, else the
    unscoped part leaks into the night theme (`.floor .belt text` did)."""
    css = (STATIC / "dashboard.css").read_text()
    for rule in re.findall(r'([^{}]*:root\[data-theme="light"\][^{]*)\{', css):
        rule = re.sub(r"/\*.*?\*/", "", rule, flags=re.S)
        for selector in rule.split(","):
            assert selector.strip().startswith(':root[data-theme="light"]'), selector


def test_live_system_theme_changes_sync_button_and_dispatch_themechange(page, client):
    """f69-02: when the system preference changes with nothing stored the button and charts stay
    in sync (C1026-2)."""
    page.set_viewport_size(DISPLAY)

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    # Intercept matchMedia to capture the system-preference listener callback
    page.add_init_script("""
        var _originalMatchMedia = window.matchMedia;
        window.matchMedia = function(query) {
            var mql = _originalMatchMedia.call(window, query);
            if (query === "(prefers-color-scheme: light)") {
                var origAddEventListener = mql.addEventListener.bind(mql);
                mql.addEventListener = function(event, callback) {
                    if (event === "change") window._themeListener = callback;
                    return origAddEventListener(event, callback);
                };
            }
            return mql;
        };
    """)
    page.emulate_media(color_scheme="dark")
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#theme-btn", state="visible", timeout=REFRESH)
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark"
    assert page.locator("#theme-btn").evaluate("el => el.getAttribute('aria-checked')") == "true"
    # Simulate a live system preference change to light (the browser won't fire this naturally)
    page.evaluate("window._themeFired = false")
    page.evaluate("""
        document.addEventListener('themechange', function() { window._themeFired = true; });
    """)
    page.evaluate("""
        var mql = matchMedia("(prefers-color-scheme: light)");
        Object.defineProperty(mql, 'matches', { value: true, writable: true, configurable: true });
        window._themeListener({ matches: true });
    """)
    # data-theme should have changed
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
    # aria-checked should be false (night is off, light is on)
    assert page.locator("#theme-btn").evaluate("el => el.getAttribute('aria-checked')") == "false"
    assert (
        page.evaluate("document.getElementById('theme-btn').title") == "Switch to the night theme"
    )
    # themechange should have been dispatched (charts redraw on this event)
    assert page.evaluate("window._themeFired") is True


# --- plate panels (f81-01) ---------------------------------------------------------------------


def test_the_new_tokens_exist_in_dark_root():
    """D2: --tick, --stripe and --notch are defined in the dark :root."""
    css = (STATIC / "dashboard.css").read_text()
    dark = _block(css, ":root {")
    assert "--tick" in dark
    assert "--stripe" in dark
    assert "--notch" in dark


def test_the_new_tokens_resolve_in_dark_root():
    """The new tokens resolve to concrete values in dark mode."""
    css = (STATIC / "dashboard.css").read_text()
    tokens = _resolve_tokens(css, "dark")
    # --tick resolves to ink-2
    assert _hex_to_rgb(tokens["--tick"]) == _hex_to_rgb(tokens["--ink-2"])
    # --stripe is a repeating-linear-gradient containing var(--hazard)
    assert "var(--hazard)" in tokens["--stripe"]
    # --notch is a polygon
    assert "polygon" in tokens["--notch"]


def test_the_new_tokens_exist_in_light_root():
    """D2: --tick inherits --ink-2 from the light theme;
    --stripe and --notch are theme-independent.
    """
    css = (STATIC / "dashboard.css").read_text()
    light_start = css.index(':root[data-theme="light"]')
    light_body_start = css.index("{", light_start) + 1
    light_body_end = css.index("}", light_body_start)
    light_block = css[light_start:light_body_end]
    # --tick inherits --ink-2 (no need to repeat it explicitly)
    # --stripe uses --hazard which is the same in both themes
    # --notch is a geometric value, theme-independent
    assert "--tick" in light_block or "--ink-2" in light_block


def test_body_has_the_faint_grid():
    """D3: the body has a 32 px grid from --grid."""
    css = (STATIC / "dashboard.css").read_text()
    body_match = re.search(r"body\s*\{([^}]*)\}", css)
    assert body_match, "no body rule"
    body_decls = body_match[1]
    assert "linear-gradient" in body_decls, "grid requires linear-gradients"
    assert "32px" in body_decls, "grid must be 32px"
    assert "var(--grid)" in body_decls


def test_panel_has_position_relative_and_corner_ticks():
    """Every .panel gets position: relative and two corner ticks via ::before / ::after."""
    css = (STATIC / "dashboard.css").read_text()
    panel_block = re.search(r"\.panel\s*\{([^}]*)\}", css)
    assert panel_block
    assert "position: relative" in panel_block[1]
    # corner ticks use var(--tick)
    assert re.search(r"\.panel::before.*var\(--tick\)", css, re.S)
    assert re.search(r"\.panel::after.*var\(--tick\)", css, re.S)


def test_panel_with_h2_has_plate_header():
    """.panel > h2 is the plate header: plate background, rule border-bottom, stripe via ::after."""
    css = (STATIC / "dashboard.css").read_text()
    # panel > h2 has plate background
    h2_block = re.search(r"\.panel > h2\s*\{([^}]*)\}", css)
    assert h2_block
    assert "background: var(--plate)" in h2_block[1]
    assert "border-bottom: 1px solid var(--rule)" in h2_block[1]
    # stripe via ::after
    assert re.search(r"\.panel > h2::after.*var\(--stripe\)", css, re.S)


def test_panel_needs_has_yellow_plate():
    """.panel.needs > h2 has hazard-yellow background."""
    css = (STATIC / "dashboard.css").read_text()
    needs_h2 = re.search(r"\.panel\.needs > h2\s*\{([^}]*)\}", css)
    assert needs_h2
    assert "background: var(--hazard)" in needs_h2[1]
    assert "color: var(--hazard-ink)" in needs_h2[1]


def test_panel_needs_stripe_uses_hazard_ink():
    """.panel.needs > h2::after stripe uses hazard-ink."""
    css = (STATIC / "dashboard.css").read_text()
    # The needs variant's stripe must reference hazard-ink
    needs_after = re.search(r"\.panel\.needs > h2::after\s*\{([^}]*)\}", css)
    assert needs_after
    assert "var(--hazard-ink)" in needs_after[1]


def test_panel_removes_top_padding_only_when_h2_first():
    """Only panels whose first child is h2 lose their top padding."""
    css = (STATIC / "dashboard.css").read_text()
    # The :has() selector removes padding-top
    assert ":has(> h2:first-child)" in css
    assert "padding-top: 0" in css


def test_queue_panel_title_is_h2():
    """The Queue panel's title is an <h2>, matching the other panels."""
    queue_html = (STATIC.parent / "templates" / "_partials" / "queue.html").read_text()
    assert "<h2>Queue</h2>" in queue_html


def test_queued_job_count_has_text_separator():
    """f81-10: queued-job count has a whitespace separator so it does not touch the <small> text."""
    queue_html = (STATIC.parent / "templates" / "_partials" / "queue.html").read_text()
    assert "{{ queued_jobs | length }} <small>" in queue_html, (
        "queued_jobs count must be separated from <small> by a space",
    )


def test_about_uses_tick_token():
    """.about corner ticks use var(--tick)."""
    css = (STATIC / "dashboard.css").read_text()
    about_ticks = re.search(r"\.about::before.*?var\(--tick\)", css)
    assert about_ticks, ".about::before must use var(--tick)"
    about_after = re.search(r"\.about::after.*?var\(--tick\)", css)
    assert about_after, ".about::after must use var(--tick)"


def test_aside_uses_tick_token():
    """.aside corner ticks use var(--tick)."""
    css = (STATIC / "dashboard.css").read_text()
    aside_ticks = re.search(r"\.aside::before.*?var\(--tick\)", css)
    assert aside_ticks, ".aside::before must use var(--tick)"
    aside_after = re.search(r"\.aside::after.*?var\(--tick\)", css)
    assert aside_after, ".aside::after must use var(--tick)"


def test_about_stripe_uses_stripe_token():
    """.about > header .stripe uses var(--stripe)."""
    css = (STATIC / "dashboard.css").read_text()
    stripe_decl = re.search(r"\.about > header \.stripe[^{]*\{([^}]*)\}", css)
    assert stripe_decl
    assert "var(--stripe)" in stripe_decl[1]


def test_panel_with_h2_shows_plate_in_dark(page, client):
    """A non-needs .panel with h2 shows the plate header and ticks in dark mode."""
    page.set_viewport_size(DISPLAY)
    page.emulate_media(color_scheme="dark")

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.evaluate("() => document.fonts.ready")

    # Find a .panel (not .needs) with h2 on the overview page
    panels = page.locator(".panel:not(.needs):has(> h2)")
    assert panels.count() > 0, "Overview should have non-needs panels with h2"

    # Check the first panel's h2 has plate background
    first_panel = panels.first
    h2 = first_panel.locator("h2")
    assert h2.is_visible()

    # The h2 background should be the plate color
    h2_bg = h2.evaluate("el => getComputedStyle(el).backgroundColor")
    # var(--plate) in dark mode is #1f2730 -> rgb(31, 39, 48)
    assert h2_bg == "rgb(31, 39, 48)", f"plate h2 background {h2_bg} != rgb(31, 39, 48)"


def test_panel_with_h2_shows_plate_in_light(page, client):
    """A non-needs .panel with h2 shows the plate header and ticks in light mode."""
    page.set_viewport_size(DISPLAY)
    page.emulate_media(color_scheme="light")

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.evaluate("() => document.fonts.ready")

    panels = page.locator(".panel:not(.needs):has(> h2)")
    assert panels.count() > 0

    first_panel = panels.first
    h2 = first_panel.locator("h2")
    assert h2.is_visible()

    # The h2 background should be the plate color (light theme)
    h2_bg = h2.evaluate("el => getComputedStyle(el).backgroundColor")
    # var(--plate) in light mode is #ffffff -> rgb(255, 255, 255)
    assert h2_bg == "rgb(255, 255, 255)", f"plate h2 background {h2_bg} != rgb(255, 255, 255)"


def test_needs_you_panel_shows_yellow_plate(page, client):
    """The 'Needs you' panel shows the hazard-yellow plate."""
    page.set_viewport_size(DISPLAY)
    page.emulate_media(color_scheme="dark")

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.evaluate("() => document.fonts.ready")

    # The needs panel
    needs_panel = page.locator(".panel.needs")
    assert needs_panel.count() > 0

    h2 = needs_panel.locator("h2")
    assert h2.is_visible()

    # The h2 background should be hazard yellow
    h2_bg = h2.evaluate("el => getComputedStyle(el).backgroundColor")
    # var(--hazard) is #f2b10a -> rgb(242, 177, 10)
    assert h2_bg == "rgb(242, 177, 10)", f"needs h2 background {h2_bg} != hazard yellow"


def test_about_and_aside_still_render(page, client):
    """.about and .aside still render with their own ticks."""
    page.set_viewport_size(DISPLAY)
    page.emulate_media(color_scheme="dark")

    def route(r):
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=client.get(url).text, content_type="text/html; charset=utf-8")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")
    page.evaluate("() => document.fonts.ready")

    # .about should exist on the card page or similar
    # .aside should exist on the set-aside plate
    # We check the CSS tokens are correct rather than rendering
    css = (STATIC / "dashboard.css").read_text()
    # .about still has its own tick positioning
    assert re.search(r"\.about::before.*top: -1px.*left: -1px", css, re.S)
    assert re.search(r"\.about::after.*bottom: -1px.*right: -1px", css, re.S)
    # .aside has bottom ticks
    assert re.search(r"\.aside::before.*left: -1px.*bottom: -1px", css, re.S)
    assert re.search(r"\.aside::after.*right: -1px.*bottom: -1px", css, re.S)


# --- one button set (f81-03) --------------------------------------------------------------------


def test_btn_go_has_clip_path_notch():
    """D5: .btn.go has clip-path: var(--notch)."""
    css = (STATIC / "dashboard.css").read_text()
    go_block = re.search(r"\.btn\.go\s*\{([^}]*)\}", css)
    assert go_block, ".btn.go rule not found"
    assert "clip-path: var(--notch)" in go_block[1]


def test_btn_has_44px_min_height():
    """D5: .btn has min-height: 44px."""
    css = (STATIC / "dashboard.css").read_text()
    btn_block = re.search(r"\.btn\s*\{([^}]*)\}", css)
    assert btn_block, ".btn rule not found"
    assert "min-height: 44px" in btn_block[1]


def test_btn_go_disabled_is_muted():
    """D5: .btn.go:disabled is muted, transparent, dashed border."""
    css = (STATIC / "dashboard.css").read_text()
    disabled_block = re.search(r"\.btn\.go:disabled\s*\{([^}]*)\}", css)
    assert disabled_block, ".btn.go:disabled rule not found"
    assert "color: var(--muted)" in disabled_block[1]
    assert "background: transparent" in disabled_block[1]
    assert re.search(r"border.*dashed", disabled_block[1])


# --- square parts (f81-02) ---------------------------------------------------------------------


def test_no_border_radius_except_top_bar_status_dot():
    """No border-radius in dashboard.css except the top bar's status dot (f81-02)."""
    css = (STATIC / "dashboard.css").read_text()
    # Find all rules with border-radius
    rules_with_radius = re.findall(r"([^{}]*?)\{([^}]*)\}", css)
    for selector, body in rules_with_radius:
        if "border-radius" not in body:
            continue
        # border-radius: 0 is removing radius, not adding it
        if re.search(r"border-radius:\s*0\b", body):
            continue
        # The top bar's status dot is allowed
        if ".factory-status .dot" in selector and "border-radius" in body:
            continue
        # The gauge mark dot is allowed (it's a light, not an ornament)
        if ".gauge .mark::after" in selector and "border-radius" in body:
            continue
        # The theme switch plate and knob are allowed (it's a switch, not a panel)
        if ".theme-switch .plate" in selector and "border-radius" in body:
            continue
        if ".theme-switch .knob" in selector and "border-radius" in body:
            continue
        pytest.fail(f"border-radius found in {selector}: {body}")


def test_idle_crate_svg_exists():
    """The idle crate SVG exists at the expected path."""
    svg_path = STATIC.parent / "templates" / "_partials" / "idle_crate.svg"
    assert svg_path.exists(), "idle_crate.svg not found"
    svg = svg_path.read_text()
    assert "<svg" in svg
    assert 'viewBox="0 0 40 34"' in svg
    assert 'stroke="currentColor"' in svg


def test_idle_crate_svg_draws_a_crate():
    """The idle crate SVG draws a crate on a floor line."""
    svg_path = STATIC.parent / "templates" / "_partials" / "idle_crate.svg"
    svg = svg_path.read_text()
    # Crate body (rect)
    assert "<rect" in svg
    # Crate internal lines (dashed)
    assert "stroke-dasharray" in svg
    # Floor line
    assert "<path" in svg and "M0 32h40" in svg


def test_pill_is_square_with_square_lamp():
    """Tags are square with a square lamp, colours as before (f81-02)."""
    css = (STATIC / "dashboard.css").read_text()
    # .pill has no border-radius
    pill_block = re.search(r"\.pill\s*\{([^}]*)\}", css)
    assert pill_block
    assert "border-radius" not in pill_block[1], ".pill must not have border-radius"
    # .pill uses mono font, uppercase
    assert "var(--mono)" in pill_block[1]
    assert "text-transform: uppercase" in pill_block[1]
    # The lamp (::before) is a square (no border-radius)
    pill_dot = re.search(r"\.pill::before\s*\{([^}]*)\}", css)
    assert pill_dot
    assert "border-radius" not in pill_dot[1], ".pill::before must be square"
    # The dot keeps its colours (good, warn, running)
    assert "--dot: var(--good)" in css
    assert "--dot: var(--warn)" in css
    assert "--dot: var(--a1)" in css


def test_meter_has_slot_styling():
    """The meter sits in a slot with border and floor background."""
    css = (STATIC / "dashboard.css").read_text()
    meter_block = re.search(r"\.meter\s*\{([^}]*)\}", css)
    assert meter_block
    assert "border: 1px solid var(--rule)" in meter_block[1]
    assert "background: var(--floor)" in meter_block[1]
    # The fill is inset
    meter_span = re.search(r"\.meter > span\s*\{([^}]*)\}", css)
    assert meter_span
    assert "inset: 1px" in meter_span[1]


def test_gauge_has_quarter_ticks():
    """The meter-ticks rule has quarter ticks under the meter."""
    css = (STATIC / "dashboard.css").read_text()
    gauge_block = re.search(r"\.meter-ticks\s*\{([^}]*)\}", css)
    assert gauge_block
    assert "background-image" in gauge_block[1] or "linear-gradient" in gauge_block[1]
    assert "25%" in gauge_block[1], "quarter ticks use 25% spacing"


# --- f85-02: Before and after on the card's page ---------------------------------------------

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 8
CARD = "f50-pictured"


def _pictured(
    db_path: Path,
    tmp_path: Path,
    *,
    project: str = PROJECT,
    pictures: dict[str, dict[str, str]] | None = None,
    pages: list[str] | None = None,
    live: str = "",
    factory: bool = False,
    listed: bool = True,
    files: tuple[str, ...] = (),
) -> TestClient:
    """A client over the fixture with ``project``'s checkout at ``tmp_path / project``: a card
    ``f50-pictured`` (signed off sheet) whose picture folder holds ``files`` and, when
    ``listed``, f85-01's ``shots.json``."""
    repo = tmp_path / project
    (repo / ".softfield").mkdir(parents=True)
    toml = '[shots]\nprepare = "p"\nserve = "s {port}"\nready = "/"\n'
    if live:
        toml += f'live = "{live}"\n'
    (repo / ".softfield" / "project.toml").write_text(toml, encoding="utf-8")
    if factory:
        (repo / "runner").mkdir()
        (repo / "runner" / "loop.py").write_text("", encoding="utf-8")
        (repo / "factory_dashboard").mkdir()
        (repo / "factory_dashboard" / "app.py").write_text("", encoding="utf-8")
    folder = repo / ".softfield" / "var" / "shots" / CARD
    folder.mkdir(parents=True)
    for name in files:
        (folder / name).write_bytes(PNG)
    if listed:
        (folder / "shots.json").write_text(
            json.dumps({"pages": pages or ["/board"], "base": "x", "pictures": pictures or {}}),
            encoding="utf-8",
        )
    conn = metrics.open_db(db_path)
    try:
        project_id = metrics.upsert_project(conn, project, repo=str(repo))
        metrics.upsert_milestone(
            conn, project_id, CARD, title="Pictured", signoff={"changed": "It changed."}
        )
    finally:
        conn.close()
    from factory_dashboard.app import get_now

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


TAKEN = {"state": "taken", "reason": ""}
ALL_TAKEN = {
    f"{when}-{width}-{n}.png": TAKEN
    for when in ("before", "after")
    for width in ("phone", "wide")
    for n in (1, 2)
}


def _panel(html: str) -> str:
    found = re.search(r'<section class="shots" id="shots".*?</section>', html, re.DOTALL)
    assert found, "no Before and after panel"
    return found[0]


def test_a_card_with_a_list_shows_the_panel_under_what_changed_one_plate_per_address(
    db_path, tmp_path
):
    client = _pictured(
        db_path, tmp_path, pages=["/board", "/memory/"], pictures=ALL_TAKEN, files=tuple(ALL_TAKEN)
    )
    html = client.get(f"/milestones/{CARD}").text
    assert (
        html.index('id="what-changed"') < html.index('id="shots"') < html.index('id="how-to-test"')
    )
    panel = _panel(html)
    assert panel.index("/board") < panel.index("/memory/")
    assert panel.count('class="page-plate"') == 2
    assert f"/milestones/{CARD}/shots/after-phone-1.png" in panel
    assert f"/milestones/{CARD}/shots/before-wide-2.png" in panel
    assert "Before and after" in panel


def test_a_card_without_a_list_shows_no_panel(db_path, tmp_path):
    client = _pictured(db_path, tmp_path, listed=False)
    assert 'id="shots"' not in client.get(f"/milestones/{CARD}").text


def test_the_pictures_route_serves_only_named_pngs_of_the_cards_folder(db_path, tmp_path):
    client = _pictured(
        db_path, tmp_path, pictures=ALL_TAKEN, files=("after-phone-1.png", "notes.txt", "x.png")
    )
    served = client.get(f"/milestones/{CARD}/shots/after-phone-1.png")
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/png"
    assert served.content == PNG
    for name in (
        "notes.txt",
        "x.png",
        "after-phone-1.jpg",
        "after-wide-1.png",  # not taken: missing
        "..%2Fshots.json",
        "..%2F..%2Fproject.toml",
        "after-phone-01.png",
        "shots.json",
    ):
        assert client.get(f"/milestones/{CARD}/shots/{name}").status_code == 404, name
    assert client.get("/milestones/f99-other/shots/after-phone-1.png").status_code == 404


def test_the_pictures_come_from_the_projects_own_folder(db_path, tmp_path):
    client = _pictured(
        db_path,
        tmp_path,
        project=OTHER,
        pictures={"after-phone-1.png": TAKEN},
        files=("after-phone-1.png",),
    )
    own = client.get(f"/milestones/{CARD}/shots/after-phone-1.png")
    assert own.status_code == 404  # the page's project is coucou, whose folder has none
    served = client.get(f"/milestones/{CARD}/shots/after-phone-1.png?project={OTHER}")
    assert served.status_code == 200
    assert (
        f"/milestones/{CARD}/shots/after-phone-1.png?project={OTHER}"
        in client.get(f"/milestones/{CARD}?project={OTHER}").text
    )


def test_a_before_recorded_as_new_says_the_page_did_not_exist(db_path, tmp_path):
    pictures = {
        "before-phone-1.png": {"state": "new", "reason": ""},
        "before-wide-1.png": {"state": "new", "reason": ""},
        "after-phone-1.png": TAKEN,
        "after-wide-1.png": TAKEN,
    }
    client = _pictured(
        db_path, tmp_path, pictures=pictures, files=("after-phone-1.png", "after-wide-1.png")
    )
    panel = _panel(client.get(f"/milestones/{CARD}").text)
    assert "This page didn't exist before" in panel
    assert "before-phone-1.png" not in panel


def test_a_picture_that_failed_shows_its_reason_in_a_dashed_plate(db_path, tmp_path):
    pictures = {
        "before-phone-1.png": {"state": "failed", "reason": "the app stopped with code 1"},
        "after-phone-1.png": {"state": "failed", "reason": "it answered 500"},
    }
    client = _pictured(db_path, tmp_path, pictures=pictures)
    panel = _panel(client.get(f"/milestones/{CARD}").text)
    assert "The page before couldn't be drawn" in panel
    assert "the app stopped with code 1" in panel
    assert "it answered 500" in panel
    assert 'class="missing"' in panel
    assert "<img" not in panel


def test_a_softfield_cards_address_opens_the_dashboards_page_in_a_new_tab(db_path, tmp_path):
    client = _pictured(db_path, tmp_path, factory=True, live="http://192.168.1.20:8000")
    panel = _panel(client.get(f"/milestones/{CARD}").text)
    link = re.search(r'<a [^>]*href="(/board\?project=coucou)"[^>]*>', panel)
    assert link, panel
    assert 'target="_blank"' in link[0] and 'rel="noopener"' in link[0]
    assert "192.168.1.20" not in panel


def test_another_projects_address_joins_its_live_address(db_path, tmp_path):
    client = _pictured(
        db_path, tmp_path, pages=["/memory/"], live="http://192.168.1.20:8000/", project=OTHER
    )
    panel = _panel(client.get(f"/milestones/{CARD}?project={OTHER}").text)
    link = re.search(r'<a [^>]*href="(http://192.168.1.20:8000/memory/)"[^>]*>', panel)
    assert link, panel
    assert 'target="_blank"' in link[0] and 'rel="noopener"' in link[0]


def test_an_address_with_no_live_is_plain_text_and_a_foreign_address_never_a_link(
    db_path, tmp_path
):
    client = _pictured(db_path, tmp_path, pages=["/memory/", "//evil.example/x"], project=OTHER)
    panel = _panel(client.get(f"/milestones/{CARD}?project={OTHER}").text)
    assert "/memory/" in panel
    assert 'target="_blank"' not in panel


def test_a_foreign_address_is_never_a_link_even_with_a_live_address(db_path, tmp_path):
    client = _pictured(
        db_path,
        tmp_path,
        pages=["//evil.example/x", "https://evil.example/", "/ok"],
        live="http://a:1",
        project=OTHER,
    )
    panel = _panel(client.get(f"/milestones/{CARD}?project={OTHER}").text)
    assert "evil.example" not in re.findall(r'href="([^"]*)"', panel)
    assert not any("evil.example" in href for href in re.findall(r'href="([^"]*)"', panel))
    assert 'href="http://a:1/ok"' in panel


def test_the_panel_has_its_switches_and_the_plans_mockup_when_the_thread_has_one(db_path, tmp_path):
    client = _pictured(db_path, tmp_path, pictures=ALL_TAKEN, files=tuple(ALL_TAKEN))
    plain = _panel(client.get(f"/milestones/{CARD}").text)
    assert "The plan's mock-up" not in plain
    for word in ("Before", "After", "Phone", "Wide"):
        assert f">{word}</button>" in plain
    conn = metrics.open_db(db_path)
    try:
        project_id = metrics.find_project(conn, PROJECT)
        assert project_id is not None
        thread = metrics.planner_thread(conn, project_id, "f50", NOW.isoformat())
        metrics.add_planner_message(
            conn,
            thread["id"],
            "lead",
            NOW.isoformat(),
            "Here.",
            proposals=[{"id": "p1", "kind": "mockup", "title": "Mock", "path": "x"}],
        )
    finally:
        conn.close()
    panel = _panel(client.get(f"/milestones/{CARD}").text)
    assert 'href="/planning/f50/proposals/p1?project=coucou"' in panel
    assert "The plan's mock-up" in panel
    # a later reply with other proposals, F85's own case, doesn't lose the link
    conn = metrics.open_db(db_path)
    try:
        metrics.add_planner_message(
            conn,
            thread["id"],
            "lead",
            NOW.isoformat(),
            "An ADR.",
            proposals=[{"id": "adr-9", "kind": "adr", "title": "ADR 9", "path": "y"}],
        )
    finally:
        conn.close()
    panel = _panel(client.get(f"/milestones/{CARD}").text)
    assert 'href="/planning/f50/proposals/p1?project=coucou"' in panel


def test_a_card_without_a_sheet_shows_no_panel_even_with_a_list(db_path, tmp_path):
    client = _pictured(db_path, tmp_path, pictures=ALL_TAKEN, files=tuple(ALL_TAKEN))
    conn = metrics.open_db(db_path)
    try:
        project_id = metrics.find_project(conn, PROJECT)
        assert project_id is not None
        metrics.upsert_milestone(conn, project_id, "f51-unsigned", title="No sheet")
    finally:
        conn.close()
    folder = tmp_path / PROJECT / ".softfield" / "var" / "shots"
    (folder / "f51-unsigned").mkdir()
    (folder / "f51-unsigned" / "shots.json").write_text(
        (folder / CARD / "shots.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert 'id="shots"' not in client.get("/milestones/f51-unsigned").text


def test_a_broken_project_toml_leaves_the_panel_with_plain_addresses(db_path, tmp_path):
    client = _pictured(db_path, tmp_path, live="http://a:1")
    (tmp_path / PROJECT / ".softfield" / "project.toml").write_text("[shots\n", encoding="utf-8")
    response = client.get(f"/milestones/{CARD}")
    assert response.status_code == 200
    assert 'target="_blank"' not in _panel(response.text)


def _shown(page) -> list[str]:
    """The pictures the panel shows now, as their file names."""
    hrefs = page.locator("#shots a.shot:visible").evaluate_all(
        "links => links.map(link => link.getAttribute('href'))"
    )
    return [href.split("/")[-1].split("?")[0] for href in hrefs]


def _lay_out(page) -> None:
    page.evaluate("() => document.fonts.ready")
    # the tabs scroll sideways on a phone by design
    page.evaluate("() => document.querySelector('nav.tabs').setAttribute('data-layout', 'overlay')")
    problems = layout_problems(page)
    assert problems == [], "\n".join(problems)


def test_on_a_phone_the_switches_flip_the_pictures(page, db_path, tmp_path):
    client = _pictured(db_path, tmp_path, pictures=ALL_TAKEN, files=tuple(ALL_TAKEN))
    page.set_viewport_size(PHONE)
    open_planning_page(page, client, f"/milestones/{CARD}")
    assert _shown(page) == ["after-phone-1.png"]
    assert page.locator("#shots figcaption:visible").inner_text().lower() == "after · main now"
    _lay_out(page)
    page.locator('#shots [data-ba="before"]').click()
    assert _shown(page) == ["before-phone-1.png"]
    assert page.locator('#shots [data-ba="before"]').get_attribute("aria-pressed") == "true"
    page.locator('#shots [data-w="wide"]').click()
    assert _shown(page) == ["before-wide-1.png"]


def test_on_a_wide_screen_before_and_after_sit_side_by_side(page, db_path, tmp_path):
    client = _pictured(db_path, tmp_path, pictures=ALL_TAKEN, files=tuple(ALL_TAKEN))
    page.set_viewport_size({"width": 1440, "height": 900})
    open_planning_page(page, client, f"/milestones/{CARD}")
    assert _shown(page) == ["before-wide-1.png", "after-wide-1.png"]
    assert page.locator("#shots .switch.ba").is_hidden()
    before = page.locator('#shots figure[data-when="before"]').bounding_box()
    after = page.locator('#shots figure[data-when="after"]').bounding_box()
    assert before["y"] == after["y"] and before["x"] + before["width"] <= after["x"]
    _lay_out(page)
    page.locator('#shots [data-w="phone"]').click()
    assert _shown(page) == ["before-phone-1.png", "after-phone-1.png"]


def test_the_projects_send_order_button_carries_btn_and_go(client):
    """f81-09: the "Send new order" button on the Projects page carries ``btn`` and ``go``
    so ``.btn.go`` supplies the hazard-yellow background when enabled (f81-08 removed it
    from ``.projects-page .send-order``)."""
    html = client.get("/projects").text
    btn = re.search(r'<button[^>]*class="([^"]*)"[^>]*>Send new order</button>', html)
    assert btn, "no 'Send new order' button found"
    classes = btn[1].split()
    assert "btn" in classes, f"button classes {classes} missing 'btn'"
    assert "go" in classes, f"button classes {classes} missing 'go'"
