# Platform facts — `subagent_type` resolution and `${CLAUDE_PLUGIN_ROOT}` substitution (0.5 evals A and B)

**Tested against:** `3127526` (the plugin tree; `agents/implementer.md` and `agents/reviewer.md`
last changed at `9fc74a3`), plus a throwaway skill added only to a scratch copy of the plugin ·
model: `claude-sonnet-5` (the CLI default in the headless runs; every agent on `inherit`, so
both subagents ran on it too) · Claude Code `2.1.270` · 2026-09-18

## What was tested

Two platform facts the 0.5 design depends on, from `site/notes/overhaul-0.5-09-evals-and-fixture.md`:

- **A.** A main-conversation skill (as `run-package` and `set-constraints` will be) can spawn a
  plugin agent with the Agent tool, and the `subagent_type` string that resolves is
  `dev-team:<agent>`, not the bare `<agent>`.
- **B.** `${CLAUDE_PLUGIN_ROOT}` is substituted with an absolute path in a plugin skill's body,
  and in a plugin agent's body — `agents/implementer.md` Procedure step 1 reads the lint block
  from `${CLAUDE_PLUGIN_ROOT}/pyproject-lint-config.toml`.

## Method

Real runs, headless, no network beyond the model API.

- The plugin was copied to a scratchpad (`…/evalAB/plug/dev-team`) and a throwaway skill
  `skills/zz-eval-platform/SKILL.md` (`disable-model-invocation: true`) was added to the copy
  only, so the probe is a genuine dev-team plugin skill loaded from a path unrelated to the
  project directory. The repo itself was not touched.
- Scratch project: `…/evalAB/proj`, a fresh `git init` with one commit.
- Run 1: `claude -p "/dev-team:zz-eval-platform" --plugin-dir <copy> --output-format stream-json
  --verbose --permission-mode bypassPermissions`. The skill told the model to (1) quote verbatim a
  line `MARKER-SKILL-BODY: ${CLAUDE_PLUGIN_ROOT}/pyproject-lint-config.toml` without resolving
  anything, (2) spawn `dev-team:reviewer` with "reply with the single word ok", falling back to
  `reviewer` only on an error, (3) spawn `dev-team:implementer` told to use no tools and quote,
  character for character, the lint-config path in its own Procedure step 1.
- Run 2 (the bare form, which run 1 never needed to try): a plain prompt telling the main
  conversation to call the Agent tool once with `subagent_type: "reviewer"` and no retry.
- Evidence was read from the stream-json transcript, not the model's summary: the `init`
  event's agent list, every `tool_use` / `tool_result`, and the order they happened in.
- Cost: run 1 $0.38 (2 subagents, 13 s); run 2 a few cents.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| A1 — plugin agents registered | `dev-team:*` names in the agent list | `init` lists `dev-team:architect … dev-team:reviewer` (7), no bare names | ✅ |
| A2 — skill spawns `dev-team:reviewer` | succeeds | Agent call with `subagent_type: "dev-team:reviewer"` returned `ok`; `subagent_stats.by_type` = `{dev-team:reviewer: 1, dev-team:implementer: 1}`, 0 failed | ✅ |
| A3 — bare `reviewer` | tells us whether both forms work | **errors**: `Agent type 'reviewer' not found. Available agents: claude, claude-code-guide, dev-team:architect, …, dev-team:reviewer, Explore, general-purpose, Plan, statusline-setup` | ✅ (only the prefixed form resolves) |
| B1 — substitution in a skill body | absolute path | quoted line read `MARKER-SKILL-BODY: /private/tmp/…/evalAB/plug/dev-team/pyproject-lint-config.toml` — the copy's path, not the project's; no tool call preceded the quote | ✅ |
| B2 — substitution in an agent body | absolute path | implementer replied `PATH: /private/tmp/…/evalAB/plug/dev-team/pyproject-lint-config.toml`; the subagent made no tool calls | ✅ |

## Verdict

**Both claims hold.** The resolved `subagent_type` form is **`dev-team:<agent>`**; the bare
name is rejected outright, so every Agent call the 0.5 skills make (`run-package` above all)
must use the prefixed form. `${CLAUDE_PLUGIN_ROOT}` is substituted in a plugin skill body and
in a plugin agent body alike, so implementer step 1's lint-config path and any
`${CLAUDE_PLUGIN_ROOT}/skills/…/references/…` path in the new skills can be relied on.

Limits: B is inferred from what the model quoted when told not to resolve anything; the raw
injected skill text and agent system prompt are not in the stream-json. The quoted paths name
the scratch copy of the plugin, which was reachable from no tool call and differs from the
working directory, so the model could not have produced them except from substituted text.
One model (`claude-sonnet-5`), one run per case: these are platform-resolution facts, not
behavioral ones, so one run each was judged enough.
