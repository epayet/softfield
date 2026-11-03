# .softfield

This folder belongs to [Softfield](https://github.com/epayet/softfield), a software factory. It holds its tickets, cards, decisions and settings for this project.

**You can ignore it.** You don't need Softfield to work on this project, and only what Softfield itself starts reads these files.

**One thing does reach you, on the machine that ran `softfield init`:** git's `core.hooksPath` points at this folder, so each commit there runs `softfield check-all` first, and any hooks in `.git/hooks` don't run. A fresh clone doesn't have this setting.

To remove the factory from this project, delete this folder and run `git config --unset core.hooksPath`.
