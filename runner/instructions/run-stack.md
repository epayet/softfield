# A project's stack: what the Projects page needs to run its app

ADR 46. The project owns its stack: plain Docker Compose, which works in any clone without the
factory. The factory only runs main with it, from its own checkout, and follows main.

## `compose.yaml`, at the repo's root
- **The main service publishes its web port on one fixed host port:**
  `ports: ["${APP_PORT:-81NN}:8000"]`, where `81NN` is this project's own port (below) and
  `8000` the port the app listens on inside its container.
- **Lasting data lives under `${APP_DATA:-./.data}`,** a bind mount: SQLite files, uploads,
  anything that must survive a rebuild, e.g. `volumes: ["${APP_DATA:-./.data}:/data"]`, and
  the app's settings point there (`/data/db.sqlite3`). Add `.data/` to `.gitignore`.
- **`restart: unless-stopped`** on every service, so a running app comes back after a reboot
  until it is stopped.
- **The main service runs its migrations before it serves,** in its own `command`, so a plain
  `docker compose up` migrates too. For Django:
  `command: sh -c "python manage.py migrate --noinput && exec <the server>"`.
  A failed migration stops the container: the page shows Crashed, with its logs.
- Nothing in it mentions Softfield (ADR 41), and it needs no file outside the repo.

## The port
Pick one from 8100–8199 that:
- no other project's `compose.yaml` on this machine uses (look in each registered repo);
- is free on the machine now (`ss -ltn` shows nothing listening on it).
Write it as the default in `${APP_PORT:-81NN}`. The page reads the port from Docker, so it is
written in this one place only.

## `[run]` in `.softfield/project.toml`
```toml
[run]
service = "web"   # the main service: its published port is the app's link
path = "/"        # the page the link opens, if it isn't "/"
```
Without `[run]` the Projects page offers to plant a card for a stack instead of Run.

## Existing data
If the app already has data somewhere (a `db.sqlite3` in the repo, a folder in the home),
**copy** it into `~/.local/share/softfield/data/<project>`, the folder the factory's app gets
as `APP_DATA` (`<project>` is the project's name in lower case, `-` for anything else). Never
move it: the old files stay until the owner removes them. Agents never use that folder: in a
worktree `APP_DATA` is unset and the app uses `./.data` or the test fixtures.

## Done when
- `docker compose up -d` in a fresh clone builds, migrates and serves on the chosen port, with
  its data under `./.data`; `docker compose stop` and `down` work too.
- `[run]` names the main service, and the Projects page shows Run for the project.
- No job runs `docker compose` (ADR 46 item 7): the stack card's tests stay native, and its
  last message tells the owner to press Run and check the app.
