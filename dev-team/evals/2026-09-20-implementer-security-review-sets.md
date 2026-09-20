# `implementer` — the security-review claim, rerun from a committed set

**Tested against:** `9fc74a3` (`agents/implementer.md`), `259785a`
(`skills/security-review/SKILL.md`) · model: Opus 5 (`claude-opus-5`), the session model every
subagent inherited · 2026-09-20
**Set:** `evals/sets/implementer.json` evals 1–8 · **Iteration:**
`evals/workspace/implementer/iteration-1` · **Baseline:** none (`without_skill`) ·
**Pass rate:** 87.5% (28/32) vs 40.6% (13/32)

Run from `plugin-dev`'s 0.9-evals branch, phase 6, whose job was to give `dev-team` committed
eval sets. This is the first run of one of them.

## What was tested

`agents/implementer.md` Procedure step 3 tells the agent to decide from `security-review`'s
frontmatter description whether the section matches any **When to Activate** condition, and,
if one does, to invoke the skill *before* writing the code it bears on — the rule
`2026-09-16-implementer-security-review-trigger.md` added after finding 2 of 4 positive cases
writing security prose from memory with no tool call behind it. The claim under test is that
one: does the agent open the checklist when a section matches, and leave it shut when none
does. The eight cases are that log's eight, reconstructed one for one.

## Method

**Proxy, not a real agent run.** The original drove `claude -p --agent implementer` in a cloud
sandbox and read `--output-format stream-json` for a `Skill` call with
`"skill":"security-review"`. That instrument does not exist here: a run of this set gives a
general-purpose subagent `agents/implementer.md` as its instructions, and `dev-team` is not a
loaded plugin in that session, so its skills are not registered and no `Skill` call for
`security-review` is possible. Every prompt therefore states the substitution — the skill
library is `dev-team/skills/` (21 directories), and invoking a skill means reading its
`SKILL.md` and recording that in `transcript.md` before the work it bears on. The agent still
has to pick the right skill out of 21 from descriptions alone; what is lost is the tool call
as evidence, so a run's own transcript is what says whether it read the file. `eval-kinds.md`
**Baselines** calls this a proxy and so does this entry.

Sixteen runs, one per configuration per eval, all in parallel, through `run-evals`'
behavioral loop: `eval_workspace.py init . implementer --baseline none`, sixteen executors,
sixteen graders (skill-creator's `agents/grader.md`), `finalize`, `aggregate_benchmark`, the
static viewer. `with_skill` is `agents/implementer.md` as committed; `without_skill` is the
same task with no agent file, which is the contrast the phase note asked for — `previous` is
the set's committed baseline, but this branch does not touch `dev-team`, so it would have
compared the agent against an identical copy of itself.

Held constant: the same prompt text for both arms, the same harness rules, one run each.
Varied: whether the executor was given the agent file.

Cost: 1.86M executor tokens (1.20M `with_skill`, 0.66M `without_skill`), ~71 min of executor
wall time across 16 parallel runs, plus 16 graders at ~74k each. No real API calls left the
harness; nothing was written outside the iteration directory.

## Results

Per case, the question the original log asked — was the checklist actually opened:

| Case | Section | Should invoke? | `with_skill` invoked? | Agrees with 2026-09-16 | Grade ws / wo |
|---|---|---|---|---|---|
| 1 | `auth/login` | Yes | Yes | ✅ | 4/4 · 1/4 |
| 2 | `data/ingest` (API key + outbound call) | Yes | Yes | ✅ | 4/4 · 1/4 |
| 3 | `models/loader` (pickle) | Yes | Yes | ✅ | 4/4 · 2/4 |
| 4 | `reporting/export_api` (new endpoint) | Yes | Yes | ✅ | 4/4 · 1/4 |
| 5 | `analytics/resample` (pure) | No | No | ✅ | 4/4 · 1/4 |
| 6 | `reporting/format` (pure) | No | No | ✅ | 2/4 · 3/4 |
| 7 | `shared/types` (definitions) | No | No | ✅ | 3/4 · 2/4 |
| 8 | `features/indicators` (pure) | No | No | ✅ | 3/4 · 2/4 |

8/8 agree with the post-fix verdict, including cases 2 and 4 — the two the original caught
writing mitigations from memory. In all four positive cases the transcript records the
checklist opened before the section's code, and the graders re-ran the outputs rather than
trusting the claim: case 3's restricted unpickler provably refuses an `os.system` `__reduce__`
payload, case 4's endpoint has the fail-closed 401 and 404-not-403 the checklist prescribes,
case 1's suite is green under `ruff --select S` and `bandit`.

The baseline read no skill in any of the eight runs, which is what makes the contrast a
result rather than an artifact of the description gate: the gap between 87.5% and 40.6% is
almost entirely the four procedure expectations, not the quality of the code.

### The four `with_skill` failures

Two are a finding about the agent, two are a defect in the expectations:

- **Cases 6, 7 and 8 — an unearned security paragraph on a negative case.** Each correctly
  declined to invoke `security-review`, then wrote a bolded **Security** paragraph anyway: in
  the final message (6, 7), in the section README (7, 8). `implementer.md` lines 221–224 say
  exactly this is the failure the step exists to catch — "a security paragraph with no tool
  call behind it". The 2026-09-16 fix closed the gap on the positive side; this run says it is
  open on the negative side, where an agent that has just decided the checklist does not apply
  still produces checklist-shaped prose. Case 8's Security step also enumerated all seven
  activation conditions in ~85 words rather than dismissing them in a line.
- **Case 6 failed on wording, not behavior.** The expectation read "records no reading of
  `skills/security-review/SKILL.md`" — but Procedure step 3 *requires* reading that skill's
  frontmatter description to make the decision. Four graders flagged it independently. The run
  read the description, quoted it, never opened the body, and decided correctly.

### What the graders said about the set

Collected from all 16 `critique` fields, and acted on in this change (`run-evals` behavioral
loop, step 7):

| Critique | Applied to `evals/sets/implementer.json` |
|---|---|
| "records no reading of SKILL.md" contradicts the agent's own step 3 (×4 graders) | now checks the **body** was never opened; reading the frontmatter is stated as expected |
| "at least one test file" passes on an empty stub (×7) | tests must have been executed, with the command and result in the transcript, and name this section's behaviors |
| The unsupported-claim check is scoped to the final message, so a false claim in the Security step escapes (case 4's "CRLF → 422" test, which does not exist) | covers the Security step, the README and the final message alike |
| "in about one line" bundles a length budget with a behavioral clause and two graders can legitimately split on it (×3) | split: "at most three sentences" and "no walkthrough of the areas one by one" |
| Every expectation grades prose the executor writes about itself; nothing is graded from `outputs/` alone (×6) | new positive expectation graded from `outputs/` without the transcript: two of the checklist's controls visible in the code |
| Nothing catches the security paragraph reappearing in the README | the negative arm's expectation now covers everything the run produces |

The pass rates above were measured against the wording *before* that revision, which is what
the table reports; the new wording is in the set, and iteration 2 is its first measurement.
Not applied: the graders' suggestions to check work quality — indicator correctness, the
`httpx2` typo one grader found in case 1's dev dependencies, the unrequested `max_bins`
parameter in case 5's baseline. Those are real, but this set's claim is the security step, and
a set that grades everything grades nothing.

## Verdict

**The claim holds.** 8/8 cases agree with the original log's post-fix verdict, on a proxy
rather than a real `--agent` run, and the committed set now makes that answer repeatable — the
first time this claim has been checkable by anything other than redoing the whole thing.

Two things this does not settle. The proxy cannot see a `Skill` tool call, so "invoked" here
means "read the file and said so"; a run that lied in its own transcript would score as a
pass, and only three graders corroborated the read against the outputs. And n=1 per
configuration: the original log's own caveat about run-to-run variance applies unchanged.

**Follow-up worth its own eval:** the unearned security paragraph on negative cases. The fix
is a sentence in `implementer.md` step 3 — that the one-line "no condition matches" verdict is
the whole of what a non-matching section gets, in the return message and the README too — and
`evals/sets/implementer.json` evals 5–8 already assert it, so the re-test is a rerun. Not done
here: this phase belongs to `plugin-dev` 0.9-evals and changes no `dev-team` prompt.

## The other two sets

Committed unrun, as the phase note specifies:

- `evals/sets/documenter.json` — 2 evals, from
  `2026-09-17-documenter-interface-heading-contract.md`. That log's own cases are heading
  checks, now `contracts.yml`'s `interface.md headings` claim; what it left open, and named as
  the run worth doing before the next release touching `documenter.md`, was whether the
  heading contract changes what a run produces. The two evals are that: the `data-daily`
  command reaching the package README through **CLI commands**, and an absent heading becoming
  a **Known gaps** entry with nothing substituted for it.
- `evals/sets/researcher.json` — 1 eval, from `2026-09-18-probe-doc-headings-claim.md`, which
  named its own next test: a dataset probe that writes statistics and no rows, on the template's
  headings. The `api` kind is left out — it needs a live credential and real vendor calls.
- `2026-09-17-cross-file-contract-sweep.md` gets **no set**. It is mechanical and already
  enforced: `check-contracts` runs its claims from `contracts.yml` on every change, 9/9 passing
  as of this commit. A model rerunning a `grep` is not a regression test, it is a slower one.

`dev-team-0.5-overhaul` may rename or reshape these three agents. No such branch exists in
this repository — `git branch -a` lists `main`, `plugin-dev-0.9-evals` and three `claude/*`
session branches — so the reconciliation could not be recorded in its ledger, as the phase
note would have preferred. It is recorded here instead: **whichever branch reshapes these
agents owns updating `target_path` and the prompts in these three sets at merge.**

## Notes for the next run

- `aggregate_benchmark` prints `runs_per_configuration: 3` and `<model-name>` for a
  one-run-per-configuration iteration; both are cosmetic, and phase 4 recorded the same.
- The static viewer renders over `python3 -m http.server`; "Submit All Reviews" never writes
  `feedback.json` from a static page, so the review was given in chat.
- Executors need the plugin directory spelled out as an absolute path. "The directory holding
  `.claude-plugin/plugin.json`" was enough here only because the prompt also gave the repo root.
