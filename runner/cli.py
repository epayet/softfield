"""``uv run runner``: the deterministic build runner. No AI in here; see docs/workflow.md."""

import argparse
import sys
from pathlib import Path

from runner.config import load_config
from runner.gates import layout_problems
from runner.loop import RunnerError, run_session
from runner.milestone import milestone_metrics, review_milestone


def _repo() -> Path:
    here = Path.cwd()
    for candidate in (here, *here.parents):
        if (candidate / "workflow" / "runner.toml").is_file():
            return candidate
    raise SystemExit("run this inside the coucou repository")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="runner", description=__doc__)
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="work through tasks/ready (the default)")
    run.add_argument("--once", action="store_true", help="stop after one task")
    run.add_argument("--dry-run", action="store_true", help="show what would run next")
    run.add_argument("--no-escalate", action="store_true", help="don't call Claude on escalations")
    review = sub.add_parser("review", help="run the milestone review loop")
    review.add_argument("--milestone", type=int, required=True)
    review.add_argument("--base", help="git ref the milestone started from (default mN-start)")
    status = sub.add_parser("status", help="milestone metrics so far")
    status.add_argument("--milestone", type=int, required=True)
    sub.add_parser("check-layout", help="check unit test file naming")
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
        elif args.command == "review":
            stop = review_milestone(cfg, args.milestone, args.base or f"m{args.milestone}-start")
            print(f"Review loop stopped: {stop}")
        elif args.command == "status":
            m = milestone_metrics(repo, args.milestone)
            print(f"done {m.done}, escalated {m.escalated}, attempts {m.attempts}")
        elif args.command == "check-layout":
            problems = layout_problems(repo)
            print("\n".join(problems) or "layout OK")
            return 1 if problems else 0
    except RunnerError as exc:
        print(f"runner: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
