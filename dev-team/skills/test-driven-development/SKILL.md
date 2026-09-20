---
name: test-driven-development
description: Drives development with tests using the red-green-refactor loop. Preloaded into the tester and the implementer. Invoke when writing any test, fixing any bug, or when a test cannot be made to pass.
license: agent-skills by Addy Osmani, MIT. Complete terms in LICENSE.
user-invocable: false
---

# Test-Driven Development

## Overview

Write a failing test before writing the code that makes it pass. For bug fixes, reproduce the
bug with a test before attempting a fix. Tests are proof — "seems right" is not done. A
codebase with good tests is an AI agent's superpower; a codebase without tests is a liability.

The stack is fixed: `pytest`, run through `uv`. Run the focused test during the loop and the
full suite before you finish:

```bash
uv run pytest tests/unit/ingest/test_parsers.py::test_parses_empty_page -x   # focused
uv run pytest                                                                 # full suite
```

## The TDD Cycle

```
    RED                GREEN              REFACTOR
 Write a test    Write minimal code    Clean up the
 that fails  ──→  to make it pass  ──→  implementation  ──→  (repeat)
      │                  │                    │
      ▼                  ▼                    ▼
   Test FAILS        Test PASSES         Tests still PASS
```

### Step 1: RED — Write a Failing Test

Write the test first. It must fail. A test that passes immediately proves nothing.

```python
# RED: this test fails because create_task doesn't exist yet
from datetime import datetime

from tasks.service import create_task


def test_create_task_sets_title_and_default_status():
    task = create_task(title="Buy groceries")

    assert task.id is not None
    assert task.title == "Buy groceries"
    assert task.status == "pending"
    assert isinstance(task.created_at, datetime)
```

### Step 2: GREEN — Make It Pass

Write the minimum code to make the test pass. Don't over-engineer:

```python
# GREEN: minimal implementation
def create_task(title: str) -> Task:
    """Creates a pending task with a fresh id."""
    task = Task(id=new_id(), title=title, status="pending", created_at=datetime.now(UTC))
    _store.insert(task)
    return task
```

### Step 3: REFACTOR — Clean Up

With tests green, improve the code without changing behavior:

- Extract shared logic
- Improve naming
- Remove duplication
- Optimize if necessary

Run tests after every refactor step to confirm nothing broke.

## The Prove-It Pattern (Bug Fixes)

When a bug is reported, **do not start by trying to fix it.** Start by writing a test that
reproduces it.

```
Bug report arrives
       │
       ▼
  Write a test that demonstrates the bug
       │
       ▼
  Test FAILS (confirming the bug exists)
       │
       ▼
  Implement the fix
       │
       ▼
  Test PASSES (proving the fix works)
       │
       ▼
  Run full test suite (no regressions)
```

**Example:**

```python
# Bug: "completing a task doesn't set completed_at"

# Step 1: write the reproduction test (it should FAIL)
def test_complete_task_sets_completed_at():
    task = create_task(title="Test")

    completed = complete_task(task.id)

    assert completed.status == "completed"
    assert isinstance(completed.completed_at, datetime)  # fails → bug confirmed


# Step 2: fix the bug
def complete_task(task_id: str) -> Task:
    """Marks a task completed and records when."""
    return _store.update(
        task_id,
        status="completed",
        completed_at=datetime.now(UTC),  # this was missing
    )

# Step 3: the test passes → bug fixed, regression guarded
```

## The Test Pyramid

Invest testing effort according to the pyramid — most tests should be small and fast, with
progressively fewer tests at higher levels:

```
          ╱╲
         ╱  ╲         End-to-end (~5%)
        ╱    ╲        A whole pipeline, run through its CLI command
       ╱──────╲
      ╱        ╲      Integration (~15%)
     ╱          ╲     Sections together, a package's public surface, a real file or DB
    ╱────────────╲
   ╱              ╲   Unit (~80%)
  ╱                ╲  Pure logic, isolated, milliseconds each
 ╱──────────────────╲
```

**The Beyonce Rule:** If you liked it, you should have put a test on it. Infrastructure
changes, refactoring, and migrations are not responsible for catching your bugs — your tests
are. If a change breaks your code and you didn't have a test for it, that's on you.

### Test Sizes (Resource Model)

Beyond the pyramid levels, classify tests by what resources they consume:

| Size | Constraints | Speed | Example |
|------|------------|-------|---------|
| **Small** | One process; no network, no filesystem outside `tmp_path`, no subprocess, no database server | Milliseconds | Pure functions, parsers fed a fixture, data transforms |
| **Medium** | `tmp_path` files, a local SQLite or DuckDB file, a subprocess running the package's own CLI; still no network | Seconds | A section against a real on-disk store; a CLI command via `subprocess.run` |
| **Large** | Network and external services allowed | Minutes | A live call to a probed API; a full pipeline over real data |

Small tests should make up the vast majority of your suite. They're fast, reliable, and easy
to debug when they fail. Mark medium and large tests (`@pytest.mark.integration`,
`@pytest.mark.live`) so the fast suite can run without them.

### Decision Guide

```
Is it pure logic with no side effects?
  → Unit test (small)

Does it cross a boundary (a file, a database, another section, a subprocess)?
  → Integration test (medium)

Is it a pipeline a person runs end to end?
  → End-to-end test (large) — limit these to the pipelines surface.md names
```

## Writing Good Tests

### Test State, Not Interactions

Assert on the *outcome* of an operation, not on which methods were called internally. Tests
that verify call sequences break when you refactor, even if the behavior is unchanged.

```python
# Good: tests what the function does (state-based)
def test_list_tasks_newest_first():
    tasks = list_tasks(sort_by="created_at", descending=True)

    assert tasks[0].created_at > tasks[1].created_at


# Bad: tests how the function works internally (interaction-based)
def test_list_tasks_queries_with_order_by(monkeypatch):
    calls = []
    monkeypatch.setattr(db, "query", lambda sql: calls.append(sql) or [])

    list_tasks(sort_by="created_at", descending=True)

    assert "ORDER BY created_at DESC" in calls[0]
```

### DAMP Over DRY in Tests

In production code, DRY (Don't Repeat Yourself) is usually right. In tests, **DAMP
(Descriptive And Meaningful Phrases)** is better. A test should read like a specification —
each test should tell a complete story without requiring the reader to trace through shared
helpers.

```python
# DAMP: each test is self-contained and readable
def test_create_task_rejects_empty_title():
    with pytest.raises(ValueError, match="title is required"):
        create_task(title="", assignee="user-1")


def test_create_task_trims_whitespace_from_title():
    task = create_task(title="  Buy groceries  ", assignee="user-1")

    assert task.title == "Buy groceries"

# Over-DRY: a shared fixture that builds the input for every test hides what each one checks.
# Don't do that just to avoid repeating a two-field call.
```

Duplication in tests is acceptable when it makes each test independently understandable. A
`@pytest.fixture` earns its place when the setup is expensive or has teardown (a database, a
temporary directory tree), not when it saves one line.

### Prefer Real Implementations Over Mocks

Use the simplest test double that gets the job done. The more your tests use real code, the
more confidence they provide.

```
Preference order (most to least preferred):
1. Real implementation  → Highest confidence, catches real bugs
2. Fake                 → In-memory version of a dependency (e.g., a dict-backed store)
3. Stub                 → Returns canned data, no behavior (monkeypatch a function's return)
4. Mock (interaction)   → Verifies calls — use sparingly
```

**Use mocks only when:** the real implementation is too slow, non-deterministic, or has side
effects you can't control (external APIs, sending email). Over-mocking creates tests that pass
while production breaks. For files, use a real file under `tmp_path`; for environment
variables and module attributes, `monkeypatch`.

### Use the Arrange-Act-Assert Pattern

```python
def test_check_overdue_flags_task_past_deadline():
    # Arrange: set up the scenario
    task = create_task(title="Test", deadline=date(2025, 1, 1))

    # Act: perform the action being tested
    result = check_overdue(task, today=date(2025, 1, 2))

    # Assert: verify the outcome
    assert result.is_overdue
```

### One Assertion Per Concept

```python
# Good: each test verifies one behavior
def test_create_task_rejects_empty_title(): ...
def test_create_task_trims_whitespace_from_title(): ...
def test_create_task_rejects_title_over_255_chars(): ...


# Bad: everything in one test
def test_title_validation():
    with pytest.raises(ValueError):
        create_task(title="")
    assert create_task(title="  hello  ").title == "hello"
    with pytest.raises(ValueError):
        create_task(title="a" * 256)
```

When one behavior has many input cases, `@pytest.mark.parametrize` keeps one concept per test
function while each case still reports on its own.

### Name Tests Descriptively

```python
# Good: reads like a specification
def test_complete_task_sets_status_and_records_timestamp(): ...
def test_complete_task_raises_not_found_for_unknown_id(): ...
def test_complete_task_is_idempotent_on_completed_task(): ...


# Bad: vague names
def test_works(): ...
def test_errors(): ...
def test_3(): ...
```

## Test Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Testing implementation details | Tests break when refactoring even if behavior is unchanged | Test inputs and outputs, not internal structure |
| Flaky tests (timing, order-dependent) | Erode trust in the test suite | Use deterministic assertions; freeze time and seed randomness; isolate test state |
| Testing framework code | Wastes time testing third-party behavior | Only test YOUR code — not pydantic's validation, not pandas' groupby |
| Snapshot abuse | Large snapshots nobody reviews, break on any change | Assert on the fields that matter; review every snapshot change |
| No test isolation | Tests pass individually but fail together | Each test sets up its own state; `tmp_path` and `monkeypatch` undo themselves |
| Mocking everything | Tests pass but production breaks | Prefer real implementations > fakes > stubs > mocks. Mock only at boundaries where real deps are slow or non-deterministic |

## Project convention

> Project convention. Not from the upstream skill: these are this plugin's rules about where
> tests live and who writes which ones.

- **Tests mirror source.** `src/<pkg>/<section>/<module>.py` →
  `tests/unit/<section>/test_<module>.py`. The rule and its details are `project-structure`
  §1; it is restated here by reference only.
- **Intent tests live in `tests/intent/<section>/`.** The `tester` agent writes them from the
  section's design, never from the code. The implementer runs them and never edits them: a
  failing intent test is fixed in the code, or reported as a disagreement with the design —
  never by changing the test.
- **An external `api` source's fixture is its probe's `<source>.sample.json`**, copied into
  the tests' fixtures, never a hand-written dict. A hand-written fixture encodes what you
  expect the API to return; the sample is what it did return.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll write tests after the code works" | You won't. And tests written after the fact test implementation, not behavior. |
| "This is too simple to test" | Simple code gets complicated. The test documents the expected behavior. |
| "Tests slow me down" | Tests slow you down now. They speed you up every time you change the code later. |
| "I tested it manually" | Manual testing doesn't persist. Tomorrow's change might break it with no way to know. |
| "The code is self-explanatory" | Tests ARE the specification. They document what the code should do, not what it does. |
| "It's just a prototype" | Prototypes become production code. Tests from day one prevent the "test debt" crisis. |
| "Let me run the tests again just to be extra sure" | After a clean test run, repeating the same command adds nothing unless the code has changed since. Run again after subsequent edits, not as reassurance. |

## Red Flags

- Writing code without any corresponding tests
- Running a bare `pytest` or `python -m pytest` instead of `uv run pytest` — it may pick up a
  different interpreter and a different installed copy of the package
- Tests that pass on the first run (they may not be testing what you think)
- "All tests pass" but no tests were actually run (check the collected count)
- Bug fixes without reproduction tests
- Tests that test framework behavior instead of application behavior
- Test names that don't describe the expected behavior
- `@pytest.mark.skip` or `xfail` added to make the suite pass
- Running the same test command twice in a row without any intervening code change

## Verification

After completing any implementation:

- [ ] Every new behavior has a corresponding test
- [ ] The full suite passes under `uv run pytest`
- [ ] Bug fixes include a reproduction test that failed before the fix
- [ ] Test names describe the behavior being verified
- [ ] No tests were skipped, `xfail`ed, or deleted
- [ ] Coverage hasn't decreased (if tracked)

**Note:** Run each test command after a change that could affect the result. After a clean
run, don't repeat the same command unless the code has changed since — re-running on
unchanged code adds no confidence.

## Provenance

Upstream `addyosmani/agent-skills` `skills/test-driven-development/SKILL.md` at `c004a74`.
Dropped: When to Use (the description carries the triggers), Discover the Stack First,
Browser Testing with DevTools, When to Use Subagents for Testing, See Also. Rewritten: every
example to `pytest`; Test Sizes to Python resources; the stack-command red flag. Added:
§Project convention.
