# Constraint-Driven Development

The method `/dev-team:set-constraints` follows. Vendored from `agent-skills` by Addy Osmani
(MIT; terms in `../LICENSE`) and adapted to this plugin's stack — `uv`, `pytest`, `ruff`,
`mypy`, `interrogate`, `lint-imports`. The file it produces is `docs/constraints.md`, in the
shape `constraints-template.md` beside this file fixes.

## Overview

The other knowledge skills in this plugin describe what good looks like: `python-style-guide`
the inside of a file, `project-structure` its size and placement, `test-driven-development`
the cycle, `security-review` the threat list. All of that is prose an agent reads and may or
may not follow, and none of it carries a number the project chose.

This produces something different: a written record of **this project's** bar, with numbers,
that outlives the conversation and can be checked mechanically.

The reason matters. When you wrote the code, reading it told you whether it was any good. An
agent writes more in an afternoon than you will read that week, so the judgement moves out of
your head and into checks that run around the loop. Those checks need to exist, they need
numbers you actually chose, and they need to fire close enough to the work that the agent
fixes its own output.

The design says what to build. Tests prove it works. Constraints define what "good enough to
ship" means, before anyone argues about it in a review.

## Step 1: Detect before you ask

Never ask what you can read. Before the first question, gather:

| What | Where to look |
|------|---------------|
| Stack and toolchain | root `pyproject.toml`; `docs/architecture.md` **Toolchain** |
| Existing thresholds | `[tool.coverage.report] fail_under`, `[tool.mypy] strict`, `[tool.interrogate] fail-under`, `[tool.ruff.lint] select` |
| Coverage today | an existing `.coverage` or `coverage.xml`; otherwise none — do not run the suite to find out |
| CI | `.github/workflows/` |
| A bar already written | `docs/constraints.md` — revision mode |

Report what you found in two lines, then ask only what is left.

## Step 2: Four questions, each with a default

Every question has a default, so "I don't know" is a complete answer that still produces a
working file.

```
Q1: What line-coverage floor should every package clear?
    80 % · 90 % · none — measure only
DEFAULT: 80 %. High enough to force a test, low enough to allow a config line.
```

```
Q2: How strict should type checking be?
    mypy --strict · mypy default · none
DEFAULT: --strict. A new repo starts clean; strictness added later costs a sweep.
```

```
Q3: What docstring coverage should every package clear?
    95 % · 80 % · none
DEFAULT: 95 %. python-style-guide already requires a docstring on everything; this makes
it a number interrogate can fail.
```

```
Q4: Anything to record without enforcing yet?
    none · a runtime budget per pipeline, in seconds
DEFAULT: none.
```

Stop at four. A twelve-question intake produces a file nobody understands and a user who
regrets starting.

## Step 6: Guard the bar itself

Someone will point out that if the agent writes the code and the checks, the checks prove
nothing. Half right, and worth engineering around.

Agents don't craft clever loopholes. They hit a red check and take the cheapest road to green.
Watch for these five moves in the diff, at review time:

1. **The threshold moved.** A `--cov-fail-under` lowered, `--strict` dropped, a path excluded
   from a command. Compare `docs/constraints.md` against its state at the previous review.
2. **A test got easier.** `@pytest.mark.skip` or `xfail` added, a test file deleted,
   `assert` lines or `pytest.raises` blocks pulled out of tests that stayed.
3. **A checker got silenced.** A new `# noqa` or `# type: ignore`. `# pragma: no cover` needs
   special attention: it drops code from coverage instead of testing it.
4. **Work is unfinished.** A stub that raises `NotImplementedError`, an `except Exception:
   pass` turning a failure into silence, a `TODO` standing where the implementation should be.
5. **An exception appeared.** A new row in the Exceptions table nobody discussed, or a
   `project-structure` §2 limit exceeded "temporarily".

None of this needs tooling beyond `git diff`. Tightening the bar should be silent; loosening
it should be loud. In this plugin the reviewer's axis 0 is that guard, and the **Guarded**
list in the template is its checklist.

**Not all checks are equally circular.** Rank them by one question: can the agent make this
pass by writing code that doesn't work?

- **External** — `mypy` encodes the type system, `ruff` rule sets encode published style
  rules. The agent can't argue with these.
- **Project** — `lint-imports` contracts, `project-structure` limits. A human owns the file.
- **Suite** — the tests, and coverage of them. Most useful, and the only genuinely circular
  one — which is why this plugin has a tester writing intent tests from the design, apart from
  the implementer's own.

A bar made entirely of the third kind is worth less than one with an outside opinion in it.

## Step 7: Ratchets, when you don't have a number

Set 80 % coverage on a codebase at 62 % and you get a red build forever, then a team that
learns to ignore red builds.

The alternative asks for no decision: record where you are, then refuse to get worse. Put it
in the **Measured** table with today's number and a target. Every review reports against the
recorded value, not an aspiration. When a number improves, update it; when it holds at the
target, move the row to **Enforced**.

## Sane Defaults

When the user has no opinion, use these. They are chosen to be met by a new package on day
one.

| Constraint | Default | Why this number |
|------------|---------|-----------------|
| Line coverage per package | ≥ 80 % | High enough to force a test, low enough to allow a config line |
| Types | `mypy --strict`, 0 errors | Cheapest to hold from the first section; costly to adopt later |
| Docstring coverage | ≥ 95 % (`interrogate`) | `python-style-guide` requires them; 5 % absorbs trivial dunders |
| Coverage on an existing codebase | today's value, as Measured | No argument needed to adopt |
| Exception lifetime | 90 days | Long enough to plan the fix, short enough to remember |

State the number and the reason together. A threshold without a rationale gets deleted by the
next person who hits it.

## Escalation Path

Constraints work at three levels of teeth. Start at the first.

1. **Written only.** `docs/constraints.md` exists and agents read it. Costs nothing, catches
   the honest mistakes, relies on the agent complying.
2. **Scripted.** Every row names a command, and the implementer, the reviewer,
   `status.py --gate` and CI run them. Deterministic, no new dependency. This plugin sits
   here.
3. **Tool-backed.** A dedicated runner for diff scoping, budgets and ratchets. Worth it only
   when the check-running outgrows the rows of one file.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "We'll add constraints once the code settles" | Code settles around whatever was allowed while it was moving |
| "The tests are the constraints" | Tests you wrote prove you agree with yourself; they say nothing about coverage, types or docstrings |
| "We can't hit 80 % coverage" | Then don't set 80 %. Measure today's number and hold it |
| "This will slow the agent down" | The slow rows run once per section at step 8, not per edit |
| "I'll remember what our standards are" | The agent won't, and it's writing most of the code |
| "Constraints will block us shipping" | An exception with a reason and a date unblocks you. Deleting the constraint unblocks everyone forever |

## Red Flags

Stop and reconsider if you notice:

- The interview ran past four questions, or produced a file the user can't explain
- A threshold was set that the codebase fails today, with no plan to reach it
- A row has a number but no command behind it
- Every row is judged by the project's own test suite, with no outside opinion
- `docs/constraints.md` changed in the same commit as the section that was failing it
- An exception has no reason, or an expiry more than 90 days out
- An agent proposed relaxing a threshold instead of fixing the code

## Provenance

Upstream `addyosmani/agent-skills` `skills/constraint-driven-development/SKILL.md` at
`c004a74`; upstream writes `CONSTRAINTS.md` at the repo root, this plugin `docs/constraints.md`.
Dropped: When to Use, Loading Constraints, Steps 3–5 (the template, JS tooling, the lifecycle —
fixed here), Verification, See Also, the floor-guard reference. Rewritten: the four questions
and every threshold, suppression and tool to Python. Added: nothing but this plugin's names.
