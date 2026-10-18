---
name: code_fix_acceptance
description: "When AI completes a code fix, before reporting 'fix complete' to the user, it must perform systematic acceptance per this skill. Acceptance covers: impact scope and blast radius analysis, full-module regression testing, complete upstream/downstream call chain integration testing, eleven production-omission prevention principles (including forward compatibility, non-fix-path verification, external output spec compliance, producer-consumer end-to-end verification), streaming service-level verification, and documentation sync. This skill must be triggered when AI completes any non-trivial code fix (bug fix, feature change, refactoring, configuration adjustment). Even if the user doesn't request acceptance, AI must not claim 'fixed' or 'fix complete' without going through this skill's checks. Trigger words include 'fix complete', 'done', 'acceptance', 'fix done', or when AI is about to report fix results."
---

# Code Fix Acceptance

## Overview

Code changes do not equal fix completion. A complete fix acceptance must answer three questions: What scope was affected? Were all affected scopes verified? Did verification cover real call chains rather than just isolated unit test paths?

Every rule in this skill comes from real production omissions — not theoretical reasoning, but actual pitfalls encountered. Check each rule one by one during acceptance; no skipping.

## Scope of Applicability

- **Must accept**: Bug fixes, feature changes, refactoring, configuration adjustments, dependency upgrades — any change that modifies runtime behavior
- **May skip**: Pure documentation changes, comment additions, formatting (no logic changes)
- **Criterion**: If the changed code will be executed at runtime, acceptance is required

---

## Acceptance Workflow

### Step 1: Impact Scope and Blast Radius Analysis

After making changes, don't rush to test — first understand what was actually affected.

**Operations**:

1. **List all changed files**: `git diff --name-only` to get the complete list of files changed in this round
2. **Dependency tracking for each change point**:
   - Who calls this file/function? (trace upstream)
   - What does this file/function call? (trace downstream)
   - Were shared interfaces, common modules, or data models modified? If so, trace one to two levels outward along the dependency chain
3. **Assess blast radius**:
   - Is the change confined to the current module? (Low risk)
   - Does the change propagate to other modules through shared interfaces/common functions/data models? (Medium-high risk — these modules must be covered in subsequent steps)
   - Does the change modify identifier generation, path concatenation, or storage format? (Check forward compatibility — see Principle 9)
   - Does the change add/modify externally output message formats or API response structures? (Cross-check against interface specs — see Principle 10)
   - Does the change involve producer→consumer chains? (Verify consumer-side handling logic — see Principle 11)
4. **Output impact scope checklist**:

```markdown
## Impact Scope Analysis

| Changed File | Change Type | Upstream Callers | Downstream Dependencies | Blast Risk |
|--------------|-------------|-----------------|------------------------|------------|
| xxx.py | Function signature change | handler_a, handler_b | service_x | High |
| yyy.py | Logic fix | Direct call | None | Low |
```

If there are high blast-risk changes, the affected modules must be covered in subsequent steps.

### Step 2: Regression Acceptance and Test Supplementation

After confirming the impact scope, verify that all affected modules have undergone regression verification.

**Operations**:

1. **Test coverage check for changed files**:
   - For each changed file, run `grep -r "function_name" tests/` to confirm whether the changed function has test coverage
   - Files without test coverage — must be manually verified or have tests added; cannot be skipped
   - Cannot just run "seemingly related" test files. If N files were changed, all N files must each be checked for tests

2. **Regression test execution**:
   - Run full `pytest` (or `pytest tests/`), not just the related subset
   - Running only a subset is equivalent to assuming "other modules are unaffected" — and cross-module impact is exactly what's most easily missed
   - If the test suite is large, run full at least once to confirm no unexpected cascading failures

3. **Acceptance doc P0+P1 regression**:
   - If the project has acceptance docs (e.g., `docs/test_acceptance/` directory), run the P0+P1 items from the corresponding acceptance doc for affected modules and confirm no negative impact
   - Acceptance docs typically cover more complete business scenarios than unit tests, and are a supplement to — not a replacement for — full pytest
   - If changes involve new features, update acceptance docs accordingly

4. **Test supplementation**:
   - Add necessary test cases and acceptance criteria for modified functionality
   - If the fix was a bug, at least one test should reproduce the original bug (verifying the fix works)
   - If changes involve new parameters/new paths, add corresponding entry-point tests
   - Test cases must be complex enough to expose real problems — realistic data density, edge cases, at least one failure scenario. Simple happy-path tests (e.g., 4-page simple deck) give false confidence and cannot trigger real layout/logic issues.

5. **Output test coverage report**:

```markdown
## Test Coverage Report

| Changed File | Changed Function | Has Tests | Test File | Test Result |
|--------------|-----------------|-----------|-----------|-------------|
| xxx.py | func_a | ✅ | test_xxx.py | Pass |
| yyy.py | func_b | ❌ | None | Tests added |
```

### Step 2b: Visual Output Verification

When changes involve UI/visual output, automated QA passing ≠ visual quality acceptable. The actual rendered result must be verified through screenshots, HTML preview, or PPTX rendering.

**Operations**:

1. **Determine whether visual verification is needed**:
   - If changes involve templates, layouts, styles, rendering logic, or any user-facing visual output — visual verification is required
   - If changes are purely backend logic with no visual output — mark as N/A and skip

2. **Render and inspect**:
   - Generate the actual rendered output (screenshot, HTML preview, PPTX file, etc.)
   - Visually inspect the rendered result against the design intent

### Step 2c: Product Entry Point Integration

If this change added new features/templates/components, verify they are wired into the product's default entry point (default config, routing, menu) — not only available in an isolated environment.

**Operations**:

1. **Determine whether entry point check is needed**:
   - If changes added new templates, new routes, new menu items, new default configurations — entry point check is required
   - If changes are fixes to existing already-wired code — mark as N/A and skip

2. **Verify default entry point integration**:
   - Confirm the new feature/template/component is reachable from the product's default entry point (not just via a test URL or isolated config)
   - If the product has a default config/registry/factory, confirm the new item is registered there
   - If the product has routing/menu, confirm the new item appears in the default route/menu


### Step 3: Complete Upstream/Downstream Call Chain Coverage

This is the step most easily missed. Unit tests only cover the tested function's own behavior, but real calls are chained: upstream passes parameters → this function handles them → downstream is called. Fixing the middle link may produce different results when the upstream passes different parameters, or when the downstream is called with different parameters.

**Operations**:

1. **Identify key call chains**:
   - For each changed function, trace one level upstream and one level downstream to find the complete call chain
   - Key chains include: entry points (API handlers, message handlers), shared function calls, and data flow paths

2. **Call chain verification table**:

```markdown
## Call Chain Coverage

| Call Chain | Entry Point | Intermediate Functions | Endpoint | Test Coverage |
|------------|-------------|----------------------|----------|---------------|
| API → handler → service → db | POST /api/xxx | handler_xxx, service_xxx | db_xxx | ✅/❌ |
```

3. **Integration test execution**:
   - Construct targeted requests for each key call chain, triggering the modified code path
   - Verify behavior through streaming output (SSE messages) or actual functional effects
   - If behavior doesn't match expectations, first recheck whether build/load steps were missed — don't directly debug code

---

## Eleven Production-Omission Prevention Principles

These eleven principles are summarized from real production omissions. Check each one during acceptance.

### Principle 1: Grep deleted variables

**Scenario**: Deleted a variable definition but missed references elsewhere.

**Check method**: For each deleted variable/function, run `grep -rn "deleted_name" src/` to confirm no remaining references.

### Principle 2: Test coverage per changed file

**Scenario**: Changed N files but only ran tests "seemingly related" — files without coverage were never verified.

**Check method**: For each changed file, `grep -r "function_name" tests/` confirms test coverage. Files without tests must be manually verified or have tests added.

### Principle 3: Service-level path coverage

**Scenario**: Unit tests passed but service wasn't restarted; verified old code running in the service.

**Check method**: See "Service-Level Verification" section below.

### Principle 4: Full test suite

**Scenario**: Ran only a subset, missing cascading failures in other modules.

**Check method**: Run full `pytest tests/` and confirm no unexpected failures.

### Principle 5: Read through complete logic

**Scenario**: Only checked the modified code segment, missing issues introduced by surrounding logic.

**Check method**: Read the complete function containing the change — including all branching and exception handling paths.

### Principle 6: Test configuration compliance

**Scenario**: Test configuration bypassed certain paths (e.g., disabled middleware, mocked dependencies), so real paths were never verified.

**Check method**: Confirm test configuration matches production configuration, especially middleware, authentication, and external service calls.

### Principle 7: Design intent full-path coverage

**Scenario**: Only verified the most common entry point, missing other paths designed in the functionality.

**Check method**: Cross-check the design doc to confirm all designed paths have been verified.

### Principle 8: Fix path + non-fix path

**Scenario**: Only verified the fixed path, breaking unmodified paths.

**Check method**: For modules involved in the fix, verify both the fixed path and the original functionality paths.

### Principle 9: Forward compatibility

**Scenario**: Modified identifier generation, path concatenation, or storage format, causing old data to be unlocatable.

**Check method**:
1. Confirm whether the change affects data identifiers, file paths, or storage keys
2. If affected, create or use old-format data and confirm the new code can read it
3. If incompatible, the fix plan must include a migration strategy

### Principle 10: External output spec compliance

**Scenario**: Added new SSE message types or API response fields without cross-checking against the interface spec.

**Check method**:
1. Confirm whether the change adds/modifies externally output message formats
2. If new messages/fields are added, cross-check against the interface spec (e.g., `docs/howto/gateway_integration_guide.md`)
3. Confirm the spec has been updated with descriptions of the new messages/fields

### Principle 11: Producer-consumer end-to-end

**Scenario**: Producer-side outputs data correctly but consumer-side lacks handling logic.

**Check method**:
1. If the change modifies producer output format, confirm the consumer has corresponding handling logic
2. Construct end-to-end test data and verify the consumer correctly processes the producer's output

---

## Service-Level Verification

Unit tests passing ≠ function correct. For changes involving the following scenarios, the service must be restarted for end-to-end verification:

**Must restart service for acceptance**:
- API endpoint changes (new, modified, deleted)
- Middleware or hook changes
- Configuration changes (environment variables, config files)
- Database schema or query changes
- External service call changes
- SSE message format changes
- Dependency version changes
- Visual output changes (UI rendering, template modifications, style changes)
- Default product entry point changes (new templates, routing changes)

**May accept via unit tests only (no service restart needed)**:
- Pure utility function fixes (no side effects, no I/O)
- Pure documentation changes
- Test code changes

If in doubt, default to restarting the service. The time cost of restarting is far less than the cost of fixing a production incident.

### Ensure changes take effect before acceptance

Restarting the service isn't simply "stop and start" — different tech stacks have different build/load mechanisms. If changes aren't compiled or loaded into the runtime, you're verifying old code and getting a "seems fine" false pass.

**Confirm changes take effect by tech stack**:

| Tech Stack | Requires Rebuild | Confirmation Method |
|-----------|-----------------|-------------------|
| Python (uvicorn/FastAPI) | No compilation needed, but confirm process started with new code | Check load time in startup logs after launch, or construct a request to trigger the new code path and verify behavior change |
| Node.js (npm) | Requires `npm run build` (if build step exists) | After build, confirm `dist/` or `build/` directory is updated, then start service |
| Go | Requires `go build` | Confirm generated binary timestamp is updated, then start |
| Frontend (React/Vue) | Requires `npm run build` | Confirm bundled output is updated; browser needs hard refresh (clear cache) |
| Docker | Requires `docker build` | Confirm image ID changed; old container stopped and replaced |

**Core principle**: Before starting the service, confirm that this round's code changes will actually be executed — built, compiled, loaded. If unsure, manually verify (e.g., add temporary logging in code, confirm requests trigger the new code).

### Must confirm old processes are fully killed before restarting

`ps aux | grep` to check all related processes (including both `uvicorn` and `server.py` startup methods), `kill -9` each one. Old processes holding ports can cause new process startup failures or requests hitting old processes — returning old behavior that "looks normal," which is extremely deceptive. This pitfall has caused multiple false passes of "changed code but verified old code."

```bash
# Check and kill old processes
ps aux | grep -E "uvicorn|server.py" | grep -v grep
kill -9 <PID>  # For each related process
```

### Verification method

After confirming changes have taken effect and service has been restarted:

1. Confirm startup logs have no errors
2. Construct targeted requests to trigger the modified code paths
3. Verify behavior matches expectations through streaming output (SSE messages) or actual functional effects
4. If changes involve multiple paths, construct requests to verify each path separately
5. If behavior doesn't match expectations, first recheck whether build/load steps were missed — don't directly debug code

---

## Documentation Sync Check

After all above acceptance passes, confirm whether documentation updates were completed for this fix:

1. **Patch log**: Was this fix's content, reason, and impact scope recorded in the patch log/changelog?
2. **Progress doc**: Was the progress doc updated with the fix status?
3. **Design doc**: If the fix affected module design (interface changes, data model changes, behavior changes), was the corresponding module's design doc updated?

If any of the above is incomplete, mark as TODO in the acceptance report; cannot default to completed.

---

## Acceptance Report Output

After all checks complete, output the acceptance report:

```markdown
# Fix Acceptance Report

## Fix Overview
- Problem: [One-line description]
- Fix approach: [One-line description]
- Changed files: [File list]

## Step 1: Impact Scope
- Blast risk: Low / Medium / High
- Impact scope checklist: [See table above]

## Step 2: Regression Tests
- Full test suite: ✅ Pass / ❌ N failures
- Acceptance doc P0+P1: ✅ Pass / ❌ N failures / N/A (no acceptance doc)
- Test coverage report: [See table above]
- Tests added: N items / No additions needed

## Step 3: Call Chain Coverage
- Key chains: [See table above]
- Integration tests: ✅ Covered / ❌ Missing

## Eleven Principles Cross-Check
1. Deleted variable grep: ✅ / N/A
2. Per-file test coverage: ✅ / ❌ [Uncovered files]
3. Service-level path coverage: ✅ / ❌ [Uncovered paths]
4. Full test suite: ✅ / ❌
5. Read through complete logic: ✅ / ❌
6. Test configuration compliance: ✅ / ⚠️ [Bypassed paths]
7. Design intent full-path: ✅ / ❌ [Uncovered entry points]
8. Fix path + non-fix path: ✅ / ❌ [Unverified non-fix paths]
9. Forward compatibility: ✅ / ❌ [Existing data incompatible]
10. External output spec compliance: ✅ / ❌ [New output not checked against interface spec]
11. Producer-consumer end-to-end: ✅ / ❌ [Consumer-side handling logic missing]

## Streaming Verification
- End-to-end acceptance required: ✅ Required / ⏭️ Not needed (pure utility function/docs)
- Build/compile confirmed: ✅ Built and effective / ❌ Not built
- Old processes killed: ✅ / ❌
- Service restarted: ✅ / ❌
- Streaming verification: ✅ Behavior matches expectations / ❌
- Visual output verified: ✅/❌/N/A
- Product entry point integration: ✅/❌/N/A

## Documentation Sync
- Patch log: ✅ / ❌ Pending
- Progress doc: ✅ / ❌ Pending
- Design doc: ✅ / ❌ Pending / N/A

## Core Objective Alignment
- Original request re-read: ✅ Confirmed fix directly addresses original problem
- Objective drift check: ✅ No drift / ❌ Drifted to: [What was addressed instead]
- Notes: [If the fix only partially addresses the original request, explain what remains]

## Commit File Completeness
- Staged files checked via `git diff --cached --name-only`: ✅ / ❌ (not checked)
- Core files present (handler/factory/config): ✅ All present / ❌ Missing: [List]
- Notes: [Any files that should have been staged but were missed]

## Acceptance Conclusion
✅ Acceptance passed, may report fix complete
❌ Acceptance not passed: [Failed items and reasons]
```

Only when the acceptance conclusion is "passed" may "fix complete" be reported to the user.
