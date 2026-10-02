# ADR 14: Rated developers, configurable agents, and routing by what each service has left

- **Status:** Accepted (by the owner, 2026-09-30; shaped item by item in conversation)
- **Date:** 2026-09-30
- **Deciders:** project owner (accepts), Claude (drafts)
- **Goes with:** [ADR 13](13-factory-dashboard.md) (the metrics database and dashboard these ratings live in)

## Context

The owner has two free allowances beyond Claude Pro and the local GPU, and wants the factory to use them, with Claude staying the lead:
- **Ollama Cloud (free):** gemma4:31b, gpt-oss:20b and 120b, nemotron-3-nano:30b, nemotron-3-super and nemotron-3-ultra.
  - They're driven by OpenCode exactly like LM Studio: one more provider in `opencode.json`.
  - Usage is metered per token. The legacy free plan has 5-hour and weekly windows; plans after 2026-08-31 get a monthly credit.
  - 1 concurrent request. Prompts are not logged ([pricing](https://ollama.com/pricing)).
  - **No usage API** (open issues [#15132](https://github.com/ollama/ollama/issues/15132), [#16448](https://github.com/ollama/ollama/issues/16448), [#18653](https://github.com/ollama/ollama/issues/18653)).
- **GitHub Copilot Free:**
  - 50 chat/agent requests a month. The Copilot CLI is included (`copilot -p`, with a choice of model); "Copilot code review" is not.
  - GitHub's user billing usage endpoints (`/users/{user}/settings/billing/...`) are documented for paid plans only.

**How the Ollama models compare with the local Qwen3.6-35B-A3B**, before any evidence:
- gpt-oss:20b and nemotron-3-nano (~3B active) are the same class or smaller.
- gemma4:31b is roughly level.
- gpt-oss:120b, nemotron-3-super (120B, 12B active) and nemotron-3-ultra are candidates for a stronger developer. None is expected to be Claude-level.

**Copilot is a harness over other vendors' models, not a model.** Review suits its allowance: one short read-only prompt per job, and a second vendor's blind spots.

**Evidence from M4** ([review](../reviews/m4.md)):
- **Tokens per junior ticket:** 0.5M–13M input (≈3M on average), so a free cloud allowance buys a few tickets, not a milestone.
- **Escalations:** 7, at 0.3–0.6M of Claude each.
- **Lead spend:** ≈18M in all, ≈10M of it an idle open session (fixed by ADR 12).
- **The M4 review parked "a separate reviewer role"** (item 15) until M5 shows whether checkpoints are enough. A shadow reviewer answers that without changing M5.

**What the owner asked for:**
- use the extra allowances where they help most
- see which agent did what, how well, and at what cost
- track each agent's capacity over time, so that a new local model can be rated and slotted in one day
- move towards a factory where any agent, the lead included, can be swapped ([ADR 02](02-software-factory.md))

## Decisions (⚑ = deviates from an earlier decision)

### A. Names and agents
1. ⚑ **"Junior" becomes "developer"**, in AGENTS.md, `docs/agents/junior.md` (renamed `developer.md`), `docs/task-format.md`, `docs/task-writing.md`, lead.md, and the runner's prompts and reports.
   - With stronger cloud models joining, "junior" stops being accurate.
   - The ticket field becomes `agent: lead | developer`; `junior` stays accepted for old tickets.
2. **An agent is a harness plus a model.** Its id is `<harness>-<model>`: `local-qwen3.6-35b-a3b`, `ollama-gpt-oss-120b`, `claude-sonnet`, `claude-opus`, `copilot-<model>`.
   - The same model through a different harness is a different agent, because the harness changes results.
   - Ratings belong to the id, so a new local model is a new developer.
3. **Agents and roles are declared in `workflow/runner.toml`:**
   ```toml
   [agents.ollama-gpt-oss-120b]
   harness = "opencode"
   model = "ollama/gpt-oss:120b-cloud"      # the exact tag comes from the probe
   rating = { coding = 6, reviewing = 5 }   # the lead's starting estimate (item 7)

   [roles]
   developer = ["local-qwen3.6-35b-a3b"]
   last-attempt = ["local-qwen3.6-35b-a3b"]
   direction = ["claude-opus"]
   checkpoint = ["claude-sonnet"]
   checkpoint-shadow = ["copilot-<model>"]
   escalation = ["claude-opus"]
   lead-ticket = ["claude-opus"]
   review = ["claude-opus"]
   ```
   **There are no budget or balance settings to maintain:**
   - The runner tracks every agent's spend (tokens or requests) and every refusal with its time.
   - Where a harness has a usage API, its adapter reads it: Claude's OAuth usage endpoint behind `/usage`, and GitHub's billing endpoints if they answer on Free.
   - Claude is used until its limit, with today's pause-until-reset behaviour.
4. **One neutral job spec, one adapter per harness.**
   - A job is a role, a prompt, the tools it may use (read-only, edit globs, allowed commands) and a timeout.
   - Each adapter translates the spec (Claude: `--allowedTools` and `Edit(<glob>)`; OpenCode: its permissions; Copilot: `--allow-tool`/`--deny-tool`), and reports usage and refusals.
   - `runner/claude.py` becomes one adapter among three. This is the ground a swappable lead stands on (item 15).

### B. Difficulty and ratings
5. **Every ticket gets `difficulty:` from 1 to 10,** set by the lead at plan time from a short rubric in `docs/task-writing.md`: concepts, files to read and change, dependencies, new patterns, UI, i18n and offline. Difficulty 10 means "only the lead should do this".
6. **Two ratings per agent, from 1 to 10, kept simple.**
   - **Coding** is Elo-style: each ticket is a game against its difficulty.
     - The result:
       - 1: merged at the first attempt
       - 0.5: merged later
       - 0: escalated or blocked
       - −0.25: a finding the final review confirms on the ticket's code
     - The rating moves by (result − expected) × K. Beating a hard ticket raises it a lot, failing an easy one drops it a lot, and an expected result barely moves it. At rating = difficulty, the expected result is 0.5.
     - On a ticket that passed through several agents, the attempt that merged gets the result, and earlier failed attempts count as losses for their developers.
   - **Reviewing** is confirmed ÷ (confirmed + rejected + missed), over the final review's verdicts on a reviewer's findings, scaled to 1–10.
7. **Starting ratings need no benchmark.**
   - The lead sets an estimate in the config, from the model's size and public results.
   - It's **provisional**, and moves fast (a larger K) over its first ~5 tickets.
   - The local Qwen starts from its M1–M4 history.
8. **`runner bench <task…> --agents …` is optional:** it firms up a rating before real work, when credits allow.
   - It replays finished tickets in a throwaway worktree (`var/bench/`), from the parent of each ticket's merge, with today's workflow files overlaid, so every agent gets identical conditions.
   - It runs the same gates, but no Claude: a failed last attempt is recorded as "would escalate".
   - It stops at the first refusal.
   - Start with m4-09 (≈1M tokens locally). m4-06 (≈11M) waits for a later allowance period.

### C. Routing
9. **Hard work goes to cloud first, and leftovers get spent.**
   - A ticket goes to the cheapest developer whose coding rating covers its difficulty, which is local when it does.
   - Harder tickets and last attempts go to the best-rated available cloud developer.
   - When the forecast (ADR 13) says a service will reset with credit unused, it also takes ordinary tickets.
   - Local never refuses, so work never stops.
10. **A refusal is not a failure.** A quota or limit error:
    - ends the attempt without counting it
    - records the refusal and its reset (reusing `usage_limit_reset` in `runner/claude.py` where the message says when)
    - reruns the attempt on the next candidate
11. **Capability is not trust.**
    - Ratings measure skill. Protected and security code, ADRs, tickets and the final review stay with the lead by rule, whatever the ratings say.
    - Only the owner accepts ADRs and signs off.
    - Claude is rated too, but its rating isn't used for routing.

### D. Earning roles and judging
12. **An agent earns a role by shadowing it.**
    - It does the job alongside the current holder, with its output recorded but not acted on.
    - The dashboard marks it eligible, and the owner changes `[roles]` at a milestone review. Starting bars:
      - **checkpoint:** a reviewing rating ≥ 8 over 2+ milestones, no missed blocking finding, and a coding rating ≥ the difficulty of the tickets it reviews
      - **direction:** a coding rating ≥ the ticket's difficulty + 2, and above the developer that failed
      - **escalation:** stays with the lead for now
    - First shadow: Copilot beside Sonnet at M5's checkpoints. M5 stays the clean ADR 12 baseline.
13. **Judging adds no jobs:** it comes from jobs that already run.
    - Checkpoints and the review write their findings as a JSON block the runner parses (severity, file:line, summary, detail, route).
    - Directions and escalations already read the developer's thinking. They add a short **process note**: did it follow the ticket, run its checks, go round in circles. Notes are descriptive, shown on the job's page, and never scored.
    - The final review marks each checkpoint finding **confirmed, rejected or missed**, and gives the milestone a score from 1 to 10.
14. **Milestone results feed factory trends, not individual ratings,** since a mixed result can't be split fairly. They are:
    - the final review's score
    - the verdict and review rounds
    - an optional owner score, `runner signoff N --score 7`, on how the result felt on the devices. There's no prompt, and leaving it out is fine.

### E. Reporting and direction
15. **Towards a swappable lead** (the direction; not built here). With item 4 in place, what's left is:
    - the lead roles naming another agent
    - a lead calibration (replaying past escalations and checkpoints against their recorded outcomes)
    - nudge files like CLAUDE.md for the other tool

    AGENTS.md and lead.md are already tool-neutral. That's one small ADR, when wanted.
16. ⚑ **The milestone report reads its numbers from the metrics database** (amends lead.md "Sign-off sheet" and "Reporting").
    - `runner report N` writes the numbers section of `docs/reviews/mN.md` as a frozen snapshot, because the database is local and not in git.
    - The lead writes only the human parts: what changed, how to test it, what's left, decisions waiting, lessons, findings.
    - Per-run session reports in `docs/sessions/` shrink to a summary and a link to the dashboard.
17. **Privacy:** code, diffs and, for directions and escalations only, the developer's thinking go to Ollama and GitHub as well as Anthropic. Secrets are never in the repo.

## Consequences
- **The owner's steps:** `ollama signin`; install the Copilot CLI (`npm i -g @github/copilot`) and log in.
- **Probes before the code** (the lead, by hand), with their facts recorded here:
  - **Ollama:** a small OpenCode run on a cloud model, for its model tag, what a refusal looks like, and what ~100k tokens costs of the allowance.
  - **Copilot:** a `copilot -p` read-only review, for its tool flags, requests per prompt, the models Free offers, and whether the billing endpoints answer (`gh api`).
  - **Claude:** a check of the Claude usage endpoint.
- **Runner work:** adapters, the router, ratings (pure functions), findings as JSON, the shadow, the bench and `runner report`, each with runner tests. It's a factory milestone of mostly lead tickets, after ADR 13's database.
- **Decided later, on evidence:**
  - cloud developers' place in `[roles]`, from their ratings
  - at the M5 review: whether Copilot takes `checkpoint`

## Probe results (2026-10-01, f1-18)
Facts only, by the lead, with the commands as run.

### Ollama Cloud
- **Login:** already signed in; `ollama run gpt-oss:20b-cloud "Say hi"` answered ("Hi! 👋", after a short thinking block). `ollama list` shows no cloud model: cloud tags need no pull, and `ollama ps` stays empty.
- **Tags** (`ollama show <tag>`, all with completion, tools and thinking):

  | tag | parameters | context | quantization |
  |---|---|---|---|
  | `gpt-oss:20b-cloud` | 20.9B | 131072 | MXFP4 |
  | `gpt-oss:120b-cloud` | 116.8B | 131072 | MXFP4 |
  | `gemma4:31b-cloud` | 32.7B (+ vision) | 262144 | BF16 |
  | `nemotron-3-nano:30b-cloud` | 32B | 262144 | FP8 |
  | `nemotron-3-super:cloud` | 120B | 262144 | NVFP4 |
  | `nemotron-3-ultra:cloud` | 550B | 262144 | (not shown) |
- **OpenCode:** `opencode.json` has an `ollama` provider (`@ai-sdk/openai-compatible`, `baseURL` `http://127.0.0.1:11434/v1`, i.e. the local daemon, which forwards `-cloud` tags with its login; no API key in the repo) listing the six tags. `opencode models ollama` lists them as `ollama/<tag>`; it also lists local `qwen3.5:*` tags from outside this repo's config.
- **One run:** `opencode run --format json -m ollama/gpt-oss:120b-cloud --title probe-ollama "Read pyproject.toml and reply with the project's name only. Do not edit any file."` → one `read`, then "coucou"; 2 steps, ≈0.8 s from the first step's start to the last one's end. Saved as `tests/runner/fixtures/probes/opencode-ollama.jsonl`; its events have LM Studio's shape, so `parse_events` and `stream_facts` read it unchanged (input 7795, output 92, peak 7867, reasoning 0: gpt-oss's thinking isn't reported as reasoning tokens through this provider). OpenCode's `cost` is 0.
- **Refusal (quota or limit):** not probed: none happened, and no command here shows one. Its shape is still unknown; the adapter must treat an unrecognised error from a cloud tag as a possible refusal until one is seen.
- **Cost of the allowance:** not probed: neither `ollama` nor OpenCode reports it, and there's no usage API (Context). Only ollama.com's account page shows it.

### Copilot CLI (through `runner/copilot.py`)
- **Login:** logged in; `GET /copilot_internal/user` gives `access_type_sku: free_limited_copilot`, `cli_enabled: true`.
- **Flags** (`uv run runner copilot-review --copilot-help`): those `review_command` uses all exist (`--prompt`, `--silent`, `--model`, `--deny-tool`, `--disable-builtin-mcps`, `--disallow-temp-dir`). Also useful for the adapter: `--output-format json` (JSONL), `--usage-output-file <file>` (final usage as JSON), `--max-ai-credits <n>`, `--no-custom-instructions` (else it loads AGENTS.md), `--no-ask-user`, `--available-tools`/`--excluded-tools`, `--reasoning-effort`, `--no-auto-update`. `--model auto` lets Copilot pick, and is the default.
- **One review:** `uv run runner copilot-review "Read-only review of runner/copilot.py: … Then try to run the shell command 'git log -1 --oneline' … Finally state the exact model name …"` → two findings with file:line (the daily cap resets on an unreadable counter file; the count isn't atomic). Saved as `tests/runner/fixtures/probes/copilot-review.txt`. Reads worked with no `--allow-tool`.
- **Deny rules held:** the shell command was refused: "Permission to run this tool was denied due to the following rules: `shell`".
- **Models Free offers:** not found. With no `--model`, it said "Auto mode selects the model" and couldn't name it. `--model gpt-5-mini` and `--model no-such-model` both fail at once with `Error: Model "<name>" from --model flag is not available.` (exit 1), so a refused model name looks like a missing one. No models endpoint answered (`/copilot_internal/v2/models`: 404). The CLI's model picker, or a `--usage-output-file` run, is where to look next.
- **Requests per prompt:** after the review, `quota_snapshots.chat` read `entitlement 200, quota_remaining 199.7, percent_remaining 99.8` with `token_based_billing: true`: Free is metered in fractional credits (200 a month here, not 50 requests), and the review used at most 0.3 of them (whether anything was used before this month's probe is unknown). The snapshot's timestamp didn't move after the next failed prompt, so it may lag. Two of today's three capped prompts were spent on the model names above.

### Billing
- **User:** `epayet` (`gh auth status`: github.com, token scopes `admin:public_key, gist, read:org, repo`).
- `uv run runner github-get /users/epayet/settings/billing/usage` and `…/billing/premium_request/usage`: 404, with gh's note "This API operation needs the `user` scope". Whether they answer on Free is not probed: it needs the owner to run `gh auth refresh -h github.com -s user`.
- **`uv run runner github-get /copilot_internal/user` answers on Free** with `quota_snapshots` (`chat`, `completions`: 2000, `premium_interactions`: 0) and `quota_reset_date: 2026-11-01`. It's undocumented and internal, but it is a usage reading for the Copilot adapter with today's scopes.
- **Claude's usage endpoint:** not probed here (it would mean reading the OAuth token in a headless job).

## F2's cloud developers (2026-10-02, f2-09)
From the metrics database (read-only): every F2 job with role `developer` or `last-attempt` on an `ollama-*` agent. Both were developers from 2026-10-02 (ADR 15 item 7, the owner), before any valid bench. The 2026-10-02 bench on f1-36 (gpt-oss-120b failed 3×; nemotron-3-super interrupted) doesn't count: it edited the main checkout (f2-12).

| Agent | Ticket (difficulty) | Attempts | Minutes | Result |
|---|---|---|---|---|
| `ollama-gpt-oss-120b` | f2-06 (4) | 5, over two runs | 0.4, 1.0, 2.3; 1.5, 1.0 | lost: no change, then ruff 4×; local merged it on the last attempt (29 min) |
| `ollama-gpt-oss-120b` | f2-13 (3) | 1 | 9.4 | merged at the first attempt, 56 lines |
| `ollama-nemotron-3-super` | f2-07 (3) | 2, one per run | 19.8, 16.9 | lost: BLOCKED needs-info (OpenCode's 120 s shell timeout read as a stuck `check-all`), then needs-file (it wiped `conftest.py` with Write); the lead finished it |

- **First-attempt passes:** gpt-oss-120b 1 of 2 tickets; nemotron-3-super 0 of 1. The local Qwen in F1: 12 of 19, 28 min an attempt ([F1 review](../reviews/factory-f1.md)).
- **Speed:** gpt-oss-120b's passing attempt took 9.4 min, a third of local's 28, and its failures ended in 0.4–2.3 min, so a lost ticket cost minutes, not GPU hours. nemotron-3-super's took 17–20 min and burnt 44 refused commands in its second.
- **Refusals and resets:** none. No Ollama `usage_events` were recorded, so what a ticket costs of Ollama's allowance is still only the owner's reading on ollama.com (the bench used 7% on one ticket, `docs/milestones/f2.md`).
- **Tokens as recorded:** gpt-oss-120b 33–57k input an attempt, about its peak context: its cached prompt isn't reported through this provider, so the real input is higher. nemotron-3-super 0.7M and 1.1M.
- **Ratings from results** (ADR 15 item 9, `rating_changes`): gpt-oss-120b 6 → 4.5 (f2-06) → 5.1 (f2-13); nemotron-3-super 6 → 4.3 (f2-07). The config's estimates become 5 and 4.
- **Roles:** gpt-oss-120b stays a developer (it passed a ticket, and cloud first still sends it difficulty ≤ 5 before local). nemotron-3-super leaves `[roles] developer`: it failed its only ticket, twice; it comes back through the bench.
