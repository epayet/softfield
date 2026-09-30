"""``uv run runner``: the deterministic build runner. No AI in here; see docs/workflow.md."""

import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path

from runner import checks, i18n, owner
from runner.config import load_config
from runner.gates import layout_problems
from runner.gitops import Git
from runner.loop import RunnerError, run_session
from runner.milestone import (
    RESTART,
    milestone_metrics,
    milestone_summary,
    review_milestone,
    run_milestone,
)
from runner.state import load_state


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
    milestone.add_argument("number", type=int)
    milestone.add_argument("--base", help="git ref the milestone started from (default mN-start)")
    signoff = sub.add_parser("signoff", help="the owner: mark a milestone done and tag it")
    signoff.add_argument("number", type=int)
    signoff.add_argument("--force", action="store_true", help="even with tickets left")
    for name in ("accept", "reject"):
        decide = sub.add_parser(name, help=f"the owner: {name} an ADR")
        decide.add_argument("number", type=int)
    review = sub.add_parser("review", help="run the milestone review loop")
    review.add_argument("--milestone", type=int, required=True)
    review.add_argument("--base", help="git ref the milestone started from (default mN-start)")
    status = sub.add_parser("status", help="milestone metrics so far")
    status.add_argument("--milestone", type=int, required=True)
    commits = sub.add_parser("commits", help="list the commits the local model made")
    commits.add_argument("--milestone", type=int, required=True)
    commits.add_argument("--base", help="git ref to list from (default mN-start)")
    check_all = sub.add_parser("check-all", help="every check; non-zero exit on any failure")
    check_all.add_argument("--fix", action="store_true", help="format and autofix first")
    check_all.add_argument("--task", help="the task being worked on (keeps its own tests in)")
    check_all.add_argument("--hook", action="store_true", help="as the pre-commit hook")
    sub.add_parser("check-layout", help="check unit test file naming")
    sub.add_parser("check-i18n", help="check every user-facing string has a French translation")
    args = parser.parse_args(argv)

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
            stop = run_milestone(cfg, args.number, args.base or f"m{args.number}-start")
            if stop == RESTART:
                # An escalation changed the runner: carry on in a fresh process (ADR 12).
                print("runner: the runner's code changed; restarting.", flush=True)
                argv_again = [sys.executable, "-m", "runner.cli", *sys.argv[1:]]
                os.execv(sys.executable, argv_again)  # noqa: S606 - our own interpreter and args
            state = load_state(cfg.runs_dir / "state.json")
            code, text = owner.verdict(repo, args.number, state, stop)
            owner.record_verdict(repo, text)
            print("\n" + text, end="")
            return code
        elif args.command == "signoff":
            owner.signoff(repo, args.number, _today(), force=args.force)
            print(f"M{args.number} signed off and tagged m{args.number}-done.")
        elif args.command in ("accept", "reject"):
            decision = "Accepted" if args.command == "accept" else "Rejected"
            path = owner.decide_adr(repo, args.number, decision, _today())
            print(f"{path.relative_to(repo)}: {decision}.")
        elif args.command == "review":
            stop = review_milestone(cfg, args.milestone, args.base or f"m{args.milestone}-start")
            print(f"Review loop stopped: {stop}")
        elif args.command == "status":
            m = milestone_metrics(repo, args.milestone)
            print(f"done {m.done}, escalated {m.escalated}, attempts {m.attempts}")
            print(milestone_summary(repo, args.milestone))
        elif args.command == "commits":
            found = Git(repo).local_model_commits(args.base or f"m{args.milestone}-start")
            for c in found:
                print(f"{c.sha[:9]}  {c.task}  attempts {c.attempts}  {c.size} lines  ({c.author})")
            print(f"{len(found)} local-model commit(s)")
        elif args.command == "check-all":
            if args.hook and checks.hook_can_skip(Git(repo).staged_files()):
                return 0
            results = checks.check_all(repo, cfg.gate_timeout, task_id=args.task, fix=args.fix)
            print(checks.render(results), end="")
            return 0 if all(r.ok for r in results) else 1
        elif args.command == "check-i18n":
            problems = i18n.regenerated_problems(repo, cfg.gate_timeout)
            problems += i18n.compiled_out_of_date(repo)
            print("\n".join(problems) or "translations OK")
            return 1 if problems else 0
        elif args.command == "check-layout":
            problems = layout_problems(repo)
            print("\n".join(problems) or "layout OK")
            return 1 if problems else 0
    except (RunnerError, owner.OwnerError) as exc:
        print(f"runner: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
