"""``POST /projects/{name}/run`` and ``/stop`` (ADR 46 items 6 and 8, F239 D5): the dashboard's
first write that isn't a request row. It runs a fixed Compose command on a project from the
registry, behind the same guard as ``/requests``. No test runs Docker: ``_docker`` is replaced."""

import json
from pathlib import Path

import pytest

from runner import config, metrics, stacks
from runner.stacks import Result
from tests.factory_dashboard.conftest import PROJECT

SAME = "http://127.0.0.1:8765"  # the test client's own origin
HTMX = {"HX-Request": "true", "Origin": SAME}
APP = "coaster-ranker"


class Docker:
    """``_docker`` replaced: records each call; ``ps`` answers with ``self.ps``, ``logs`` with
    ``self.logs``, ``config --services`` with ``self.config_services``."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.ps = ""
        self.logs = ""
        self.config_services = ""

    def __call__(self, args, cwd, env) -> Result:
        self.calls.append(list(args))
        if "ps" in args:
            return Result(0, self.ps, "")
        if "config" in args and "--services" in args:
            return Result(0, self.config_services, "")
        return Result(0, self.logs if "logs" in args else "", "")

    def commands(self) -> list[str]:
        """The Compose verb of each call: ``up``, ``stop``, ``ps``."""
        return [c[3] for c in self.calls if c[:1] == ["compose"]]


@pytest.fixture
def docker(monkeypatch, tmp_path: Path) -> Docker:
    fake = Docker()
    monkeypatch.setattr(stacks, "_docker", fake)
    monkeypatch.setattr(stacks, "SHARE", tmp_path / "share")
    # an app that is already checked out, so `start` needs no git
    (tmp_path / "share" / "run" / APP).mkdir(parents=True)
    return fake


def _repo(folder: Path, run: bool = True) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / ".softfield").mkdir(exist_ok=True)
    toml = f'[project]\nname = "{APP}"\n' + ('\n[run]\nservice = "web"\n' if run else "")
    (folder / ".softfield" / "project.toml").write_text(toml, encoding="utf-8")
    return folder


def _register(db_path: Path, name: str, repo: Path) -> None:
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, name, repo=str(repo))
    finally:
        conn.close()


@pytest.fixture
def app_repo(db_path: Path, tmp_path: Path) -> Path:
    repo = _repo(tmp_path / "Coaster Ranker")
    _register(db_path, APP, repo)
    return repo


def _crashed() -> str:
    """The main service exited 1: crashed, not stopped (`STOPPED_CODES`)."""
    web = json.loads(_running())
    web.update(State="exited", ExitCode=1, Status="Exited (1) 3 minutes ago", Publishers=[])
    return json.dumps(web) + "\n"


def _running() -> str:
    web = {
        "ID": "id-web",
        "Name": f"{APP}-web-1",
        "Service": "web",
        "State": "running",
        "Health": "",
        "ExitCode": 0,
        "Status": "Up 2 seconds",
        "Publishers": [{"PublishedPort": 8123, "TargetPort": 8000}],
    }
    return json.dumps(web) + "\n"


@pytest.mark.parametrize("action", ["run", "stop"])
@pytest.mark.parametrize(
    "headers",
    [
        {},  # no HX-Request: a plain form or a script
        {"Origin": SAME},
        {"HX-Request": "true", "Origin": "http://evil.example"},  # another site's page
        {"HX-Request": "true"},  # neither Origin nor Referer
    ],
)
def test_without_the_guard_it_is_403_and_docker_never_runs(
    client, docker, app_repo, action, headers
):
    response = client.post(f"/projects/{APP}/{action}", headers=headers)
    assert response.status_code == 403
    assert docker.calls == []


@pytest.mark.parametrize("action", ["run", "stop"])
def test_an_unknown_project_is_404(client, docker, action):
    assert client.post(f"/projects/nowhere/{action}", headers=HTMX).status_code == 404
    assert docker.calls == []


def test_a_project_without_run_is_404(client, docker, db_path, tmp_path):
    _register(db_path, PROJECT, _repo(tmp_path / "coucou", run=False))
    assert client.post(f"/projects/{PROJECT}/run", headers=HTMX).status_code == 404
    assert docker.calls == []


def test_softfield_itself_is_404_even_with_a_run_table(
    client, docker, db_path, tmp_path, monkeypatch
):
    home = _repo(tmp_path / "softfield")
    monkeypatch.setattr(config, "HOME", home)
    _register(db_path, "softfield", home)
    assert client.post("/projects/softfield/run", headers=HTMX).status_code == 404
    assert docker.calls == []


def test_a_guarded_run_starts_the_app_once_and_answers_its_row(client, docker, app_repo):
    docker.ps = _running()
    response = client.post(f"/projects/{APP}/run", headers=HTMX)
    assert response.status_code == 200
    assert docker.commands().count("up") == 1
    assert "Running" in response.text
    # the row's button is now Stop, posting back to its own row
    assert f'hx-post="/projects/{APP}/stop"' in response.text
    assert f'hx-post="/projects/{APP}/run"' not in response.text


def test_a_run_whose_app_is_still_coming_up_says_starting(client, docker, app_repo):
    docker.ps = _running().replace('"Health": ""', '"Health": "starting"')
    response = client.post(f"/projects/{APP}/run", headers=HTMX)
    assert response.status_code == 200
    assert "Starting" in response.text


def test_a_guarded_stop_stops_the_app_and_offers_run(client, docker, app_repo):
    response = client.post(f"/projects/{APP}/stop", headers=HTMX)
    assert response.status_code == 200
    assert docker.commands().count("stop") == 1
    assert "up" not in docker.commands()
    assert "Stopped" in response.text
    assert f'hx-post="/projects/{APP}/run"' in response.text


def test_a_crashed_apps_row_offers_run_not_stop(client, docker, app_repo):
    """f239-05: a crashed app is brought back with Run; Stop is for an app that is up."""
    docker.ps = _crashed()
    response = client.post(f"/projects/{APP}/stop", headers=HTMX)
    assert "Crashed" in response.text
    assert f'hx-post="/projects/{APP}/run"' in response.text
    assert f'hx-post="/projects/{APP}/stop"' not in response.text


def test_a_failed_start_answers_the_row_with_why(client, docker, app_repo, monkeypatch):
    def failing(args, cwd, env) -> Result:
        docker.calls.append(list(args))
        if "up" in args:
            return Result(1, "", "port is already allocated")
        return Result(0, "", "")

    monkeypatch.setattr(stacks, "_docker", failing)
    response = client.post(f"/projects/{APP}/run", headers=HTMX)
    assert response.status_code == 200
    assert "port is already allocated" in response.text
    assert "Stopped" in response.text


def _with_services(services: list[str]) -> str:
    """``docker compose config --services`` output for a list of service names."""
    return "\n".join(services) + "\n"


def test_the_page_shows_logs_lines_and_service_chooser_lists_services(client, docker, app_repo):
    docker.ps = _running()
    docker.config_services = "web\nworker\n"
    docker.logs = "web-1 | line one\nweb-1 | line two\n"
    response = client.get(f"/projects/{APP}/logs")
    assert response.status_code == 200
    assert "line one" in response.text
    assert "line two" in response.text
    assert 'value="web"' in response.text
    assert 'value="worker"' in response.text
    assert '<option value="">' in response.text or "<option value=''>" in response.text


def test_service_param_asks_logs_for_that_service_only(client, docker, app_repo):
    docker.ps = _running()
    docker.config_services = "web\nworker\n"
    docker.logs = "worker-1 | worker log\n"
    response = client.get(f"/projects/{APP}/logs?service=web")
    assert response.status_code == 200
    assert docker.calls[-1][:5] == ["compose", "-p", "coaster-ranker", "logs", "--no-color"]
    assert "web" in docker.calls[-1]
    assert "worker" not in "".join(docker.calls[-1])


def test_an_unknown_project_answers_404(client, docker):
    assert client.get("/projects/nowhere/logs").status_code == 404


def test_the_logs_page_escapes_lines_and_takes_dockers_own_time(client, docker, app_repo):
    """Docker's ``CreatedAt`` isn't ISO ("2026-11-12 09:00:00 +0100 CET"): the page never
    parses it (the first draft did, and answered 500 for every real app)."""
    web = json.loads(_running())
    web["CreatedAt"] = "2026-11-12 09:00:00 +0100 CET"
    docker.ps = json.dumps(web) + "\n"
    docker.logs = "web-1 | <script>alert(1)</script>\n"
    response = client.get(f"/projects/{APP}/logs")
    assert response.status_code == 200
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
    assert "updated at" in response.text


def test_the_logs_page_polls_itself_for_its_service_and_can_pause(client, docker, app_repo):
    docker.ps = _running()
    docker.config_services = "web\nworker\n"
    page = client.get(f"/projects/{APP}/logs?service=worker").text
    assert f'hx-get="/projects/{APP}/logs?service=worker"' in page
    assert 'hx-trigger="every 5s [!window.logsPaused]"' in page
    assert 'hx-select="#logs-live"' in page and 'id="logs-live"' in page
    assert 'name="service"' in page  # the chooser sends its choice
    assert 'id="logs-pause"' in page


def test_an_unknown_service_answers_404(client, docker, app_repo):
    docker.ps = _running()
    assert client.get(f"/projects/{APP}/logs?service=ghost").status_code == 404
