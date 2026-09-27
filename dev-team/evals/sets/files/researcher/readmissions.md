# Source probe — readmissions — dataset — 2026-09-20

Purpose: the `risk` package's `model` section predicts 30-day readmission; the designer picks the target, the feature set and the split from this document.
Profile: readmissions.profile.py · Statistics: readmissions.stats.json

## Access

Location: `evals/sets/files/researcher/readmissions.csv` — `readable`. Env var: `n/a`. Format: CSV,
comma-separated, header row, UTF-8, no quoting beyond the header. Size on disk 38,437 bytes
(37.5 KB), one file, uncompressed.

## Provenance

`none found`. No data card, README, column dictionary, licence or collection note sits beside
the file, and the file name gives no publisher. **Observed schema** below is the only
description of this data that exists anywhere.

## Shape

246 rows × 12 columns. The whole file was profiled — no sample, no seed.

## Observed schema

| column | dtype as loaded | declared dtype | null % | distinct | range or top-k | notes |
|---|---|---|---|---|---|---|
| `patient_id` | object | string | 0.0 | 114 | pattern `P\d{4}`, `P1000`–`P1139` | identifier; not unique (see below) |
| `full_name` | object | string | 0.0 | 178 | `<redacted>` | personal; statistics only |
| `email` | object | string | 0.0 | 178 | `<redacted>` | personal; every value ends `@example.invalid` |
| `admitted_at` | object | timestamp | 0.0 | 239 | 2025-01-06 20:00 – 2026-01-13 04:00 | `YYYY-MM-DD HH:MM:SS`, all 246 parse; no timezone |
| `age` | int64 | integer | 0.0 | 74 | 21–94; quartiles 41 / 57.5 / 77 | — |
| `region` | object | category | 0.0 | 4 | west 72, east 62, south 57, north 55 | — |
| `systolic` | float64 | numeric | 5.3 | 80 | 96–184; quartiles 122 / 144 / 165 | 13 nulls = 8 literal `n/a` + 5 empty; pandas' default NA parsing reads both as null, so it loads float64; with `keep_default_na=False` it loads object |
| `cholesterol` | float64 | numeric | 8.9 | 208 | 120.2–289.9; quartiles 162.3 / 203.0 / 245.3 | 22 empty cells, no literal `n/a` |
| `site_version` | object | string | 0.0 | 1 | `v3` 100% | constant |
| `discharge_code` | object | category | 0.0 | 4 | D01 79, D02 76, D03 65, R30 26 | see **Leakage** |
| `notes` | object | free text | 0.0 | 237 | `<redacted>`; length 20–128 chars, median 64 | personal; clinical free text, statistics only |
| `readmitted_30d` | int64 | integer 0/1 | 0.0 | 2 | 0: 220 (89.4%), 1: 26 (10.6%) | the target |

Every column is `observed`: the file was loaded whole with pandas and the statistics above come
from that load and nothing else.

## Duplicates and keys

- Exact-duplicate rows: **6**.
- `patient_id`: **not unique** — 114 distinct values over 246 rows; 132 rows repeat a value
  already seen. A patient has several admissions.
- `admitted_at`: not unique — 239 distinct over 246 rows.
- No single column is a key. The composite (`patient_id`, `admitted_at`) was not checked after
  dropping the exact duplicates.

## Target

`readmitted_30d`, integer 0/1, no null. Class balance 220 : 26 (89.4% : 10.6%). **Baseline any
model must beat: 89.4% accuracy by always predicting 0**; equivalently, a useful model is judged
on the 26 positives (recall / precision on class 1), not on accuracy.

## Leakage

- `discharge_code` **separates the target perfectly**: every `R30` row is `readmitted_30d = 1`
  and every `D01`/`D02`/`D03` row is `0` (26 : 26). It is an outcome code written after the
  readmission and cannot be known at prediction time. Exclude it.
- `patient_id` is an identifier a model will memorize across a patient's repeated admissions.
- `full_name`, `email` are identifiers and personal data; never features.
- `notes` is free text whose writing time is unknown — it may be written at discharge or after;
  `unverified`. Treat as leaking until its timing is established.

## Features

| column | usable | why not |
|---|---|---|
| `age` | yes | — |
| `region` | yes | 4 levels, one-hot |
| `systolic` | yes | 5.3% null; impute or flag |
| `cholesterol` | yes | 8.9% null; impute or flag |
| `admitted_at` | derived only | as calendar features (month, weekday); the raw timestamp is the split key |
| `site_version` | no | constant (`v3`, 100%) |
| `discharge_code` | no | leaks the target |
| `patient_id` | no | identifier; the group key for the split |
| `full_name`, `email`, `notes` | no | personal data; redacted |

## Splitting

Rows are **not independent**. `admitted_at` orders them over 2025-01 to 2026-01 (65 / 59 / 55 /
58 / 9 rows per quarter), so a random split leaks the future into the past: the split must be
**chronological on `admitted_at`**. `patient_id` repeats (114 patients, 246 rows), so the split
must also be **grouped by `patient_id`**, or the same patient lands on both sides.

## Supported tasks

- Binary classification of `readmitted_30d`: **supported with caution** — 26 positives is a
  small minority; expect wide confidence intervals and evaluate on class-1 recall and precision,
  not accuracy.
- Regression, survival or time-to-readmission: **not supported** — no readmission date, no
  length-of-stay column.
- Any task using `discharge_code` as an input: **not supported** — it is the label.

## Quirks

- Redacted under the statistics-only rule: `full_name`, `email`, `notes`.
- `systolic` mixes literal `n/a` (8) and empty cells (5) for missing; the loaded dtype depends
  on the reader's NA handling (float64 by default, object with `keep_default_na=False`).
- `cholesterol` uses empty cells only.
- `discharge_code` is a perfect proxy for the target (see **Leakage**).
- `site_version` is constant.
- 6 exact-duplicate rows.
- No provenance of any kind; nothing to diff the observations against.

## Cost and time of a full pass

Under one second wall time; peak memory under 5 MB; fits in memory with no sampling.

## Sections served

## risk/model

Purpose: the `risk` package's `model` section predicts 30-day readmission; the designer picks
the target, the feature set and the split from this document.

| column | role for this section | evidence |
|---|---|---|
| `readmitted_30d` | target; 220 : 26, majority baseline 89.4% | observed |
| `discharge_code` | excluded — leaks the target (R30 ⇔ 1) | observed |
| `admitted_at` | split key, chronological; calendar features derivable | observed |
| `patient_id` | split key, grouped; never a feature | observed |
| `age` | feature | observed |
| `region` | feature, 4 levels | observed |
| `systolic` | feature, 5.3% null | observed |
| `cholesterol` | feature, 8.9% null | observed |
| `site_version` | dropped — constant | observed |
