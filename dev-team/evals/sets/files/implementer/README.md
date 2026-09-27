# Fixtures for `evals/sets/implementer.json`

Two small repos, one per new eval, each the state a `run-package data` run would find on disk
at the IMPLEMENT step of one section. Read-only: an executor writes into its `outputs/`.

| Directory | Eval | Section | What is planted |
|---|---|---|---|
| `clean-deviation/` | 9 | `data/clean` | the design's dedupe clause (`set(rows)`, "Trade is a frozen dataclass") is unimplementable: the shipped `ingest` README says `Trade` is mutable and unhashable. Internal to the section, so it is a `deviation`, `Status: proposed`. `docs/deviations.md` is absent |
| `storage-spec-change/` | 10 | `data/storage` | the contract's Section interfaces row says `clean_trades(rows: list[Trade]) -> list[Trade]`; the shipped `clean` README says it returns `CleanResult`. A consumed shipped signature the contract names, so it is `spec-change:contract`. `docs/deviations.md` exists with a header only |

Both hold `docs/architecture.md`, `docs/packages/data/contract.md`, the section's design,
`docs/decisions.md`, a root and package `pyproject.toml`, `.gitignore` (with `.dev-team/`), the
shipped sibling sections with their READMEs, and `packages/data/tests/intent/<section>/`. No
`docs/constraints.md`, no probe docs, no reviews, no change file.
