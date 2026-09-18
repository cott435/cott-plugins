# `docs/sources/<source>.md` — the source probe

Written by the `researcher` in probe mode, one per external source. The path is repo-wide on
purpose: a source belongs to no package, so two packages that consume it read one document
instead of probing it twice and disagreeing. Read by designers (the parser, and the feature
set), the implementer (its fixtures), the reviewer (what shipped against what was observed),
and the architect (the access stop, and the two headings that can change a package contract).

Canonical: it describes the external system **on the date probed**, the way an `interface.md`
describes a shipped package. Budget 200 lines.

Two kinds. Read the one your prompt's `Kind:` names and ignore the other.

**Every document opens with the same three lines**, before heading 1:

```
# Source probe — <source> — <kind> — <date>

Purpose: <from the prompt>
Probe: <source>.probe.py · Sample: <source>.sample.json          (api)
Profile: <source>.profile.py · Statistics: <source>.stats.json   (dataset)
```

**Authority is per heading, not per document.** This file outranks the vendor's or the
publisher's documentation only where you observed something. Where you could not — a write
endpoint no probe may call, a dataset sampled rather than read whole — the claim still belongs
here, marked as a claim. Never let documented and observed sit under one heading unlabelled:
readers trust this document because it says which is which, and one unmarked line spends that
trust on every other line.

## Kind `api`

1. **Access** — `Env var: <NAME>` — `unset` | `set, rejected (<status>)` | `valid`, plus
   whatever tier or quota the response revealed. Then the mechanism as actually used: a static
   key (say which header or query param) or an OAuth2 grant (its token endpoint, the grant
   type, the lifetime of the token issued, the scopes returned). A client that refreshes a
   token is a different client from one that sets a header, and this is where that is settled.

2. **Endpoints** — table: endpoint | method | auth | params called | **evidence** | documented
   for. `evidence` is `observed` for a read endpoint you called, `sandbox` for an exchange
   against a vendor sandbox on its own credential, `documented` for a write endpoint or webhook
   you only read about. That column is what tells a designer which half of this document
   outranks the vendor's docs.

3. **Observed schema** — per endpoint: field | type as returned | nullable seen | notes.
   Written from the recorded sample and nothing else. This is the heading designers build the
   parser against, field for field.

4. **Pagination** — as it actually behaved: the token field, the page size seen, the last-page
   signal.

5. **Rate limits and quotas** — documented, plus any header or 429 observed.

6. **Error responses** — table: endpoint | bad request made | status | envelope as returned.
   One deliberately bad request per endpoint, because the parser meets these too.

7. **Write semantics** — only when the purpose implies a write. Per write endpoint, and
   `documented` unless a sandbox was used: the idempotency mechanism, what a retry does, what a
   partial failure leaves behind. A client that retries on a guess corrupts data rather than
   losing it, so this heading exists even though nothing under it was observed.

8. **Webhooks** — only when the service offers one. Registration, payload shape, signature
   verification, delivery and retry guarantees — as documented.

9. **Quirks** — every place the response differed from the documentation, one line each.

10. **Cost and time of a full pull** — extrapolated from the calls made: requests, wall time,
    quota consumed.

11. **Changes since last probe** — re-run only, diffed against the previous version.

12. **Differs from the extracted skill's fixtures** — only when an extracted skill exists.

## Kind `dataset`

1. **Access** — `Location: <path | URI | table>` — `missing` | `unreadable (<error>)` |
   `readable`. The env var if the store needs one, `n/a` if not. Then format, size on disk,
   file count or partitioning, and compression.

2. **Provenance** — what the dataset claims about itself: a data card, a README, a column
   dictionary, the licence or terms, how it was collected, how often it refreshes, any stated
   known bias, each with where it came from. **`none found` is an answer**, and an important
   one: it means **Observed schema** below is the only description of this data that exists
   anywhere, and every consumer is reading it.

3. **Shape** — rows × columns, and whether this profile covers the whole dataset or a seeded
   sample. A sample names its seed and its n; without them every number below is a statistic
   nobody can reproduce.

4. **Observed schema** — per column: column | dtype as loaded | declared dtype | null % |
   distinct | range or top-k | notes. The two dtype columns are separate because a column the
   file declares as an integer and pandas loads as an object is the bug the designer needs to
   see.

5. **Duplicates and keys** — the exact-duplicate row count, and each candidate key column with
   whether it is actually unique. This settles whether the section can join or deduplicate at
   all.

6. **Target** — task-fit runs only. The `y` column, its type, its class balance or quantiles,
   how many rows have no target, and the **baseline** any model must beat: the majority-class
   rate, or the error of predicting the mean. Without that number, 97% accuracy reads as
   success when it is worse than always guessing the majority.

7. **Leakage** — task-fit runs only. Columns unknowable at prediction time, columns that proxy
   the target, and identifiers a model will simply memorize — one line each. This comes before
   the feature list because a leaking column is not a weak feature, it is a fake result.

8. **Features** — task-fit runs only. Table: column | usable | why not. The reasons that matter
   are constant or near-constant, a cardinality no encoding survives, and a null rate that
   leaves nothing to learn from.

9. **Splitting** — task-fit runs only. Whether rows are independent; time ordering and whether a
   random split is valid; group structure. A time column means the split is chronological; a
   repeated entity — patient, customer, device — means it is by group, or the same subject
   lands on both sides of it.

10. **Supported tasks** — task-fit runs only. What this data can carry and what it cannot, each
    with its reason. A target with eleven positive rows does not support classification, and
    this is the cheapest that finding will ever be.

11. **Quirks** — every place the data differed from its provenance, one line each, and every
    column redacted under the statistics-only rule so a designer knows the field is there.

12. **Cost and time of a full pass** — from the profile run: wall time, peak memory, and whether
    it fits in memory at all.

13. **Changes since last probe** — re-run only, diffed against the previous version.

14. **Differs from the extracted skill's fixtures** — only when an extracted skill exists.
