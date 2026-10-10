# Gotchas

- **Probes make real API calls, and read real data.** An `api` gets one request per read
  endpoint the section needs plus one deliberately bad one; it never sends a write. A `dataset`
  is profiled into statistics, never rows. Keys come from env or a root `.env`; the researcher
  never writes a value anywhere. `/dev-team:plan-repo` probes the brief's datasets before the
  repo contract, because data that cannot support the task changes which packages exist.
- **Work on a branch, commit your hand edits.** The run gate refuses `main`/`master` and a
  dirty tree outside the four exempt paths. Hand edits that depart from the design are
  CRITICAL findings until the ledger records them; `/dev-team:pair` writes those entries. `git log` is the run history: every commit carries
  a `Dev-Team-Run:` trailer.
- **Re-running the same command is the continue action** after a stop. Doing nothing in the
  ledger means "accept the assumptions".
- **`run-package` is a loop in your conversation.** It reads each return's first line only and
  prints only the rows whose state changed, but a package of five sections is still dozens of
  turns. Run it with `/clear` behind you.
- **Return size is context cost.** Agents return short summaries; the content is on disk.
- **Descriptions are always loaded.** Keep agent `description` fields short — the combined
  budget warns at 15,000 tokens.
- **Nesting depth.** The driver's spawns are layer 1. `map-repo` forks an architect that
  spawns one architect per package, layer 2; `plan-repo` spawns researchers for datasets. Both
  are within the three-layer limit.
- **Expect blocks on an adopted repo.** Open questions with no assumption stop a section by
  design. Answer them when the driver asks, or in `docs/decisions.md`, and re-run.
- **import-linter needs the packages importable.** Run `uv run lint-imports` inside the
  workspace, and expect it to fail on a package in `root_packages` with no code yet — which is
  why the block grows as packages are built.
- **The docs site builds strict from the first section.** The scaffold's nav names only files
  that exist; each `surface` section adds its package's API page, and
  `/dev-team:finalize-project` writes `docs/index.md`. MkDocs' `docs_dir` is `docs/`, your
  planning docs; change it in the repo contract's Toolchain before the first scaffold if you
  would rather not publish them.
- **No section named `report`.** Claude Code refuses a subagent's Write of a `.md` file whose
  name starts with `report`, `summary`, `findings` or `analysis`, so a section or source named
  that way could never get its design or probe doc. The architect names it after what it
  produces, one word such as `digest` (`project-structure` §4).
- **Implementers are parallel.** Two sections that must edit one file the write guard cannot
  split are the `--serial` case; the three edits every section shares — `uv add`, an
  entry-point line, the `.gitignore` block — go through `locked.py`.
- **A blocked or let-through implementer is a BLOCKED row.** A section whose implementer
  blocked, or was let through after three red attempts, shows BLOCKED with `gate …` evidence,
  and `/dev-team:run-package` asks about it. Answer the question, or type the `next:` line.
  An implementer's return no longer lists test or lint results: read
  `.dev-team/gate/<pkg>/<section>.txt`.
- **A package shipped under 2.3 may now print `shipped: no (surface check FAIL)`.** Run
  `status.py --surface <pkg>` and correct the README rows it names: one exported name per row,
  in backticks, no grouped or dotted names.
- **A package shipped under 2.4 may now print `shipped: no (paths needed)`.** `shipped:` needs
  the paths review. Run `/dev-team:run-package <pkg>` once: the driver spawns the paths review,
  and its findings re-open the sections they name as FIX rounds. A package with no
  `[project.scripts]` commands reads `paths: approved (no commands)` and stays shipped.
- **An existing repo keeps its old argument cap.** The lint block now caps positional
  parameters only, but the scaffold merges it only into a new repo. In your root
  `pyproject.toml`, replace `PLR0913` with `PLR0917` and `max-args` with `max-positional-args`,
  add `required-version = ">=0.16.0"` under `[tool.ruff]`, and upgrade ruff to 0.16.0 or later.
  An older ruff then refuses to run instead of skipping the rule.
- **The stop gate fails a run that adds a trivial single-use helper or an options bag**
  (`FAIL shape: …` in the gate record). Inline the helper or name its parameters; code already
  reviewed, and adopted code, is measured and never failed.
- **`paths` is a reserved section name.** Rename a section called `paths` in the package
  contract before its next run: its reviews would share `reviews/paths/` with the paths review.
- **`status.py --fields` prints seven lines, and `reviews/paths/` holds reports with letter
  `p`.** A script of your own that reads `--fields` or the review directories reads the sixth
  line, `paths report:`, and the seventh, `dependency readmes:` — the `depends on` READMEs that
  exist, `none` when none does, which the driver now sends as **Dependency READMEs** — and
  skips `reviews/paths/` when it means a section's reports. A hand-run that copied the six
  lines still works.
- **Upgrading from 2.5: `surface` is ready earlier.** With a `## Call paths` heading in the
  contract, the `surface` row is ready at PLAN, DESIGN and TEST before any sibling is DONE;
  IMPLEMENT still waits for every section. A package mid-build whose contract gains the
  heading at its next PLAN sees its surface designer spawn in the next batch; nothing already
  designed is re-opened. A contract without the heading keeps the 2.5 timing.
- **Upgrading from 2.5: the package contract has a fifth item.** **Call paths** sits after
  **Pipelines**; **Public surface (intent)**, **Consumes**, **Package conventions** and
  **Open decisions** are items 6 to 9. A contract written before 2.6 still parses: every
  reader finds its headings by name.
- **Upgrading from 2.5: the paths review compares the code to the contract.** Once a contract
  has **Call paths**, a frame on a command's path that the contract does not list, or one it
  lists that the code does not pass through, is a break (CRITICAL) under the section that
  holds it, and P1 uses the command's own budget. Without the heading the review runs as in
  2.5.
- **Upgrading from 2.7: a shipped package prints `shipped: no (integration needed)`.**
  `shipped:` now needs the integration check. Run `/dev-team:run-package <pkg>` once: the
  driver runs the check, re-opens any section a failure lies in, and closes the package again
  when it passes. The repo-wide `pytest` row that the stop gate skipped runs here for the first
  time, so expect it to find what nothing ran before.
- **Upgrading from 2.7: the scaffold step writes `.github/workflows/ci.yml`.** An existing
  workspace prints `scaffold: needed (no .github/workflows/ci.yml)`, and the next
  `/dev-team:run-package` writes it before anything else. Make its `checks` job a required
  status check in the GitHub repository's branch protection: until then a red run still
  merges. The workflow is matched line by line against the Floor and Enforced rows, so a row
  `/dev-team:set-constraints` adds later is added to it by the next scaffold step.
- **Upgrading from 2.5: a legacy close writes the heading.** `/dev-team:sync-plan <pkg>` (or
  `run-package`'s close) on a contract with no **Call paths** writes it as built from
  `status.py --paths`, and writes `docs/packages/<pkg>/changes/paths-<command>.md` for each
  command deeper than 8. Those change files re-open the sections they name at DESIGN when
  approved; nothing is rebuilt until then.
- **A README with grouped or dotted name cells fails its section's next gate.** The same
  correction, in that section.
- **A 2.2-or-later ledger entry still `open` re-opens its step** even when its document was
  committed since. Run `/dev-team:run-package <pkg>`: the answering agent is handed it. If it
  was in fact answered, set its `Status:` to `resolved` by hand.
- **A hookless session leaves inboxes unsynced.** A session or harness that runs the agents
  without this plugin's hooks writes an inbox no hook merges; the run gate says so and names
  `sync_decisions.py --all`.
- **Interactive session for a hard section:** `claude --agent dev-team:implementer` gives the
  main thread the implementer's prompt, tools and model, so you get its rules and return format
  while steering turn by turn. The stop gate is a `SubagentStop` hook and does not fire there.
