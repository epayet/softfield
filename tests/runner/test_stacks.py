"""A project's app on Docker Compose (ADR 46, F239 D1 to D4): ``[run]``, and `runner/stacks.py`
on recorded ``docker compose`` output. No test runs Docker: ``_docker`` is replaced."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from runner import config, stacks
from runner.config import ConfigError, Run, project_run
from runner.stacks import Result, Stack
from tests.runner.conftest import git

RUN = '[run]\nservice = "web"\n'


def _project(repo: Path, toml: str) -> Path:
    (repo / ".softfield").mkdir(exist_ok=True)
    (repo / ".softfield" / "project.toml").write_text(toml, encoding="utf-8")
    return repo


@pytest.fixture
def share(tmp_path: Path, monkeypatch) -> Path:
    """Where the checkouts, the data and the results live: a folder of the test's own."""
    folder = tmp_path / "share"
    monkeypatch.setattr(stacks, "SHARE", folder)
    return folder


@pytest.fixture
def app(tmp_path: Path) -> Path:
    """A project with a stack, on main, with one commit."""
    repo = tmp_path / "Coaster Ranker"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "Test")
    _project(repo, '[project]\nname = "coaster-ranker"\n\n' + RUN)
    (repo / "compose.yaml").write_text("services:\n  web:\n    image: app\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "one")
    return repo


class Docker:
    """``_docker`` replaced: records each call and answers from a script, by command."""

    def __init__(self, answers: dict[str, Result] | None = None) -> None:
        self.calls: list[tuple[list[str], Path, dict[str, str]]] = []
        self.answers = answers or {}

    def __call__(self, args, cwd, env) -> Result:
        self.calls.append((list(args), Path(cwd), dict(env)))
        for word, answer in self.answers.items():
            if word in args:
                return answer
        return Result(0, "", "")


@pytest.fixture
def docker(monkeypatch) -> Docker:
    fake = Docker()
    monkeypatch.setattr(stacks, "_docker", fake)
    return fake


def _ps(*containers: dict[str, Any]) -> Result:
    """``ps --format json`` as Compose v2.21 and later print it: one object a line."""
    return Result(0, "\n".join(json.dumps(c) for c in containers) + "\n", "")


def _container(
    service="web", state="running", health="", code=0, port=8123, **more
) -> dict[str, Any]:
    publishers = [
        {"URL": "0.0.0.0", "TargetPort": 8000, "PublishedPort": port, "Protocol": "tcp"},
        {"URL": "::", "TargetPort": 8000, "PublishedPort": port, "Protocol": "tcp"},
    ]
    return {
        "ID": f"id-{service}",
        "Name": f"coaster-ranker-{service}-1",
        "Service": service,
        "State": state,
        "Health": health,
        "ExitCode": code,
        "Status": more.pop("status", state),
        "CreatedAt": "2026-11-12 09:00:00 +0100 CET",
        "Publishers": publishers if port else [],
        **more,
    }


# --- [run] ----------------------------------------------------------------------------


def test_project_run_is_none_without_a_run_table(tmp_path):
    assert project_run(tmp_path) is None  # no project.toml at all
    assert project_run(_project(tmp_path, '[project]\nname = "x"\n')) is None


def test_project_run_defaults_its_path_to_the_root(tmp_path):
    assert project_run(_project(tmp_path, RUN)) == Run(service="web", path="/")
    found = project_run(_project(tmp_path, '[run]\nservice = "app"\npath = "/home"\n'))
    assert found == Run(service="app", path="/home")


@pytest.mark.parametrize(
    "toml", ['[run]\npath = "/"\n', "run = 3\n", '[run]\nservice = ""\n', "[run\n"]
)
def test_project_run_without_a_service_is_a_config_error(tmp_path, toml):
    with pytest.raises(ConfigError):
        project_run(_project(tmp_path, toml))


# --- stack_for ------------------------------------------------------------------------


def test_stack_for_reads_run_and_the_projects_name(app, share):
    stack = stacks.stack_for(app)
    assert stack == Stack(project="coaster-ranker", repo=app, service="web", path="/")
    assert stack.checkout == share / "run" / "coaster-ranker"
    assert stack.data == share / "data" / "coaster-ranker"
    assert stack.result_file == share / "run" / "coaster-ranker.json"


def test_stack_for_is_none_without_run(app):
    _project(app, '[project]\nname = "coaster-ranker"\n')
    assert stacks.stack_for(app) is None


def test_stack_for_is_none_for_softfield_itself(app, monkeypatch, tmp_path):
    """Softfield runs from ``live``, a checkout of its own repo: never a stack, even with
    ``[run]`` (ADR 46 item 8)."""
    live = tmp_path / "live"
    git(app, "worktree", "add", "-q", "--detach", str(live), "main")
    monkeypatch.setattr(config, "HOME", live)
    assert stacks.stack_for(app) is None
    monkeypatch.setattr(config, "HOME", app)
    assert stacks.stack_for(app) is None


def test_a_project_name_never_leaves_the_run_folder(tmp_path, share):
    """The name becomes a folder and Compose's project: nothing in it climbs out (isolation)."""
    repo = _project(tmp_path, '[project]\nname = "../../Etc Passwd"\n\n' + RUN)
    stack = stacks.stack_for(repo)
    assert stack is not None
    assert stack.project == "etc-passwd"
    assert stack.checkout.parent == share / "run"


# --- state ----------------------------------------------------------------------------


@pytest.fixture
def stack(app, share) -> Stack:
    found = stacks.stack_for(app)
    assert found is not None
    return found


@pytest.mark.parametrize(
    ("containers", "word"),
    [
        ((), "stopped"),
        ((_container(),), "running"),
        ((_container(health="healthy"), _container("db", port=0)), "running"),
        ((_container(state="created"),), "starting"),
        ((_container(health="starting"),), "starting"),
        ((_container(state="restarting"),), "starting"),  # inspect: restarted 3 times
        ((_container(state="exited", code=1),), "crashed"),
        ((_container(), _container("db", state="exited", code=2, port=0)), "crashed"),
        ((_container(health="unhealthy"),), "crashed"),
        ((_container(state="exited", code=0), _container("db", "exited", code=143)), "stopped"),
    ],
)
def test_state_words_come_out_of_ps(stack, docker, containers, word):
    docker.answers = {"ps": _ps(*containers), "inspect": Result(0, "3\n", "")}
    assert stacks.state(stack).word == word


def test_state_reads_ps_printed_as_one_array(stack, docker):
    """Compose before 2.21 prints one JSON array."""
    docker.answers = {"ps": Result(0, json.dumps([_container()]), "")}
    assert stacks.state(stack).word == "running"


def test_state_gives_the_main_services_published_port(stack, docker):
    docker.answers = {"ps": _ps(_container("db", port=5432), _container(port=8142))}
    found = stacks.state(stack)
    assert (found.word, found.url_port) == ("running", 8142)


def test_a_crash_says_which_container_and_how(stack, docker):
    status = "Exited (3) 2 minutes ago"
    docker.answers = {"ps": _ps(_container(state="exited", code=3, status=status))}
    found = stacks.state(stack)
    assert found.word == "crashed"
    assert "coaster-ranker-web-1" in found.detail and status in found.detail


def test_restarts_are_counted_by_inspecting_the_container(stack, docker):
    """``ps`` doesn't say how often Docker restarted it; ``inspect`` of its id does."""
    docker.answers = {
        "ps": _ps(_container(state="restarting")),
        "inspect": Result(0, "7\n", ""),
    }
    assert stacks.state(stack).word == "crashed"
    assert docker.calls[-1][0] == ["inspect", "--format", "{{.RestartCount}}", "id-web"]


def _checkout(stack: Stack) -> str:
    stack.checkout.parent.mkdir(parents=True, exist_ok=True)
    git(stack.repo, "worktree", "add", "-q", "--detach", str(stack.checkout), "main")
    return git(stack.checkout, "rev-parse", "HEAD").strip()


def _result(stack: Stack, commit: str, ok: bool) -> None:
    record = {"commit": commit, "ok": ok, "at": "2026-11-12T09:30:00", "tail": "build: no"}
    stack.result_file.write_text(json.dumps(record), encoding="utf-8")


def test_a_failed_update_of_the_checkouts_commit_wins_over_the_containers(stack, docker):
    commit = _checkout(stack)
    _result(stack, commit, ok=False)
    docker.answers = {"ps": _ps(_container())}
    found = stacks.state(stack)
    assert found.word == "update failed"
    assert "build: no" in found.detail
    assert found.since == "2026-11-12T09:30:00"
    assert found.url_port == 8123  # the old containers still serve


def test_a_failed_update_carries_the_commit_it_failed_on(stack, docker):
    commit = _checkout(stack)
    docker.answers = {"ps": _ps(_container())}
    assert stacks.state(stack).commit == ""
    _result(stack, commit, ok=False)
    assert stacks.state(stack).commit == commit


def test_services_are_the_names_compose_prints(stack, docker):
    docker.answers = {"--services": Result(0, "web\ndb\n\n", "")}
    assert stacks.services(stack) == ["web", "db"]
    args = docker.calls[-1][0]
    assert args[:3] == ["compose", "-p", stack.project]
    assert args[3:] == ["config", "--services"]


def test_services_are_empty_when_docker_fails(stack, docker):
    docker.answers = {"--services": Result(1, "", "no such file")}
    assert stacks.services(stack) == []


def test_services_drop_anything_that_is_not_a_service_name(stack, docker):
    docker.answers = {"--services": Result(0, "web\n--since=0\nweb db\n../x\n", "")}
    assert stacks.services(stack) == ["web"]


def test_an_old_or_good_update_result_says_nothing(stack, docker):
    commit = _checkout(stack)
    docker.answers = {"ps": _ps(_container())}
    _result(stack, "0" * 40, ok=False)
    assert stacks.state(stack).word == "running"
    _result(stack, commit, ok=True)
    assert stacks.state(stack).word == "running"


@pytest.mark.parametrize(
    "answer",
    [
        Result(127, "", "docker is not installed on this machine"),
        Result(1, "", "permission denied while trying to connect to the Docker daemon socket"),
    ],
)
def test_docker_missing_or_refused_is_a_state_not_an_exception(stack, docker, answer):
    docker.answers = {"ps": answer}
    found = stacks.state(stack)
    assert found.word == "no docker"
    assert answer.err in found.detail


def test_the_real_docker_missing_is_a_result(monkeypatch, tmp_path):
    """``_docker`` itself turns a missing binary into a result, so `state` can say so."""

    def missing(*args, **kwargs):
        raise FileNotFoundError("docker")

    monkeypatch.setattr(subprocess, "run", missing)
    found = stacks._docker(["compose", "version"], tmp_path, {})
    assert found.code != 0 and "not installed" in found.err


# --- start, stop, logs ----------------------------------------------------------------


def test_start_makes_the_checkout_at_main_then_brings_the_stack_up(stack, docker):
    main = git(stack.repo, "rev-parse", "main").strip()
    stacks.start(stack)
    assert git(stack.checkout, "rev-parse", "HEAD").strip() == main
    assert git(stack.checkout, "branch", "--show-current").strip() == ""  # detached
    assert stack.data.is_dir()
    args, cwd, env = docker.calls[-1]
    assert args == ["compose", "-p", "coaster-ranker", "up", "-d", "--build"]
    assert cwd == stack.checkout
    assert env["APP_DATA"] == str(stack.data)


def test_start_keeps_an_existing_checkout(stack, docker):
    _checkout(stack)
    git(stack.repo, "commit", "-q", "--allow-empty", "-m", "two")
    before = git(stack.checkout, "rev-parse", "HEAD")
    stacks.start(stack)
    assert git(stack.checkout, "rev-parse", "HEAD") == before  # following main is f239-02's


def test_every_compose_call_carries_the_project_and_its_data(stack, docker):
    docker.answers = {"ps": _ps(_container())}
    stacks.start(stack)
    stacks.state(stack)
    stacks.logs(stack)
    stacks.logs(stack, service="db", lines=30)
    stacks.stop(stack)
    compose = [call for call in docker.calls if call[0][0] == "compose"]
    assert len(compose) == 5
    for args, cwd, env in compose:
        assert args[:3] == ["compose", "-p", "coaster-ranker"]
        assert cwd == stack.checkout
        assert env["APP_DATA"] == str(stack.data)
    assert [c[0][3:] for c in compose] == [
        ["up", "-d", "--build"],
        ["ps", "--all", "--format", "json"],
        ["logs", "--no-color", "--tail", "200"],
        ["logs", "--no-color", "--tail", "30", "db"],
        ["stop"],
    ]


def test_a_failed_compose_command_is_a_plain_error(stack, docker):
    docker.answers = {"up": Result(1, "", "line one\nservice web: build failed")}
    with pytest.raises(stacks.StackError, match="build failed"):
        stacks.start(stack)


def test_logs_give_the_output_or_the_error(stack, docker):
    docker.answers = {"logs": Result(0, "web-1  | hello\n", "")}
    assert stacks.logs(stack) == "web-1  | hello\n"
    docker.answers = {"logs": Result(1, "", "no such service: nope")}
    assert "no such service" in stacks.logs(stack, service="nope")


@pytest.mark.parametrize("service", ["-f", "--since=0", "web db", "", "../x"])
def test_logs_take_a_service_name_only(stack, docker, service):
    """The logs page passes ``?service=`` on: it never becomes an option (isolation)."""
    with pytest.raises(ValueError, match="not a service name"):
        stacks.logs(stack, service=service)
    assert docker.calls == []


def test_the_lines_asked_for_stay_a_number_in_bounds(stack, docker):
    stacks.logs(stack, lines=10**9)
    stacks.logs(stack, lines=-5)
    assert [c[0][-1] for c in docker.calls] == [str(stacks.MAX_LINES), "1"]


def test_a_held_lock_gives_up_with_a_plain_error(stack, docker, monkeypatch):
    """The runner and the dashboard never run two Compose commands at once on one project."""
    monkeypatch.setattr(stacks, "LOCK_WAIT", 0.2)
    with stacks._locked(stack), pytest.raises(stacks.StackError, match="busy"):
        stacks.stop(stack)
    assert docker.calls == []
    stacks.stop(stack)  # free again
    assert docker.calls[-1][0][-1] == "stop"


# --- follow main ------------------------------------------------------------------------


def _moves_main(stack: Stack, name: str = "two") -> str:
    git(stack.repo, "commit", "-q", "--allow-empty", "-m", name)
    return git(stack.repo, "rev-parse", "main").strip()


def _ups(docker: Docker) -> list[list[str]]:
    return [args for args, _, _ in docker.calls if "up" in args]


def _record(stack: Stack) -> dict[str, Any]:
    record: dict[str, Any] = json.loads(stack.result_file.read_text(encoding="utf-8"))
    return record


def test_main_moving_moves_a_running_checkout_and_rebuilds_once(stack, docker):
    _checkout(stack)
    docker.answers = {"ps": _ps(_container())}
    main = _moves_main(stack)
    assert stacks.follow_main(stack) is True
    assert git(stack.checkout, "rev-parse", "HEAD").strip() == main
    assert _ups(docker) == [["compose", "-p", "coaster-ranker", "up", "-d", "--build"]]
    assert _record(stack)["ok"] is True and _record(stack)["commit"] == main
    assert stacks.follow_main(stack) is False  # already at main: nothing more
    assert len(_ups(docker)) == 1


def test_a_failed_build_says_update_failed_with_the_tail_while_old_containers_answer(stack, docker):
    _checkout(stack)
    lines = "\n".join(f"step {n}" for n in range(60))
    docker.answers = {"--build": Result(1, lines, "boom"), "ps": _ps(_container())}
    main = _moves_main(stack)
    stacks.follow_main(stack)  # never raises
    record = _record(stack)
    assert record["ok"] is False and record["commit"] == main
    assert record["tail"].splitlines()[-1] == "boom"
    assert len(record["tail"].splitlines()) <= 40
    found = stacks.state(stack)
    assert found.word == "update failed" and found.url_port == 8123


def test_a_rebuild_copies_the_data_and_keeps_three_copies(stack, docker):
    _checkout(stack)
    docker.answers = {"ps": _ps(_container())}
    stack.data.mkdir(parents=True)
    (stack.data / "db.sqlite").write_text("rows", encoding="utf-8")
    mains = []
    for name in ("two", "three", "four", "five"):
        mains.append(_moves_main(stack, name))
        stacks.follow_main(stack)
    copies = sorted(p.name for p in stack.data.parent.glob("coaster-ranker.before-*"))
    assert copies == sorted(f"coaster-ranker.before-{m[:12]}" for m in mains[1:])
    newest = stack.data.parent / f"coaster-ranker.before-{mains[-1][:12]}"
    assert (newest / "db.sqlite").read_text(encoding="utf-8") == "rows"


def test_a_failed_copy_never_calls_up(stack, docker, monkeypatch):
    _checkout(stack)
    docker.answers = {"ps": _ps(_container())}

    def broken(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(shutil, "copytree", broken)
    main = _moves_main(stack)
    stacks.follow_main(stack)
    assert _ups(docker) == []
    record = _record(stack)
    assert record["ok"] is False and "disk full" in record["tail"] and record["commit"] == main


def test_a_stopped_apps_checkout_follows_main_and_nothing_starts(stack, docker):
    _checkout(stack)
    docker.answers = {"ps": _ps()}
    main = _moves_main(stack)
    assert stacks.follow_main(stack) is True
    assert git(stack.checkout, "rev-parse", "HEAD").strip() == main
    assert _ups(docker) == []
    assert not stack.result_file.exists()


def test_a_stopped_app_after_a_failed_update_says_stopped(stack, docker):
    """Stop is how the owner clears a failed update: it leaves Needs you (f239-07)."""
    commit = _checkout(stack)
    _result(stack, commit, ok=False)
    docker.answers = {"ps": _ps(_container(state="exited", code=0))}
    assert stacks.state(stack).word == "stopped"


def test_a_start_after_a_failed_update_builds_and_clears_it(stack, docker):
    """Run builds main's image (a stopped app's checkout moved without one), and a start that
    works is main's good result."""
    commit = _checkout(stack)
    _result(stack, commit, ok=False)
    stacks.start(stack)
    assert _ups(docker) == [["compose", "-p", "coaster-ranker", "up", "-d", "--build"]]
    assert _record(stack)["ok"] is True and _record(stack)["commit"] == commit
    docker.answers = {"ps": _ps(_container())}
    assert stacks.state(stack).word == "running"


def test_without_a_checkout_follow_main_leaves_it_to_start(stack, docker):
    _moves_main(stack)
    assert stacks.follow_main(stack) is False
    assert not stack.checkout.exists() and docker.calls == []


def test_the_runner_leaves_projects_without_run_and_softfield_alone(app, share, docker):
    from runner import loop

    (app / ".softfield" / "project.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    loop._follow_main(app)
    assert docker.calls == []
    assert stacks.stack_for(app) is None


def test_the_runners_follow_never_raises(app, share, monkeypatch):
    from runner import loop

    def broken(repo):
        raise RuntimeError("bad toml")

    monkeypatch.setattr(stacks, "stack_for", broken)
    loop._follow_main(app)
