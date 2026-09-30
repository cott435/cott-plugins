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

**The 2.2 layout here.** `build.py` still writes the section's ledger at the 2.0 path,
`docs/deviations/data/ingest.md`, so the tolerated case also proves the gate reads the old
location; the new one, `docs/packages/data/deviations/ingest.md`, is written by
`guard-implementer-section-ledger-new`, and reviews at `docs/packages/data/reviews/ingest/`
appear in `gate-diff-since-review`, `gate-diff-before-review` and the reviewer and architect
guard cases. Every record is `.dev-team/gate/<pkg>/<section>.txt`, and every marker case writes
the per-section `.dev-team/stop/<pkg>/<section>` (or `.dev-team/stop/scaffold`); no case
writes the 2.1 single marker. Decision stubs and `Applied:` lines live in
`docs/packages/data/decisions/<section>.md`, the `sync-*` cases' inbox.

Needs `ruff` on PATH and `pytest` importable by `python3`.
