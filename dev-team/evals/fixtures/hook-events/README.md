# Fixture — `hook-events`

Recorded hook inputs for the four scripts under `hooks/`, one case per path through each,
piped into the script exactly as `hooks/hooks.json` runs it (`python3 <script>`, with
`CLAUDE_PLUGIN_ROOT` set to the plugin and `CLAUDE_PLUGIN_DATA` to a temporary directory).
Written for phase 2 of the remake (`site/notes/remake-02-hooks.md`), whose case table every
file here covers; `gate-guarded-expired`, `gate-guarded-threshold`, `gate-no-section`,
`gate-surface-before-design`, `guard-out-of-scope-cwd` and the `guard-*` extras beyond one
allowed and one refused path per role go past that table.

```
python3 evals/fixtures/hook-events/check.py            # every case; exit 1 names each failure
python3 evals/fixtures/hook-events/check.py gate-pass  # one case
python3 evals/fixtures/hook-events/build.py <dest>     # build the gate's repo to look at
```

`events/<case>.json` holds the script, the repo it runs in (`built`, `arch` or `plain`), the
files to write first, the attempt counter to preset, the event (`{cwd}` stands for the repo),
and what must hold after: exit code, stderr, files, `.dev-team/gate.txt`, the counter.
`check.py`'s docstring lists every key.

`build.py` makes the gate's repo: the brief and dataset from `two-package/`, the `data`
contract (`ingest` and `surface` rows), a `docs/constraints.md` whose Floor and Enforced rows
pass with `ruff` on PATH, and a `docs/deviations.md` with one `proposed` entry citing
`design §5 load_trades`; then one commit carrying `Dev-Team-Run: run-package data` with
`data/ingest`'s code, README and two intent tests, one green and one red that cites that
clause. So the unmodified repo is the tolerated case, and every other gate case is one edit
on top of it. The coverage case stands a failing one-line command in for a coverage tool,
since `pytest-cov` is not assumed installed.

The four `gate-report-*` cases run the gate by hand (`--report`, `args` in the case, no
stdin), as `/dev-team:pair` does at wrap-up: a pass over `--base HEAD~1`, a fail over the
working tree, a bad flag and a `--base` that is not a commit.

The fifteen `sync-*` cases (2.2, `site/notes/2.2-02-decisions-sync.md`) run
`sync_decisions.py` in an `arch` repo whose `docs/decisions.md` holds D1–D3 and whose
`docs/packages/data/decisions/` inbox the case writes: numbering one and two `D?` stubs, an
`Applied:` line added once (`sync-applied-dedupe`, then `sync-idempotent` from its result), a
stale `Decision:` in an inbox that never flows, a self-numbered stub and one whose question
differs from the central entry (both renumbered), two inboxes in turn (`-a`, then `-b` from
`-a`'s result), a missing central ledger, a write that is not an inbox, an out-of-scope repo,
malformed stdin, `--all` by hand, and a crashed holder's lock (`setup.stale_lock`).

Needs `ruff` on PATH and `pytest` importable by `python3`.
