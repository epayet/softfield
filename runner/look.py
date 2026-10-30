"""``softfield look``: what a planner or a review job may read (ADR 28). No AI in it.

Three forms, all read-only (``look disk`` says where the disk space went, f175):
- ``look sql "<one SELECT>"`` prints rows of the metrics database. The file is opened
  read-only, and SQLite's authorizer allows reads only: a write, an ``ATTACH`` (which makes a
  file even on a read-only connection) or a ``PRAGMA`` that changes anything is refused by
  SQLite itself, whatever the statement's text looks like.
- ``look page <address>`` prints a dashboard page as plain text, or its data as is when the
  address serves JSON. It asks the dashboard's own app, in this process: no server, no port,
  and only ever a GET, so no form is sent and nothing can be approved or signed off.

Rows, cells and pages are capped, and the output says when it cut.
"""

import getpass
import os
import sqlite3
import warnings
from html.parser import HTMLParser
from pathlib import Path

COMMAND = "softfield look"  # the prefix in a planner's and a review's tool list, no other's
MAX_ROWS = 200
MAX_CELL = 500  # characters of one cell
MAX_PAGE = 40_000  # characters of one page

# What SQLite may do for a look: read rows, call functions, recurse in a WITH. Anything else
# (INSERT, UPDATE, DELETE, CREATE, DROP, ATTACH, DETACH, a transaction…) is denied.
_READS = frozenset(
    {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}
)
# The PRAGMAs that only describe the schema; their argument is a table's or an index's name.
_PRAGMAS = frozenset(
    {
        "table_list",
        "table_info",
        "table_xinfo",
        "index_list",
        "index_info",
        "index_xinfo",
        "foreign_key_list",
    }
)


class LookError(Exception):
    """A look that can't be answered, in one plain line."""


def _reads_only(action: int, first: str | None, *_: str | None) -> int:
    """SQLite's authorizer: asked for each thing a statement would do, as it is compiled."""
    if action in _READS:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_PRAGMA and first in _PRAGMAS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _one_line(text: object) -> str:
    return " ".join(str(text).split())


def _present(db: Path) -> None:
    if not db.is_file():  # asked first: a read-only open never makes one
        raise LookError(f"no metrics database at {db}")


def _cell(value: object) -> tuple[str, bool]:
    """A cell on one line, and whether it was cut."""
    if value is None:
        return "NULL", False
    if isinstance(value, bytes):
        return f"<{len(value)} bytes>", False
    shown = str(value).replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
    shown = shown.replace("\r", "\\r")
    if len(shown) > MAX_CELL:
        return shown[:MAX_CELL] + "…", True
    return shown, False


def sql(db: Path, query: str) -> str:
    """The rows of one SELECT on the metrics database: a line of column names, then a line a
    row, cells apart by a tab. At most ``MAX_ROWS`` rows and ``MAX_CELL`` characters a cell,
    with a last line saying what was cut."""
    from factory_dashboard.queries import connect  # the dashboard's read-only open

    _present(db)
    conn = connect(db)
    try:
        conn.set_authorizer(_reads_only)
        cursor = conn.execute(query)
        names = [column[0] for column in cursor.description or ()]
        rows = cursor.fetchmany(MAX_ROWS + 1)
    except (sqlite3.Error, sqlite3.Warning) as exc:  # two statements in one is a Warning
        raise LookError(f"the query was refused: {_one_line(exc)}") from None
    finally:
        conn.close()
    if not names:
        raise LookError("the query was refused: it gives no rows, and a look only reads")
    lines, cut = ["\t".join(names)], 0
    for row in rows[:MAX_ROWS]:
        cells = [_cell(value) for value in row]
        cut += sum(1 for _, was_cut in cells if was_cut)
        lines.append("\t".join(shown for shown, _ in cells))
    if len(rows) > MAX_ROWS:
        lines.append(f"(cut: the first {MAX_ROWS} rows; there are more)")
    if cut:
        cells_cut = "1 cell" if cut == 1 else f"{cut} cells"
        lines.append(f"(cut: {cells_cut} longer than {MAX_CELL} characters, ending in …)")
    return "\n".join(lines)


# --- where the disk went ----------------------------------------------------------------------

TMP_LABEL = "/tmp, all of it"  # noqa: S108 - a label, not a path used
MAX_HELD = 20  # deleted-but-open files listed; the rest are counted
_TMP_ROOT = "softfield-"  # the runner's own folder in /tmp, then the user id (f175-02)


def _size(path: Path) -> tuple[int, int]:
    """Bytes and files under ``path`` (itself, when a file), links not followed, anything that
    can't be read skipped. A path that isn't there is 0 and 0."""
    total = files = 0
    pending = [path]
    while pending:
        here = pending.pop()
        try:
            info = here.lstat()
            if here.is_symlink() or not here.is_dir():
                total, files = total + info.st_size, files + 1
                continue
            with os.scandir(here) as entries:
                pending.extend(Path(entry.path) for entry in entries)
        except OSError:
            continue
    return total, files


def _amount(size: tuple[int, int]) -> str:
    nbytes, files = size
    shown = f"{nbytes / 1e9:.1f} GB" if nbytes >= 1e9 else f"{nbytes / 1e6:.1f} MB"
    return f"{shown}, {files} files"


def _holding(proc: Path, uid: int) -> list[tuple[int, int, str]]:
    """Files deleted but still open in the user's processes: size, pid, command; the largest
    first. A file held by two descriptors counts once."""
    seen: set[tuple[int, int, int]] = set()
    found: list[tuple[int, int, str]] = []
    try:
        pids = [p for p in proc.iterdir() if p.name.isdigit()]
    except OSError:
        return []
    for pid in pids:
        try:
            if pid.stat().st_uid != uid:
                continue
            links = list((pid / "fd").iterdir())
        except OSError:
            continue
        for link in links:
            try:
                if not os.readlink(link).endswith(" (deleted)"):
                    continue
                info = link.stat()
                key = (int(pid.name), info.st_dev, info.st_ino)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    command = (pid / "comm").read_text().strip()
                except OSError:
                    command = "?"
                found.append((info.st_size, int(pid.name), command))
            except OSError:
                continue
    return sorted(found, reverse=True)


def disk(
    db: Path,
    bench: Path,
    runs: Path,
    *,
    tmp: Path = Path("/tmp"),  # noqa: S108 - the place being measured, never written to
    proc: Path = Path("/proc"),
    uid: int | None = None,
    user: str | None = None,
) -> str:
    """Where the factory's disk space went, a line a place with its size and file count, then
    the deleted files still held open, largest first. Read-only; what can't be read is skipped."""
    uid = os.getuid() if uid is None else uid
    user = user or getpass.getuser()
    try:
        names = sorted(p.name for p in tmp.iterdir())
    except OSError:
        names = []
    # each top-level entry is walked once, then counted in the group that names it
    groups: dict[str, list[int]] = {
        f"{_TMP_ROOT}{uid}": [0, 0, 0],
        f"pytest-of-{user}": [0, 0, 0],
        "Chromium temp folders": [0, 0, 0],
        "Playwright folders": [0, 0, 0],
        "tmp*.sqlite databases": [0, 0, 0],
    }
    everything = [0, 0]
    for name in names:
        nbytes, files = _size(tmp / name)
        everything[0] += nbytes
        everything[1] += files
        if name == f"{_TMP_ROOT}{uid}" or name == f"pytest-of-{user}":
            group = name
        elif name.lstrip(".").startswith(("org.chromium.", "com.google.", "chromium")):
            group = "Chromium temp folders"
        elif name.lstrip(".").startswith("playwright"):
            group = "Playwright folders"
        elif name.startswith("tmp") and name.endswith(".sqlite"):
            group = "tmp*.sqlite databases"
        else:
            continue
        counts = groups[group]
        counts[0], counts[1], counts[2] = counts[0] + nbytes, counts[1] + files, counts[2] + 1
    lines = [f"{TMP_LABEL:32} {_amount((everything[0], everything[1]))}"]
    for group, (nbytes, files, folders) in groups.items():
        label = f"  {group}" + (f" ({folders})" if folders > 1 else "")
        lines.append(f"{label:32} {_amount((nbytes, files))}")
    lines += [
        f"{'the bench folder':32} {_amount(_size(bench))}",
        f"{'.factory/var/runs/':32} {_amount(_size(runs))}",
        f"{'the metrics database':32} {_amount(_size(db))}",
        f"{'its write-ahead log (-wal)':32} {_amount(_size(db.with_name(db.name + '-wal')))}",
    ]
    held = _holding(proc, uid)
    if not held:
        lines.append("deleted files still held open: none")
    else:
        lines.append(f"deleted files still held open: {len(held)}, largest first")
        lines += [
            f"  {_amount((n, 1)).split(',')[0]:>10}  pid {pid}  {cmd}"
            for n, pid, cmd in held[:MAX_HELD]
        ]
        if len(held) > MAX_HELD:
            rest = sum(n for n, _, _ in held[MAX_HELD:])
            lines.append(f"  (and {len(held) - MAX_HELD} more, {_amount((rest, 0)).split(',')[0]})")
    return "\n".join(lines)


# --- a page as text ---------------------------------------------------------------------------

_UNSEEN = frozenset({"script", "style", "template"})  # nothing in them is on the page
# The tags that start a new line; everything else runs on in its line.
_BLOCKS = frozenset(
    {
        *("address", "article", "aside", "blockquote", "br", "caption", "dd", "details"),
        *("dialog", "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form"),
        *("h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav", "ol"),
        *("option", "p", "pre", "section", "summary", "table", "tbody", "td", "tfoot", "th"),
        *("thead", "title", "tr", "ul"),
    }
)


class _Text(HTMLParser):
    """A page's words, a line a block: no tag, script or style, no blank line."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self._line: list[str] = []
        self._unseen = 0

    def _end_line(self) -> None:
        words = " ".join("".join(self._line).split())
        self._line = []
        if words:
            self.lines.append(words)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _UNSEEN:
            self._unseen += 1
        elif tag in _BLOCKS:
            self._end_line()

    def handle_endtag(self, tag: str) -> None:
        if tag in _UNSEEN:
            self._unseen = max(0, self._unseen - 1)
        elif tag in _BLOCKS:
            self._end_line()

    def handle_data(self, data: str) -> None:
        if not self._unseen:
            self._line.append(data)

    def close(self) -> None:
        super().close()
        self._end_line()


def text(html: str) -> str:
    """An HTML page as plain text: its words, without tags, scripts or styles, blank runs
    collapsed."""
    parser = _Text()
    parser.feed(html)
    parser.close()
    return "\n".join(parser.lines)


def page(db: Path, project: str, address: str) -> str:
    """The dashboard's page at ``address`` (``/``, ``/planning``, ``/milestones/f95``, with its
    query if any) over ``db``, showing ``project``: an HTML page as ``text``, a JSON answer as
    is, at most ``MAX_PAGE`` characters. One GET on the dashboard's app in this process, its
    own redirects followed; nothing listens and nothing leaves the machine."""
    with warnings.catch_warnings():  # the import's own warnings aren't the page's words
        warnings.simplefilter("ignore")
        from fastapi.testclient import TestClient  # FastAPI loads only for this command

    from factory_dashboard.app import HOST, create_app

    if not address.startswith("/") or address.startswith("//"):
        raise LookError(f"an address is a page's path, like /planning, not {_one_line(address)!r}")
    _present(db)
    client = TestClient(
        create_app(db, project),
        base_url=f"http://{HOST}",
        raise_server_exceptions=False,  # a page that breaks is one line, not a traceback
        follow_redirects=True,
    )
    # the floor's data address answers JSON when asked for it (`/line/live`)
    response = client.get(address, headers={"accept": "application/json, text/html"})
    if response.status_code >= 400:
        raise LookError(f"no page at {address} (the dashboard answered {response.status_code})")
    kind = response.headers.get("content-type", "")
    shown = text(response.text) if "html" in kind else response.text
    if len(shown) > MAX_PAGE:
        return f"{shown[:MAX_PAGE]}\n(cut: the first {MAX_PAGE} of {len(shown)} characters)"
    return shown
