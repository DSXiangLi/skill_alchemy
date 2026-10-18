---
name: pre_completion_gate
description: >-
  Before AI reports "done", "complete", "fixed", or "ready" to the user, it must pass this
  gate. Checks: did you start the real service (not just py_compile/pytest)? Did you send real
  HTTP/SSE requests? Did you check actual output (not just "no errors")? Did you test adjacent
  modules affected by this change? Did you verify visual output if UI is involved? Is the test
  case complex enough to expose real problems (not just 4-page smoke deck)? Did you restart
  the service after code changes? This skill must trigger whenever AI is about to report any
  completion status — even if the user didn't ask for verification. AI must not say "done",
  "complete", "fixed", "已修复", "已完成", "可以测试了" without passing this gate. Trigger words:
  "done", "complete", "fixed", "ready", "已修复", "已完成", "完成", "可以测试了", "验收通过",
  or when AI is about to summarize work results to the user.
---

# Pre-Completion Gate

## Why This Skill Exists

This is the single most frequent error across all historical sessions: AI claims "done" after syntax checks or unit tests pass, but the user immediately finds real problems — visual overlap, service won't start, features don't work, UI misaligned. In 88+ sessions, the user had to explicitly demand "start the service and test for real" every single time.

The gap: AI's verification standard is "code runs without errors", but the user's standard is "the feature works in real usage". These are not the same thing.

## Scope

**Must gate**: Any code change that modifies runtime behavior (bug fix, feature, refactor, config change).

**May skip**: Pure documentation, comments, formatting (no logic changes).

## Gate Checklist

Before saying "done" or "complete", AI must answer ALL of the following. If any answer is "no", it is not done.

### Check 1: Real Service Verification

**Did you start the actual service (not just run unit tests)?**

```bash
# Confirm the service is running with the new code
curl -s http://localhost:<port>/health
# Or check the process
ps aux | grep <service_name>
```

- `py_compile` passing ≠ code works
- `pytest` passing ≠ feature works
- "No import errors" ≠ service starts

**If you only ran pytest without starting the service, the answer is NO.** Start the service, send a real request, check the response.

### Check 2: Real Request Verification

**Did you send a real HTTP/SSE request and check the actual response?**

```bash
# Send a real request, not a mock
curl -X POST http://localhost:<port>/api/endpoint -d '{"real":"data"}'
# Check the actual response, not just status code
```

- Status 200 ≠ response is correct
- "No exception" ≠ output is right
- Must verify the actual response body, not just "it didn't crash"

### Check 3: Visual Output Verification (if UI is involved)

**If the change affects UI/visual output, did you check the actual rendered result?**

- Automated QA passing ≠ visual quality acceptable
- "HTML renders" ≠ layout is correct
- Must verify: no text overlap, no misaligned containers, no blank areas, content is linked to actual data

If the user would see the result, you must see it too — through a screenshot, HTML preview, or PPTX render.

### Check 4: Adjacent Module Regression

**Did you test modules that depend on the changed code?**

```bash
# Find all callers of changed functions
grep -rn "changed_function_name" --include="*.py" src/
```

- Fixed module A ≠ module B (which calls A) still works
- Changed config ≠ all agents using that config still work
- Must test at least one downstream consumer of the changed code

### Check 5: Service Restart After Code Changes

**If you modified server-side code, did you restart the service?**

- Changed code ≠ service is running new code
- "Saved the file" ≠ service picked up the change
- Must restart the service and verify it starts successfully with the new code

### Check 6: Test Case Complexity

**Is your test case complex enough to expose real problems?**

- 4-page simple deck ≠ real validation (too simple to trigger layout issues)
- Single happy path ≠ coverage
- Must test with realistic data density, edge cases, and at least one failure scenario

## Gate Report Output

```markdown
# Pre-Completion Gate Report

## Change Summary
- Change type: [bug fix / feature / refactor / config]
- Changed files: [list]

## Gate Results

| Check | Question | Answer | Evidence |
|-------|----------|--------|----------|
| 1 | Service started with new code? | ✅/❌ | [curl output / process check] |
| 2 | Real request sent and verified? | ✅/❌ | [request + response] |
| 3 | Visual output checked? | ✅/❌/N/A | [screenshot / "N/A - no UI"] |
| 4 | Adjacent modules tested? | ✅/❌ | [grep results + test output] |
| 5 | Service restarted after changes? | ✅/❌/N/A | [restart log] |
| 6 | Test case complex enough? | ✅/❌ | [test description] |

## Gate Decision

✅ ALL CHECKS PASSED — Ready to report completion
❌ CHECKS FAILED — Cannot report completion. Missing: [list]
```

## Execution Principles

1. **This gate is mandatory**: Even if the user says "just tell me when you're done", you must pass this gate before saying "done". "Done" means verified, not just coded.

2. **Real > simulated**: Always prefer real service, real requests, real data over mocks and unit tests. The user's standard is "does it work when I use it", not "does the test pass".

3. **Adjacent modules matter**: Your fix for module A might break module B that calls A. Always grep for callers and test at least one.

4. **Complexity exposes problems**: Simple test cases give false confidence. Use realistic data density and edge cases.

5. **Restart is not optional**: Modified server code requires service restart. "I changed the file" is not "the service is running the new code".
