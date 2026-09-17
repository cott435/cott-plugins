# `documenter` — does it look for `interface.md` headings that are ever written?

**Tested against:** `259785a` (`agents/documenter.md`, `agents/implementer.md`,
`skills/finalize-project/SKILL.md`) · model: none — no agent was run, see **Method** ·
2026-09-17

## What was tested

`agents/documenter.md` told the agent that `interface.md` "follows a fixed seven-heading
template (Public names, Pipelines, **Scripts**, Configuration, Shapes provided, Deviations,
**Consumers**)". The owner of that template — `agents/implementer.md`, surface mode — writes
heading 3 as **CLI commands** and heading 7 as **Consumers (computed)**. The claim under test:
every heading the documenter is told to expect is a heading something in this plugin actually
writes. If not, the documenter is parsing for headings that cannot occur, and the CLI-commands
row of every package README (`finalize-project` step 3, "Pipelines and CLI commands — from
`interface.md`") depends on one of them.

## Method

**Mechanical, not behavioral.** A behavioral run — `claude -p --agent documenter` against a
fixture repo, the harness
`2026-09-16-implementer-security-review-trigger.md` used — was **not possible**: the audit ran
from a Cowork session whose shell has the `claude` CLI stubbed
(`claude: claude is not enabled in this environment`), so no agent could be launched. What was
run instead, and what that does and does not settle:

1. Built a fixture `interface.md` for a package `data` by following the implementer's surface-mode
   template heading for heading — the document a real `/dev-team:finalize-package data` run is
   instructed to produce.
2. Exact-heading match (`grep -c '^## <heading>$'`) for each of the four names in dispute.
3. Swept every agent and skill in the plugin for any instruction that would write a `Scripts`
   heading in any form (`## Scripts`, `**Scripts**`, a numbered template item).

Sample size 1 fixture, 0 model runs, no API cost. Held constant: the implementer's template as
committed at `259785a`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `## Scripts` in a template-conformant `interface.md` | present, per `documenter.md` | 0 matches | ❌ |
| `## CLI commands` in the same file | — | 1 match | — |
| `## Consumers` in the same file | present, per `documenter.md` | 0 matches | ❌ |
| `## Consumers (computed)` in the same file | — | 1 match | — |
| Anything in the plugin that writes a `Scripts` heading | at least one | 0 instructions, in 7 agents and 20 skills | ❌ |
| Other `interface.md` headings the documenter reads (Public names, Pipelines, Configuration, Shapes provided) | present | 4/4 match | ✅ |
| Other readers of `interface.md` by heading — `reviewer.md` (Public names, Shapes provided), `sync-plan` (Consumers (computed)), `finalize-project` (Public names) | correct | 4/4 correct | ✅ |

## Verdict

**The claim does not hold, for two of the seven headings.** `Scripts` is written nowhere in the
plugin, and `Consumers` is written only as `Consumers (computed)`. The mismatch is real and
confined to `agents/documenter.md`; every other consumer of `interface.md` cites its headings
correctly.

**What this does not settle:** whether the mismatch changes what a documenter run actually
produces. A model reading a real `interface.md` may well map `Scripts` onto the `CLI commands`
table by proximity and produce a correct README anyway — the failure mode the audit asserted
("will report a missing heading and drop CLI commands") is plausible but **unverified**. The
instruction was wrong either way, and it sat next to a second instruction
(`finalize-project` step 3) that named the right heading, so the run's output depended on which
of two conflicting instructions won.

**Fixed** in the same change, uncommitted at the time of writing — see the working-tree diff to
`agents/documenter.md`. The paragraph no longer restates the template: it names only the six
headings the documenter consumes, spelled as the owner writes them, and says that a heading it
cannot find is a **Known gaps** entry rather than something to substitute a similar heading for.
That removes the duplicated heading list, which is what let the two files drift.

**Not re-run.** The fix is verifiable by inspection — the six names now match the owner's
template exactly — and the behavioral question above needs a harness this environment cannot
provide. To close it properly, from a machine with a working CLI:

```
claude --plugin-dir ~/dev/cott-plugins/dev-team -p \
  "/dev-team:finalize-project"        # in a fixture repo whose docs/packages/data/interface.md
                                      # is the fixture above, then check whether
                                      # packages/data/README.md carries the data-daily command
```

Worth running before the next release that touches `documenter.md`: it is the only agent in the
plugin whose whole job is parsing other agents' output by heading, so it is the one where a
heading contract failing silently costs the most.
