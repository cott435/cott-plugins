# L — fixed context cost per agent run, from eval K

**Tested against:** `9d1c048` plus the uncommitted phase-9 docs (the same runs as
[eval K](2026-09-19-k-end-to-end.md)) · model: `claude-sonnet-5` · Claude Code `2.1.270` ·
2026-09-19

## What was tested

Note 09 §L, a measurement rather than a claim: for every Agent call the driver made in eval K,
the tokens an agent holds before it does any work (its fixed cost) and the tokens it ends
with. The result decides whether a *derived* task packet is worth building in 0.6. Nothing in
the plugin changes because of it in 0.5.

## Method

The data comes from K's stream logs, runs 3, 4 and 9, the three `run-package` invocations. For
every `task_started` with a `subagent_type`, the stream's `task_progress` /
`task_notification` events carry `usage.total_tokens`, the agent's context size at that
moment.

- **fixed**: the value at the first progress event, after one tool use. That is the system
  prompt, preloaded skills, the task prompt and the first tool result. It is an upper bound on
  the pure fixed cost by one tool result, typically a single `Read` or `git` call.
- **total**: the value at the task's completion notification, the context the agent ended
  with. It is not a sum over turns.

The designers spawned inside the forked `plan-package` runs (2 and 5) are listed separately.
A forked skill's own architect emits no task events, so those runs have no architect row.
No extra cost: this re-reads K's logs.

## Results

| K run | role | spawn | fixed | total |
|---|---|---|---:|---:|
| 3 | tester | Test-section intent run for data/ingest | 39,503 | 87,765 |
| 3 | implementer | Implement-section run for data/ingest | 54,141 | 141,257 |
| 3 | tester | Test-section reconcile run for data/ingest | 39,676 | 64,116 |
| 3 | reviewer | Review-section run for data/ingest | 38,409 | 119,157 |
| 3 | implementer | Implement-section run 2 for data/ingest | 54,319 | 108,764 |
| 3 | tester | Test-section reconcile run 2 for data/ingest | 39,644 | 62,523 |
| 3 | reviewer | Review-section run 2 for data/ingest | 38,487 | 70,674 |
| 3 | architect | Plan-package completion run for data | 38,396 | 93,775 |
| 3 | designer (depth 2) | Design data/clean section | 25,940 | 41,081 |
| 3 | designer (depth 2) | Design data/storage section | 26,170 | 46,032 |
| 3 | reviewer | Review-plan run for data | 38,499 | 92,820 |
| 4 | tester | Test-section intent for data/clean | 39,596 | 92,753 |
| 4 | implementer | Implement-section data/clean | 54,382 | 105,277 |
| 4 | tester | Test-section reconcile for data/clean | 39,625 | 50,469 |
| 4 | reviewer | Review-section data/clean | 38,489 | 76,905 |
| 4 | tester | Test-section intent for data/storage | 39,611 | 94,402 |
| 4 | implementer | Implement-section data/storage | 54,315 | 117,644 |
| 4 | tester | Test-section reconcile for data/storage | 39,754 | 48,670 |
| 4 | reviewer | Review-section data/storage | 38,476 | 77,602 |
| 4 | implementer | Finalize-package data surface build | 54,299 | 145,162 |
| 4 | reviewer | Review-package data | 38,465 | 125,797 |
| 4 | architect | Sync-design data | 38,420 | 75,822 |
| 9 | tester | Test-section intent for analysis/features | 39,590 | 98,968 |
| 9 | implementer | Implement-section analysis/features run 1 | 54,439 | 184,496 |
| 9 | tester | Test-section reconcile for analysis/features | 39,771 | 50,696 |
| 9 | reviewer | Review-section analysis/features | 38,474 | 91,658 |
| 9 | tester | Test-section intent for analysis/report | 39,670 | 78,007 |
| 9 | implementer | Implement-section analysis/report run 1 | 54,449 | 105,585 |
| 9 | tester | Test-section reconcile for analysis/report | 39,735 | 48,983 |
| 9 | reviewer | Review-section analysis/report | 38,456 | 85,064 |
| 9 | implementer | Finalize-package analysis | 54,392 | 132,085 |
| 9 | reviewer | Review-package analysis | 38,444 | 84,182 |
| 9 | architect | Sync-design analysis | 38,417 | 66,559 |

Plan-time designers outside the driver: run 2 `dev-team:designer` (ingest) 25,880 → 41,943;
run 5 `general-purpose` (features) 29,710 → 61,094 and (report) 29,670 → 76,833.

Per role, over the driver's 33 spawns:

| role | runs | fixed (min–max, mean) | total (min–max, mean) | fixed as % of mean total |
|---|---:|---|---|---:|
| implementer | 8 | 54,141–54,449, 54,342 | 105,277–184,496, 130,034 | 42 % |
| tester | 11 | 39,503–39,771, 39,652 | 48,670–98,968, 70,668 | 56 % |
| reviewer | 9 | 38,409–38,499, 38,467 | 70,674–125,797, 91,540 | 42 % |
| architect | 3 | 38,396–38,420, 38,411 | 66,559–93,775, 78,719 | 49 % |
| designer (depth 2) | 2 | 25,940–26,170, 26,055 | 41,081–46,032, 43,556 | 60 % |

## Verdict

Measured. Fixed cost barely varies by role (the spread is under 350 tokens) whatever the
section or package. It is set by the agent body and its preloaded skills, not by the task.
The implementer carries about 54k before its first read, 16k more than the reviewer or
tester, which lines up with the longest agent body (about 5,700 words, against 3,400 for the reviewer
and 1,600 for the tester) and one more preloaded skill (`git-workflow-and-versioning`). Fixed cost is 40–60 % of what each
agent ends with. So a derived task packet could only save the reads an agent does *after* its
first tool use. Those reads are the 16k–130k spread between fixed and total, which is widest
for the implementer and the package reviewer. The fixed half would shrink only by cutting
agent bodies or preloads. That is the number 0.6 should weigh a packet against. No plugin
change is made on its basis in 0.5.
