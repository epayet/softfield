import re
import sqlite3

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient

from factory_dashboard import app as app_module
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
    assert "runner backfill" in capsys.readouterr().err


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
