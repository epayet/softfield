"""Notifications to a closed phone, through ntfy (ADR 31): sent as the runner stores what needs
the owner, saying only its kind and the project, opening the page where the owner acts."""

import socket
import sqlite3
import tomllib
import urllib.request
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from runner import claude, cli, metrics, notify, owner
from runner.agents import JobResult
from runner.state import State
from runner.tasks import append_footer
from tests.runner.conftest import write_task
from tests.runner.test_loop import _plan_message, _run, fake_model  # noqa: F401 - a fixture
from tests.runner.test_owner import _db, _review
from tests.runner.test_requests import NOW, _apply, _ask

HOME = "http://192.168.1.42:8765"


class Sent(list[dict[str, Any]]):
    """What reached ``notify._post``: never the network."""

    def __init__(self) -> None:
        super().__init__()
        self.fail: BaseException | None = None


def _machine(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def sent(tmp_path_factory, monkeypatch) -> Sent:
    """A machine whose settings name a topic; each post recorded, or failing as set."""
    machine = _machine(
        tmp_path_factory.mktemp("machine") / "factory.toml",
        '[notify]\nntfy = "https://ntfy.sh/abc"\n',
    )
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    monkeypatch.setattr(notify, "lan_ip", lambda: "192.168.1.42")
    posts = Sent()

    def post(address: str, body: bytes, headers: dict[str, str]) -> None:
        if posts.fail is not None:
            raise posts.fail
        posts.append({"address": address, "body": body.decode(), **headers})

    monkeypatch.setattr(notify, "_post", post)
    return posts


# --- the lead's reply (runner/loop.py) -----------------------------------------------------


@pytest.mark.usefixtures("fake_model")
def test_a_leads_reply_on_a_card_sends_that_the_lead_answered(repo, sent, monkeypatch):
    _plan_message(repo, "f7", "When will the secret board be done?")
    monkeypatch.setattr(
        claude,
        "run_claude",
        lambda *a, **k: JobResult(ok=True, text="Private answer.", duration_s=1.0, session_id="s"),
    )
    report = _run(repo)
    [one] = sent
    assert one == {
        "address": "https://ntfy.sh/abc",
        "body": f"{repo.name} · The lead answered you",
        "Title": repo.name,
        "Click": f"{HOME}/planning/f7?project={repo.name}",
    }
    assert not [n for n in report.notes if n.startswith(notify.NOT_SENT)]


@pytest.mark.usefixtures("fake_model")
def test_each_reply_sends_though_its_item_is_still_open(repo, sent, monkeypatch):
    _plan_message(repo, "f7", "One?")
    _plan_message(repo, "f7", "Two?")
    monkeypatch.setattr(
        claude, "run_claude", lambda *a, **k: JobResult(ok=True, text="Yes.", duration_s=1.0)
    )
    _run(repo)
    assert [s["body"] for s in sent] == [f"{repo.name} · The lead answered you"] * 2


@pytest.mark.usefixtures("fake_model")
def test_a_failed_or_slow_request_is_one_report_note_and_the_job_goes_on(repo, sent, monkeypatch):
    sent.fail = TimeoutError("timed out")
    _plan_message(repo, "f7", "Hello?")
    monkeypatch.setattr(
        claude, "run_claude", lambda *a, **k: JobResult(ok=True, text="Hi.", duration_s=1.0)
    )
    report = _run(repo)
    notes = [n for n in report.notes if n.startswith(notify.NOT_SENT)]
    assert notes == [f"{notify.NOT_SENT} (TimeoutError: timed out)."]
    conn = metrics.open_db(repo / "var" / "factory-metrics.sqlite")
    try:
        texts = [r["text"] for r in conn.execute("SELECT text FROM planner_messages")]
    finally:
        conn.close()
    assert any(str(t).startswith("Hi.") for t in texts)  # the reply was stored all the same


def test_the_post_has_a_5_second_limit(monkeypatch):
    seen: dict[str, Any] = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            pass

        def read(self) -> bytes:
            return b""

    def urlopen(request, timeout):
        seen.update(timeout=timeout, method=request.get_method(), url=request.full_url)
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    notify._post("https://ntfy.sh/abc", b"x", {})
    assert seen == {"timeout": 5, "method": "POST", "url": "https://ntfy.sh/abc"}


# --- a verdict's items (runner/owner.py) ---------------------------------------------------


def _blocked(repo: Path, task_id: str = "m1-04-thing") -> None:
    path = write_task(repo / ".factory" / "tasks" / "blocked", task_id)
    append_footer(path, {"result": "blocked", "reason": "a secret reason"})


def test_a_verdict_raising_two_things_on_one_card_sends_one(repo, sent):
    _blocked(repo)
    code, _ = owner.verdict(repo, "m1", State(), "adr-needed", db=_db(repo))
    assert code == 2
    [one] = sent
    assert one["body"] == f"{repo.name} · 2 things need you on one card"
    assert one["Click"] == f"{HOME}/planning/m1?project={repo.name}"


def test_an_open_item_stored_again_sends_nothing_and_a_resolved_one_opening_again_sends(repo, sent):
    owner.verdict(repo, "m1", State(), "adr-needed", db=_db(repo))
    assert [s["body"] for s in sent] == [f"{repo.name} · A review stopped"]
    assert sent[0]["Click"] == f"{HOME}/planning/m1?project={repo.name}"
    owner.verdict(repo, "m1", State(), "adr-needed", db=_db(repo))  # a verdict rerun
    assert len(sent) == 1
    conn = sqlite3.connect(_db(repo))
    conn.execute("UPDATE owner_items SET resolved = '2026-10-01'")
    conn.commit()
    conn.close()
    owner.verdict(repo, "m1", State(), "adr-needed", db=_db(repo))
    assert len(sent) == 2


def test_a_card_ready_for_sign_off_opens_its_thread(repo, sent):
    _review(repo)
    owner.verdict(repo, "m1", State(), "clean", db=_db(repo))
    [one] = sent
    assert one["body"] == f"{repo.name} · A card is ready for your sign-off"
    assert one["Click"] == f"{HOME}/planning/m1?project={repo.name}"


@pytest.mark.parametrize("kind", ["adr", "escalated", "blocked"])
def test_a_tickets_decision_opens_the_overview(repo, sent, kind):
    state = State()
    if kind == "blocked":
        _blocked(repo)
    else:
        write_task(repo / ".factory" / "tasks" / "escalated", "m1-02-photos")
    if kind == "adr":
        state.owner = {"m1-02-photos": {"adr": ".factory/adr/14-photos.md", "question": "Keep?"}}
    owner.verdict(repo, "m1", state, "clean", db=_db(repo))
    [one] = sent
    assert one["body"] == f"{repo.name} · A ticket needs your decision"
    assert one["Click"] == f"{HOME}/?project={repo.name}"


def test_a_verdicts_notification_that_failed_is_a_line_of_the_verdict(repo, sent):
    sent.fail = OSError("no network")
    code, text = owner.verdict(repo, "m1", State(), "adr-needed", db=_db(repo))
    assert code == 2
    assert text.rstrip().endswith(f"Note: {notify.NOT_SENT} (OSError: no network).")


# --- the reserve switch going off (runner/requests.py) -------------------------------------


def test_the_reserve_switch_going_off_sends_once(repo, sent):
    _ask(repo, "queue", "m4-12-none")  # the project
    state = State(switches={"week": (NOW - timedelta(hours=24)).isoformat()})
    _apply(repo, state)
    [one] = sent
    assert one["body"] == f"{repo.name} · Claude's reserve: your choice"
    assert one["Click"] == f"{HOME}/?project={repo.name}"
    _apply(repo, state)
    assert len(sent) == 1


def test_the_reserve_switchs_failed_notification_is_a_line(repo, sent):
    sent.fail = OSError("down")
    _ask(repo, "queue", "m4-12-none")
    lines = _apply(repo, State(switches={"week": (NOW - timedelta(hours=24)).isoformat()}))
    assert f"{notify.NOT_SENT} (OSError: down)." in lines


# --- what a notification never says, and when it isn't sent --------------------------------


def test_no_title_text_or_reply_is_in_any_notification(repo, sent):
    _blocked(repo)
    write_task(repo / ".factory" / "tasks" / "escalated", "m1-02-photos")
    state = State(owner={"m1-02-photos": {"adr": ".factory/adr/14-photos.md", "question": "Q?"}})
    owner.verdict(repo, "m1", state, "adr-needed", db=_db(repo))
    owner.verdict(repo, "m2", State(), "adr-needed", db=_db(repo))
    assert sent
    for one in sent:
        said = " ".join(str(v) for v in one.values())
        for private in ("secret", "Q?", "photos", "adr-needed", "m1-04", "Milestone"):
            assert private not in said


def test_with_no_notify_section_nothing_is_sent_or_reported(repo, tmp_path, monkeypatch):
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(_machine(tmp_path / "f.toml", "[metrics]\n")))
    monkeypatch.setattr(notify, "_post", lambda *a: pytest.fail("sent"))
    code, text = owner.verdict(repo, "m1", State(), "adr-needed", db=_db(repo))
    assert code == 2 and "Note:" not in text
    assert notify.to_owner("p", "x", "/") is None


def test_the_metrics_database_has_no_table_of_notifications(tmp_path):
    """Item 4: the owner item is the one record; nothing about the sending is kept."""
    conn = metrics.open_db(tmp_path / "m.sqlite")
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    assert not [t for t in tables if "notif" in t]


def test_the_home_address_falls_back_on_this_machine(monkeypatch):
    def no_route() -> str:
        raise OSError("no route")

    monkeypatch.setattr(notify, "lan_ip", no_route)
    assert notify._home() == "http://127.0.0.1:8765"


def test_only_a_web_address_is_posted_to(tmp_path, monkeypatch):
    machine = _machine(tmp_path / "f.toml", '[notify]\nntfy = "file:///etc/passwd"\n')
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    monkeypatch.setattr(notify, "_post", lambda *a: pytest.fail("posted"))
    assert notify.send("p", "x", "/") == f"{notify.NOT_SENT}: [notify] ntfy is no web address."


def test_the_lan_ip_sends_no_packet(monkeypatch):
    class Udp:
        def __init__(self, family: int, kind: int) -> None:
            assert (family, kind) == (socket.AF_INET, socket.SOCK_DGRAM)

        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            pass

        def connect(self, address: tuple[str, int]) -> None:
            pass

        def getsockname(self) -> tuple[str, int]:
            return ("10.0.0.5", 4000)

    monkeypatch.setattr(socket, "socket", Udp)
    assert notify.lan_ip() == "10.0.0.5"


# --- `softfield notify setup` and `test` ---------------------------------------------------


def test_setup_writes_the_section_once_and_keeps_every_other_line(tmp_path, monkeypatch, capsys):
    before = '# my machine\n[metrics]\ndb = "/x.sqlite"  # kept\n\n[roles]\nlead = ["opus"]\n'
    machine = _machine(tmp_path / "factory.toml", before)
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    assert cli.main(["notify", "setup"]) == 0
    after = machine.read_text()
    assert after.startswith(before)
    address = tomllib.loads(after)["notify"]["ntfy"]
    topic = address.removeprefix("https://ntfy.sh/")
    assert len(topic) == 24 and topic.isalnum() and topic == topic.lower()
    assert topic in capsys.readouterr().out
    assert cli.main(["notify", "setup"]) == 0
    assert machine.read_text() == after
    assert topic in capsys.readouterr().out


def test_setup_makes_the_file_and_adds_the_address_to_a_bare_section(tmp_path, monkeypatch):
    machine = tmp_path / "new" / "factory.toml"
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(machine))
    first, written = notify.setup(machine)
    assert written and tomllib.loads(machine.read_text())["notify"]["ntfy"].endswith(first)
    machine.write_text("[notify]\n\n[metrics]\n")
    topic, written = notify.setup(machine)
    data = tomllib.loads(machine.read_text())
    assert written and data["notify"]["ntfy"] == f"https://ntfy.sh/{topic}" and "metrics" in data
    assert topic != first


def test_setup_fills_an_empty_address_and_keeps_the_file_readable(tmp_path):
    """F142 review F4: a second ``ntfy`` key would make the whole machine file unreadable."""
    machine = _machine(tmp_path / "factory.toml", '[notify]\nntfy = ""\n\n[other]\nntfy = "x"\n')
    topic, written = notify.setup(machine)
    data = tomllib.loads(machine.read_text())
    assert written and data["notify"]["ntfy"] == f"https://ntfy.sh/{topic}"
    assert data["other"] == {"ntfy": "x"}


def test_notify_test_says_whether_ntfy_took_it(sent, capsys):
    assert cli.main(["notify", "test"]) == 0
    [one] = sent
    assert one["body"] == "softfield · Notifications work"
    assert "took it" in capsys.readouterr().out
    sent.fail = OSError("refused")
    assert cli.main(["notify", "test"]) == 1
    assert "didn't take it" in capsys.readouterr().out


def test_notify_test_without_a_setting_says_to_set_it_up(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(tmp_path / "none.toml"))
    assert cli.main(["notify", "test"]) == 1
    assert "softfield notify setup" in capsys.readouterr().out
