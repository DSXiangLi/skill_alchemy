---
name: pre_commit_doc_rescan
description: "After code modifications are complete and before executing git commit/push, enforce four categories of documentation sync checks: howto docs (REST API endpoints/SSE message types), progress docs (iteration records), design docs (module design-to-code consistency), and test_acceptance docs (acceptance doc existence). When the user says 'commit', 'push', 'push to remote', 'code changes done', 'ready to commit', or when AI is about to execute git commit/push, or when AI finishes code modifications and is about to report completion, this skill must be triggered. Even if the user doesn't explicitly request a documentation check, AI must not execute commit or claim 'ready to commit' without performing a doc rescan. Documentation sync is part of the commit process, not optional follow-up work."
---

# Pre-Commit Documentation Rescan

## Overview

Code changes do not equal work completion. Every non-minor commit must undergo a documentation rescan to ensure four categories of documentation stay in sync with code. Documentation-code divergence is the most common source of project maintenance debt — changing an interface without updating docs means later developers integrate against stale docs, only to discover after hours of debugging that the interface has changed.

The rescan is not a formality: it's the last line of defense ensuring "this change" left a complete, accurate trace in the project's knowledge base.

## Scope of Applicability

**Must rescan**: New features, bug fixes, refactoring, interface changes — any change that modifies runtime behavior.

**May skip**: Pure documentation changes, comment additions, formatting, spelling corrections (no logic changes).

**Criterion**: If the changed code will be executed at runtime, a rescan is required. When in doubt, default to rescanning — the cost of extra checking is far less than the maintenance cost of documentation divergence.

## Two Usage Modes

### Mode 1: Pre-commit self-check (when user explicitly authorizes commit). AI must NOT determine it can commit on its own. Only proceed when the user explicitly says 'commit', 'push', '提交'. Words like 'check', 'review', '看看', '检查' are NOT authorization to commit.

When AI finishes code modifications and the user explicitly authorizes commit:

1. Catalog the files and modules involved in this change
2. Scan each item per the four-step checklist
3. When documentation gaps are found, supplement docs first, then execute commit
4. After full sync, output rescan report, then commit

### Mode 2: User-triggered

When the user says "check the docs", "are docs in sync", "do a rescan":

1. Confirm change scope via `git diff` or `git status`
2. Scan each item per the four-step checklist
3. Output rescan report, marking each item's sync status
4. Propose supplementation suggestions for missing/outdated docs

---

## Rescan Checklist

### Step 1: howto Documentation Sync

howto docs are the only entry point for external integrators to understand system interfaces. An undocumented endpoint is equivalent to nonexistent — integrators won't hunt for interfaces in source code.

**Operations**:

1. List all new/modified REST API endpoints in this change:
   ```bash
   grep -n '@app\.\(get\|post\|delete\|patch\|put\)(' src/sprout_harness/agent/server.py | head -50
   ```
2. For each new/modified endpoint, use grep to confirm howto docs have a record:
   ```bash
   grep -r "endpoint_path" docs/howto/
   ```
3. If howto docs are missing, check whether the following docs need supplementation:
   - `docs/howto/rest_api_reference.md` — REST API reference documentation
   - `docs/howto/gateway_integration_guide.md` — SSE integration guide
4. New/modified SSE message types (msg_type) also need checking:
   ```bash
   grep -r "msg_type.*xxx" docs/howto/gateway_integration_guide.md
   ```
5. **Read code before writing docs**: Each endpoint's documentation must first read the code to confirm actual parameters, response format, and behavior logic. Cannot write from memory.

**Output format**:

```markdown
## howto Documentation Sync

| Endpoint/msg_type | rest_api_reference | gateway_integration_guide | Status |
|-------------------|-------------------|--------------------------|--------|
| POST /disk/archive | ✅ §8.3 | N/A | Synced |
| DELETE /sessions/{sid} | ❌ | N/A | Needs supplement |
```

---

### Step 2: progress Documentation Existence

progress docs are the project iteration audit log. Looking back three months later at "why this was changed" relies on progress docs. Unrecorded changes equal lost decision context.

**Operations**:

1. Confirm whether this change has a corresponding progress doc:
   ```bash
   ls docs/progress/$(date +%m%d)_*.md
   ```
2. Confirm `docs/progress/README.md` has entries added in "Recent Updates" and "By Date Index":
   ```bash
   grep "$(date +%m%d)" docs/progress/README.md
   ```

**Criteria**:
- Non-minor commits (new features, bug fixes, refactoring, etc.) must have corresponding progress docs
- Minor changes (comments, formatting, etc.) don't need progress docs
- Progress doc naming convention: `MMDD_short_description.md`, e.g., `0828_session_archive_delete.md`

**Output format**:

```markdown
## progress Documentation

- progress doc: ✅ docs/progress/0828_session_archive_delete.md
- README index: ❌ Needs entry added in docs/progress/README.md
```

---

### Step 3: Design Documentation Sync

Design docs are a module's "specification sheet." When code diverges from design docs, either the code is wrong or the design is outdated — either way, correction is needed. Design doc–code inconsistency is the most misleading documentation debt, because later developers will trust the design doc's descriptions.

**Operations**:

1. List modules involved in this change and find corresponding design docs. The SproutHarness project has explicit module-to-design-doc mappings; see "Design Docs (design/) Details" in `AGENTS.md`.
2. Cross-check change points against design docs:
   - Do deleted functions/interfaces still have residual references?
   - Do new interfaces have corresponding descriptions?
   - Are function signatures, flow descriptions, and data structures consistent with code?
   - Are status annotations outdated (e.g., "In Design" when actually implemented)?
3. Specifically check for residual references to deleted function names in design docs:
   ```bash
   grep -rn "deleted_function_name" docs/design/
   ```

**Output format**:

```markdown
## Design Documentation Sync

| Design Doc | Check Item | Status |
|-----------|-----------|--------|
| workspace_archive_design.md | POST /disk/archive interface description | ❌ Missing |
| sse_output_schema.md | msg_type count | ❌ Outdated |
| clear_conversation_design.md | Status annotation | ❌ "In Design" should be "Implemented" |
```

---

### Step 4: test_acceptance Documentation Sync

Acceptance docs are functionality quality contracts. A new feature without acceptance docs means there are no regression check items — next time someone changes it, nobody knows what "correct behavior" is. Missing acceptance docs isn't a "documentation incomplete" problem; it's a "quality assurance has blind spots" problem.

**Operations**:

1. Confirm whether this change added new features or modules
2. If new features/modules were added, check for corresponding acceptance docs:
   ```bash
   ls docs/test_acceptance/README.md
   grep -r "feature_name" docs/test_acceptance/
   ```
3. Acceptance docs should include:
   - **P0 items**: Core functionality must-verify paths (failure causes production incidents)
   - **P1 items**: Important functionality regression paths (failure affects user experience)
4. If modifying existing functionality, check whether existing acceptance docs need updates (new paths/parameter combinations)

**Criteria**:
- New features/modules must have acceptance docs
- Modified existing features need acceptance doc update checks (new paths/parameter combinations)
- Pure bug fixes don't need new acceptance docs if existing ones already cover the path

**Output format**:

```markdown
## test_acceptance Documentation

- New features: ✅ Targeted archiving + conversation deletion
- Acceptance docs: ❌ No corresponding docs in docs/test_acceptance/
- Needs supplement: P0 items (archive+restore end-to-end, deletion cleanup verification), P1 items (archive label display, non-archived sessions unaffected)
```

---

### Step 5: Commit Authorization Gate

Before executing git commit/push, confirm the user has explicitly authorized this commit. The user saying "check" / "review" / "看看" does not equal "commit". If the user has said "don't commit" or "just check", you must completely stop the commit action. Only when the user explicitly says "commit" / "push" / "提交" does it count as authorization.

**Operations**:

1. Review the conversation context for explicit commit authorization from the user.
2. If the user said "check" / "review" / "看看" / "检查" but did not say "commit" / "push" / "提交", do NOT execute git commit/push.
3. If the user said "don't commit" or "just check", completely stop the commit action — do not proceed even if all documentation checks pass.


---

### Step 6: Commit File Completeness Check

Before committing, run `git diff --name-only` (unstaged) and `git diff --cached --name-only` (staged) and compare them to confirm all modified files — especially core files such as handlers, factories, configs, and routes — are included in the staging area. Missing core files will cause functionality loss after deployment.

**Operations**:

1. Run `git diff --name-only` to list all unstaged modified files.
2. Run `git diff --cached --name-only` to list all staged files.
3. Compare the two lists. Any modified file that is not staged (especially handlers, factories, configs, routes) may have been accidentally omitted.
4. If core files are missing from staging, stop and inform the user before committing.

---

## Rescan Report Output

After all checks complete, output the full rescan report. This report is the basis for the commit decision — only when the conclusion is "all docs synced" should git commit/push be executed.

```markdown
# Pre-Commit Documentation Rescan Report

## Change Overview
- Change type: New feature / Bug fix / Refactoring
- Changed files: [File list]

## howto Documentation Sync
- Missing endpoints: N / All synced
- Needs supplement: [Endpoint list]

## progress Documentation
- progress doc: ✅ Exists / ❌ Missing
- README index: ✅ Exists / ❌ Needs supplement

## Design Documentation Sync
- Outdated docs: N / All consistent
- Needs update: [Doc list + specific outdated content]

## test_acceptance Documentation
- Acceptance docs: ✅ Exist / ❌ Missing
- Needs supplement: [P0/P1 item list]

## Commit Authorization
- User authorization: ✅ User explicitly said 'commit'/'push'/'提交' / ❌ No explicit commit authorization
- Action: Proceed with commit / Stop — waiting for explicit user authorization

## Commit File Completeness
- Modified files (unstaged): [file list]
- Staged files: [file list]
- Missing from staging: [file list or "None"]
- Core files missing: [file list or "None"]

## Localization Completeness
- Localization involved: ✅ Yes / ❌ No
- Files checked: [file list]
- English residue found: [file:line list or "None"]

## Test Artifacts Cleanup
- Test artifacts found: [file list or "None"]
- Artifacts gitignored: ✅ Yes / ❌ No — needs .gitignore update
- Action taken: [description or "None needed"]

## Rescan Conclusion
✅ All documentation synced — documentation is ready, but commit still requires explicit user authorization
❌ Documentation gaps exist, must supplement before committing: [Gap list]
```

---

## Execution Principles

1. **Read code before writing docs**: Each endpoint/function's documentation must first read the code to confirm actual parameters, response format, and behavior logic. Cannot write docs from memory. Memory makes mistakes; code is the source of truth.

2. **Verify one by one**: After supplementing docs, use grep to confirm each new item is actually in the doc. Writing without checking equals not writing — files may fail to save, paths may be wrong, content may be swallowed by the editor.

3. **Documentation sync is part of the commit**: Not optional follow-up work. Gaps found must be supplemented before committing; cannot "commit first and fill in later" — the probability of "filling in later" approaches zero.

4. **Avoid formalism**: If a check item genuinely doesn't apply (e.g., pure backend change doesn't involve SSE docs), mark "N/A" — no need to force-fill.

5. **Commit authorization required**: This skill runs before commit, but it does not authorize commit. Only the user's explicit instruction authorizes commit. If the user has not explicitly said 'commit'/'push'/'提交', do not execute git commit/push even if all documentation checks pass.
