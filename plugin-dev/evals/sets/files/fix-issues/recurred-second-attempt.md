# fix-issues eval 2 — one recurred issue, a second attempt

Seed: build the fixture in `fixture.md` (same directory as this sheet) with the two
additions below. The ledger then holds TO-001 and TO-002 (`open`) and TO-003 (`recurred`).

## The edit before the first commit (fixture step 3)

In `$TMP/repo/toy/agents/writer.md`, change the Procedure's step 2 from

    2. Run `python3 -m pytest -q` and read the summary line.

to

    2. Run `python3 -m pytest -q` and read the summary line. The counts you return are the ones it printed.

That is the edit TO-003's first attempt made; the fixture's one code commit on `main` is that
attempt's commit.

## The further issue (fixture step 5, after TO-002)

```
I new --dir $TMP/repo/toy --title "writer returned tests: 4 passed, 0 failed after pytest printed 1 failed, 3 passed" --fault agent --severity ERROR --check claims --applies-to agent:writer --rule-file agents/writer.md --rule-line 25 --rule-quote 'tests: <n> passed, <n> failed' --found-version 0.1.0 --found-session 0a0d17f0 --found-date 2026-09-28 --finding "pytest printed '1 failed, 3 passed' and the writer's return said 'tests: 4 passed, 0 failed'. The return's tests line is the summary line's counts, not a claim." --unit U01 --step U01.S3 --evidence "1 failed, 3 passed" --report runs/audits/reports/2026-09-28-0a0d17f0.md --finding-id E2
```

Then the first attempt and the rerun audit's verdict on it, with `SHA` being
`git -C $TMP/repo rev-parse --short HEAD` (the one commit on `main` at this point):

```
I fix --dir $TMP/repo/toy TO-003 --branch toy-audit-fixes-20260930 --commit SHA --files agents/writer.md --evals evals/2026-09-30-writer-fix.md --verify "watch agent:writer; held when the return's tests line repeats the counts of the pytest summary line in the Bash step before it; recurred when the tests line's counts differ from that summary line"
```

```
I check-result --dir $TMP/repo/toy TO-003 --attempt 1 --verdict recurred --session 1b2c3d4e --version 0.1.0 --date 2026-10-02 --unit U02 --step U02.S4 --evidence "tests: 4 passed, 0 failed"
```

`I status --dir $TMP/repo/toy TO-003` prints `recurred` before you go on to step 6.

## Answers

Answer each question you would have asked with the first line below that covers it. If none
does, take the option marked Recommended.

- Which plugin: the one in the working directory, `$TMP/repo/toy`.
- Approve the plan, as proposed: **Approve the plan.** (If asked again after a change: approve.)
- Merge the branch into `main`: **No. Leave the branch and the worktree where they are.**
- Bump the version, or run `bump-version`: **No, not now.**
- Why the first attempt did not hold: I do not know; the rerun's trace is what the Checks line
  quotes, and the sentence attempt 1 added is still in `agents/writer.md`.
- The fixture's main checkout (`$TMP/repo`) is on `main` with a clean tree; nobody else is
  working in it.

## Where to write what you would commit

Commits and branches in `$TMP/repo` and its worktrees are fine — that is the fixture's job.
Nothing is written in the cott-plugins repo. At the end, fill `outputs/` as `fixture.md`
says.
