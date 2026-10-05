# Harness — profiler, eval 3

Seed: `python3 evals/sets/files/profiler/build.py case-3 <copy>`, run from the plugin directory that
holds this eval set (the one with `.claude-plugin/plugin.json`). It builds a small git repository
in `<copy>`.

## Set up

1. Make `<copy>` with `mktemp -d` (`mktemp -d <scratchpad>/eval.XXXXXX` when the session has a
   scratchpad). Nothing else goes in it first.
2. Run the seed command. Run `build.py`; do not open it, and do not read `seed/` beside it.
3. `<copy>` is the repo root for this run. Every path in the prompt is relative to it, and every
   command the task runs is run from it.

## Facts about the seed

- As case 1's repository, plus a round-0 profile of `rawtrades` committed as a `Mode: profile` run left it: `docs/sources/rawtrades.md`, `rawtrades.profile.py` and `rawtrades.sample.json`. `build.py` runs the committed program once, so `.dev-team/data/rawtrades/rounds/0/` holds its failing rows and counts. `data/clean` has no decisions inbox.
- `build.py` prints `section commit: none`: the section has no code.
- `build.py` prints `store: built — …` and the files it built. If it prints `store: not built — …`, `uv` or the network is missing: write that line to `outputs/not-run.md` and stop; the run is recorded as not run.
- The contract is `docs/packages/data/contract.md`; the section is `data/clean`, its `source` is
  `stage:rawtrades`. `.dev-team/` is ignored by git in the copy.

## Rules for this run

- **No user.** There is nobody to ask; this sheet answers nothing else.
- **Work in the copy.** Write every file where the task says it goes, inside `<copy>`. Do not
  commit there: where your instructions say to commit, write `outputs/commit.md` instead, holding
  the paths you would stage, one per line, then the commit message.
- **Skills.** The Skill tool cannot load this plugin's skills here. When you were given a plugin
  root, invoking `planning-templates` means reading the file it names under
  `skills/planning-templates/references/` in that plugin root, and invoking
  `git-workflow-and-versioning` means reading `skills/git-workflow-and-versioning/SKILL.md` there;
  record each read in `transcript.md`.
- **No plugin root.** When your prompt names no plugin root, read nothing in the plugin
  directory but this sheet: not `skills/`, not `agents/`, not `evals/`. You run `build.py`
  from it and nothing else.
- **Hooks.** No hook runs in the copy: nothing guards a write, and no number is assigned to a
  decision stub.
- **`uv` and the network.** Any program under `docs/sources/` is run as
  `uv run --with duckdb python <path>`. Before the first such run, check `uv --version`. If `uv` is
  missing, or `uv run --with duckdb` cannot fetch `duckdb`, write the command and its error to
  `outputs/not-run.md` and stop; do not use another engine in its place.
- **Sample record.** Whenever your instructions have you draw rows to judge a kind's checks,
  record what you drew in `<outputs_dir>/sample-ids.json`, written once with the Write tool when
  your judging is done and before you write or edit anything in `<copy>`: one key per kind id
  you judged, each an object `{"flagged": [...], "passing": [...], "misjudged": [...]}` — the
  `trade_id` of every row you drew from those the kind's checks flag, of every row you drew
  from those they pass, and of each drawn row you judged the check got wrong (`[]` when none).
  Every id is one you drew and judged; none is added afterwards. Nothing else goes in the file.
- **Scratch.** Delete nothing you did not create. Leave `<copy>` in place when you finish.

## When the task is done

1. From the plugin directory: `python3 evals/sets/files/profiler/build.py collect <copy> <outputs_dir>`.
   It copies every file that differs from the seed into `outputs/` under its repo-relative path,
   and writes `outputs/changes.txt` (every path that differs), `outputs/changes.diff` (the diff of
   tracked files against the seed), `outputs/commits-after-seed.txt`, and
   `outputs/store-files.txt` (every file under `.dev-team/`, with the small text files copied
   beside it), and `outputs/sample-check.txt` (your `sample-ids.json` held against the seed's
   data and checks). Run it even when the task ended early.
2. End `transcript.md` with your final message, word for word: what you would return to whoever
   started you. Record in `transcript.md` every command you ran in the copy.
