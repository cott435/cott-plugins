# fix-issues eval 3 — `open`, nine issues across five roles

Seed: build the fixture in `fixture.md` (same directory as this sheet) exactly, with these
further issues at its step 5, in this order, so their ids are `TO-003` to `TO-009`. Each is
the same command with a different title and `--applies-to`:

```
I new --dir $TMP/repo/toy --title "<title>" --fault definition --severity WARN --check procedure --applies-to <applies-to> --rule-file agents/writer.md --rule-line 15 --rule-quote 'You only ever write under `out/`; never anywhere else.' --found-version 0.1.0 --found-session 0a0d17f0 --found-date 2026-09-28 --finding "<title>." --unit U01 --step U01.S2 --evidence "seen once" --report runs/audits/reports/2026-09-28-0a0d17f0.md --finding-id W<n>
```

| id | title | applies-to |
|---|---|---|
| TO-003 | writer returned prose before its Result line | agent:writer |
| TO-004 | checker approved a file it did not open | agent:checker |
| TO-005 | checker and writer disagree on the out/ rule | agent:writer, agent:checker, cross |
| TO-006 | packer wrote the archive before the check passed | agent:packer |
| TO-007 | ship did not print the checker's verdict | driver:ship |
| TO-008 | publish read the writer's file to decide what was next | driver:publish |
| TO-009 | packer returned done with no archive path | agent:packer |

The ledger then holds nine issues, all `open`. The toy plugin has no checker, packer or
publish file; the issues name them all the same, and that is not yours to fix.

## Answers

Answer each question you would have asked with the first line below that covers it. If none
does, take the option marked Recommended.

- Which plugin: the one in the working directory, `$TMP/repo/toy`.
- Anything else: I typed `/plugin-dev:fix-issues open` and nothing more. I have no further
  instruction, and I did not type `--here`.

## What goes in `outputs/`

As `fixture.md` says, except: `outputs/toy/` is a copy of `$TMP/repo/toy` when no worktree
was made, and `outputs/check.txt` is `I check --dir $TMP/repo/toy`. Also write
`outputs/git-status.txt`: the output of `git -C $TMP/repo status --porcelain`, taken at the
end (an empty file when the tree is clean).
