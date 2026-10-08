# `docs/packages/<pkg>/contract.md` — the package contract

Written at package scope before designers are delegated; read by designers, implementer,
reviewer, `/dev-team:run-package`, and the architect when it classifies an edit (its
**Consumes** table). Budget 200 lines, **Call paths** not counted: that item is one line per
command and one per path, and nothing else.

Where this contract needs a repo-contract shape to change, do not change it here — it is a
change item for `/dev-team:plan-repo`, stubbed as a `D<n>` scoped `repo` until that run.

1. **Purpose** — one paragraph, and which repo-contract shapes this package provides. Then
   the brief capabilities this package covers (its `covers` cell in the repo contract), one
   line each: the capability, the section that builds it, and the brief's Notes quoted
   verbatim — designers read this contract, not the brief, so this is how the user's own
   wording reaches them. *Later* capabilities are listed as `later — do not rule out`, with
   no section. Omit the list when `covers` is `—`.

2. **Sections** — table: section | responsibility | path | owner doc | builds with |
   depends on | source. Paths are `packages/<pkg>/src/<pkg>/<section>/` (or `src/<pkg>/<section>/`
   in a single-package repo); owner docs are `docs/packages/<pkg>/design/<section>.md`.
   `Depends on` names sections in this package only, and must form a DAG — it becomes an
   import-linter contract and the order `/dev-team:run-package` builds in.

   `source` is each external source the section consumes, written `<kind>:<token>` — `api`
   for a service called over the network, `dataset` for a file, table or corpus that is
   read, `stage` for data the section's own dependencies produce (below). The token is one
   lowercase word and is the name `docs/sources/<token>.md` carries; probe docs are repo-wide,
   so a source two packages consume is one document. Several sources are comma-separated
   (`api:fred, dataset:trades-2024`); no source is `—`. A bare token with no prefix means `api`,
   which is how every contract written before kinds existed still reads. `/dev-team:run-package`'s
   PROBE step probes every entry in this column before the section's designer runs, so a
   source not named here is never probed, and a kind written wrong probes the wrong thing. A
   section whose job is to clean, validate, reconcile or audit data its dependencies produce
   is marked: `stage:<token>` in `source` (the token names the data, `rawbars`, not the
   section), `dev-team:data-quality` in `builds with`, and one row under **Data stages**
   (item 3): the stage's question, its data and producers, what clean means and its pull plan.
   A marked row's `responsibility` names the stage it cleans (`cleans stage:rawmeta`); what
   the section guarantees about its output is that row's `clean means` cell, a guarantee and
   never a treatment (`repair`, `drop`): the kinds of failing row come from the profile, and
   each treatment that changes data is the user's `D<n>`. Never on a row with no `depends
   on`, and never on a section that only passes data through.

   Every section name and source token follows `project-structure` §4: one lowercase token,
   and never starting with `report`, `summary`, `findings` or `analysis`. A subagent cannot
   Write a `.md` file whose name starts with one of those words, and the section's design is
   `design/<section>.md`. When the brief names a section `report`, name what it produces in
   one word that is also a Python package name (`digest`, `markdown`), and say so in the return.

   The last row is always `surface`: responsibility *the package's pipelines (§4) and public
   surface (§6)*, path the package top level (`packages/<pkg>/src/<pkg>/`, or `src/<pkg>/` in a
   single-package repo), owner doc `docs/packages/<pkg>/design/surface.md`, `builds with` `—`,
   `depends on` every other section by name, `source` `—`. Its design is written right after
   PLAN, from this contract — **Section interfaces**, **Pipelines**, **Public surface (intent)**
   and **Call paths** — before any sibling is built, and its code is built last, from the
   shipped READMEs; its README is `docs/packages/<pkg>/interface.md`.

3. **Data stages** — only in a package with a `stage:` row; omit the heading otherwise. The
   plan for the data, written before any section is designed: one table, rows in the order
   the stages are profiled and cleaned, which is the order their cleaning sections' `depends
   on` gives. The first row is the population — what instruments, accounts, documents or
   other units exist and what keys them — because every later stage is judged against it.

   `| stage | question | data | cleaned by | clean means | judged against | pull | decision |`

   - `stage` — `stage:<token>`, the token a Sections row's `source` carries.
   - `question` — the one question the stage answers about the data, as a question (`which
     (symbol, asset type) pairs in the vendor files are instruments, and which are one
     instrument under two spellings?`).
   - `data` — what the rows are; `produced by` the sections of this package whose entry
     points yield them, by name in backticks, each in the cleaning section's `depends on`;
     `lands at <path>`.
   - `cleaned by` — the section whose `source` carries the token.
   - `clean means` — numbered guarantees, `1. … 2. …`: what the cleaning section promises
     about its output, in the brief's words from **Purpose** (`1. no two unrelated securities
     share an ID 2. a failed metadata lookup never removes a delisted instrument`). The
     profile groups its checks by these numbers. A guarantee, never a treatment.
   - `judged against` — the brief clauses, project skills and probe docs the data is held to,
     by name.
   - `pull` — how much of the data the profiler reads when none is on disk: `whole`, or
     `sample <n> <unit>, <how drawn>`; the window (`one file per month for two years plus the
     last 30 sessions`); what the scope cannot judge (`three sessions cannot show a
     delisting`); and the cost, from the vendor probes' **Cost and time of a full pull** and
     **Rate limits and quotas**: requests, time at the documented rate, quota consumed
     (`≈12,000 requests, ≈10 min at 8 req/s, no quota`).
   - `decision` — the `D<n>` that asks the user to approve the `pull` cell, one per stage,
     with the cell as its recommendation and an assumption, so an unanswered one does not
     block.

   The run gate fails a `stage:` row with no row here, a row with an empty cell, a `cleaned
   by` that is not the marked section, or a `data` cell naming a producer the cleaning
   section's `depends on` lacks. A contract written before this heading existed carries the
   plan as a **Package conventions** line,
   `` `stage:<token>` — <what the data is>; lands at <path>; judged against <standards>; pull cap <n> <unit>, D<n> ``,
   still read by the gate and the profiler; adding the heading is an item of the architect's
   change list.

4. **Section interfaces** — per section, what it returns to its dependents, as signatures.
   Reference repo shapes by name; never redefine them. This is where "what each section
   returns" is fixed, so designers of dependents have something concrete. Also every function
   of the section a **Call paths** entry names below its entry point, marked `(path only)`
   after the signature when no dependent calls it: a frame on a path is a name the contract
   owns, whoever calls it.

5. **Pipelines** — per pipeline: name, trigger, ordered section participation with what
   crosses at each step, failure behavior, and the CLI command that drives it. `download →
   clean → audit → store` is a pipeline; each arrow names a shape or a section interface.

6. **Call paths** — one bullet per command in **Public surface (intent)**, a pipeline's
   command and a one-off command alike: `` `<command>` (budget <n>): ``, then one sub-bullet
   per kind of external effect the command reaches — `vendor call`, `database write`, `file
   write`, or another kind in two words — holding the frames from the command to that effect:

   ```
   - `data-build` (budget 8):
     - vendor call: 1 `cli.build` → 2 `pipelines.run_build` → 3 `ingest.download_bars` → `polygon.get_bars`
     - database write: 1 `cli.build` → 2 `pipelines.run_build` → 3 `storage.store_bars` → `sqlite3.connect`
   ```

   Frames are numbered from 1 at the command function. A frame is `cli.<function>` (a command
   function in `cli.py`), `pipelines.<function>` (the function a **Pipelines** entry names) or
   `<section>.<function>` (a **Section interfaces** entry of that section;
   `<section>.<Class>.<method>` for a method). The effect, unnumbered and last, is the call
   that leaves the package, written as this contract knows it: an effect is whatever
   `status.py --paths` marks `[effect: …]` — a third-party module, an I/O module, `open`,
   `print`, or a call into an upstream package (kind `upstream call`) — so a command that
   prints has a `stdout write` path. One sub-bullet per effect the command reaches; when two
   effects share a kind, the kind names what it touches (`database write (runs)`). A
   **Pipelines** step that reaches no effect (a pure transformation) is a step of the pipeline
   and a frame of no path; only the calls that lead to an effect are frames. Every frame is a
   name this contract defines under **Pipelines** or **Section interfaces**: a frame with no
   owner is a frame nobody will build. The budget is the largest `depth to first effect` that
   `status.py --paths <pkg>` may report for the command — the command at depth 0, so a path of
   `n` frames has depth `n − 1` — and it is 8, the hard **Main-path depth** of
   `project-structure` §2, unless a `D<n>` with `Status: decided` allows more, cited on the
   line: `` `<command>` (budget 10, D14): ``. A package with no command writes `- none (no
   commands)`.

   Written at PLAN, before any section is designed: the designers build these frames and no
   others (a frame a design needs and the path does not list is a `spec-change: contract`),
   and the paths review holds the code to them. **As built** — the form the close writes for
   a package built before this heading existed — copies the frames from `status.py --paths
   <pkg>`, every frame of the tree from the command to each effect, `[indirect]` frames
   included, each named `<owner>.<name>` with `<name>` the frame's printed name, private or
   not (`ingest._load`; a lambda's frame is `lambda`, as printed), and `<owner>` the section
   whose path holds the frame's file (`cli` for `cli.py`, `pipelines` under `pipelines/`). The
   owner rule above does not bind an as-built entry: its frames are the code's, and **Section
   interfaces** gains nothing for them. An as-built entry keeps `budget 8`; when its depth is
   past it, the command's line ends `— past budget, see
   docs/packages/<pkg>/changes/paths-<command>.md` and never carries a `D<n>`.

7. **Public surface (intent)** — which repo shapes this package provides, which section
   realizes each, and which downstream package or CLI command consumes each. This is the
   list the `surface` section's design (`docs/packages/<pkg>/design/surface.md`) is checked
   against: a name with no consumer here does not become public later. Keep it short; the
   surface is what consumers need, not what sections offer.
   A one-off command that runs one section entry point rather than a pipeline (schema init, a
   backfill) belongs here too, with the command as the consumer — it will have no row under
   **Pipelines**.

8. **Consumes** — table: upstream package | name | shape | status (`shipped` /
   `provisional` / `stale`). The architect reads this to find planned consumers of a package
   when it classifies an edit, so list every upstream name this package will use.

9. **Package conventions** — only what goes beyond the repo contract.

10. **Open decisions** — `D<n>` numbers, one line each.

**Adopting an existing package** (`Mode: document`): every heading describes what the code
does today. Sections come from its directories, interfaces from its code, pipelines from what
its entry points actually run, Consumes from its actual imports. Where the code contradicts
its own conventions, say so under the relevant heading rather than tidying it. **Call paths**
is written in its as-built form, from `status.py --paths <pkg>`.
