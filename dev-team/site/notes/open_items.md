# Open items

## 1. A section implementer cannot register an entry point in its package's `pyproject.toml`

Found 2026-10-01 during `/dev-team:run-package core` in the `pt` repo
(`/Users/connorott/PycharmProjects/pt`), plugin 2.2.0. Re-checked against the 2.3.0 source in
this folder: the gap is unchanged.

### The problem

Nothing in dev-team lets a section other than `surface` add an `[project.entry-points."<group>"]`
line to its package's `pyproject.toml`. When a design needs one, the implementer cannot build
it. The section's tests then cannot pass, and the run stalls until the user edits
`pyproject.toml` by hand and commits it.

In `pt`, three sections of the `core` package each needed one:

| section | entry point it needs | why |
|---|---|---|
| `core/db` | `[project.entry-points."pt.migrations"]` `"core.db" = "core.db"` | the Alembic harness finds every package's migration directory through the `pt.migrations` group; without it, 12 intent tests fail with `core.migration_root_missing` |
| `core/events` | same group, `"core.events" = "core.events"` | the `core_outbox` table's revision is never found, so every DB-backed events test fails |
| `core/testing` | `[project.entry-points.pytest11]` `core_testing = "core.testing.plugin"` | the shared pytest plugin is only loaded through `pytest11`; without it, every fixture test fails |

What happened in the run:

- The `core/db` implementer returned `Result: blocked` because its Edit of
  `packages/core/pyproject.toml` was refused. The user added the line by hand (pt commit
  `0f3d9f9`) and the step was re-run.
- The `core/events` implementer returned `Result: done` with `Gate: not yet run` and a "needed
  from elsewhere" note asking for the same edit. The user added it by hand (pt commit
  `b9d7503`) and the step was re-run.
- The `core/testing` designer saw the problem coming. Its OQ-core-testing-1 says the implementer
  adds the `pytest11` line "by hand if its write guard refuses". The implementer was refused and
  reported it under "needed from elsewhere", and the run is waiting on a third hand edit.

Each section built its code, then needed the driver, the user, a hand commit and a re-spawn.
This was a property of the design, not something any agent did wrong.

### Why it happens

Every layer of the plugin assumes a non-`surface` section touches `pyproject.toml` only to add
or remove dependencies:

1. **The write guard** (`hooks/guard_writes.py`, `SECTION_SCOPE`, around lines 97–106) confines
   a section implementer to its own path, `tests/unit/<section>/`, fixtures, its ledger and
   inbox, and `.dev-team/tmp/`. Only `section == "surface"` adds
   `<package root>/pyproject.toml`, the root `pyproject.toml` and `mkdocs.yml`. The module
   docstring (around line 28) says the package `pyproject.toml` is in scope only for its
   `[project.scripts]`.
2. **`locked.py`** (`skills/status/scripts/locked.py`) runs one command under a mkdir lock. Its
   docstring names only `deps` (for `uv add`) and `gitignore`.
3. **The bash guard** (`hooks/guard_bash.py`) lets a `locked.py` command through only when the
   inner command is `uv add|remove|lock|sync` (`LOCKED_UV`, around line 44; `_locked`, around
   lines 147–155) or the `.gitignore` `printf` block. None of these can write an entry-point
   table: `uv add` edits `[project.dependencies]` only.
4. **`agents/implementer.md`** states the same rule. **Files outside your section** (around lines
   477–490) says that outside `surface`, the package `pyproject.toml`, `uv.lock` and `.gitignore`
   are edited "through `locked.py` only (step 2)". Step 2 (around lines 306–321) covers only
   `uv add` and the `.gitignore` block.
5. **The designer and architect have no matching rule.** `agents/designer.md`'s **Module plan**
   (around line 213) and the architect's contract can give a section a `pyproject.toml` change,
   such as an entry point, that the section's implementer will never be allowed to make. No
   check catches this before the build.

Deferring the edit doesn't fix it:

- **Leaving it to `surface` doesn't work.** `surface` is always the last section, and the
  section that owns the entry point needs it for its own tests and stop gate.
- **Adding it in the scaffold doesn't work.** An entry point whose target module doesn't exist
  yet breaks loading. A dangling `pytest11` entry breaks every pytest run in the workspace. A
  dangling `pt.migrations` entry breaks the harness. The entry point has to land in the same
  step as the module it names.

### Second symptom: a blocked implementer still advances the row

When the first `core/db` implementer returned `blocked`, it had already written
`packages/core/src/core/db/README.md`. `status.py` derives IMPLEMENT → REVIEW from that README
existing (`skills/status/scripts/status.py`, state rule 6 around line 27, `readme` around line
436, REVIEW around line 1005). So the next `status.py` showed `db · REVIEW · no review · yes`,
although the stop gate had never passed. A driver following `run-package` literally would have
sent two reviewers to judge code whose gate never ran. Gating IMPLEMENT → REVIEW on the
section's gate file (`.dev-team/gate/<pkg>/<section>.txt` showing PASS for the current code)
rather than on the README alone would close this. Decide whether that belongs with this fix
or is a separate item.

### Files to change

- `skills/status/scripts/locked.py`: add an entry-point operation. For example,
  `python3 locked.py deps -- entry-point --package <pkg> <group> <name> <target>`, under the same
  `deps` lock as `uv add`, since both rewrite the package `pyproject.toml`. It adds or replaces
  one line under `[project.entry-points."<group>"]` in `<package root>/pyproject.toml`, creating
  the table if needed, then runs `uv sync --all-packages`. Use a TOML-preserving edit (for
  example `tomlkit`, or a careful text insert if the script must stay stdlib-only) so comments
  and order survive. Refuse a `<target>` outside the caller's own package. Optionally, refuse a
  target module whose file under `src/<pkg>/` doesn't exist yet, so a dangling entry can't land.
- `hooks/guard_bash.py`: allow the new inner command in `_locked` (next to `LOCKED_UV`), and
  update the module docstring (around line 12).
- `hooks/guard_writes.py`: no scope change needed if the edit goes through `locked.py`. The
  write guard stays strict. Update the docstring to mention the entry-point path.
- `agents/implementer.md`: in step 2 (around lines 306–321), add "**Your entry points**" next
  to "Your dependencies", with the exact `locked.py` command. Mention it in **Files outside
  your section** (around lines 477–490). Make it explicit that the entry-point line goes in the
  same commit as the module it targets.
- `agents/designer.md`: in the **Module plan** guidance (around line 213), say that an entry
  point the section owns is listed there and built through `locked.py`, never "by hand".
- `skills/workspace-scaffold/SKILL.md` §2 (package `pyproject.toml`): note that entry-point
  tables other than `[project.scripts]` are added by the owning section's implementer through
  `locked.py`, not by the scaffold.
- `skills/status/scripts/status.py`: only if the second symptom is taken on (IMPLEMENT → REVIEW
  gated on a passing gate file, not only the README).
- `README.md`, `CHANGELOG.md`, and `contracts.yml` if it pins the list of `locked.py`
  operations or the `LOCKED_UV` set. Check with `/plugin-dev:check-contracts` after the edit.

### How to verify

Re-run a section whose design registers an entry point, from a clean checkout before the hand
commits. For example, in `pt`, `core/testing` (or `core/db` at `b2dfaad^` with `0f3d9f9`
reverted). The implementer should add the line through `locked.py`, run the gate green, and
return `done` without a "needed from elsewhere" note and without any edit by the user.

## 2. Two open spec-changes of one level: answering the first silently closes the second

Found 2026-10-01 during `/dev-team:run-package lm` in the `slm` repo
(`/Users/connorott/PycharmProjects/slm`), plugin 2.3.0. The installed copy
(`~/.claude/plugins/cache/cott-plugins/dev-team/2.3.0/skills/status/scripts/status.py`) matches
the source in this folder byte for byte.

### The problem

When one commit adds two ledger entries of the same level for a section, for example two
`spec-change:test` entries, the driver passes only the first to the agent that answers it. That
agent's commit then makes `status.py` treat **both** entries as answered. The second entry still
says `Status: open` in the ledger, but `status.py` no longer reports it. The row moves on to
IMPLEMENT and then REVIEW while an intent test that no code can pass is still in the tree.

What happened in `slm`, section `lm/checkpoint`:

1. The implementer (commit `d058488`) appended two entries to
   `docs/packages/lm/deviations/checkpoint.md` in the same commit and returned
   `Result: spec-change`:
   - `lm/checkpoint — 2026-10-01 — spec-change:test — 4`: case 22 compared logits against an
     in-memory bf16-cast model. The comparison can never be exact, because the non-persistent
     `rotary_emb.inv_freq` buffer is rebuilt in float32 on load.
   - `lm/checkpoint — 2026-10-01 — spec-change:test — 5`: the test helper
     `_edit_json(path: Path, **changes)` is called as `_edit_json(..., path="lm-open")`. That
     raises `TypeError: got multiple values for argument 'path'` before any section code runs.
2. `status.py lm` showed only the first entry:
   `checkpoint · TEST · open lm/checkpoint — 2026-10-01 — spec-change:test — 4 · …`.
3. The driver spawned the tester with `Regenerate: lm/checkpoint — 2026-10-01 — spec-change:test
   — 4`, as `run-package` says. The tester fixed entry 4, set it to `resolved`, and correctly
   reported entry 5 under "Not regenerated" because `Regenerate:` did not name it. It committed
   the intent tree (`64aad39`) with entry 5 still `Status: open` and 178/179 tests passing.
4. The next `status.py lm` showed `checkpoint · IMPLEMENT · no …/checkpoint/README.md · yes · — ·
   — ·`, with the open spec-change column at `—`. Entry 5 had disappeared from the derived state.
5. The implementer ran again, hit the same broken test, and returned `Result: spec-change`
   naming the existing entry 5 (it added no new entry). The stop gate deleted the marker
   `.dev-team/stop/lm/checkpoint` without running checks, as designed for a `spec-change`
   marker. The implementer had written the README, so `status.py` showed
   `checkpoint · REVIEW · no review · yes · — · — · 84974c6`.
6. A driver following `run-package` literally would now send two reviewers to code whose intent
   suite has a known red test. They would request changes, and the FIX implementer would hit the
   same wall. The run had to stop and ask the user. No step in the loop can reach entry 5: the
   tester's `Regenerate:` value comes only from the row's evidence, and the evidence no longer
   names it.

### Why it happens

Two separate defects. Either one alone would have been enough to cause this:

1. **`answered()` ignores the entry's `Status:` and decides by commit order alone.**
   In `skills/status/scripts/status.py`:
   - `open_spec_changes()` (around line 626) correctly keeps entries with `Status: open`.
   - `live_spec_changes()` (around line 692) then drops every entry for which
     `answered(entry, rev)` is true. `rev` is the latest commit of the design (for
     `spec-change:design`), the intent tree (for `spec-change:test`) or the contract.
   - `answered()` (around line 643) returns `_newer(rev, entry_rev(entry))`. `entry_rev()`
     (around line 630) is the commit that first added the entry's heading (`git log -S`). So any
     commit to the intent tree after `d058488` "answers" every `spec-change:test` entry added in
     or before `d058488`, whatever it actually changed and whatever the entry's `Status:` says.
   - The module docstring (state rule 4, around line 21) gives the reason: "the designer's rewrite
     answers it, and nobody sets its `Status:`". That is no longer true. `agents/tester.md`
     (around lines 44 and 255) has the tester set `Status: resolved` and `Resolved by:` on each
     `spec-change:test` entry it regenerates for, and `agents/designer.md` (around lines 27 and
     163) does the same for `spec-change:design`. The agents keep `Status:` accurate, and
     `status.py` throws that information away.
   - For a report-raised spec-change (`report_spec_changes()`, around line 671, `source:
     "report"`), there is no ledger `Status:`, so commit order is the only signal there. That
     case can keep the current rule.

2. **Only one entry per level reaches the agent that answers it.**
   - `section_state()` (around line 923) picks the first live entry of each level for the row's
     evidence: `next(e for e in spec if e["kind"] == "spec-change:test")` (around line 983), and
     the same `next(...)` for `spec-change:design` (around line 962) and `spec-change:contract`
     (around line 947). The other open entries of that level never appear in the evidence.
   - `skills/run-package/SKILL.md` builds the agent fields from that evidence, one heading each:
     the tester's **Regenerate** row (around line 137: "the entry heading from the row's
     evidence"), the designer's **Spec-change** row (around line 118), and the architect's
     **Spec-change** row (around line 209: one line per PLAN row).
   - `agents/tester.md` **Inputs** item 8 (around line 96) already accepts several headings, "one
     per line", so the tester side needs no change. The single heading comes from `status.py`
     and the driver.

The same mechanism applies to `spec-change:design`. Two design entries raised in one commit lead
to one designer rewrite, which closes both while the designer was handed only one. It has not
been observed yet.

Related: open item 1's second symptom (IMPLEMENT → REVIEW is derived from the README alone) is
what let the row reach REVIEW in step 5 above, even though the gate never ran the checks.

### Files to change

- `skills/status/scripts/status.py`:
  - `answered()`: for a ledger entry (`entry.get("source") != "report"`), stay open while
    `_status(entry) == "open"`. A reasonable rule is answered iff `Status` is no longer `open`
    **and** the answering document was committed after the entry. The second condition keeps
    an uncommitted `resolved` edit from closing it early. Keep the commit-order-only rule for
    report-raised entries. `spec-change:contract` stays architect-closed as now.
  - Rewrite the docstring sentence at state rule 4 ("nobody sets its `Status:`") and the
    **open spec-change** paragraph (around lines 58–65) to describe the new rule.
  - `section_state()`: put every live entry of the winning level into the evidence, not only the
    first. For example `open <heading 1>; <heading 2>`, or one `open <heading>` per entry
    separated in a way the driver can split. Do this for `:test` (around line 983), `:design`
    (around line 962) and `:contract` (around line 947). Check every parser of the evidence
    string. The row's `open spec-change` column (around line 1050) already lists kinds, not
    headings, so it is unaffected. `spawn_fields()` (the `--fields` output, around line 1486)
    derives `mode: delta` from `evidence.startswith("open ") and "spec-change:design" in
    evidence`. It still works with several headings, but needs re-checking against the new
    format.
  - Optional: when a spec-change entry is `open` but its level's document has been committed
    after it, report a distinct evidence string (e.g. `open <heading> (not answered by <sha>)`),
    so the condition is visible instead of silent.
- `skills/run-package/SKILL.md`:
  - Tester **Regenerate** row (around line 137): every heading the evidence names, one per line.
  - Designer **Spec-change** row (around line 118) and architect **Spec-change** row (around
    line 209): the same, so that each agent receives every open entry of its level.
- `agents/designer.md`: check that its **Spec-change** input accepts several headings, like
  `agents/tester.md` item 8 does, and that it sets `resolved` on each one it answers.
- `agents/implementer.md` (**Deviations and spec-changes**, around lines 624–667): say what to do
  when a still-open entry already describes the blocker. Today the second implementer returned
  `spec-change` naming the existing entry 5. Once `status.py` honors `Status: open`, that is the
  right behavior, because the open entry re-opens TEST by itself. Confirm the wording says so.
- `contracts.yml`: the rule "ledger entry fields its readers parse are ones planning-templates
  defines" (around line 307) lists the readers of `Status`. If a contract pins `status.py`'s
  evidence format or the driver's one-heading fields, update it. Run
  `/plugin-dev:check-contracts` afterwards.
- `CHANGELOG.md`: a patch entry.

### How to verify

- Unit-style check of `status.py` on a scratch git repo. One commit adds two
  `spec-change:test` entries for a section that has a design and an intent tree. A second
  commit touches the intent tree and sets only the first entry to `resolved`. `status.py <pkg>`
  must still show the section at TEST with the second entry's heading in the evidence. After a
  third commit sets the second entry to `resolved` (with an intent-tree change), the row must
  advance.
- With the evidence change: the same setup with both entries open must print both headings in
  the evidence, and the driver must pass both in `Regenerate:`.
- Repro in `slm`: check out `d058488` (both entries open, before the tester's `64aad39`) and run
  `status.py lm`. With the fix, the tester should be handed entries 4 and 5 together, and
  `lm/checkpoint` should not reach REVIEW with `test_load_manifest_path_disagrees` failing.

## 3. Fixed on 2026-10-01 but never run: the 9ecf4176 audit's definition edits

Context for the items below (3 to 12). On 2026-10-01 `/plugin-dev:audit-run` audited a real
`/dev-team:run-package lm` run: session `9ecf4176-309c-419e-9ecc-573e6a5026cd`, chat titled "Plan
package LM", repo `slm` (`/Users/connorott/PycharmProjects/slm`), plugin 2.3.0, 35 agent runs
(units `U01`–`U35`) over about 10 hours. 12 units were audited, plus the driver and a cross-run
check. Result: 12 errors after merging (31 as filed), 25 warnings, 41 notes. The committed record
is `evals/2026-10-01-audit-run-package-9ecf4176.md`. The full report (`report.md`), the per-unit
findings (`findings/*.md`) and the traces (`units/U<nn>.md`, `driver/seg-1.md`, `run.md`,
`flow.html`) are in `evals/workspace/audit/9ecf4176/`, which is gitignored and exists only on the
machine that ran the audit. Step ids such as `U23.S79` or `D134` are lines in those traces. The
audit sampled 12 of 35 units, so every count below is a lower bound. No designer, researcher or
reviewer unit was audited, so those three agent types have no findings at all.

### What was changed

Commit `1e81553` (merged to `main` as `2a155b8`) edited `agents/tester.md`,
`agents/implementer.md`, `agents/designer.md`, `skills/run-package/SKILL.md`,
`skills/status/scripts/status.py`, and added the state case
`evals/fixtures/state-cases/test-spec-change-two-open/`. The fixes entry is
`evals/2026-10-01-audit-fixes-9ecf4176.md`. The mechanical checks passed: `check-contracts`
43/43, state cases 84/84, hook events 154/155 (`gate-fail-attempt-1` also fails on the unedited
2.3.0 tree). `build-site` was not run after the merge. **No agent or driver was run against any
of these edits**, so whether they change behavior is unknown. Each row says what a re-run must
show.

| Id | Edit | What a run must show |
|---|---|---|
| E1 | `status.py` (`section_state`, the `spec-change:test` branch): a TEST row's evidence is now `open <h1>; <h2>`, listing every open `spec-change:test` heading. `run-package/SKILL.md` Tester **Regenerate** row takes several headings, one per line. `implementer.md` ("A spec-change" paragraph): one stop writes one entry, a second defect goes in that entry's **Found**; a `spec-change:test` entry already `open` at spawn means write the marker naming it and return `Result: spec-change` at step 1, building nothing. `run-package/SKILL.md` step 5 and **Asking**: a `spec-change` return after which the section's next row is not PLAN, DESIGN or TEST is an Ask that quotes only the row | A section with two open `spec-change:test` entries gets one tester run that resolves both, and never reaches REVIEW with a red intent test. **Overlap with item 2:** this fixes only the "one entry reaches the answering agent" half, and only for `spec-change:test`. It does not touch `answered()` ignoring `Status: open`, nor the `:design` and `:contract` branches. Item 2 is still open |
| E2 | `tester.md` and `implementer.md` return sections: a count is the bare count, a heading is only the heading, no prose after the hand-back, a marker return has no line for what was left unbuilt; `Not written:` is for cases the documents do not support, not "fixtures unproven" | Returns with no parenthesis after `Suite:`, `Intent tests:`, `Deviations:`, `Spec-change:`; no `Not yet built:`, `Marker:` or `Security:` line. This was broken in 10 of 12 audited units, so the old wording did not hold |
| E3 | `implementer.md` step 4: security conclusions go in the README's **Implementation notes**, the return has no security line | No `Security:` line in a return, and the README says which `security-review` Verification steps ran or that none did |
| E4 | `tester.md` step 1 and `implementer.md` step 0: "Read" means the Read tool on the whole file, a `grep` or line range is not a read; `implementer.md` step 13: a last pass before committing (the `TODO(decision` grep ran, every upstream `interface.md` was read, the `security-review` Verification steps ran if the skill was invoked) | An upstream `interface.md` appears as a Read step in each section's trace; a `grep -rn 'TODO(decision'` precedes every "no markers" claim |
| E5 | `tester.md` step 2: an unconditional Read of `skills/test-driven-development/SKILL.md`. The old text said the skill was preloaded, but the frontmatter never listed it, and three of five testers skipped the fallback Read. README's skill table already says the tester reads it, so the skill was not added to the frontmatter | Every tester trace has the Read. Cost: the whole 373-line file is read for one paragraph, on every tester run |
| E6 | `tester.md`: a temporary test file that prints values (`test_zz_selfcheck.py` run with `pytest -s`) is a script, so no such file is written; a memory note recommending one is deleted when read. The project memory file that holds the note is `slm/.claude/agent-memory/dev-team-tester/testing-patterns.md` ("CORRECTION (2026-09-30)", about line 246). **It was not edited**: it lives in the `slm` repo | No `test_zz_selfcheck.py` in a tester trace. Delete or correct that note in `slm`, or the agents read it again |
| E8, E9 | `run-package/SKILL.md`: a session without Glob lists `docs/packages/<pkg>/reviews/<section>/` with `find` and tests existence with a one-line Read (`limit=1`), nothing else; the contract's Sections table is a Read; the changed rows are the next message after every `status.py` run | Driver trace: no `grep ... | head`, a `_said:_` with the rows after each `status.py` run |
| E11 | `tester.md`: a `delta` run with no tests at the path is `new`, and `Deleted for passing:` carries its count; `designer.md`: `Mode: delta` stays on a never-built section | A tester sent `Design mode: delta` for a section with no tests writes the whole tree and reports a numeric `Deleted for passing:` |
| Test paths | `designer.md` **Tests** and `implementer.md` step 9: integration and end-to-end cases, the section conftest and fixtures all go under `tests/unit/<section>/` and `tests/fixtures/` | No deviation entry about moving `tests/integration/`. The write guard (`hooks/guard_writes.py`, `SECTION_SCOPE`) allows no other test path |
| Small | `implementer.md`: a section that parses no API response copies no `<source>.sample.json` and says so in the README; a runtime `pytest.skip` the design names is not **Guarded**. `tester.md`: the 88-column limit is stated at the Write step | Fewer E501 hook blocks in tester and implementer traces (about 40 in the audited run) |

Verify by re-running `/dev-team:run-package` on a package whose sections hit these cases, then
audit it with `/plugin-dev:audit-run`. A cheaper partial check: run `tester` and `implementer`
evals (`evals/sets/tester.json`, `evals/sets/implementer.json`) and look at the return shape.

## 4. HIGH: returns state checks and counts that no step in the run produced

### The problem

Implementers' returns say `lint-imports: 8 kept, 0 broken`, `ruff format --check ... clean`,
"designer's entries 1–3 were built as designed", or "loads no files / takes no user input", and
the trace holds no output that shows it. The driver branches only on `Result:`, so nothing breaks
at run time. The reviewer and the user read these lines as fact, and `run-package` tells the
driver never to check them.

Evidence (all from slm session 9ecf4176): `U07.S75` and `U07.S82` (the return's `lint-imports`
and `ruff format` results are in no command output; the one command that ran them printed
`…[311 chars]` and its visible part is a `wc -l`); `U23.S74` (`uv run lint-imports 2>&1 | tail
-8`, so the count may have been cut); `U32.S79` ("entries 1–3 built as designed", with no step
that compares code to entries); `U19.S73` (a security claim with no step checking it). Also
`U20.S65`, where the per-heading test counts were wrong (§3 20/19, §5 20/17, §7 27/29, §8 2
missing) because nothing computed them.

### Why it happens

`agents/implementer.md` (the paragraph "Every line states what this run did and saw", around line
745) says a count is the number a command printed in this run and a check called clean has its
command and output. Nothing enforces it. The run chains several checks into one Bash call with `|
tail`, which hides the lines the return later quotes. The return is written from memory of the
run. The step 13 pre-finish pass added on 2026-10-01 covers only three items (marker grep,
upstream read, security verification), not the check results. `agents/tester.md` return section
(around line 270) has the same rule for its counts.

### Files to change

- `agents/implementer.md`: the return section (around lines 745–790) and step 13. Say that each
  check result in the return is copied from a command run without `| tail` or `| head`, and that
  a result the run cannot point to is written `not run`. Consider having the return's check lines
  come from the stop gate's own record (the gate runs the same checks) instead of from the agent.
- `agents/tester.md`: the return section; `Tests: <n> written (<count by design heading>)` needs a
  command that prints the per-heading count, or the heading split is dropped.
- `agents/reviewer.md` (**The evidence**, line 115): state that the implementer's return is not
  evidence, only the gate output and the files are. Check it does not already say so.
- Optional, in `hooks/`: a hook that refuses `lint-imports` or `ruff` output piped to `tail`.

## 5. HIGH: an open decision's assumption is handled three different ways by three agents

### The problem

Decision `D12` in slm (`docs/decisions.md`, `Scope: lm`, `Status: open`, assumption
`Qwen/Qwen2.5-0.5B-Instruct`) binds the `lm` package. The three sections that met it each did a
different thing:

- `lm/prompt` implementer (`U23.S60`, `U23.S79`): built the assumption into its test fixture and
  its `SYSTEM_MESSAGE` default, left **no** `TODO(decision D12)` marker, and returned "no line
  affected". A later commit (`8630ae1`) had to add the markers.
- `lm/checkpoint` tester (`U30.S19`, `U30.S74`, `U30.S83`): wrote no xfail test for D12 and put no
  line for it under `Not written:`, although its own memory note said an earlier run missed
  exactly this. The design says D12 binds `surface`'s default argument, not this section.
- `lm/prompt` tester (`U20.S65`): reported D12 under `Not written:` instead of writing an xfail.

### Why it happens

`agents/implementer.md` lines 174–199 (**Any decision you build an assumption for gets a
marker**) describe code that hard-codes the assumed value. They do not say that a fixture or a
default that copies it counts, and `U23` read "the code is generic over templates" as "no line
affected". `agents/tester.md` line 125 (the `docs/decisions.md` row of the inputs table) and line
182 ("one per decision in scope") scope a decision by `Scope:` (`repo`, `<pkg>` or `<section>`),
while the design says which section the decision really binds. A package-scoped decision that
the design assigns to another section has no defined handling.

### Files to change

- `agents/implementer.md` lines 174–199: a fixture, default or constant that copies an open
  decision's assumed value takes the marker. Add the check to the step 13 pre-finish pass.
- `agents/tester.md` lines 125 and 182, and the **Inventory** step: a decision in scope that the
  design says binds another section gets a `Not written:` line naming the decision and the
  section the design assigns it to; one the design leaves open gets the xfail.
- `agents/designer.md`: give the design a short line naming which in-scope decisions bind this
  section, so the tester and implementer need not infer it (check whether **Open questions** or
  **Skills used** already carries it).

## 6. HIGH: a second probe of a shared source re-opens every built consumer of it

### The problem

In slm, `lm/prompt` and `lm/checkpoint` both read `docs/sources/hfhub.md` (an `api` source). The
probe run for `lm/checkpoint` (`U26`, commit `4bc7ad6`, +2202/−226 lines) extended the shared
document, and its own return said "Nothing written for lm/prompt changed". The next `status.py`
showed `prompt · DESIGN · docs/sources/hfhub.md 4bc7ad6 newer than design 365907d` (`D98`,
`D99`), although `lm/prompt` was already built and approved. That cost four more agent runs
(`U27`, `U29`, `U31`, `U33`) and one extra review round, to redesign a section nothing had changed
for. The designer's return (`U27`) said "nothing in the probe's lm/prompt section changed".

### Why it happens

`skills/status/scripts/status.py` `_probe_newer` (around line 868) re-opens DESIGN when the probe
doc changed since the design, ignoring only edits to **other sections' `## <pkg>/<section>`
entries** (`_strip_other_sections`). The document's shared body (observed schema, limits, the
sample) is not section-specific, so a probe for a second section that adds to or rewrites it
looks like a change to every consumer's input. `agents/researcher.md` (around lines 311–318) says
to keep the document and extend it, but does not separate additive changes from changes that
alter what a built section relied on.

### Files to change

- `skills/status/scripts/status.py` `_probe_newer`/`_strip_other_sections`: decide what counts as
  a change to a built design. Options: ignore a shared-body diff that only adds lines; or compare
  only the parts of the doc the design cites; or re-open DESIGN only when the section is not
  already DONE.
- `agents/researcher.md` lines ~311–318: have the probe say, in a line the status derivation can
  read, whether the shared body changed or only grew.
- `skills/run-package/SKILL.md` (the DESIGN step): if the design is to be re-confirmed rather than
  rewritten, a lighter step than a full designer run. Add state cases under
  `evals/fixtures/state-cases/` (the existing probe cases show the shape; `README.md` there
  explains the macros).

## 7. HIGH: no kind for "an intent test fails before it reaches the code"

### The problem

`lm/checkpoint`'s intent test `test_load_manifest_path_disagrees` failed with `TypeError:
_edit_json() got multiple values for argument 'path'` (`U32.S63`): the test's own helper was called
with `path=` while taking `path` positionally, so the test could never reach the section's code.
The implementer filed it as `spec-change:test` (entry 5), but that kind's row says "the code and
the design agree, and an intent test asserts otherwise", which this is not. Together with the two
entries filed in one commit, this started the sequence in item 2.

### Why it happens

`agents/implementer.md` lines 646–653 (the table **Which one, by the clause**) has no row for a
defect in the test itself. The routing (the tester regenerates) is right by accident, but an
implementer has to guess the kind and writes an entry whose **Clause** and **Said** do not fit.

### Files to change

- `agents/implementer.md` lines 646–653: add a row, for example "an intent test fails before it
  reaches your code (its own helper, fixture or import is broken) → `spec-change:test`, **Found:**
  the traceback line", and state that the **Clause** is the test's docstring citation.
- `skills/planning-templates/references/deviations-entry.md`: check the entry template covers it.
- `agents/tester.md` **Regenerate** (around lines 244–265): a `spec-change:test` whose evidence is a
  broken helper is regenerated by fixing the test, with no clause change.

## 8. HIGH: a design case that the repo's lint forbids is rewritten silently, and dependency source gets read

### The problem

The `lm/tokenizer` tester (`U04`) had two design cases it could not write as named, and rewrote
both:

- design §7 integration test `test_ledger` "skipped when `STORE_DSN` is unreachable" became a test
  that sends the same rows through store's spool route, with no DB and no skip;
- design §7 "subprocess import" test was written in-process because ruff `S603` forbids
  `subprocess`.

Both were reported under `Not written:`, which the definition reserves for cases the documents do
not support and for lint failures left as designed (`lint: <file>:<line> <rule>, left as
designed`). No ruff run on a subprocess version appears in the trace (`U04.S83`). The same tester
read the upstream `store` package's source (`layout.py`, `verify.py`, `types.py`, `manifest.py`;
`U04.S26`, `S27`, `S33`) to learn the parquet schema for its fixtures. The implementer of
`lm/tokenizer` (`U07`) hit the same skip question and opened the hook source to settle it
(`U07.S37`–`S39`).

### Why it happens

`agents/tester.md` line 51 ("never the section's or a dependency's code to learn a fact for a
test") does not say whether reading, as opposed to running, upstream source is barred, and the
design gives the fact only there when the upstream `interface.md` is silent. Lines 67–76 say to
leave an honest test as the documents support it when a lint rule fires, but a design case that
needs a subprocess or a skip is neither a gap nor a lint failure left as designed. The designer
(`agents/designer.md` line 7, **Tests**) is not told that cases must avoid what the repo's lint
and the no-skip rule forbid.

### Files to change

- `agents/tester.md` lines 51 and 67–76, and the **Design gaps** section: say outright that
  reading upstream source to learn a fact is barred (or allowed, with a `Not written:` note), and
  that a case the repo's lint or the no-skip rule makes unwritable is a `spec-change:design`
  (a design defect), not a rewrite.
- `agents/designer.md` **Tests** (item 7): no case that needs `subprocess`, a skip or an
  unreachable service unless it names the substitute.
- The upstream `interface.md` rules in `agents/implementer.md` (the section that writes
  `interface.md`) so a package's schema facts are in its interface document and the tester need
  not read the source.

## 9. MEDIUM: every section gets every upstream package's `interface.md`, so it is skipped

### The problem

`run-package` sends the `Upstream interfaces:` field per package (`D24`, `D82`, `D114` each carry
`docs/packages/store/interface.md` for every `lm` section), including `lm/arch`, whose design says
"`store` is not consumed". Five units grepped the document for a name instead of reading it
(`U13.S17`, `U17.S15`, `U20.S16`, `U23.S15`, `U35.S23`–`S24`), and `U23` and `U35` then listed it
as "Consumed" in the README. A field that is mostly irrelevant is read as optional.

### Why it happens

`skills/run-package/SKILL.md` (**Resolving values**, around lines 76–78) derives upstream packages
from the package row's `depends on`, not from what a section's design consumes. `status.py` does
the same in `--fields`/`--inputs` (around lines 101 and 1457). The 2026-10-01 edit tells agents
to read each such document once, which treats the symptom and adds a read nobody needs for
`lm/arch`.

### Files to change

- `skills/run-package/SKILL.md` rows at lines 118, 138, 195 and the resolving paragraph;
  `skills/status/scripts/status.py` around lines 101 and 1457.
- `agents/designer.md` (the section list around **Dependencies** and item 6): have the design name
  the upstream packages the section consumes, and let the driver pass only those, or fall back to
  all of them when the design does not say.

## 10. MEDIUM: the driver has no rule for a free-text answer to an Ask, and ends without a Summary

### The problem

After the Ask at `D134` the user answered in free text ("Tell me what is wrong with dev-team that
causes this"). The skill has no case for that, so the driver switched to diagnosing the plugin: it
`cat`-ed the ledger, read `status.py`, and ran `git log -S` (`D136`–`D141`), all forbidden to a
run, then edited. The segment's last message (`D155`) was free prose, not the Summary block, so
the run printed no `run-package lm: stopped at ...` line, counts, commit range or `next:`.

### Why it happens

`skills/run-package/SKILL.md` **Asking** (line 303) says to record the answer and re-run the
loop, assuming the answer picks an option. The **Summary** section (line 342) says the block is
always the last message, but it does not say what to do when the user turned the session into
something else. The 2026-10-01 edit added an Ask case for a `spec-change` return with no
re-opened row, which reduces how often this arises, but the free-text case is untouched.

### Files to change

- `skills/run-package/SKILL.md` **Asking** and **Summary** (lines 303–345): say what a free-text
  answer means (an answer that is not one of the options ends the loop at the current state and
  prints the Summary; the driver does not diagnose the plugin).

## 11. MEDIUM: testers write one-off memory notes, leave suppressions in the tree and explore on a stop

### The problem

Four small recurring faults in tester runs:

- Memory notes that are one-off facts, not recurring patterns: `U04.S82` ("`transformers` are not
  in .venv until the implementer adds them") and `U13.S21` ("design said 14 config fields, table
  had 15").
- `U17.S31` wrote `# noqa: N812` into its tree, removed it after a hook block (`U17.S32`), never
  committed it. The rule bars writing one.
- A design-defect stop writes no tests, yet `U13` and `U16` read a 382-line sibling conftest,
  listed `.venv` `site-packages`, and grepped a 58 KB probe sample before logging a defect that was
  visible in the design text (`U13.S14`–`S17`, `U16.S13`–`S21`; `U16` took 131 seconds and 19
  calls).
- Two commands took the section path into scope (`U30.S25`, `U30.S80`: `ls packages/lm` and `git
  status --short packages/lm`).

### Why it happens

The rules exist (`agents/tester.md`: memory at line 356 "Record only recurring patterns"; no
suppression at about line 65; design-defect stop at about line 152 "writes no tree at all"; listing
rules at lines 31–37) but are stated once in a long prompt and no hook enforces them.

### Files to change

- `agents/tester.md` at those lines; the **Design defects** procedure should say the read set for a
  defect stop is the prompt's documents and nothing else.
- `hooks/` (the format-on-edit hook): optionally refuse a Write that adds `# noqa` or `# type:
  ignore` under `tests/intent/`.

## 12. MEDIUM: smaller ambiguities that made agents guess

Each is one line in a definition. All were hit in the audited run.

- **May a tester inspect `.venv`?** `agents/tester.md` lines 47–48 allow "read-only inspection of
  paths you may read" but do not say whether `.venv/lib/*/site-packages` is one (`U13.S15`,
  `U16.S20`).
- **A design signature that breaches `max-args`.** `U05` classed it as a `deviation`
  (`token_stats` takes `**options: Unpack[...]` because of ruff `PLR0913`). The contract states the
  same six-parameter signature, but `token_stats` is not on its Public surface table. The table at
  `agents/implementer.md` lines 646–653 does not say how a contract-stated, non-public signature
  is classed.
- **One test file for two Interfaces rows.** `U20.S47` wrote `EncodedPrompt` and `EncodedExample`
  in `test_encoded_models.py`, against `agents/tester.md` ("one `test_<interface>.py` per
  **Interfaces** row", about line 190).
- **Where a throwaway tool or server goes.** `U07.S72` started a Postgres with its data directory
  in `var/pgtest/data`, from a memory note, where `agents/implementer.md` line 24 says
  `.dev-team/tmp/`. `var/` is gitignored, so nothing leaked.
- **Does a partial read of `docs/decisions.md` count?** `U07` read lines 1–50 and
  110–end of `docs/decisions.md` plus a grep, not the whole file (`U07.S16`–`S18`);
  `agents/implementer.md` line 77 says read it all.

Not listed above because the rules already state them and a re-run is the only test: the driver
quoting a return's detail in an Ask (`D134`), a tester naming a path outside the repo root
(`U04.S29`), and the wrong per-heading test count (`U20.S65`).

## 13. Context for items 14 to 20: the b05b2879 audit

On 2026-10-01 `/plugin-dev:audit-run` audited a second real run, in a different repo from items
3–12. Details:

- **Session:** `b05b2879-3f25-4041-817b-3c06d28efb38`, chat titled "Plan package engine".
- **Repo:** `wild-ones` (`/Users/connorott/PycharmProjects/wild-ones`), branch `design`.
- **Commands:** `/dev-team:plan-package engine`, then `/dev-team:run-package engine`. The
  run built all 11 sections of `engine` and closed the package; the last commit was `42e5bd3`.
- **Plugin versions:** run-package ran on plugin 2.3.0 (tag `dev-team-v2.3.0`, `07dcb19`).
  The plan-package architect ran on 2.2.0.
- **Size:** 74 agent runs (`U01`–`U74`) over about 5.5 hours.
- **What was audited:** 17 units, plus the driver (`seg-1`) and a cross-run check.
- **Result:** 17 errors after merging (39 as filed), 21 warnings, 29 notes.

Where the records are:

- **Committed record:** `evals/2026-10-01-audit-run-package-b05b2879.md`.
- **Full report:** `report.md` in `evals/workspace/audit/b05b2879/`.
- **Per-unit findings:** `findings/*.md` in the same folder.
- **Traces:** `units/U<nn>.md`, `driver/seg-1.md`, `run.md` and `flow.html` in the same folder.

That folder is gitignored and exists only on the machine that ran the audit. Step ids such as
`U43.S93` or `D148` are lines in those traces. Paths such as `.dev-team/gate/engine/surface.txt`
or `packages/engine/...` are in the `wild-ones` repo.

**Timing against item 3.** The audit was checked against 2.3.0. Item 3's edits (commit
`1e81553`, merged as `2a155b8`) landed after it. Each item below was re-checked against the
working tree at `2a155b8`:

- Run-package not printing the changed rows is fixed there, by item 3's E8/E9 row. It is
  not listed below.
- The closed-return-list error is only partly fixed there; item 17 is what remains.

**Ranking.** Errors were ranked high (wrong outcome, or a check that can't do its job),
medium (a recurring defect with a contained cost) or low (a one-off agent slip, or no effect
on the run). Only high and medium are written up below.

The low errors, all in the eval record:

- run-package sent `Skills to invoke: —` instead of `none` to the designers;
- the plan-package architect read past its survey list;
- READMEs name no skill rules;
- a no-op `python3 -c`;
- a false "no document covers it";
- "Project skills: none" with no `ls` behind it;
- an architect grepped the plugin cache, including `evals/`;
- an implementer did its step-0 reads out of order.

The re-check also found a bug from the item 3 merge: in `agents/tester.md`, several of the
added sentences appear twice in a row:

- "Read means the Read tool on the whole file…" in step 1;
- "Every source line, docstrings and conftest included, is 88 characters or fewer…";
- "A count is the bare count…" in the return section;
- "The Hard rules are above memory the same way…" in **Memory**;
- "A temporary test file that prints values…".

Run `git diff 07dcb19 2a155b8 -- dev-team/agents/tester.md` to see them. Remove the
duplicates before anything else is edited there.

## 14. HIGH: a `blocked` or let-through result that comes after the stop gate never reaches the driver

### The problem

The implementer hands back its report and then hits the stop gate. If the gate fails and the
implementer then ends `Result: blocked`, or ends `Gate: let through after 3 attempts`, the
driver never learns of it. The driver goes on as if the section were done: it reviews it,
closes the package and reports it shipped.

In b05b2879:

| Unit | Section | What happened | What the driver saw |
|---|---|---|---|
| `U43` | `engine/physics` round 2 | Handed back `Result: done` (`U43.S85`). The gate failed on "removed assert" (see item 16). It wrote the stop marker `.dev-team/stop/engine/physics` (`U43.S92`) and ended "Result: blocked … I can't clear it honestly" (`U43.S93`) | `D148`: "U43 handed back: Result: done". It spawned the round-2 reviewer at `D152` |
| `U71` | `engine/surface` | Handed back `Result: done` (`U71.S88`). `status.py --surface engine` failed (see item 15). It wrote the marker (`U71.S91`) and ended `Result: blocked` (`U71.S92`) | `D244`: "Result: done". It ran both surface reviews and the package close (`D247`–`D253`) |
| `U40` | `engine/combat` round 2 | Ended with an amendment, `Gate: let through after 3 attempts` (`U40.S94`) | `D136`: "Result: done" |

The driver's final summary (`D256`) reads "sections: 11/11 DONE", with no blocked agent. The
strings `Result: blocked` and `let through after 3` appear 0 times in the main session
transcript. Every implementer's Agent tool result in the main transcript reads "This agent's
report was delivered to you as a message from … (its SubagentHandback call) … it is not repeated
here".

This is the same failure the befb4798 audit found (see `evals/2026-09-30-audit-run-package-befb4798.md`).
2.3.0 "fixed" it with the amendment rule, and that fix does not work under this harness.

### Why it happens

Two causes combine:

1. **The harness delivers only the first `SubagentHandback`.** The driver gets the first
   hand-back and nothing the agent says after it. The definitions assume the driver takes
   the agent's last turn:
   - `agents/implementer.md`: around line 475 ("Your hand-back tool (`SubagentHandback`)
     delivers one report per run and your first report used it, so the amendment is your
     turn's final text") and around line 740 ("it takes your **last** turn as your answer.
     The hand-back tool delivers one report, the first; every later one … is the turn's
     final text").
   - `skills/run-package/SKILL.md`: around line 253 ("An agent's return is its **last**
     hand-back … the amendment's first line is the one you branch on").

   Under this harness the final text goes nowhere.
2. **The gate erases the only on-disk trace.** In `hooks/gate_on_stop.py` `main()` (around
   lines 700–707), a marker `.dev-team/stop/<pkg>/<section>` whose first line is `blocked` or
   `spec-change` is deleted, the counter is cleared, and the gate exits 0 without writing a
   record. The gate record `.dev-team/gate/<pkg>/<section>.txt` therefore keeps its previous
   last line. For U71 that was `result: not done (attempt 1 of 3)`, which reads like a retry
   still in progress, not a block.

   `status.py` does not read gate records when deriving state. IMPLEMENT → REVIEW comes from
   the README existing, which is the second symptom in item 1. So the row moves to REVIEW,
   the reviewer quotes the non-pass `result:` line as a WARNING
   (`agents/reviewer.md` **The evidence**, around line 122), and the section reaches DONE.

The `skills/run-package/SKILL.md` step 5 `blocked` branch (around lines 264–267) already says "an
implementer can block after its commit … the marker the gate deleted is no evidence either way".
That leaves the driver with no evidence at all.

### Files to change

- `hooks/gate_on_stop.py`:
  - When it deletes a `blocked` marker, append to the section's gate record instead of
    returning silently: a header, the marker's second line, and `result: blocked`.
  - On the let-through path the record already ends `result: letting the run stop after 3
    attempts …`. Keep that.
  - Update the module docstring (steps 3 and 6, lines 18–23 and 52–58).
- `skills/status/scripts/status.py`, `section_state` (around line 923):
  - Read the section's gate record. When its last `result:` line is `blocked`, derive
    BLOCKED with that line as evidence, provided the record is newer than the newest
    review round's `Commit:`.
  - Decide whether a let-through record should also hold the row out of REVIEW, or only
    be surfaced. This also covers item 1's second symptom (IMPLEMENT → REVIEW on the README
    alone): gate IMPLEMENT → REVIEW on a pass record for the current code. Do the two
    together.
  - Update the state-rule docstring at the top of the file (rule 1, BLOCKED).
- `skills/run-package/SKILL.md` step 5 (around lines 250–270):
  - Drop "an agent's return is its **last** hand-back".
  - Branch on the hand-back's first line, then on the next `status.py`. A BLOCKED row with
    gate evidence is **Asking**, quoting the gate record's `result:` line and its FAIL lines.
- `agents/implementer.md`:
  - Rewrite the amendment and post-gate-blocked paragraphs (around lines 470–480 and
    738–770). After the first hand-back, the agent's only channel is the stop marker and
    the gate record. The amendment block either goes away or stays as a transcript-only
    record, so that nobody counts on it reaching the driver.
  - Say plainly that a `blocked` after the gate is recorded by the gate, not by the
    agent's text.
- `agents/reviewer.md` **The evidence** (around lines 116–126): a gate record whose last
  `result:` is `blocked` means the section should never have reached review. Say so as the
  verdict (`request changes`) rather than as a WARNING.
- Add state cases under `evals/fixtures/state-cases/`: one gate record ending `result:
  blocked`, and one ending `letting the run stop after 3 attempts`. Add hook-event cases for
  the gate writing the blocked record.
- Run `/plugin-dev:check-contracts`. `contracts.yml` may pin the amendment block's shape.

### How to verify

1. Run the state and hook-event suites.
2. Reproduce on a scratch package: make an implementer's gate fail on a file outside its
   scope so it must block after its first hand-back.
3. Check that the next `status.py` shows BLOCKED and the driver Asks.
4. Audit the run with `/plugin-dev:audit-run`, and grep the main transcript for the
   blocked line's text.

## 15. HIGH: the package shipped while its own surface check was failing

### The problem

`engine` closed with `shipped: yes` (`D251`) while `status.py --surface engine` reported FAIL.
The surface implementer (`U71`) blocked on this, and the block was lost (item 14). The
section's gate record at `wild-ones/.dev-team/gate/engine/surface.txt` ends:

```
FAIL surface: surface: FAIL | - BeamEvent: in interface.md Public names, not in README Public: yes rows | - CarveEvent: … | - EndTurn: … | - Match.apply: in README Public: yes rows, not in __all__ …
result: not done (attempt 1 of 3)
```

The failing names come from the section READMEs of `model`, `rng`, `turns` and `replay`, not
from `surface`:

- Several names share one row. `git show 42e5bd3:packages/engine/src/engine/model/README.md`,
  line 44 is `` | `UseSpecial`, `EndTurn` | … | yes | `` and line 46 is
  `` | `Circle`, `TerrainDelta` | … | yes | ``.
- Some rows use `Class.method` names (`Match.apply`).
- Some rows use names from before a rename.

The `surface` implementer's write scope does not include sibling READMEs, so it had no way to
fix them. Both surface reviewers quoted the FAIL as a WARNING and approved
(`wild-ones/docs/packages/engine/reviews/surface/2026-10-01-r1-a.md:14`, `…/r1-b.md:14`). The
`wild-ones` repo is probably still in this state. Re-check with
`python3 <plugin>/skills/status/scripts/status.py --surface engine` from its root.

### Why it happens

- **The README format is looser than the parser.** The README template in
  `agents/implementer.md` (**Section README template**, item 3 at about line 529) says only
  "table: name | signature | one-line use case | **Public**". It never says one exported
  name per row, spelled exactly as `__all__` exports it. `status.py`'s `_name_cell` (around
  line 1313) takes only the first backticked span of the name cell. `surface_check` (around
  line 1322) compares those names three ways against `__all__` and `interface.md` **Public
  names**. A grouped row therefore loses every name after the first, and a `Class.method`
  row adds a name that isn't in `__all__`.
- **The check comes too late.** Nothing runs the comparison until the last section,
  `surface`. By then the authors of the faulty READMEs are long finished, and the agent that
  finds the fault can't edit them.
- **Nothing stops the ship.** `shipped: yes` is derived only from the `surface` row being
  DONE (`status.py` around line 1126). It does not re-run `surface_check`. The reviewer
  definition says gate FAIL lines are "never a finding of yours" and the non-pass `result:`
  line is a WARNING (`agents/reviewer.md` around lines 122–126), so a failing three-way
  check can be approved.

### Files to change

- `agents/implementer.md`:
  - **Section README template** item 3: one row per public name, the name cell is exactly
    the exported identifier in backticks (no grouping, no `Class.method`, no pre-rename
    spelling), and a method is listed under its class's row, not as its own `Public: yes`
    row.
  - Repeat this at step 3 or wherever the README is written, not only in the template.
- `skills/status/scripts/status.py`: add a per-section form of the check, e.g. `--surface
  <pkg> --section <s>`, checking only that section's `Public: yes` rows against the contract's
  **Public surface (intent)**. Then either:
  - `_name_cell` warns on a cell with more than one backticked span, or a `.` in the name;
    or
  - `surface_check` splits comma-separated cells.

  Also make `shipped: yes` require `surface_check(pkg)[0] == "PASS"` (around line 1126), so
  that `shipped: no (surface check FAIL)` prints otherwise.
- `hooks/gate_on_stop.py`: run the per-section check in every section's gate (step 5 of the
  docstring), so the README author meets the failure in its own run.
- `agents/reviewer.md` **The evidence** and **The `surface` section** (around line 221): a
  three-way agreement FAIL on `surface` is CRITICAL, or the verdict is `request changes`. It
  is not a WARNING.
- `skills/run-package/SKILL.md`: at the package close, a `shipped: no (surface check …)` line
  is **Asking**, not a summary line.
- Add state cases for a grouped-name README row and for `shipped` with a failing surface
  check. `contracts.yml` may pin the README template's headings; run `check-contracts`.

### How to verify

1. Run the state cases.
2. Run `status.py --surface engine` in `wild-ones` at `42e5bd3`: it must print FAIL and
   `shipped: no`.
3. Re-run one section implementer with a design whose public names include two types, and
   check that its README lists them on separate rows.

## 16. HIGH: the stop gate reports a rewritten assert as a "removed assert"

### The problem

The gate's **Guarded** check fails a section when an `assert` line in a test is changed, not
only when it is removed. A change file that changes a signature forces every test calling that
function to be rewritten. Every such section therefore fails the gate on all three attempts and
ends blocked or let through.

In b05b2879, the change file `wild-ones/docs/packages/engine/changes/parameter-objects.md` moved
`damage(...)` and `first_body_on_segment(...)` to parameter objects:

- **`U40`, combat round 2.** It rewrote `assert damage(world, 1, amount, source="bazooka",
  cause=BLAST, by=0) == 0` as `assert damage(world, 1, amount, Hit("bazooka", BLAST, 0)) ==
  0` (`U40.S93`: 1 assert line removed, 16 added). The gate failed `guarded removed assert
  at packages/engine/tests/unit/combat/test_vitals.py:106` on all three attempts, and the run
  ended let through (`U40.S95`).
- **`U43`, physics round 2.** Same cause, at `test_segment.py` lines 16–78. It blocked, and
  the block was lost (item 14).

The project had no `docs/constraints.md`, so no **Exceptions** row could pardon either case.

### Why it happens

`hooks/gate_on_stop.py`, `check_guarded` (around lines 490–515). For each deleted test line,
`text.strip() not in added_by_file.get(path, set())` plus `text.strip().startswith("assert ")`
counts as a removed assert. Any change to an assert's text, even one where the new line is
also an assert, counts as a removal.

`agents/implementer.md` (the **Guarded** bullet, around line 721) and `agents/reviewer.md`
describe the rule as "a removed assert or `pytest.raises`". That matches what the rule is
for, not what the code does.

The implementer also has no route for a gate FAIL in its own file that it cannot honestly
fix. Its only options are to fix the code, or to block for a file it may not edit
(`U40` finding F4).

### Files to change

- `hooks/gate_on_stop.py` `check_guarded`: count removed asserts per file and per hunk, and
  flag only a net loss. Fewer `assert`/`pytest.raises` lines added than removed in a file is
  one option. Matching each removed assert to an added assert in the same hunk is a stricter
  one. Say in a comment why a rewrite isn't a removal. Update the docstring's step 5.
- Optionally pardon a rewritten assert when an `open`/`resolved` change file under
  `docs/packages/<pkg>/changes/` names the section. Weigh this against the simpler net-count
  rule above.
- `agents/implementer.md` **Guarded** bullet (around line 721): state the rule as it will
  then be ("an assert removed without one added in its place").
- `agents/implementer.md`, gate-retry section: name what to do with a FAIL in the agent's own
  file that is a false positive. For example, block with the gate line quoted, so it reaches
  the user through item 14's path.
- Hook-event fixtures under `evals/fixtures/`: one case of a rewritten assert (must pass) and
  one of a dropped assert (must fail).

### How to verify

1. Run the hook-event suite with the two new cases.
2. In `wild-ones`, replay the gate's Guarded check against `23c1fbb..9bdb512` for
   `packages/engine/tests/unit/combat/`. It must not report `test_vitals.py:106`.

## 17. MEDIUM: return messages still break their closed line lists (residue after item 3)

### The problem

Every role's return is a closed list of lines, and the driver reads only the first line.
In b05b2879, 9 of 17 audited units added lines or prose anyway:

| Role | Units | What they added |
|---|---|---|
| Implementer | `U07`, `U28`, `U40`, `U57` | `Security:` and `Sizes:` (`U07.S41`); `Other checks: ruff … lint-imports … pylint` (`U28.S99`); multi-paragraph `Fixed:` in amendments (`U40.S90`, `U40.S94`) |
| Tester | `U06`, `U26` | Parentheticals after `Suite:` and `Tests:` |
| Architect | `U01`, `U34`, `U74` | Paragraphs, file lists and a `Changes:` block after the rows (`U74.S85`) |

The same lines also appear in implementer returns that had no unit audit: `U21`, `U48`, `U60`,
`U66` and `U71`.

Item 3's E2 and E3 rows (commit `1e81553`) fixed the bare-count rule and moved security to the
README. Three contradictions are left.

### Why it happens

- **Size notes.** `agents/implementer.md` step 10 (around line 441) still says "Note
  anything past a soft limit in your return". The return list (around lines 750–790) has no
  line for it.
- **Other check results.** Steps 9 and 10 have the implementer run mypy, doctests,
  `ruff check`, `ruff format --check` and pylint's size check. The full report has a line
  only for the test command and `lint-imports`. With no line to put them on, agents invent
  `Other checks:` (`U28` finding F5).
- **Architect commit staging.** In `agents/architect.md`, **Commit** (around line 625) says
  to stage "exactly the paths your return lists as written or modified". The return rule at
  line 616 says "no list of files". To follow the commit rule, the architect has to list
  paths (`U74` finding F4).

Item 4 (returns stating checks no step produced) is the related open problem. The fix for one
should account for the other.

### Files to change

- `agents/implementer.md`:
  - Step 10: send soft-limit notes to the README's **Implementation notes**.
  - Return list: add one `Checks: <command> pass|fail` line per check run in steps 9–10,
    copied from output (see item 4); or say they are not reported and the gate record
    carries them.
  - Amendment block: `Fixed:` is one line per gate FAIL line, nothing else.
- `agents/architect.md` **Commit**: stage the paths this run wrote, from `git status
  --short`, not "the paths your return lists".
- `agents/tester.md`: no change beyond removing item 13's duplicated sentences.
- `contracts.yml`: if a claim pins the return lists, update it; run `check-contracts`.

### How to verify

Run the implementer and architect eval sets (`evals/sets/implementer.json`,
`evals/sets/architect.json` if it exists). Grep the returns for `Sizes:`, `Other checks:` and
`Security:`, and for any prose after the architect's rows.

## 18. MEDIUM: an open-decision `xfail` whose reason `ruff format` wraps fails the Guarded grep

### The problem

The tester for `engine/rng` (`U05`) wrote an `xfail` for open decision D3 as
`@pytest.mark.xfail(strict=False, reason="D3 open — assumption: …")`. `ruff format` wrapped it
at 88 columns, so the committed file reads:

```
153: @pytest.mark.xfail(
154:     strict=False, reason="D3 open — assumption: in-repo pure-Python PRNG"
```

(`git show 8e7252b:packages/engine/tests/intent/rng/test_rng.py`). The Guarded grep reads line 153
and reports "xfail without a D<n>". Later testers saw it in their own greps and had to reason
it away each time: `U20.S22`, `U26.S18` and `U49.S24` all list
`rng/test_rng.py:153:@pytest.mark.xfail(`. Any open decision whose reason makes the decorator
longer than 88 characters hits this.

### Why it happens

- **The tester rule.** `agents/tester.md`, the `docs/decisions.md` row of the inputs table
  (around line 125), requires "the `D<n>` written literally in the reason string on the
  decorator's own line … the stop gate's Guarded grep reads that line".
- **The formatter.** The format-on-edit hook runs `ruff format`, and a long decorator call
  is split across lines with no way for the tester to prevent it. Item 3's "88 characters
  or fewer" sentence makes this worse, because a tester obeying it must let the formatter
  wrap.
- **The gate.** `hooks/gate_on_stop.py` checks one line at a time: `XFAIL =
  re.compile(r"xfail")` and `DECISION = re.compile(r"\bD\d+(?!\d)")` (around lines 107–108),
  applied per added line (around line 509).

### Files to change

- `hooks/gate_on_stop.py`: for an added line that matches `xfail` and ends with an open
  `(`, read the following added lines up to the matching `)`. Look for `D<n>` in that
  span, not in the first line alone. Mirror this in any other place the gate or a guard
  greps for `xfail`. Check `hooks/` for a second copy.
- `agents/tester.md` (around line 125): say the `D<n>` must be in the decorator call,
  which may span lines after formatting. Recommend the short form `reason="D3 open"`, with
  the assumption in the test's docstring, so the call stays on one line.
- `agents/reviewer.md` (around line 70, the Guarded list): same wording, so a reviewer
  doesn't flag a wrapped decorator.
- Hook-event fixture: a wrapped `xfail(` decorator with `D3` on the next line must pass.
  One with no `D<n>` anywhere in the call must fail.

## 19. MEDIUM: a reviewer approved a departure from the design that had no ledger entry

### The problem

The round-1 conformance reviewer for `engine/rng` (`U09`) found that `derive` accepts a `bool`
or a float `purpose`. The design requires `TypeError` for every non-`int` argument, "a `bool`
is rejected explicitly" (`git show 428dcc1:docs/packages/engine/design/rng.md`, line 110). The
implementer disclosed the choice only in the README's Implementation notes. No
`docs/packages/engine/deviations/rng.md` exists even at the end of the run.

The reviewer filed it as a WARNING. Its Coverage row reads `fail (WARNING)`, the commit says
`r1-a: approve (0 critical)` (`34cbaa8`), and the return says `Verdict: approve`
(`U09.S38`–`S41`). The definition makes this a CRITICAL silent deviation. In the same run,
that reviewer's Scope also listed `docs/packages/content/interface.md` as judged ("nothing
consumed") without ever opening it.

### Why it happens

The rule is clear and stated three times in `agents/reviewer.md`:

- around line 161: "A **silent or unreasoned deviation** — a departure from the design with
  no `…/deviations/<section>.md` entry";
- around line 211: "A departure the notes describe with no ledger entry is a silent
  deviation";
- around line 334: "A departure from the design with no entry at all is a CRITICAL".

What tipped the reviewer was that the design contradicts itself. The §5 interface row for
`derive` lists only `ValueError` for `purpose`, while the §6 prose requires `TypeError`
(`U09` finding F6). The reviewer had no rule for grading code that follows one of two
contradictory design items, and softened the finding.

The implementer should have filed `spec-change:design` per the kind table in
`agents/implementer.md` (around line 641: "two items of the design contradict each other →
`spec-change:design`"). It wrote a README note instead, which `agents/implementer.md` doesn't
explicitly forbid at the README template's item 7.

### Files to change

- `agents/reviewer.md`, the CRITICAL list (around lines 150–165):
  - When the design contradicts itself and the code follows one side with no ledger
    entry, that is still CRITICAL (the silence).
  - The reviewer adds a `spec-change:design` naming both items, and the verdict is
    `spec-change`.
  - Add one sentence where the Coverage table is filled in: a `fail` row is CRITICAL unless
    a ledger entry covers it.
- `agents/implementer.md`, README template item 7 (around lines 536–540): a departure from
  the design is cited by its ledger heading. A departure described in the notes without a
  ledger entry is not allowed. Write the entry, or the `spec-change:design` if the design
  contradicts itself.
- `agents/designer.md`: optionally, a closing check that §5 interface rows and §6 exception
  prose agree. The same contradiction class appeared in `U57` (turns §4 vs §5).

## 20. MEDIUM: more evidence for item 4 (counts no step computed)

b05b2879 repeats item 4's per-heading count problem in a second repo. The `engine/model`
tester (`U06`) returned `Tests: 133 written (§3 … 46, §4 9, §5 10, §7 … 61, §8 1)` (`U06.S68`).
The parts sum to 127, not 133, and §6 is left out. The only count the run computed was per file
(`U06.S63`, "total 133"). The committed tree (`7899f13`), keyed by each docstring's first
`Design §<n>`, gives §3 57, §4 9, §5 9, §6 1, §7 56, §8 1.

There is no new fix. It strengthens item 4's case for making `Tests: <n> written (<count by
design heading>)` come from a command, or for dropping the heading split. Use `wild-ones` at
`7899f13` as a second verification case for item 4.
