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

   `source` is each external source the section consumes, written `<kind>:<token>` — `api` for a
   service called over the network, `dataset` for a file, table or corpus that is read. The
   token is one lowercase word and is the name `docs/sources/<token>.md` carries; probe docs are
   repo-wide, so a source two packages consume is one document. Several sources are
   comma-separated (`api:fred, dataset:trades-2024`); no source is `—`. A bare token with no
   prefix means `api`, which is how every contract written before kinds existed still reads.
   `/dev-team:run-package`'s PROBE step probes every entry in this column before the section's
   designer runs, so a source not named here is never probed, and a kind written wrong probes
   the wrong thing.

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

3. **Section interfaces** — per section, what it returns to its dependents, as signatures.
   Reference repo shapes by name; never redefine them. This is where "what each section
   returns" is fixed, so designers of dependents have something concrete. Also every function
   of the section a **Call paths** entry names below its entry point, marked `(path only)`
   after the signature when no dependent calls it: a frame on a path is a name the contract
   owns, whoever calls it.

4. **Pipelines** — per pipeline: name, trigger, ordered section participation with what
   crosses at each step, failure behavior, and the CLI command that drives it. `download →
   clean → audit → store` is a pipeline; each arrow names a shape or a section interface.

5. **Call paths** — one bullet per command in **Public surface (intent)**, a pipeline's
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

6. **Public surface (intent)** — which repo shapes this package provides, which section
   realizes each, and which downstream package or CLI command consumes each. This is the
   list the `surface` section's design (`docs/packages/<pkg>/design/surface.md`) is checked
   against: a name with no consumer here does not become public later. Keep it short; the
   surface is what consumers need, not what sections offer.
   A one-off command that runs one section entry point rather than a pipeline (schema init, a
   backfill) belongs here too, with the command as the consumer — it will have no row under
   **Pipelines**.

7. **Consumes** — table: upstream package | name | shape | status (`shipped` /
   `provisional` / `stale`). The architect reads this to find planned consumers of a package
   when it classifies an edit, so list every upstream name this package will use.

8. **Package conventions** — only what goes beyond the repo contract.

9. **Open decisions** — `D<n>` numbers, one line each.

**Adopting an existing package** (`Mode: document`): every heading describes what the code
does today. Sections come from its directories, interfaces from its code, pipelines from what
its entry points actually run, Consumes from its actual imports. Where the code contradicts
its own conventions, say so under the relevant heading rather than tidying it. **Call paths**
is written in its as-built form, from `status.py --paths <pkg>`.
