---
id: f236-02-setup-ends-at-the-session-exit
milestone: f236-softfield-init-adds-a-project-to
agent: lead
difficulty: 3
depends_on: [f236-01-doctor-registers-the-project]
files:
  - runner/setup.py
  - runner/cli.py
  - runner/instructions/bootstrap.md
tests:
  - tests/runner/test_setup.py
  - tests/runner/test_cli.py
---

### Goal
The setup's Claude asks the owner before adding the project and runs `softfield create` on their yes, tells them when they can leave, and a session left early leaves clear words on how to finish.

### Context
Read D4 to D6 in `.softfield/cards/f236-softfield-init-adds-a-project-to.md`, then the `init` and `create` branches in `runner/cli.py` (f236-01 added `create`), `NEXT` and `claude_command` in `runner/setup.py`, and `runner/instructions/bootstrap.md` (its opening paragraph, and step 10 of "Both").
- Today `init` ends with `os.execvp`, so nothing of it runs after Claude. Run Claude as a child process in the owner's terminal instead (`subprocess.run`, inheriting stdin, stdout and stderr). After it exits, whatever its exit code: if the project has no live row, print the two lines D5 gives; if it has one, print nothing more.
- `init` in a folder with a `.softfield/project.toml` and no live row for its name opens the setup session again (D6), writing and committing nothing; with `--no-claude` it prints what `doctor` finds instead.
- bootstrap.md: the opening says `init` wrote the files and the project joins the factory only through `softfield create`, on the owner's yes. Step 10: after `softfield accept 0`, run `softfield doctor` and fix what it says; when it passes, ask "Ready to add <name> to the factory?"; on yes run `softfield create`, then end with its hand-over lines as printed and "You can leave this session now (/exit)." Never run `create` unasked. `NEXT` says the same in one line.

### Done when
- `init` with a stubbed Claude that exits at once leaves no row and prints the "isn't in the factory yet" and "To finish" lines
- with a stubbed Claude that registers the project before exiting, `init` prints neither line
- a second `init` in a set-up but unregistered folder starts the session again with the "Carry on the setup" opening and leaves git's history unchanged
- bootstrap.md's step 10 asks before `softfield create` and ends with the line saying the owner can leave
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
