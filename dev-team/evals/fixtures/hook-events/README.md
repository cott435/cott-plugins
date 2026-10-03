# Fixture — `hook-events`

Recorded hook inputs for the five scripts under `hooks/`, one case per path through each,
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
files to write first, the attempt counter to preset, the transcript, the event (`{cwd}` stands for
the repo), and what must hold after: exit code, stderr, files, `.dev-team/gate/<pkg>/<section>.txt`,
the counter.
`check.py`'s docstring lists every key.

`build.py` makes the gate's repo: the brief and dataset from `two-package/`, the `data`
contract (`ingest` and `surface` rows), a `docs/constraints.md` whose Floor and Enforced rows
pass with `ruff` on PATH, and a `docs/deviations/data/ingest.md` with one `proposed` entry
citing `design §5 load_trades`; then one commit, summary `data/ingest: …`, carrying
`Dev-Team-Run: run-package data` with `data/ingest`'s code, README, one green unit test and two
intent tests, one green and one red that cites that clause. So the unmodified repo is the tolerated case, and every other gate case is one edit
on top of it. The coverage case stands a failing one-line command in for a coverage tool,
since `pytest-cov` is not assumed installed.

Since 2.2 (`site/notes/2.2-03-gate.md`) the gate is gated on one section, read from the
implementer's spawn prompt: a case's `setup.transcript` is written as the first `user` record
of the JSONL the event's `agent_transcript_path` names, and `setup.transcript_file` copies a
recorded one instead (`transcripts/agent-implementer-ingest.jsonl`, recorded in 2.2's phase 0;
`gate-recorded-transcript` reads it). Every gate case carries `Section: data/ingest` but these:
`gate-surface` (`data/surface`), `gate-scaffold` and `gate-scaffold-marker` (`Scaffold: data`),
and the four that exercise 2.1's diff-based discovery, the fallback — `gate-fallback-no-transcript`
(no file), `gate-fallback-no-section-line`, `gate-no-section` and `gate-surface-before-design`
(no `Section:` line). The built section carries one unit test, so every section run shows
`PASS unit data/ingest`. The 2.2 cases: the section from the transcript with a sibling's
half-built file `ELSEWHERE`; a sibling's marker ignored and the section's own marker and the
scaffold marker honoured; the diff since the newest review's `Commit:` (`{RUN_SHA}` in a
case's files) with the same `# noqa` caught after the review and not before it; the unit
suite red and missing (`setup.remove`); a `repo` pytest row `SKIPPED`; a failure in another
section's file `ELSEWHERE` whether committed or dirty; and the retry message's commit rule. A
failure outside the section is `ELSEWHERE` whether or not the run touched the file, so
`gate-elsewhere-touched`, a FAIL under 2.1, expects `ELSEWHERE` since 2.2.

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

The `guard-*` cases (2.2, `site/notes/2.2-04-guards.md`) run `guard_writes.py` in an `arch`
repo. The 2.1 ones keep their events and expectations, the role-wide rule. The 2.2 section
cases also write a `data` contract (`ingest`, `clean`, `surface`) and a `setup.transcript`: a
`PreToolUse` event carries no `agent_transcript_path`, so `check.py` writes it where the guard
derives it, `<transcript_path minus .jsonl>/subagents/agent-<agent_id>.jsonl`. An implementer
on `data/ingest` writes its own code, unit tests, inbox, ledger (new and old path), scratch
under `.dev-team/tmp/` and marker, and is refused a sibling's code, unit tests, inbox and
marker, its intent tests, `docs/decisions.md` and the package `pyproject.toml` (the refusal
names `locked.py`). On `data/surface` it may write `interface.md` and `mkdocs.yml`. A
`Scaffold:` run and a missing transcript fall back to the role-wide rule. The role cases cover the
2.2 paths: the designer's inbox allowed and `docs/decisions.md` refused, a review under
`docs/packages/<pkg>/reviews/<section>/` allowed to the reviewer and refused to the architect,
and a change file under the package allowed to the architect.

The nineteen `bash-*` cases (same note) pipe `tool_input.command` into `guard_bash.py`:
a redirect, an append with a here-document, `sed -i`, `tee`, `python3 -c` opening for write,
a chain whose second half redirects, and a reviewer's redirect are refused. Allowed are
`/dev/null`, `.dev-team/tmp/` (relative and absolute), `2>&1`, `python3 -c` that only reads,
and two `locked.py` commands (`{plugin}` in the event stands for this plugin's root). An
unparseable command fails open with the rule on stderr, and the main thread, `Explore`, an
out-of-scope repo and malformed stdin exit 0.

The phase-12 cases (`site/notes/2.2-12-run-fixes.md`): `gate-guarded-intent-elsewhere` (an
`xfail` whose reason is a constant, in the section's intent tree: `ELSEWHERE guarded … (the
tester's file)`, and the gate passes), `gate-guarded-decision-constant` (`reason=D5_OPEN` in a
unit test cites D5: no Guarded hit), `gate-intent-test-fail-still-fail` (a red intent test is
still `FAIL intent`, while the lint failure in the same file is `ELSEWHERE`); `sync-mirror-edit`,
`sync-mirror-removal`, `sync-mirror-other-section` and `sync-mirror-idempotent` (a section's own
central `Applied:` lines follow its inbox; another section's are untouched);
`bash-python-stdin-refused`, `bash-python-heredoc-no-script-refused` and
`bash-python-stdin-read-allowed` (a python here-document script), `bash-locked-sed-refused` and
`bash-locked-sh-refused` (`locked.py` exempts only `uv add|remove|lock|sync` and the
`.gitignore` printf, which `bash-locked-allowed` and `bash-locked-uv-add` keep allowed); and, from 12.7's stop, `guard-implementer-surface-package-pyproject` and
`guard-implementer-surface-api-page` (a `surface` implementer writes its package
`pyproject.toml` and `docs/api/<pkg>/index.md`, while `guard-implementer-section-pyproject`
still refuses the package `pyproject.toml` to `ingest`).

**The 2.4 record** (`site/notes/2.4-02-gate-record.md`). Every record now carries a
`commit:` line on line 2, the newest commit touching the section's code, unit tree and README
(`status.py`'s `gate_commit`), so `status.py` can tell which commit it speaks for; `--report`
records carry it too. A marker stop is recorded instead of leaving no trace: header slot
`blocked` or `spec-change`, the `commit:` line, the earlier attempt's check lines when this
agent already ran a gate attempt, `blocked: <the marker's second line>` (or `spec-change:
<heading>`), and `result: blocked` (or `spec-change`). `check.py` substitutes `{RUN_SHA}` in
`expect` strings as in `setup.files`, and `gate_only` skips `commit:`, `blocked:` and
`spec-change:` lines. The cases: `gate-record-commit` (`gate-pass`'s setup; `commit:
{RUN_SHA}`, `result: pass`); `gate-own-marker` and `gate-marker` (unchanged setups, the record
now written: `blocked: (no reason given)` and `blocked: D4 needs an answer`, `result:
blocked`); `gate-marker-after-fail` (an `attempt 1` record with a `FAIL intent …` line and
`result: not done`, then a `blocked` marker: the FAIL line is carried, the old header and
result are gone); `gate-marker-spec-change` (`spec-change: data/ingest — 2026-09-27 —
spec-change:test — 1`, `result: spec-change`); `gate-marker-no-reason` (a one-line marker:
`blocked: (no reason given)`); and `gate-report-base`, which also checks for the `commit:`
line.

**The 2.4 guards** (`site/notes/2.4-04-entry-points-and-guards.md`). Both guards also act in a
repo that has `docs/brief.md` and no `docs/architecture.md` (`bash-brief-only-refused`,
`guard-brief-only-refused`, `guard-brief-only-allowed`, in a `plain` repo plus the brief). A
refused redirect now reads `may not redirect to <target>: it is outside .dev-team/tmp/`
(`bash-redirect-wording`), so `bash-append-refused`, `bash-chain-refused`,
`bash-locked-sh-refused`, `bash-redirect-refused` and `bash-reviewer-refused` expect that text
instead of `redirect: <target>`; every other refusal keeps `may not write a repo file from the
shell (…)`. A researcher may redirect outside the repo root (`bash-researcher-outside-allowed`)
and not inside it (`bash-researcher-inside-refused`). `entry_point.py` is let through only under
`locked.py deps` for the package the caller's `Section:` names, with the `ingest`/`clean`/`surface`
contract and a `Section: data/ingest` transcript as in the `guard-implementer-section-*` cases:
`bash-locked-entry-point-allowed`; refused for another package
(`bash-locked-entry-point-other-pkg-refused`), unwrapped (`bash-entry-point-unwrapped-refused`)
and with no transcript (`bash-locked-entry-point-no-section-refused`). The write guard refuses a
`surface` implementer a sibling section's code, naming its owner
(`guard-surface-sibling-code-refused`), while the package's own `__init__.py` stays allowed
(`guard-surface-own-init-allowed`); and refuses a tester a Write or Edit that adds a suppression
comment under `tests/intent/` (`guard-tester-noqa-write-refused`,
`guard-tester-type-ignore-edit-refused`), counting old against new, so an Edit that keeps an
existing `# noqa` passes (`guard-tester-noqa-existing-kept`) and an event with no text fails open
(`guard-tester-no-text-allowed`).

**The 2.4 gate checks** (`site/notes/2.4-05-gate-checks.md`). `build.py`'s README now has an
**Entry points and interfaces** table with one row, `` `load_trades` ``, `Public: yes`, and the
contract a **Public surface (intent)** item naming it, so every `data/ingest` record carries
`PASS surface names data/ingest` (`gate-surface-names-pass`) and a grouped cell fails it
(`gate-surface-names-grouped-fail`). Removed asserts are a net count per file and per kind:
`gate-assert-rewritten-pass` rewrites the unit test's one assert (`load_trades(csv_file)` to
`load_trades(str(csv_file))`) and passes, while `gate-assert-dropped-fail` deletes it
(`(1 removed, 0 added)`) and `gate-raises-dropped-fail` replaces a `with pytest.raises(…)`
block, committed under `prior`, with a plain call; all three put a round-1 review at
`{RUN_SHA}`, so the diff starts there and has removed lines at all. A wrapped
`@pytest.mark.xfail(` call is read to its closing bracket: `reason="D3 open"` two lines down
passes (`gate-xfail-wrapped-pass`), `reason="later"` fails at the decorator's line
(`gate-xfail-wrapped-no-decision-fail`). `gate-tail-ruff-arrow` stands a Floor row in for ruff
0.15, printing ` --> <path>:3:1` under its message with three lines after it; the FAIL line
keeps the arrow line. The command builds the path from two strings, so only the output, not
the command echoed in the FAIL line, can hold it. No earlier case removed or rewrote an assert,
so none changed its expectation.

**The 2.5 lint floor** (`site/notes/2.5-readability-01-lint-floor-and-cap.md`). The plugin's
lint block requires ruff 0.16.0 or later, so both suites run with such a ruff first on PATH; the
plan's shim is `evals/workspace/bin/ruff`. `fmt-positional-cap` (six positional parameters:
`PLR0917`) and `fmt-keyword-only-free` (three positional, four keyword-only: clean) pin the
cap; `fmt-no-config` now lacks both the old and the new code. Six cases whose planted files
tripped a rule ruff's defaults gained were repaired without changing what they test:
`fmt-repo-config`, `gate-diff-before-review`, `gate-guarded-decision-constant`,
`gate-guarded-exception`, `gate-report-fail`, `gate-xfail-wrapped-pass`.

**The 2.5 shape check** (`site/notes/2.5-readability-02-shape-slice.md`). Every section run,
and `--report`, now runs `status.py --shape <pkg> --section <section>` and copies its lines, so
every `data/ingest` record carries `PASS shape data/ingest` (`gate-shape-pass`,
`gate-report-shape`). `gate-shape-trivial-helper-fail` writes
`packages/data/src/data/ingest/helper.py`, whose `_strip` is a one-statement private helper
with one call site, and the gate fails at its `def` line with the retry text that explains a
`FAIL shape` line. `gate-shape-helper-before-review` commits the same file under `prior` and
puts a round-1 review at `{RUN_SHA}`, so the helper is not on an added line and passes.
`helper.py` passes ruff's defaults, so no case gained a lint line, and no earlier case changed.

**The 2.5 shape check, complete** (`site/notes/2.5-readability-05-shape-complete.md`). The gate
itself is unchanged; `--shape` now also fails an added options bag and prints two `MEASURED`
lines. `gate-shape-options-bag-fail` writes `packages/data/src/data/ingest/bag.py`, whose
`load_with` takes `**options: Unpack[LoadOptions]`, and the gate fails at its `def` line;
`gate-shape-measured` (`gate-pass`'s setup) passes with `MEASURED shape indirect: 0`, a
`MEASURED shape depth load_trades:` line and `PASS shape data/ingest` in the record. Every
`data/ingest` record now carries `MEASURED` lines, so `gate-pass` and `gate-elsewhere`, the two
cases whose `gate_only` list would otherwise reject them, gained `MEASURED` there.

**The 2.2 layout here.** `build.py` still writes the section's ledger at the 2.0 path,
`docs/deviations/data/ingest.md`, so the tolerated case also proves the gate reads the old
location; the new one, `docs/packages/data/deviations/ingest.md`, is written by
`guard-implementer-section-ledger-new`, and reviews at `docs/packages/data/reviews/ingest/`
appear in `gate-diff-since-review`, `gate-diff-before-review` and the reviewer and architect
guard cases. Every record is `.dev-team/gate/<pkg>/<section>.txt`, and every marker case writes
the per-section `.dev-team/stop/<pkg>/<section>` (or `.dev-team/stop/scaffold`); no case
writes the 2.1 single marker. Decision stubs and `Applied:` lines live in
`docs/packages/data/decisions/<section>.md`, the `sync-*` cases' inbox.

Needs ruff 0.16.0 or later on PATH and `pytest` importable by `python3`.
