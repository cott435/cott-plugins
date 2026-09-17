# `names_listed` gains `where` and `form` — does the three-file rule now enforce itself?

**Tested against:** uncommitted — `where`, `form` and the `skills/**/*.py` authored glob are new
in this change, see the working-tree diff · model: none, the subject is a deterministic script ·
2026-09-17

## What was tested

`dev-team/CLAUDE.md` states that adding a skill means updating three files:
`reserved-skill-names`, `README.md`'s Contents tree, and `site/site.yml`'s
`workflow_skills_order`. Only the first was checked; the other two were eyeball work, which is
how a plugin ends up shipping a Contents tree that is a version behind. Two `contracts.yml`
claims now cover them, which needed two additions to `names_listed` — `form`, because those two
lists are a fenced directory tree and a YAML sequence rather than backticked prose, and `where`,
because the run order is answerable for workflow skills only.

A claim that cannot be observed failing is not enforcement. So each new claim was run against a
bundle carrying a defect of exactly the shape it exists to catch, and against cases it must
**not** fire on, which is where a `where` filter goes wrong.

## Method

`dev-team` at this change's working tree is the reference bundle — eight claims, 8/8 passing.
Copied it to scratch, planted one defect at a time, ran `contract_sweep.py --quiet` over each.
No model runs, no API cost.

The third new claim, `forbid` on unprefixed commands, is tested here too: it was written
structurally — any slash-initial token carrying a hyphen, plus `/status`, not already prefixed
`dev-team:` — rather than as a list of the 21 skill names, so that a skill added later is
covered without touching the pattern. That design only holds if it neither misses a bare command
nor fires on Claude Code's own.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| real bundle, all eight claims | 8/8 PASS, exit 0 | 8/8 PASS, exit 0 | ✅ |
| `probe-source/` cut from README's Contents tree | FAIL naming the skill | FAIL `not listed in README.md: probe-source` | ✅ |
| `status/` misspelled `stauts/` in the tree | FAIL both directions | FAIL `not listed: status; listed but no such directory: stauts` | ✅ |
| bare `` `/plan-package data` `` added to a prompt | FAIL naming the line | FAIL `agents/architect.md:404` | ✅ |
| `/dev-team:plan-package`, `/agents`, `/model` on one line | no failure | no failure | ✅ |
| new `skills/ship-it/` with `disable-model-invocation: true` | FAIL on all three lists | FAIL on reserved-names, README tree, site.yml | ✅ |
| new `skills/some-guide/` without it | FAIL on two lists, **not** the run order | FAIL on reserved-names and README tree only | ✅ |
| `where` key misspelled `disable-model-invokation` | FAIL, not a silent pass | FAIL `` `dirs: skills/*` + `where` matched no directory `` | ✅ |

The two real defects the claims found on their first run are the ones that justify them: **D2**
— 21 unprefixed commands across `site/flow.md`'s three diagrams and prose — and **D3** —
`status.py` printing `/finalize-package` and `/plan-package` to the user. Both were fixed in the
same change, along with **D5**, `status` missing from the run order, which the new `where` claim
reported by name.

## Second round — the `unless` leak

The first round tested the command claim with one bare command on its own line, which is not how
a bare command would actually get written. `unless` is matched against the whole **line**, and
`/reload-plugins` sits in all 14 guard blocks — the exact place someone writes a command name. So
the claim was re-probed with the exemption present:

| Case | Expected | Observed (before) | After |
|---|---|---|---|
| `` `/plan-repo` `` alone | FAIL | FAIL | FAIL ✅ |
| `` `/plan-repo` ``; if missing, `` `/reload-plugins` `` | FAIL | **passed — missed** | FAIL ✅ |
| a bare command on the `reserved-skill-names` line | FAIL | **passed — missed** | FAIL ✅ |
| `` `/dev-team:plan-repo` ``, not `` `/plan-package` `` | FAIL | — | FAIL ✅ |
| bare `` `/status` `` | FAIL | — | FAIL ✅ |
| two bare commands on one line | FAIL | — | FAIL ✅ |
| only prefixed + `/agents` + `/model` | silent | silent | silent ✅ |
| a guard block verbatim | silent | silent | silent ✅ |

**Fixed by removing both exemptions rather than by widening the test.** `/reload-plugins` moved
into the pattern as a second negative lookahead, where it exempts the token and not the line. The
other exemption existed for one sentence in `reserved-skill-names` describing the collision this
list prevents; that sentence now says "the project's own unprefixed `plan-repo` command" — a
name, not a command — so the claim carries no `unless` at all and the leak has nowhere to live.

## Verdict

**Every case behaved as intended, and the interesting ones are the two that must not fire.**
Three findings worth keeping:

- **A `where` typo has to fail loudly.** A frontmatter filter that matches nothing would
  otherwise report `0 names, all listed` — a claim that has quietly turned itself off while
  still printing `PASS`, which is worse than not declaring it. `check_names_listed` now returns
  `FAIL` on an empty selection, and the message names `dirs` and `where` so the typo is visible.
- **`form: list` had to tolerate a trailing comment.** The first version anchored the bullet to
  end-of-line, so adding `status` to `site.yml` with a comment explaining why it is not a step
  still read as missing. The checker was fixed rather than the comment removed: a claim that
  dictates how the file it checks may be annotated will eventually be worked around.
- **A line-level `unless` is a hole, not a caveat.** The skill already warned that the checks
  are line-based, filed under "write your exemption to survive a line break". That is the smaller
  half. The real cost is that one exempt phrase pardons everything else on its line, and an
  exemption tends to live exactly where the thing it pardons is discussed. Prefer a negative
  lookahead in the pattern, which exempts a token; reach for `unless` only when the legitimate
  case cannot be distinguished by its own text, and then expect to test a violation sitting
  beside it. The bundle's older `scripts/` claim still has eight line-level exemptions and has
  not been probed this way.
- **The structural `forbid` pattern beats a list of names.** The 21 skill names were the obvious
  way to write it and would have been a fourth copy of the list this bundle already fought to
  reduce to one. Requiring a hyphen is what makes it work: every plugin command has one and
  Claude Code's own (`/agents`, `/model`, `/plugin`, `/clear`) have none, so the only exemption
  needed is `/reload-plugins`.

**Still not a behavioral eval.** This settles that the checker reports what the files say. It
says nothing about whether an agent obeys a rule it reads; that needs a real run, and
`claude -p --agent …` remains unavailable here (the CLI is stubbed).

**Re-run both halves whenever `contract_sweep.py` changes.** The eight cases above rebuild from
a fresh copy of the bundle in under a minute.
