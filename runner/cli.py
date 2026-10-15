"""``softfield``: the deterministic build runner. No AI in here; see docs/workflow.md."""

import argparse
import os
import socket
import subprocess
import sys
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

from runner import (
    backfill,
    bench,
    checks,
    config,
    copilot,
    i18n,
    look,
    loop,
    metrics,
    owner,
    procs,
    report,
    requests,
    setup,
)
from runner.config import (
    PROJECT_TOML,
    Config,
    ConfigError,
    load_config,
    machine_metrics_db,
    project_name,
)
from runner.gates import layout_problems
from runner.gitops import Git, GitError
from runner.loop import RunnerError, local_agent, run_session
from runner.milestone import (
    PARKED,
    RESTART,
    milestone_metrics,
    milestone_summary,
    review_milestone,
    run_due_review,
    run_milestone,
)
from runner.requests import ticket_problems
from runner.state import load_state, save_state
from runner.tasks import TaskError, milestone_arg


def _here() -> Path | None:
    """The project this folder is in: the nearest with a ``.factory/project.toml``."""
    here = Path.cwd()
    return next((c for c in (here, *here.parents) if (c / PROJECT_TOML).is_file()), None)


def _repo() -> Path:
    if (repo := _here()) is None:
        raise SystemExit("run this inside a project: no .factory/project.toml here or above")
    return repo


def _lan_address() -> str:
    """This machine's home-network address, for `runner dashboard --lan` (f5-03): the source
    address of a UDP socket "connected" to a public IP. A UDP connect only picks the route;
    it sends nothing."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            udp.connect(("1.1.1.1", 80))
            return str(udp.getsockname()[0])
    except OSError as exc:
        raise RunnerError(f"no home-network address found ({exc}); give --host instead") from exc


def _today() -> date:
    return datetime.now().astimezone().date()


RESTARTED_ENV = "COUCOU_RUNNER_RESTARTED"  # set by `_restart` for the process it starts


def _switch_request(cfg: Config, switch: str, value: str) -> None:
    """`runner reserve` and `runner run --use-reserve`: the request the dashboard's switch
    writes (ADR 22 item 4), so both go by the same code. The command applies it at once
    (`_apply_requests`), unless a run is live: that run applies it at its next pick."""
    _request(cfg, requests.RESERVE, switch, value)


def _request(cfg: Config, kind: str, subject: str | None, value: str | None) -> None:
    """The owner's request as the dashboard writes it, for a console command."""
    conn = metrics.open_db(cfg.metrics_db)
    try:
        project = metrics.upsert_project(conn, cfg.project_name, repo=str(cfg.repo))
        metrics.add_request(conn, project, kind, subject, value, loop.now().isoformat())
    finally:
        conn.close()


def _restart() -> None:
    """Carry on in a fresh process: Claude changed runner/, and Python keeps the old modules.
    The switches are in state.json, so nothing else is handed on."""
    print("runner: the runner's code changed; restarting.", flush=True)
    argv_again = [sys.executable, "-m", "runner.cli", *sys.argv[1:]]
    env = dict(os.environ)
    env[RESTARTED_ENV] = "1"  # so `--use-reserve` doesn't start its 24 hours again
    os.execve(sys.executable, argv_again, env)  # noqa: S606 - our own interpreter and args


_UNLOADED: set[str] = set()  # projects whose project.toml didn't load, said once


def _project_configs() -> list[Config]:
    """The registered projects the runner works on, in the owner's order: not paused, with a
    ``.factory/project.toml`` that loads (ADR 30 item 6). One that doesn't load is said."""
    db = machine_metrics_db()
    if not db.is_file():
        return []
    conn = metrics.open_db(db)
    try:
        rows = metrics.projects_in_order(conn)
    finally:
        conn.close()
    configs = []
    for row in rows:
        repo = Path(row.repo) if row.repo else None
        if row.paused or repo is None or not (repo / PROJECT_TOML).is_file():
            continue
        try:
            configs.append(load_config(repo))
        except (OSError, ValueError, KeyError, ConfigError) as exc:
            if row.name not in _UNLOADED:  # once, not every round
                _UNLOADED.add(row.name)
                print(f"runner: {row.name}'s {PROJECT_TOML} doesn't load ({exc}): skipped")
            continue
        _UNLOADED.discard(row.name)
    return configs


GUIDE = """
Run
  softfield run                  every project, in the Projects page's order (Ctrl-C stops it)
  softfield run --here           only this folder's project
  softfield run --dry-run        what would run next, per project
Dashboard
  softfield dashboard --lan      serve it on the home Wi-Fi; it opens on /projects
  softfield dashboard update     bring it to Softfield's latest main now
Projects
  softfield init                 set up this folder as a project, then Claude finishes with you
  softfield doctor               what a project still needs; passing hands it to the runner
  softfield accept N | reject N  an ADR, in its project's folder
  softfield forget <name>        take a project off the list (its folder stays)
  softfield signoff <key>        sign a milestone off, in its project's folder
Always on
  softfield service install      systemd units for the runner and the dashboard
All commands: softfield --help"""


def _guide() -> int:
    """A bare `softfield`: whether a runner runs, the projects in order, and the commands."""
    configs = _project_configs()
    running = [cfg.project_name for cfg in configs if loop.live_run(cfg) is not None]
    try:
        head = Git(config.HOME).head()[:9]
    except GitError:
        head = "a folder outside git"
    print(f"Softfield on {head} ({config.HOME})")
    print("Runner: " + (f"running ({', '.join(running)})" if running else "not running"))
    db = machine_metrics_db()
    rows = []
    if db.is_file():
        conn = metrics.open_db(db)
        try:
            rows = metrics.projects_in_order(conn)
        finally:
            conn.close()
    if rows:
        print("Projects, in order:")
        for place, row in enumerate(rows, start=1):
            note = f"  ({row.paused})" if row.paused else ""
            print(f"  {place}. {row.name}  {row.repo or ''}{note}")
    else:
        print("No project yet: set one up in its folder with `softfield init`.")
    print(GUIDE)
    return 0


def _forget(name: str, db: Path, *, ask: bool) -> int:
    """`softfield forget <name>`: off the Projects page and the runner's list. Its folder stays
    (delete it yourself); its history stays in the database, so past numbers still add up."""
    conn = metrics.open_db(db)
    try:
        row = next((p for p in metrics.projects_in_order(conn) if p.name == name), None)
        if row is None:
            print(f"softfield: no project {name}")
            return 1
        if ask:
            answer = input(f"Forget {name} ({row.repo})? Its folder stays. [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                return 1
        metrics.set_project_paused(conn, name, metrics.FORGOTTEN)
    finally:
        conn.close()
    print(f"{name}: forgotten. Its folder stays: {row.repo}")
    return 0


def _machine_command(args: argparse.Namespace) -> int:
    """The commands that need no project: `init` makes one, `service` serves them all, and
    `dashboard` outside a project opens on the first in the owner's order (ADR 30)."""
    db = machine_metrics_db()
    if args.command == "init":
        folder = Path.cwd()
        try:
            origin, written = setup.init(folder, db)
        except (setup.SetupError, GitError) as exc:
            print(f"softfield: {exc}")
            return 1
        kind = "a new" if origin == "new" else "an existing"
        print(f"{folder.name}: set up as {kind} project, registered, committed.")
        print("Wrote " + ", ".join(written) + ".")
        if args.no_claude:
            print(f"Next: open Claude here and follow {setup.bootstrap()}.")
            return 0
        print("\n" + setup.NEXT + "\n")
        command = setup.claude_command(folder, origin)
        os.execvp(command[0], command)  # noqa: S606 - the owner's Claude, in their terminal
    if args.command == "forget":
        return _forget(args.name, db, ask=not args.yes)
    if args.command == "dashboard" and args.action == "update":
        source = loop.softfield_repo()
        if source is None:
            print("softfield: this install isn't a checkout of Softfield's repo: nothing to follow")
            return 1
        moved = loop.update_live(source)
        head = Git(config.HOME).head()[:9]
        if moved:
            print(f"The dashboard moves to Softfield's main ({head}) and reloads in a few seconds;")
            print("a running runner restarts on the same code at its next pick.")
        else:
            print(f"The dashboard is on Softfield's main already ({head}).")
        return 0
    if args.command == "service":
        units = Path.home() / ".config" / "systemd" / "user"
        for path in setup.install_units(units, Path.home()):
            print(f"Wrote {path}")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        print("Start them, and at every boot:")
        print("  systemctl --user enable --now softfield-runner softfield-dashboard")
        print("Their logs: journalctl --user -u softfield-runner -f")
        print("To keep them up while you're logged out: loginctl enable-linger $USER")
        return 0
    conn = metrics.open_db(db)  # the dashboard, outside any project
    try:
        first = next(iter(metrics.projects_in_order(conn)), None)
    finally:
        conn.close()
    if first is None:
        print("runner: no project yet: set one up in its folder with `softfield init`")
        return 1
    return _serve_dashboard(args, args.db or db, first.name)


def _serve_dashboard(args: argparse.Namespace, db: Path, project: str) -> int:
    if not db.is_file():
        raise RunnerError(f"no metrics database at {db}; `softfield backfill` makes one")
    host = _lan_address() if args.lan else args.host or "127.0.0.1"
    from factory_dashboard import app  # FastAPI loads only for this command

    print(f"The factory dashboard: http://{host}:{args.port}/projects (Ctrl-C stops it)")
    if args.lan:
        print("Open that address on your phone, on the same Wi-Fi.")
    app.serve(db, project, port=args.port, host=host)
    return 0


def _run_projects(args: argparse.Namespace, restarted: bool) -> int:
    """`softfield run`: every project, from any folder (ADR 30 item 6)."""
    configs = _project_configs()
    if not configs:
        print("runner: no project to run: set one up in its folder with `softfield init`")
        return 1
    if getattr(args, "dry_run", False):
        for cfg in configs:
            print(f"== {cfg.project_name} ({cfg.repo})")
            loop.dry_run_plan(cfg)
        return 0
    running = [cfg.project_name for cfg in configs if loop.live_run(cfg) is not None]
    if running:
        print(f"runner: a run is live already ({', '.join(running)}): one runner at a time")
        return 1
    if getattr(args, "use_reserve", None) is not None and not restarted:
        windows = ("week", "five_hour") if args.use_reserve == "both" else (args.use_reserve,)
        for cfg in configs:
            for switch in windows:
                _switch_request(cfg, switch.replace("-", "_"), "on")
    for cfg in configs:
        _apply_requests(cfg, cfg.metrics_db)
    review = lambda cfg, key: _review(cfg, cfg.repo, key)  # noqa: E731
    if loop.run_projects(
        _project_configs, review, escalate=not getattr(args, "no_escalate", False)
    ):
        _restart()
    return 0


def _review(cfg: Config, repo: Path, key: str) -> bool:
    """A review `runner run` found due (f4-20), and its verdict, as `runner milestone` gives
    them; whether to restart: a review that changed runner/ (state.json keeps its rounds).
    The caller restarts, so `softfield run` first closes the other projects' sessions: an
    exec from inside the review left Coucou's run live, and the new process refused to
    start beside it (2026-10-15). One parked for Claude is no stop and has no verdict yet:
    back to the queue (F53 D1)."""
    stop = run_due_review(cfg, key)
    if stop == RESTART:
        return True
    if stop == PARKED:
        return False
    state = load_state(cfg.runs_dir / "state.json")
    _, text = owner.verdict(repo, key, state, stop, db=cfg.metrics_db)
    owner.record_verdict(repo, text)
    print("\n" + text, end="", flush=True)
    return False


# The checks never apply the owner's requests: they run inside jobs, on task branches, and as
# the pre-commit hook, in the middle of someone else's commit. Nor does a look (ADR 28 item
# 3): it runs inside a planner or a review job and writes nothing.
_NO_REQUESTS = ("check-all", "check-layout", "check-i18n", "check-tickets", "look")


def _apply_requests(cfg: Config, db: Path) -> None:
    """The owner's requests from the dashboard made while nothing ran (f5 D2): the next
    command applies them first, and turns off the switches whose 24 hours are over. A live
    run applies its own, at its next pick."""
    state_path = cfg.runs_dir / "state.json"
    try:
        if loop.live_run(replace(cfg, metrics_db=db)) is not None:
            return
        state = load_state(state_path)
        lines = requests.apply_requests(cfg.repo, db, loop.now(), state)
        if lines:
            save_state(state, state_path)
    except Exception as exc:
        print(
            f"runner: the owner's requests weren't read ({type(exc).__name__}: {exc})",
            file=sys.stderr,
        )
        return
    for line in lines:
        print(f"runner: the owner's request: {line}", flush=True)


def main(argv: list[str] | None = None) -> int:
    procs.stop_on_sigterm()
    parser = argparse.ArgumentParser(prog="softfield", description=__doc__)
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser(
        "run",
        help="every registered project's queue, in the owner's order, reviewing each milestone"
        " it finishes (the default)",
    )
    run.add_argument("--here", action="store_true", help="only this folder's project")
    run.add_argument("--once", action="store_true", help="stop after one task (this project)")
    run.add_argument("--dry-run", action="store_true", help="show what would run next")
    run.add_argument("--no-escalate", action="store_true", help="don't call Claude on escalations")
    run.add_argument(
        "--use-reserve",
        nargs="?",
        const="both",
        choices=("both", "week", "five-hour"),
        help="turn on the reserve switches (both, or one window's) for 24 hours as it starts",
    )
    reserve = sub.add_parser(
        "reserve", help="the owner: let the factory use Claude's reserve, for 24 hours (ADR 22)"
    )
    reserve.add_argument("window", choices=("week", "five-hour"))
    reserve.add_argument("value", choices=("on", "off"))
    sub.add_parser("pause", help="the owner: hold the factory after the job it is on (f5-18)")
    sub.add_parser("resume", help="the owner: let a paused factory go on")
    milestone = sub.add_parser(
        "milestone", help="run a whole milestone: tickets, review, then a verdict (ADR 12)"
    )
    milestone.add_argument("number", help="4 for M4, or a key like f1")
    milestone.add_argument("--base", help="git ref it started from (default <key>-start)")
    signoff = sub.add_parser("signoff", help="the owner: mark a milestone done and tag it")
    signoff.add_argument("number", help="4 for M4, or a key like f1")
    signoff.add_argument("--force", action="store_true", help="even with tickets left")
    signoff.add_argument(
        "--score", type=int, help="optional, 1-10: how the result felt on the devices"
    )
    queue = sub.add_parser(
        "queue", help="the owner: move a ticket from .factory/tasks/later to ready"
    )
    queue.add_argument("ticket", help="its id, or a unique prefix like m4-12")
    for name in ("accept", "reject"):
        decide = sub.add_parser(name, help=f"the owner: {name} an ADR")
        decide.add_argument("number", type=int)
    review = sub.add_parser("review", help="run the milestone review loop")
    review.add_argument("--milestone", required=True)
    review.add_argument("--base", help="git ref the milestone started from (default mN-start)")
    status = sub.add_parser("status", help="milestone metrics so far")
    status.add_argument("--milestone", required=True)
    commits = sub.add_parser("commits", help="list the commits the local model made")
    commits.add_argument("--milestone", required=True)
    commits.add_argument("--base", help="git ref to list from (default mN-start)")
    check_all = sub.add_parser("check-all", help="every check; non-zero exit on any failure")
    check_all.add_argument("--fix", action="store_true", help="format and autofix first")
    check_all.add_argument("--task", help="the task being worked on (keeps its own tests in)")
    check_all.add_argument("--hook", action="store_true", help="as the pre-commit hook")
    sub.add_parser("check-layout", help="check unit test file naming")
    sub.add_parser("check-i18n", help="check every user-facing string has a French translation")
    check_tickets = sub.add_parser(
        "check-tickets", help="what Approve would refuse in drafted tickets (read-only)"
    )
    check_tickets.add_argument(
        "tickets", nargs="*", help="ticket files (default: every one in .factory/tasks/later/)"
    )
    look_cmd = sub.add_parser(
        "look",
        help="read-only: a SELECT on the metrics database, or a dashboard page as text (ADR 28)",
    )
    look_what = look_cmd.add_subparsers(dest="what", required=True)
    look_sql = look_what.add_parser(
        "sql", help="the rows of one SELECT; `PRAGMA table_list` and `table_info(<table>)` too"
    )
    look_sql.add_argument("query", help="one statement, in quotes")
    look_page = look_what.add_parser(
        "page", help="a dashboard page as plain text, or its data as is (/line/live)"
    )
    look_page.add_argument("address", help="its path, e.g. /, /planning or /milestones/f95")
    copilot_review = sub.add_parser(
        "copilot-review", help="one read-only Copilot prompt (f1's probes; capped per day)"
    )
    copilot_review.add_argument("prompt", nargs="?", default="")
    copilot_review.add_argument("--model", help="a Copilot model name (default: Copilot's)")
    copilot_review.add_argument("--copilot-help", action="store_true", help="copilot --help")
    github_get = sub.add_parser("github-get", help="a GET on GitHub's API, e.g. /user")
    github_get.add_argument("path")
    backfill_cmd = sub.add_parser(
        "backfill", help="load past milestones into the metrics database from their logs"
    )
    backfill_cmd.add_argument("--db", type=Path, help="the database (default: [metrics] db)")
    bench_cmd = sub.add_parser(
        "bench", help="replay finished tickets for chosen agents, off main (ADR 14 item 8)"
    )
    bench_cmd.add_argument(
        "tickets", nargs="+", help="finished tickets, e.g. m4-09-…; with --review, milestones"
    )
    bench_cmd.add_argument(
        "--agents", nargs="+", required=True, help="agent ids from the machine's factory.toml"
    )
    bench_cmd.add_argument(
        "--review",
        action="store_true",
        help="replay the milestones' checkpoints and score the findings (ADR 16 item 10)",
    )
    ratings_cmd = sub.add_parser("ratings", help="each agent's rating now (ADR 15 item 9)")
    ratings_cmd.add_argument(
        "--replay",
        action="store_true",
        help="first recompute every agent's from its estimate under ADR 24",
    )
    ratings_cmd.add_argument(
        "--void-benches-before",
        type=datetime.fromisoformat,
        metavar="ISO_TIME",
        help="first void the OpenCode agents' ticket benches started before then (f7-07)",
    )
    ratings_cmd.add_argument("--db", type=Path, help="the database (default: [metrics] db)")
    report_cmd = sub.add_parser(
        "report", help="write a milestone's numbers into .factory/reviews/<key>.md"
    )
    report_cmd.add_argument("number", help="4 for M4, or a key like f1")
    report_cmd.add_argument("--db", type=Path, help="the database (default: [metrics] db)")
    dashboard = sub.add_parser(
        "dashboard", help="serve the factory dashboard at 127.0.0.1 until Ctrl-C (ADR 13)"
    )
    dashboard.add_argument(
        "action",
        nargs="?",
        choices=("update",),
        help="update: bring the dashboard to Softfield's latest main now (the runner's code too,"
        " which it otherwise does at its next pick)",
    )
    dashboard.add_argument("--port", type=int, default=8765)
    dashboard.add_argument(
        "--host", help="the address to listen on (default 127.0.0.1), e.g. this machine's LAN IP"
    )
    dashboard.add_argument(
        "--lan", action="store_true", help="listen on this machine's home-network address"
    )
    dashboard.add_argument("--db", type=Path, help="the database (default: [metrics] db)")
    init = sub.add_parser(
        "init", help="set this folder up as a project, new or existing, then open Claude (ADR 30)"
    )
    init.add_argument("--no-claude", action="store_true", help="write the files only")
    doctor = sub.add_parser("doctor", help="whether this project is ready for the web (ADR 30)")
    doctor.add_argument("--quick", action="store_true", help="skip running check-all")
    forget = sub.add_parser(
        "forget", help="take a project off the Projects page and the runner's list (not its folder)"
    )
    forget.add_argument("name")
    forget.add_argument("--yes", action="store_true", help="don't ask to confirm")
    service = sub.add_parser("service", help="the runner and the dashboard as systemd services")
    service.add_argument("action", choices=("install",))
    args = parser.parse_args(argv)
    if getattr(args, "lan", False) and args.host:
        dashboard.error("--lan finds this machine's address itself: give --lan or --host, not both")
    restarted = os.environ.pop(RESTARTED_ENV, None) == "1"
    if args.command is None:
        return _guide()
    if args.command == "run" and not (getattr(args, "here", False) or getattr(args, "once", False)):
        return _run_projects(args, restarted)
    if args.command in ("init", "service", "forget") or (
        args.command == "dashboard" and (args.action == "update" or _here() is None)
    ):
        return _machine_command(args)

    repo = _repo()
    cfg = load_config(repo)
    dry_run = getattr(args, "dry_run", False)
    use_reserve = getattr(args, "use_reserve", None)
    if args.command == "reserve":
        _switch_request(cfg, args.window.replace("-", "_"), args.value)
    elif args.command in (requests.PAUSE, requests.RESUME):
        _request(cfg, args.command, None, None)
    elif use_reserve is not None and not restarted and not dry_run:
        # a restart keeps the first 24 hours, or their end
        for switch in ("week", "five_hour") if use_reserve == "both" else (use_reserve,):
            _switch_request(cfg, switch.replace("-", "_"), "on")
    if args.command not in _NO_REQUESTS and not dry_run:
        _apply_requests(cfg, getattr(args, "db", None) or cfg.metrics_db)
    try:
        if args.command in (None, "run"):
            while True:
                session = run_session(
                    cfg,
                    once=getattr(args, "once", False),
                    dry_run=getattr(args, "dry_run", False),
                    escalate=not getattr(args, "no_escalate", False),
                )
                if session is not None and session.restart:
                    _restart()  # `runner run` is the standing command (ADR 17): it carries on
                if session is None or (session.review is None and not session.idle):
                    break
                if session.review is not None and _review(cfg, repo, session.review):
                    _restart()  # else back to the queue (f4-20)
        elif args.command == "milestone":
            key = milestone_arg(repo, args.number)
            owner.rerun_started(repo, key, db=cfg.metrics_db)
            stop = run_milestone(cfg, key, args.base or f"{key}-start")
            if stop == RESTART:
                _restart()  # an escalation changed the runner (ADR 12)
            state = load_state(cfg.runs_dir / "state.json")
            code, text = owner.verdict(repo, key, state, stop, db=cfg.metrics_db)
            owner.record_verdict(repo, text)
            print("\n" + text, end="")
            return code
        elif args.command == "signoff":
            key = milestone_arg(repo, args.number)
            owner.signoff(
                repo, key, _today(), force=args.force, db=cfg.metrics_db, score=args.score
            )
            print(f"{key.upper()} signed off and tagged {key}-done.")
        elif args.command == "queue":
            print(f"{loop.queue_ticket(cfg, args.ticket)}: back in .factory/tasks/ready/.")
        elif args.command == "reserve":
            if loop.live_run(cfg) is not None:  # `_apply_requests` left it to the run
                print(f"runner: a run is live: the run turns it {args.value} at its next pick.")
        elif args.command in (requests.PAUSE, requests.RESUME):
            if loop.live_run(cfg) is not None:  # `_apply_requests` left it to the run
                then = "pauses after the job it is on" if args.command == "pause" else "resumes"
                print(f"runner: a run is live: it {then}.")
        elif args.command in ("accept", "reject"):
            decision = "Accepted" if args.command == "accept" else "Rejected"
            path = owner.decide_adr(repo, args.number, decision, _today(), db=cfg.metrics_db)
            print(f"{path.relative_to(repo)}: {decision}.")
        elif args.command == "review":
            key = milestone_arg(repo, args.milestone)
            stop = review_milestone(cfg, key, args.base or f"{key}-start")
            print(f"Review loop stopped: {stop}")
        elif args.command == "status":
            key = milestone_arg(repo, args.milestone)
            m = milestone_metrics(repo, key)
            print(f"done {m.done}, escalated {m.escalated}, attempts {m.attempts}")
            print(milestone_summary(repo, key))
        elif args.command == "commits":
            found = Git(repo).local_model_commits(
                args.base or f"{milestone_arg(repo, args.milestone)}-start"
            )
            for c in found:
                print(f"{c.sha[:9]}  {c.task}  attempts {c.attempts}  {c.size} lines  ({c.author})")
            print(f"{len(found)} local-model commit(s)")
        elif args.command == "check-all":
            if args.hook and checks.hook_can_skip(Git(repo).staged_files()):
                return 0
            for name in checks.GIT_HOOK_ENV:  # never let tests' git reach this repo's index
                os.environ.pop(name, None)
            results = checks.check_all(repo, cfg.gate_timeout, task_id=args.task, fix=args.fix)
            print(checks.render(results), end="")
            return 0 if all(r.ok for r in results) else 1
        elif args.command == "check-i18n":
            problems = i18n.regenerated_problems(repo, cfg.gate_timeout)
            problems += i18n.compiled_out_of_date(repo)
            print("\n".join(problems) or "translations OK")
            return 1 if problems else 0
        elif args.command == "copilot-review":
            if args.copilot_help:
                cmd = ["copilot", "--help"]
                proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
                print(proc.stdout + proc.stderr, end="")
                return proc.returncode
            if not args.prompt:
                raise copilot.CopilotError("a prompt is needed")
            print(copilot.probe_review(repo, args.prompt, args.model, _today()))
        elif args.command == "github-get":
            cmd = copilot.github_get_command(args.path)
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            print(proc.stdout + proc.stderr, end="")
            return proc.returncode
        elif args.command == "backfill":
            conn = metrics.open_db(args.db or cfg.metrics_db)
            try:
                summary = backfill.backfill(conn, repo, cfg.runs_dir, local_agent=local_agent(cfg))
            finally:
                conn.close()
            print(backfill.render(summary), end="")
        elif args.command == "bench" and args.review:
            keys = [milestone_arg(repo, m) for m in args.tickets]
            replayed = bench.run_review_bench(cfg, keys, args.agents)
            for replay in replayed.reviews:
                print(
                    f"{replay.milestone} checkpoint {replay.checkpoint}  {replay.agent:<28}"
                    f" {replay.outcome}: {replay.note}"
                )
                for f in replay.score.unscored if replay.score else ():
                    where = f"{f.file}:{f.line}" if f.line else f.file or "?"
                    print(f"    new, for you to judge: [{f.severity}] {where} {f.summary}")
            if replayed.stopped:
                print(f"Stopped: {replayed.stopped}")
                return 1
        elif args.command == "bench":
            benched = bench.run_bench(cfg, args.tickets, args.agents)
            for r in benched.results:
                print(f"{r.ticket}  {r.agent:<28} {r.outcome} (attempt {r.attempts})")
            if benched.stopped:
                print(f"Stopped: {benched.stopped}")
                return 1
        elif args.command == "ratings":
            conn = metrics.open_db(args.db or cfg.metrics_db)
            try:
                start = loop.starting_ratings(cfg)
                project = metrics.upsert_project(conn, project_name(repo), repo=str(repo))
                if (cut_off := args.void_benches_before) is not None:
                    if cut_off.tzinfo is None:
                        raise RunnerError(f"--void-benches-before {cut_off}: give its time zone")
                    voided = loop.void_benches_before(conn, project, cfg.agents, cut_off)
                    print(f"Voided {sum(voided.values())} bench jobs before {cut_off}:")
                    for agent, count in sorted(voided.items()):
                        print(f"{agent:<28} {count}")
                    print()
                if args.replay:
                    print("Replayed under ADR 24:")
                    for redone in loop.replay_ratings(conn, project, start, loop.now()):
                        moved = f"→ {redone.after:.2f}" if redone.written else "unchanged"
                        print(
                            f"{redone.agent:<28} {redone.before:.2f} {moved},"
                            f" {redone.games} coding games"
                        )
                    print()
                current, _ = loop.standing(conn, start)
            finally:
                conn.close()
            for agent, rating in sorted(current.items(), key=lambda item: -item[1]):
                print(f"{agent:<28} {rating:.2f}")
        elif args.command == "report":
            key = milestone_arg(repo, args.number)
            path = report.write_milestone_report(repo, args.db or cfg.metrics_db, key)
            print(f"{path.relative_to(repo)}: {key.upper()}'s numbers written.")
        elif args.command == "dashboard":
            return _serve_dashboard(args, args.db or cfg.metrics_db, project_name(repo))
        elif args.command == "doctor":
            print(f"Checking {project_name(repo)} ({repo})")
            adr = setup.proposed_adr_00(repo)
            if adr is not None and sys.stdin.isatty():  # its review is the setup's last step
                print(f"ADR 00 waits for you: {adr.relative_to(repo)}")
                if input("Accept ADR 00 now? [y/N] ").strip().lower() in ("y", "yes"):
                    path = owner.decide_adr(repo, 0, "Accepted", _today(), db=cfg.metrics_db)
                    print(f"{path.relative_to(repo)}: Accepted.")
            findings = setup.doctor(repo, cfg.metrics_db, run_checks=not args.quick)
            for finding in findings:
                print(f"{'ok' if finding.ok else '--'}  {finding.what}")
            if not all(f.ok for f in findings):
                return 1
            try:
                host = _lan_address()
            except RunnerError:
                host = "127.0.0.1"
            name, card = project_name(repo), setup.first_card(repo)
            setup.publish_cards(repo, name, cfg.metrics_db)  # on its desk at once
            planning = False
            if setup.ready(name, cfg.metrics_db):
                print("The runner takes it from its next round, between two jobs.")
                if card is not None:  # the lead plans it without waiting for a message
                    at = datetime.now().astimezone().isoformat()
                    planning = setup.plan_first_card(name, card, cfg.metrics_db, at)
            print(setup.hand_over(name, card, host, planning=planning))
        elif args.command == "check-tickets":
            given = args.tickets or sorted(
                p.relative_to(repo).as_posix()
                for p in (repo / ".factory" / "tasks" / "later").glob("*.md")
            )
            problems = ticket_problems(repo, given)
            print("\n".join(problems) or "tickets OK")
            return 1 if problems else 0
        elif args.command == "look":
            if args.what == "sql":
                print(look.sql(cfg.metrics_db, args.query))
            else:
                print(look.page(cfg.metrics_db, project_name(repo), args.address))
        elif args.command == "check-layout":
            problems = layout_problems(repo)
            print("\n".join(problems) or "layout OK")
            return 1 if problems else 0
    except (
        RunnerError,
        owner.OwnerError,
        TaskError,
        copilot.CopilotError,
        report.ReportError,
        look.LookError,
    ) as exc:
        print(f"runner: {exc}", file=sys.stderr)
        return 1
    finally:
        # A Ctrl-C or a crash leaves no run looking alive or on the reserve (f2-03). A
        # self-restart ended its run before `execve`, and the new run keeps the yes.
        loop.end_open_runs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
