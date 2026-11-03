"""The review's pictures (ADR 40): plain tests with the browser replaced by ``_shoot``, on a real
server and a real worktree; and two with real Chromium, on a tiny app of their own."""

import http.server
import json
import os
import re
import struct
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

from runner import metrics, shots
from runner.config import ConfigError, Shots, project_shots
from tests.runner.conftest import MACHINE, git

KEY = "f9-pages"
BASE = f"{KEY}-start"
ROOT = Path(__file__).resolve().parents[2]

DOC = """\
# Milestone F9: pages

## Done when
- `/not-a-page` is mentioned elsewhere

## Before and after
Some words about `/in-a-sentence`.
- `/first`
- `/second?x=1`: and a note

## Plan
- `/not-this-one`
"""

# The app: answers GET with pages/<address>.html from the tree it runs in; logs every request.
APP = """\
import http.server, os, pathlib, sys

class App(http.server.BaseHTTPRequestHandler):
    def _log(self):
        with open(os.environ["APP_LOG"], "a") as log:
            log.write(self.command + " " + self.path + "\\n")

    def do_GET(self):
        self._log()
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", os.environ["APP_OTHER"] + "/redirected")
            self.end_headers()
            return
        name = self.path.strip("/") or "index"
        page = pathlib.Path("pages") / (name + ".html")
        if name == "broken":
            self.send_response(500)
            self.end_headers()
            return
        found = page.is_file()
        self.send_response(200 if found else 404)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(page.read_bytes() if found else b"nope")

    def do_POST(self):
        self._log()
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass

http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), App).serve_forever()
"""


def _toml(serve: str = f"{sys.executable} app.py {{port}}", prepare: str = "true") -> str:
    return f"\n[shots]\nprepare = '{prepare}'\nserve = '{serve}'\nready = '/'\n"


@pytest.fixture
def app(repo, tmp_path_factory, monkeypatch):
    """A project with the tiny app and a card listing two pages, tagged at its start. Its
    temporary folders go under a folder of their own, to be seen empty."""
    log = tmp_path_factory.mktemp("log") / "requests"
    monkeypatch.setenv("APP_LOG", str(log))
    monkeypatch.setenv("APP_OTHER", "http://localhost:1")
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path_factory.mktemp("tmp")))
    (repo / "app.py").write_text(APP)
    (repo / "pages").mkdir()
    (repo / "pages" / "index.html").write_text("home")
    (repo / "pages" / "first.html").write_text("<h1>old first</h1>")
    (repo / ".softfield" / "cards").mkdir()
    (repo / ".softfield" / "cards" / f"{KEY}.md").write_text(
        "## Before and after\n- `/first`\n- `/second`\n"
    )
    with (repo / ".softfield" / "project.toml").open("a") as toml:
        toml.write(_toml())
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "plan")
    git(repo, "tag", BASE)
    (repo / "pages" / "second.html").write_text("<h1>second</h1>")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "work")
    return repo


@pytest.fixture
def shoot(monkeypatch):
    """No browser: a picture of each wanted page the app answers, as ``_browse`` decides. Each
    call is kept: (the tree's text for the page, the files)."""
    calls = []

    def fake(origin, wanted, folder):
        import urllib.error
        import urllib.request

        results = {}
        for w in wanted:
            try:
                urllib.request.urlopen(origin + w.address).read()
            except urllib.error.HTTPError:
                results[w.file] = shots.Picture(shots.NEW)
                continue
            (folder / w.file).write_bytes(b"png")
            results[w.file] = shots.Picture(shots.TAKEN)
        calls.append([w.file for w in wanted])
        return results

    monkeypatch.setattr(shots, "_shoot", fake)
    return calls


def _folder(repo):
    return repo / shots.SHOTS_DIR / KEY


def _list(repo):
    return json.loads((_folder(repo) / shots.LIST_FILE).read_text())


def _take(repo):
    lines: list[str] = []
    shots.take(repo, KEY, BASE, lines.append)
    return lines


def _set_shots(repo, text):
    """The project's [shots] now, on main: the current commands serve both trees."""
    path = repo / ".softfield" / "project.toml"
    path.write_text(path.read_text().split("\n[shots]")[0] + text)


def _pngs(repo):
    return sorted(p.name for p in _folder(repo).glob("*.png"))


def test_pages_reads_the_section_in_order():
    assert shots.pages(DOC) == ["/first", "/second?x=1"]


def test_pages_without_the_section_is_none():
    assert shots.pages("# A card\n\n## Plan\n- `/first`\n") == []


def test_only_a_get_to_the_app_itself_is_allowed():
    origin = "http://127.0.0.1:5000"
    assert shots.allowed("GET", origin + "/board?x=1", origin)
    assert not shots.allowed("POST", origin + "/board", origin)
    assert not shots.allowed("HEAD", origin + "/board", origin)
    assert not shots.allowed("GET", "http://127.0.0.1:5001/board", origin)
    assert not shots.allowed("GET", "http://example.com/", origin)
    assert not shots.allowed("GET", "http://127.0.0.1:5000@example.com/", origin)
    assert not shots.allowed("GET", "https://127.0.0.1:5000/", origin)


def test_shots_is_read_with_the_project(tmp_path):
    (tmp_path / ".softfield").mkdir()
    toml = tmp_path / ".softfield" / "project.toml"
    assert project_shots(tmp_path) is None
    toml.write_text("[project]\nname = 'x'\n")
    assert project_shots(tmp_path) is None
    toml.write_text(_toml("serve {port}", "fill") + "live = 'http://192.168.1.20:8000'\n")
    assert project_shots(tmp_path) == Shots("fill", "serve {port}", "/", "http://192.168.1.20:8000")


@pytest.mark.parametrize(
    "text",
    [
        "[shots]\nserve = 'a {port}'\nready = '/'\n",
        _toml("serve on no port"),
        "shots = 'not a table'\n",
    ],
)
def test_a_shots_section_that_cant_work_says_so(tmp_path, text):
    (tmp_path / ".softfield").mkdir()
    (tmp_path / ".softfield" / "project.toml").write_text(text)
    with pytest.raises(ConfigError, match=r"\[shots\]"):
        project_shots(tmp_path)


def test_a_project_toml_that_doesnt_parse_says_so(tmp_path):
    """As a ConfigError, the one the dashboard's card page catches."""
    (tmp_path / ".softfield").mkdir()
    (tmp_path / ".softfield" / "project.toml").write_text("[shots\n")
    with pytest.raises(ConfigError, match=r"project\.toml"):
        project_shots(tmp_path)


def test_a_round_leaves_the_named_pictures_and_the_list(app, shoot):
    lines = _take(app)
    assert _pngs(app) == sorted(
        f"{when}-{width}-{n}.png"
        for when in ("before", "after")
        for width in ("phone", "wide")
        for n in (1, 2)
        if (when, n) != ("before", 2)
    )
    listed = _list(app)
    assert listed["pages"] == ["/first", "/second"]
    assert listed["pictures"]["after-wide-2.png"] == {"state": "taken", "reason": ""}
    assert len(lines) == 1 and "6 taken" in lines[0]


def test_an_address_the_old_code_doesnt_have_didnt_exist_before(app, shoot):
    _take(app)
    assert _list(app)["pictures"]["before-phone-2.png"]["state"] == shots.NEW
    assert not (_folder(app) / "before-phone-2.png").exists()
    assert (_folder(app) / "after-phone-2.png").exists()


def test_a_second_round_takes_the_after_again_and_leaves_the_before(app, shoot):
    _take(app)
    (_folder(app) / "before-wide-1.png").write_bytes(b"as it was")
    (_folder(app) / "after-wide-1.png").write_bytes(b"old after")
    shoot.clear()
    _take(app)
    assert all(file.startswith("after-") for call in shoot for file in call)
    assert (_folder(app) / "before-wide-1.png").read_bytes() == b"as it was"
    assert (_folder(app) / "after-wide-1.png").read_bytes() == b"png"
    assert _list(app)["pictures"]["before-phone-2.png"]["state"] == shots.NEW


def test_a_before_that_failed_is_tried_again_next_round(app, shoot):
    git(app, "tag", "-d", BASE)
    _take(app)
    assert "before-phone-1.png" not in _pngs(app)
    assert _list(app)["pictures"]["before-phone-1.png"]["state"] == shots.FAILED
    assert _list(app)["pictures"]["after-phone-1.png"]["state"] == shots.TAKEN
    git(app, "tag", BASE, "HEAD~1")
    _take(app)
    assert _list(app)["pictures"]["before-phone-1.png"]["state"] == shots.TAKEN


def test_a_changed_list_of_pages_starts_the_pictures_again(app, shoot):
    _take(app)
    (_folder(app) / "before-wide-1.png").write_bytes(b"of the old first page")
    (app / ".softfield" / "cards" / f"{KEY}.md").write_text("## Before and after\n- `/second`\n")
    _take(app)
    assert _list(app)["pages"] == ["/second"]
    assert _pngs(app) == ["after-phone-1.png", "after-wide-1.png"]
    assert _list(app)["pictures"]["before-wide-1.png"]["state"] == shots.NEW


def test_an_after_that_fails_leaves_no_old_picture(app, shoot, monkeypatch):
    _take(app)
    _set_shots(app, _toml("exit 3 {port}"))
    _take(app)
    assert not [name for name in _pngs(app) if name.startswith("after-")]
    assert _list(app)["pictures"]["after-wide-1.png"]["state"] == shots.FAILED


def test_a_server_that_doesnt_start_is_recorded_with_its_reason(app, shoot):
    _set_shots(app, _toml("echo no database for port {port} >&2; exit 3"))
    lines = _take(app)
    picture = _list(app)["pictures"]["after-phone-1.png"]
    assert picture["state"] == shots.FAILED
    assert "code 3" in picture["reason"] and "no database" in picture["reason"]
    assert _list(app)["pictures"]["before-wide-2.png"]["state"] == shots.FAILED
    assert _pngs(app) == []
    assert "0 taken" in lines[0]
    assert shoot == []


def test_a_server_that_never_answers_is_recorded(app, shoot, monkeypatch):
    monkeypatch.setattr(shots, "READY_LIMIT", 0.5)
    _set_shots(app, _toml("sleep 60 # {port}"))
    _take(app)
    assert "didn't answer" in _list(app)["pictures"]["after-phone-1.png"]["reason"]


def test_a_failing_prepare_is_recorded_for_every_picture(app, shoot):
    _set_shots(app, _toml(prepare="echo no fixtures >&2; exit 1"))
    _take(app)
    pictures = _list(app)["pictures"]
    assert len(pictures) == 8
    assert all("no fixtures" in p["reason"] for p in pictures.values())
    assert shoot == []


def test_prepare_and_both_servers_get_the_same_data_and_their_own_tree(
    app, shoot, tmp_path_factory
):
    seen = tmp_path_factory.mktemp("seen") / "seen"
    _set_shots(
        app,
        _toml(
            f'echo "$PWD $SOFTFIELD_SHOTS_DATA" >> {seen}; {sys.executable} app.py {{port}}',
            f'echo "$PWD $SOFTFIELD_SHOTS_DATA" >> {seen}; touch "$SOFTFIELD_SHOTS_DATA/made"',
        ),
    )
    _take(app)
    (prepare_tree, data), (after_tree, after_data), (before_tree, before_data) = [
        line.split() for line in seen.read_text().splitlines()
    ]
    assert Path(prepare_tree) == Path(after_tree) == app
    assert Path(before_tree) != app
    assert data == after_data == before_data


def test_a_failing_browser_is_recorded_with_its_reason(app, monkeypatch):
    monkeypatch.setattr(shots, "_BROWSER", ["sh", "-c", "echo Chromium is missing >&2; exit 1"])
    lines = _take(app)
    picture = _list(app)["pictures"]["after-phone-1.png"]
    assert picture["state"] == shots.FAILED and "Chromium is missing" in picture["reason"]
    assert "0 taken" in lines[0]


def test_whatever_else_goes_wrong_the_round_goes_on(app, monkeypatch):
    def broken(*args):
        raise RuntimeError("no disk")

    monkeypatch.setattr(shots, "_round", broken)
    assert "no disk" in _take(app)[0]


def test_an_incomplete_shots_section_doesnt_stop_the_round(app, shoot):
    _set_shots(app, "\n[shots]\nready = '/'\n")
    assert "[shots]" in _take(app)[0]


def test_no_shots_section_gets_no_folder(repo, shoot):
    (repo / ".softfield" / "cards").mkdir()
    (repo / ".softfield" / "cards" / f"{KEY}.md").write_text("## Before and after\n- `/a`\n")
    assert _take(repo) == []
    assert not (repo / shots.SHOTS_DIR).exists()


def test_a_card_without_the_section_gets_no_folder(app, shoot):
    (app / ".softfield" / "cards" / f"{KEY}.md").write_text("# Nothing to see\n")
    assert _take(app) == []
    assert not (app / shots.SHOTS_DIR).exists()


def test_a_project_with_no_card_doc_gets_no_folder(repo, shoot):
    assert _take(repo) == []
    assert not (repo / shots.SHOTS_DIR).exists()


def _gone(pid: int) -> bool:
    for _ in range(50):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    return False


@pytest.mark.parametrize("fails", [False, True], ids=["success", "failure"])
def test_nothing_is_left_behind(app, shoot, monkeypatch, tmp_path_factory, fails):
    """The server, a child it started, the worktree and the data folder, a failure included."""
    pids = tmp_path_factory.mktemp("pids") / "pids"
    if fails:

        def broken(origin, wanted, folder):
            raise RuntimeError("the browser fell over")

        monkeypatch.setattr(shots, "_shoot", broken)
    _set_shots(app, _toml(f"sleep 300 & echo $! $$ >> {pids}; {sys.executable} app.py {{port}}"))
    _take(app)
    numbers = [int(pid) for pid in pids.read_text().split()]
    assert len(numbers) == 4  # the after's, the before's
    assert all(_gone(pid) for pid in numbers)
    assert len(git(app, "worktree", "list").splitlines()) == 1
    assert list(Path(tempfile.gettempdir()).iterdir()) == []
    if fails:
        reason = _list(app)["pictures"]["after-wide-1.png"]["reason"]
        assert "fell over" in reason


# --- with real Chromium ---------------------------------------------------------------------


def _png_width(path: Path) -> int:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return int(struct.unpack(">I", data[16:20])[0])


class _Other(http.server.BaseHTTPRequestHandler):
    hits: list[str] = []  # noqa: RUF012 - one server, one test

    def do_GET(self) -> None:
        self.hits.append(self.path)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args) -> None:
        pass


@pytest.fixture
def other_host():
    """A second server, the "other host": what the pictured page must never reach."""
    _Other.hits = []
    server = http.server.HTTPServer(("127.0.0.1", 0), _Other)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://localhost:{server.server_port}", _Other.hits
    server.shutdown()
    thread.join()


def test_real_pictures_and_a_page_that_tries_everything(app, other_host, monkeypatch):
    """The whole of it in Chromium: a 404 before, the two widths, and a page that POSTs, submits
    a form and reaches for another host, directly and through a redirect."""
    other, other_hits = other_host
    monkeypatch.setenv("APP_OTHER", other)
    (app / "pages" / "first.html").write_text(
        f"""<h1>new first</h1>
        <img src="{other}/image">
        <img src="/redirect">
        <form id="f" method="post" action="/form"></form>
        <script>
          fetch("/fetch-post", {{method: "POST"}}).catch(() => {{}});
          fetch("{other}/fetch").catch(() => {{}});
          if (matchMedia("(prefers-color-scheme: dark)").matches) fetch("/dark-theme");
          setTimeout(() => document.getElementById("f").submit(), 50);
        </script>"""
    )
    _take(app)
    folder = _folder(app)
    assert _png_width(folder / "before-phone-1.png") == 390
    assert _png_width(folder / "before-wide-1.png") == 1440
    assert _png_width(folder / "after-phone-1.png") == 390
    assert _png_width(folder / "after-wide-2.png") == 1440
    pictures = _list(app)["pictures"]
    assert pictures["before-phone-2.png"]["state"] == shots.NEW
    assert not (folder / "before-phone-2.png").exists()
    assert pictures["after-phone-2.png"]["state"] == shots.TAKEN
    requests = Path(os.environ["APP_LOG"]).read_text().splitlines()
    assert "GET /redirect" in requests  # the page did try
    assert "GET /dark-theme" in requests  # D3
    assert not [r for r in requests if not r.startswith("GET ")]
    assert other_hits == []


def test_a_500_is_recorded_by_the_browser(app):
    (app / ".softfield" / "cards" / f"{KEY}.md").write_text("## Before and after\n- `/broken`\n")
    _take(app)
    picture = _list(app)["pictures"]["after-wide-1.png"]
    assert picture == {"state": shots.FAILED, "reason": "it answered 500"}
    assert _pngs(app) == []


def test_softfields_own_shots_picture_the_dashboard(tmp_path, monkeypatch):
    """ADR 40 item 4: a copy of the metrics database, the dashboard of the tree on that copy."""
    db = tmp_path / "metrics.sqlite"
    metrics.open_db(db).close()
    machine = tmp_path / "machine.toml"
    machine.write_text(re.sub(r'(?m)^db = "[^"]*"', f'db = "{db}"', MACHINE.read_text()))
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    found = project_shots(ROOT)
    assert found is not None
    folder = tmp_path / "pictures"
    folder.mkdir()
    results = shots._round(ROOT, found, "HEAD", shots._wanted("after", ["/"]), [], folder)
    assert results == {
        "after-phone-1.png": shots.Picture(shots.TAKEN),
        "after-wide-1.png": shots.Picture(shots.TAKEN),
    }
    assert _png_width(folder / "after-phone-1.png") == 390
    assert _png_width(folder / "after-wide-1.png") == 1440
