"""``uv run runner``: the deterministic build runner. No AI in here; see docs/workflow.md."""

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
    copilot,
    i18n,
    loop,
    metrics,
    owner,
    procs,
    report,
    requests,
)
from runner.config import Config, load_config
from runner.gates import layout_problems
from runner.gitops import Git
from runner.loop import RunnerError, local_agent, run_session
from runner.milestone import (
    RESTART,
    milestone_metrics,
    milestone_summary,
    review_milestone,
    run_due_review,
    run_milestone,
)
from runner.state import load_state, save_state
from runner.tasks import TaskError, milestone_arg


def _repo() -> Path:
    here = Path.cwd()
    for candidate in (here, *here.parents):
        if (candidate / "workflow" / "runner.toml").is_file():
            return candidate
    raise SystemExit("run this inside the coucou repository")


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
        project = metrics.upsert_project(conn, cfg.repo.name, repo=str(cfg.repo))
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


def _review(cfg: Config, repo: Path, key: str) -> None:
    """A review `runner run` found due (f4-20), and its verdict, as `runner milestone` gives
    them. A review that changes runner/ restarts the command; state.json keeps its rounds."""
    stop = run_due_review(cfg, key)
    if stop == RESTART:
        _restart()
    state = load_state(cfg.runs_dir / "state.json")
    _, text = owner.verdict(repo, key, state, stop, db=cfg.metrics_db)
    owner.record_verdict(repo, text)
    print("\n" + text, end="", flush=True)


# The checks never apply the owner's requests: they run inside jobs, on task branches, and as
# the pre-commit hook, in the middle of someone else's commit.
_NO_REQUESTS = ("check-all", "check-layout", "check-i18n")


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
    parser = argparse.ArgumentParser(prog="runner", description=__doc__)
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser(
        "run", help="work through tasks/ready, reviewing each milestone it finishes (the default)"
    )
    run.add_argument("--once", action="store_true", help="stop after one task")
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
    queue = sub.add_parser("queue", help="the owner: move a ticket from tasks/later to ready")
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
        "--agents", nargs="+", required=True, help="agent ids from workflow/runner.toml"
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
        "report", help="write a milestone's numbers into docs/reviews/<key>.md"
    )
    report_cmd.add_argument("number", help="4 for M4, or a key like f1")
    report_cmd.add_argument("--db", type=Path, help="the database (default: [metrics] db)")
    dashboard = sub.add_parser(
        "dashboard", help="serve the factory dashboard at 127.0.0.1 until Ctrl-C (ADR 13)"
    )
    dashboard.add_argument("--port", type=int, default=8765)
    dashboard.add_argument(
        "--host", help="the address to listen on (default 127.0.0.1), e.g. this machine's LAN IP"
    )
    dashboard.add_argument(
        "--lan", action="store_true", help="listen on this machine's home-network address"
    )
    dashboard.add_argument("--db", type=Path, help="the database (default: [metrics] db)")
    args = parser.parse_args(argv)
    if getattr(args, "lan", False) and args.host:
        dashboard.error("--lan finds this machine's address itself: give --lan or --host, not both")
    restarted = os.environ.pop(RESTARTED_ENV, None) == "1"

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
                if session is None or session.review is None:
                    break
                _review(cfg, repo, session.review)  # then back to the queue (f4-20)
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
            print(f"{loop.queue_ticket(cfg, args.ticket)}: back in tasks/ready/.")
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
                project = metrics.upsert_project(conn, repo.name, repo=str(repo))
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
            db = args.db or cfg.metrics_db
            if not db.is_file():
                raise RunnerError(
                    f"no metrics database at {db}; `uv run runner backfill` makes one"
                )
            host = _lan_address() if args.lan else args.host or "127.0.0.1"
            from factory_dashboard import app  # FastAPI loads only for this command

            print(f"The factory dashboard: http://{host}:{args.port}/ (Ctrl-C stops it)")
            if args.lan:
                print("Open that address on your phone, on the same Wi-Fi.")
            app.serve(db, repo.name, port=args.port, host=host)
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
