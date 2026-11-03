"""Before and after pictures of a card's pages, taken by the runner at the review (ADR 40).

The project's ``[shots]`` says how its app is served. Nothing here may stop a review: a picture
that can't be taken is recorded with its reason in the card's ``shots.json``.

Playwright is a dev dependency, and the installed ``softfield`` has none: the browser runs in a
process of its own, from Softfield's own project (``python -m runner.shots``)."""

import contextlib
import http.client
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import IO
from urllib.parse import urlsplit

from runner import procs
from runner.config import Shots, project_shots
from runner.gitops import Git
from runner.tasks import milestone_file

DATA_ENV = "SOFTFIELD_SHOTS_DATA"
SHOTS_DIR = Path(".softfield") / "var" / "shots"
LIST_FILE = "shots.json"
WIDTHS = {"phone": 390, "wide": 1440}  # px; the height is only the first screen's, full page
HEIGHTS = {"phone": 844, "wide": 900}

PREPARE_LIMIT = 300.0  # seconds
READY_LIMIT = 180.0  # `uv run` in a new worktree builds its .venv first
PAGE_LIMIT = 30_000  # ms, for a page to load
SETTLE_LIMIT = 5_000  # ms, for what a loaded page still fetches; a page that polls may never rest
PICTURE_LIMIT = 60.0  # seconds per picture, for the browser process as a whole
TAIL = 400  # characters of a command's output kept as the reason

TAKEN, NEW, FAILED = "taken", "new", "failed"  # new: the old code answers 404

_SOFTFIELD = Path(__file__).resolve().parents[1]
_BROWSER = ["uv", "run", "--frozen", "python", "-m", "runner.shots"]
_PAGE_RE = re.compile(r"^\s*[-*]\s+`(/[^`]*)`", re.MULTILINE)
_SECTION_RE = re.compile(r"^## Before and after[ \t]*\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)


@dataclass(frozen=True)
class Picture:
    state: str  # TAKEN, NEW or FAILED
    reason: str = ""


@dataclass(frozen=True)
class Wanted:
    file: str
    address: str


class _Failed(Exception):
    """What keeps a tree from being pictured, in plain words."""


def pages(doc_text: str) -> list[str]:
    """The backticked addresses under ``## Before and after``, in order; none without it."""
    section = _SECTION_RE.search(doc_text)
    return _PAGE_RE.findall(section[1]) if section else []


def allowed(method: str, url: str, origin: str) -> bool:
    """The browser's one rule (ADR 40 item 3): GET, to the app being pictured, and nothing else."""
    parts = urlsplit(url)
    return method == "GET" and f"{parts.scheme}://{parts.netloc}" == origin


def picture_file(when: str, width: str, n: int) -> str:
    return f"{when}-{width}-{n}.png"


def _wanted(when: str, addresses: Sequence[str]) -> list[Wanted]:
    return [
        Wanted(picture_file(when, width, n), address)
        for n, address in enumerate(addresses, start=1)
        for width in WIDTHS
    ]


def _width_of(file: str) -> str:
    return file.split("-")[1]


def _failed(wanted: Sequence[Wanted], reason: str) -> dict[str, Picture]:
    return {w.file: Picture(FAILED, reason) for w in wanted}


def _tail(text: str) -> str:
    return text.strip()[-TAIL:]


def _shoot(origin: str, wanted: Sequence[Wanted], folder: Path) -> dict[str, Picture]:
    """Each wanted picture, from the browser's own process."""
    spec = {
        "origin": origin,
        "folder": str(folder),
        "wanted": [[w.file, w.address] for w in wanted],
    }
    code, out, err = procs.run_bounded(
        [*_BROWSER, json.dumps(spec)], _SOFTFIELD, PICTURE_LIMIT * len(wanted)
    )
    if code is None:
        return _failed(wanted, "the browser ran out of time")
    if code != 0:
        return _failed(wanted, f"the browser failed: {_tail(err)}")
    return {file: Picture(**picture) for file, picture in json.loads(out).items()}


def _browse(origin: str, wanted: Sequence[Wanted], folder: Path) -> dict[str, Picture]:
    """In the browser's process. The routes refuse everything but GETs to ``origin``; a redirect
    isn't routed again, so the browser also resolves no name but 127.0.0.1."""
    from playwright.sync_api import Error, Page, Route, WebSocketRoute, sync_playwright

    def guard(route: Route) -> None:
        if allowed(route.request.method, route.request.url, origin):
            route.continue_()
        else:
            route.abort()

    def refuse_socket(socket: WebSocketRoute) -> None:
        socket.close()

    def draw(page: Page, want: Wanted) -> Picture:
        response = page.goto(origin + want.address, timeout=PAGE_LIMIT, wait_until="load")
        if response is None:
            return Picture(FAILED, "no answer")
        if response.status == 404 and want.file.startswith("before-"):
            return Picture(NEW)
        if response.status >= 400:
            return Picture(FAILED, f"it answered {response.status}")
        with contextlib.suppress(Error):
            page.wait_for_load_state("networkidle", timeout=SETTLE_LIMIT)
        page.screenshot(path=folder / want.file, full_page=True, animations="disabled")
        return Picture(TAKEN)

    results: dict[str, Picture] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            args=["--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"]
        )
        for want in wanted:
            width = _width_of(want.file)
            context = browser.new_context(
                viewport={"width": WIDTHS[width], "height": HEIGHTS[width]},
                color_scheme="dark",  # D3; "no-preference" still matches light in Chromium
                service_workers="block",  # a service worker's requests skip the routes
            )
            context.route("**/*", guard)
            context.route_web_socket("**/*", refuse_socket)
            try:
                results[want.file] = draw(context.new_page(), want)
            except Error as exc:
                results[want.file] = Picture(FAILED, _tail(str(exc).split("\n", 1)[0]))
            context.close()
        browser.close()
    return results


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _answers(port: int, address: str) -> bool:
    """Whether the app answers, a sign-in's redirect included. Never follows a redirect, and
    never goes through a proxy: it is the one request the browser's rule doesn't cover."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", address)
        return connection.getresponse().status < 500
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def _output(file: IO[str]) -> str:
    file.seek(0)
    return _tail(file.read())


@contextlib.contextmanager
def _serving(shots: Shots, tree: Path, env: Mapping[str, str]) -> Iterator[str]:
    """The app of ``tree`` on a free port, up, as its origin; stopped with its children after."""
    port = _free_port()
    command = ["sh", "-c", shots.serve.replace("{port}", str(port))]
    with tempfile.TemporaryFile("w+") as output:
        proc, folder = procs._start(command, tree, env, subprocess.DEVNULL, output, output)
        with procs._owned(proc, folder):
            deadline = time.monotonic() + READY_LIMIT
            while not _answers(port, shots.ready):
                code = proc.poll()
                if code is not None:
                    raise _Failed(f"the app stopped with code {code}: {_output(output)}")
                if time.monotonic() >= deadline:
                    raise _Failed(
                        f"the app didn't answer in {READY_LIMIT:.0f} s: {_output(output)}"
                    )
                time.sleep(0.2)
            yield f"http://127.0.0.1:{port}"
        proc.wait()


@contextlib.contextmanager
def _worktree(repo: Path, base: str, where: Path) -> Iterator[Path]:
    git = Git(repo)
    git.run("worktree", "add", "--detach", str(where), base)
    try:
        yield where
    finally:
        git.run("worktree", "remove", "--force", str(where), check=False)
        git.run("worktree", "prune", check=False)


def _pictures(
    shots: Shots, tree: Path, env: Mapping[str, str], wanted: Sequence[Wanted], folder: Path
) -> dict[str, Picture]:
    try:
        with _serving(shots, tree, env) as origin:
            return _shoot(origin, wanted, folder)
    except Exception as exc:  # a failing picture never stops the review (D6)
        return _failed(wanted, str(exc))


def _round(
    repo: Path,
    shots: Shots,
    base: str,
    after: Sequence[Wanted],
    before: Sequence[Wanted],
    folder: Path,
) -> dict[str, Picture]:
    """Everything a round pictures, on one data folder: the only difference is the code (D2)."""
    with tempfile.TemporaryDirectory(prefix="softfield-shots-", ignore_cleanup_errors=True) as tmp:
        data = Path(tmp) / "data"
        data.mkdir()
        env = {**os.environ, DATA_ENV: str(data)}
        code, out, err = procs.run_bounded(["sh", "-c", shots.prepare], repo, PREPARE_LIMIT, env)
        if code != 0:
            why = "ran out of time" if code is None else f"failed: {_tail(err or out)}"
            return _failed([*after, *before], f"prepare {why}")
        results = _pictures(shots, repo, env, after, folder)
        if before:
            try:
                with _worktree(repo, base, Path(tmp) / "tree") as tree:
                    results |= _pictures(shots, tree, env, before, folder)
            except Exception as exc:  # no start tag, say (D6)
                results |= _failed(before, str(exc))
        return results


def _kept_before(listed: Mapping[str, object], folder: Path) -> dict[str, Picture]:
    """The befores already taken: they stay as they are for as long as the review lasts."""
    kept = {}
    pictures = listed.get("pictures")
    for file, picture in pictures.items() if isinstance(pictures, dict) else ():
        state = picture["state"]
        if file.startswith("before-") and (
            state == NEW or (state == TAKEN and (folder / file).is_file())
        ):
            kept[file] = Picture(state)
    return kept


def _read_list(folder: Path) -> dict[str, object]:
    try:
        listed = json.loads((folder / LIST_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return listed if isinstance(listed, dict) else {}


def _take(repo: Path, key: str, base: str, log: Callable[[str], None]) -> None:
    doc = milestone_file(repo, "cards", key)
    addresses = pages(doc.read_text(encoding="utf-8")) if doc.is_file() else []
    if not addresses:
        return
    shots = project_shots(repo)
    if shots is None:
        return
    folder = repo / SHOTS_DIR / key
    folder.mkdir(parents=True, exist_ok=True)
    listed = _read_list(folder)
    same = listed.get("pages") == addresses and listed.get("base") == base
    kept = _kept_before(listed, folder) if same else {}
    after = _wanted("after", addresses)
    before = [w for w in _wanted("before", addresses) if w.file not in kept]
    for leftover in folder.glob("*.png"):  # a picture that fails now shows no old one
        if leftover.name not in kept:
            leftover.unlink()
    results = _round(repo, shots, base, after, before, folder)
    (folder / LIST_FILE).write_text(
        json.dumps(
            {
                "pages": addresses,
                "base": base,
                "pictures": {f: asdict(p) for f, p in sorted((kept | results).items())},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    taken = sum(p.state == TAKEN for p in results.values())
    failed = sum(p.state == FAILED for p in results.values())
    log(f"Pictures of {key}: {taken} taken, {failed} couldn't be (see {LIST_FILE}).")


def take(repo: Path, key: str, base: str, log: Callable[[str], None]) -> None:
    """The card's pictures for this review round, in ``repo``'s ``.softfield/var/shots/<key>/``:
    the after again, the before once. Nothing to do without ``[shots]`` or a list of pages, and
    whatever goes wrong, the round goes on."""
    try:
        _take(repo, key, base, log)
    except Exception as exc:
        log(f"Pictures of {key}: none, {exc}")


def _main(spec_text: str) -> int:
    """`python -m runner.shots <spec>`: the browser's process (see ``_shoot``)."""
    spec = json.loads(spec_text)
    wanted = [Wanted(file, address) for file, address in spec["wanted"]]
    results = _browse(spec["origin"], wanted, Path(spec["folder"]))
    print(json.dumps({file: asdict(picture) for file, picture in results.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1]))
