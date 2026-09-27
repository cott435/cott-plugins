# Fixture — `hook-events`

Recorded hook inputs for the three scripts under `hooks/`, one case per path through each,
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

Needs `ruff` on PATH and `pytest` importable by `python3`.
