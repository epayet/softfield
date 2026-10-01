"""``uv run runner``: the deterministic build runner. No AI in here; see docs/workflow.md."""

import argparse
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from runner import backfill, checks, copilot, i18n, loop, metrics, owner, report
from runner.config import load_config
from runner.gates import layout_problems
from runner.gitops import Git
from runner.loop import RunnerError, local_agent, run_session
from runner.milestone import (
    RESTART,
    milestone_metrics,
    milestone_summary,
    review_milestone,
    run_milestone,
)
from runner.state import load_state
from runner.tasks import TaskError, milestone_key


def _repo() -> Path:
    here = Path.cwd()
    for candidate in (here, *here.parents):
        if (candidate / "workflow" / "runner.toml").is_file():
            return candidate
    raise SystemExit("run this inside the coucou repository")


def _today() -> date:
    return datetime.now().astimezone().date()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="runner", description=__doc__)
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="work through tasks/ready (the default)")
    run.add_argument("--once", action="store_true", help="stop after one task")
    run.add_argument("--dry-run", action="store_true", help="show what would run next")
    run.add_argument("--no-escalate", action="store_true", help="don't call Claude on escalations")
    milestone = sub.add_parser(
        "milestone", help="run a whole milestone: tickets, review, then a verdict (ADR 12)"
    )
    milestone.add_argument("number", help="4 for M4, or a key like f1")
    milestone.add_argument("--base", help="git ref it started from (default <key>-start)")
    signoff = sub.add_parser("signoff", help="the owner: mark a milestone done and tag it")
    signoff.add_argument("number", help="4 for M4, or a key like f1")
    signoff.add_argument("--force", action="store_true", help="even with tickets left")
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
        "--host", default="127.0.0.1", help="the address to listen on, e.g. this machine's LAN IP"
    )
    dashboard.add_argument("--db", type=Path, help="the database (default: [metrics] db)")
    args = parser.parse_args(argv)
    # A yes to Claude's reserve, handed on by this command's own restart (below); taken out
    # so that nothing this process starts inherits it (ADR 15 item 5).
    if os.environ.pop(loop.RESERVE_ENV, None) == "1":
        loop.RESERVE.yes = True

    repo = _repo()
    cfg = load_config(repo)
    try:
        if args.command in (None, "run"):
            run_session(
                cfg,
                once=getattr(args, "once", False),
                dry_run=getattr(args, "dry_run", False),
                escalate=not getattr(args, "no_escalate", False),
            )
        elif args.command == "milestone":
            key = milestone_key(args.number)
            stop = run_milestone(cfg, key, args.base or f"{key}-start")
            if stop == RESTART:
                # An escalation changed the runner: carry on in a fresh process (ADR 12).
                print("runner: the runner's code changed; restarting.", flush=True)
                argv_again = [sys.executable, "-m", "runner.cli", *sys.argv[1:]]
                env = dict(os.environ)
                if loop.RESERVE.yes:  # the owner's yes lasts for the whole command
                    env[loop.RESERVE_ENV] = "1"
                os.execve(sys.executable, argv_again, env)  # noqa: S606 - our own interpreter and args
            state = load_state(cfg.runs_dir / "state.json")
            code, text = owner.verdict(repo, key, state, stop, db=cfg.metrics_db)
            owner.record_verdict(repo, text)
            print("\n" + text, end="")
            return code
        elif args.command == "signoff":
            key = milestone_key(args.number)
            owner.signoff(repo, key, _today(), force=args.force, db=cfg.metrics_db)
            print(f"{key.upper()} signed off and tagged {key}-done.")
        elif args.command in ("accept", "reject"):
            decision = "Accepted" if args.command == "accept" else "Rejected"
            path = owner.decide_adr(repo, args.number, decision, _today(), db=cfg.metrics_db)
            print(f"{path.relative_to(repo)}: {decision}.")
        elif args.command == "review":
            key = milestone_key(args.milestone)
            stop = review_milestone(cfg, key, args.base or f"{key}-start")
            print(f"Review loop stopped: {stop}")
        elif args.command == "status":
            m = milestone_metrics(repo, milestone_key(args.milestone))
            print(f"done {m.done}, escalated {m.escalated}, attempts {m.attempts}")
            print(milestone_summary(repo, milestone_key(args.milestone)))
        elif args.command == "commits":
            found = Git(repo).local_model_commits(
                args.base or f"{milestone_key(args.milestone)}-start"
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
        elif args.command == "report":
            key = milestone_key(args.number)
            path = report.write_milestone_report(repo, args.db or cfg.metrics_db, key)
            print(f"{path.relative_to(repo)}: {key.upper()}'s numbers written.")
        elif args.command == "dashboard":
            db = args.db or cfg.metrics_db
            if not db.is_file():
                raise RunnerError(
                    f"no metrics database at {db}; `uv run runner backfill` makes one"
                )
            from factory_dashboard import app  # FastAPI loads only for this command

            print(f"The factory dashboard: http://{args.host}:{args.port}/ (Ctrl-C stops it)")
            app.serve(db, repo.name, port=args.port, host=args.host)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
