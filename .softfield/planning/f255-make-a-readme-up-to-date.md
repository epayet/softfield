# F255: A README that welcomes people who want to use or work on Softfield

The planning thread behind F255's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-16 22:26

> Make a readme up to date and more welcoming to others who want to use it or work on it

## The lead, 2026-11-16 22:31

> I drafted a plan for F255: one lead ticket that rewrites the README for newcomers and adds a test so it can't go stale again. Two questions for you are below.
>
> 1. **What's wrong with today's README**: It's written for you, on this machine. A stranger can't tell what Softfield is for, what to install first (Linux, git, Python 3.13 and uv, Claude Code, and OpenCode with a local model if they want one) or how to install it at all. It leaves out `softfield lead`, pause and resume, phone notifications, and how to replace your opinions with their own. Your Dropbox backup reads like a requirement, not a default. AGENTS.md, where contributors start, numbers its rules from 5. The rest still matches the code (checked today against the commands and the Projects page): the daily table, setting up a project, always on, where things live, and how Softfield updates itself. Those parts stay, in a new order.
>    Action: Ticket f255-01-a-welcoming-readme.
> 2. **One README, in a newcomer's order, and no CONTRIBUTING file**: New order: what Softfield is → how it works in five lines → what you need → install → your first project → every day → make it yours → always on → where things live → how it updates itself → working on Softfield → licence. I'd skip a separate CONTRIBUTING.md. GitHub does show that file to contributors, but AGENTS.md already does the job, and a second file would be one more thing to keep up to date. The README's last section points to AGENTS.md.
>    Action: Card F255 Decision D1.
> 3. **Welcoming, but honest about where it stands**: A welcoming README shouldn't promise more than Softfield gives today. It has never been installed on another machine, and the tests have never run anywhere else. The README says so plainly: one person's factory, used daily on Linux, MIT. Others install from GitHub with `uv tool install` (ADR 41 item 6). The ticket checks every step against the code and writes down anything a fresh machine would get stuck on, rather than glossing over it. F204, Publish Softfield as a versioned package, with CI, is not a repeat: it makes the PyPI install real and will change this README's install line when it lands.
>    Action: Card F255 Decisions D2 to D4.
> 4. **A test keeps it true**: Most of today's gaps come from the README falling behind the code. A small test in the command-line tests fails the suite if the README names a command that doesn't exist, or leaves out an everyday one (init, doctor, run, dashboard, lead, pause, resume, notify). It's cheap, and it guards against exactly what this card fixes.
>    Action: Part of f255-01 (D5).
> 5. **Is github.com/epayet/softfield public, or about to be?**: Inviting others only works if they can reach the repo. If it stays private for now, I'd still write the README for a public repo: it's ready when you open it, and nobody sees it in the meantime.
>    Action: Your choice: (a) public or soon public, so the plan stays as it is (recommended); (b) private for a while, which changes nothing in the ticket but tells me how much the GitHub install line matters for now.
> 6. **A picture of the dashboard?**: A picture welcomes people more than any paragraph, but it has two costs. The dashboard changes every week, so the picture goes stale fast. And a picture of your real factory shows your cards and project names. I'd leave it out for now and add one with F204, Publish Softfield as a versioned package, with CI, taken on made-up data.
>    Action: Your choice: (a) no picture now (recommended); (b) one picture of the board on made-up data, as a second ticket.
> 7. **The lead writes it**: Every line has to be checked against the code, and writing for a stranger is judgment work. A developer's draft would come back to me to check and rewrite, so it goes to the lead directly. It's one ticket, about 27 minutes.
>    Action: f255-01 has agent: lead.
> 8. **No mock-up**: The README isn't a page the dashboard serves, so there's nothing to draw.
>    Action: Nothing.
>
> Proposals:
> - F255: a README for newcomers, kept true by a test (plan)
