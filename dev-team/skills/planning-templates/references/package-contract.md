# `docs/packages/<pkg>/contract.md` — the package contract

Written at package scope before designers are delegated; read by designers, implementer,
reviewer, `/dev-team:finalize-package`, and `/dev-team:plan-change` (its **Consumes** table). Budget 200 lines.

Where this contract needs a repo-contract shape to change, do not change it here — raise it
under **Repo contract deviations** in the integration doc.

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
   import-linter contract and the order `/dev-team:implement-section` enforces.

   `source` is each external source the section consumes, written `<kind>:<token>` — `api` for a
   service called over the network, `dataset` for a file, table or corpus that is read. The
   token is one lowercase word and is the name `docs/sources/<token>.md` carries; probe docs are
   repo-wide, so a source two packages consume is one document. Several sources are
   comma-separated (`api:fred, dataset:trades-2024`); no source is `—`. A bare token with no
   prefix means `api`, which is how every contract written before kinds existed still reads.
   `/dev-team:plan-package` probes every entry in this column before delegating designers, so a
   source not named here is never probed, and a kind written wrong probes the wrong thing.

3. **Section interfaces** — per section, what it returns to its dependents, as signatures.
   Reference repo shapes by name; never redefine them. This is where "what each section
   returns" is fixed, so designers of dependents have something concrete.

4. **Pipelines** — per pipeline: name, trigger, ordered section participation with what
   crosses at each step, failure behavior, and the CLI command that drives it. `download →
   clean → audit → store` is a pipeline; each arrow names a shape or a section interface.

5. **Public surface (intent)** — which repo shapes this package provides, which section
   realizes each, and which downstream package or CLI command consumes each. This is the
   list `surface.md` will be checked against: a name with no consumer here does not become
   public later. Keep it short; the surface is what consumers need, not what sections offer.
   A one-off command that runs one section entry point rather than a pipeline (schema init, a
   backfill) belongs here too, with the command as the consumer — it will have no row under
   **Pipelines**.

6. **Consumes** — table: upstream package | name | shape | status (`shipped` /
   `provisional` / `stale`). `/dev-team:plan-change` reads this to find planned consumers of a package,
   so list every upstream name this package will use.

7. **Package conventions** — only what goes beyond the repo contract.

8. **Open decisions** — `D<n>` numbers, one line each.

**Adopting an existing package** (`Mode: document`): every heading describes what the code
does today. Sections come from its directories, interfaces from its code, pipelines from what
its entry points actually run, Consumes from its actual imports. Where the code contradicts
its own conventions, say so under the relevant heading rather than tidying it.
