import re
import sqlite3

import pytest
import uvicorn
from fastapi.testclient import TestClient

from factory_dashboard.app import HOST, PORT, Db, create_app
from factory_dashboard.queries import connect
from runner import cli
from tests.factory_dashboard.conftest import OTHER, PROJECT

PAGES = ["/", "/milestones", "/tickets", "/jobs", "/runs", "/timeline", "/agents", "/bench"]


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
    assert re.findall(r'href="([^"?]*)\?project=other"', tabs) == PAGES
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
        assert f'"{path}"' in html
        assert client.get(path).status_code == 200
    assert "https://" not in html  # vendored: no CDN


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


def test_runner_dashboard_refuses_a_missing_database(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(uvicorn, "run", lambda *a, **k: pytest.fail("served"))
    assert cli.main(["dashboard", "--db", str(tmp_path / "none.sqlite")]) == 1
    assert "runner backfill" in capsys.readouterr().err
