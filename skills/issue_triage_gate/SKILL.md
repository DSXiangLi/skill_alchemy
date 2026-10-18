---
name: issue_triage_gate
description: >-
  When a bug or problem is reported, before AI starts fixing, it must pass this gate.
  AI must first diagnose root cause, analyze impact scope, and classify the problem —
  NOT jump straight to patching. Checks: did you read the error log fully? Did you trace
  the root cause (not just the symptom)? Did you analyze impact scope (which modules are
  affected)? Did you check if architecture can prevent this class of problem? Did you
  search for similar issues in other modules? This skill must trigger when: a user reports
  a bug/error/issue, AI encounters an error during development, user says "报错了"/"有问题"/
  "不工作"/"bug"/"error"/"crash"/"doesn't work", or when AI is about to start fixing a
  reported problem. AI must not start writing fix code without passing this gate.
  Trigger words: "报错", "bug", "error", "问题", "不工作", "broken", "crash", "fails",
  "doesn't work", "不对", "还是有问题", or when AI encounters an unexpected error.
---

# Issue Triage Gate

## Why This Skill Exists

Across 23+ sessions, the user repeatedly had to say "先不要修复，先定位问题" (don't fix yet, locate the problem first) and "你已经修复了很多次这个问题，请先排查根本原因" (you've fixed this many times, investigate the root cause first). AI's default behavior upon seeing an error is to immediately start patching — which leads to:

1. **Patch without understanding**: Fixing the symptom without knowing the root cause, so the bug returns in a different form
2. **Local fixing without global view**: Fixing one instance of a problem while the same root cause exists in 5 other modules
3. **Band-aid over surgery**: Adding try-catch/workaround instead of eliminating the problem class

The user had to say "先定位" in 23 sessions. That's 23 times AI jumped to fixing without understanding.

## Scope

**Must gate**: When any bug, error, or unexpected behavior is reported or encountered.

**May skip**: When the user explicitly says "just fix X" for a trivial, well-understood issue (e.g., typo fix).

## Gate Checklist

Before writing any fix code, complete ALL of the following:

### Check 1: Symptom Documentation

**What exactly is the problem? Document the symptom precisely.**

- What error message was shown? (exact text, not paraphrased)
- When does it happen? (what action triggers it)
- What was expected vs what actually happened?
- Is it reproducible? If so, what are the steps?

```bash
# Find the actual error in logs
grep -i "error\|exception\|traceback" <log_file> | tail -20
```

**If you can't state the symptom in one sentence, you don't understand the problem yet.**

### Check 2: Root Cause Tracing

**What is the actual root cause? Not "where does the error appear" but "why does it happen"?**

Trace the error backward:
- Error appears in file X, line Y → why?
- Because variable Z is null → why is Z null?
- Because function A didn't populate it → why didn't A populate it?
- Because config B was loaded incorrectly → why?

Keep asking "why" until you reach a cause that, if fixed, would prevent ALL instances of this problem — not just this specific occurrence.

**This is NOT root cause**: "The function threw an error because the input was null."
**This IS root cause**: "The function doesn't validate input because the schema contract was never enforced at the API boundary."

### Check 3: Impact Scope Analysis

**What else is affected by this problem (and will be affected by the fix)?**

```bash
# Find all callers of the broken function
grep -rn "broken_function" --include="*.py" src/
# Find all modules using the same pattern
grep -rn "similar_pattern" --include="*.py" src/
```

- Does the same root cause exist in other modules? (lateral migration check)
- Will the fix break any callers? (downstream impact)
- Does the fix require interface changes? (upstream impact)

### Check 4: Architecture Prevention Check

**Can the architecture prevent this entire class of problem, instead of fixing this one instance?**

- Is this a one-off bug (specific to this code) or a class of bugs (systemic pattern)?
- If systemic: fixing one instance means the bug will appear elsewhere. Fix the architecture.
- Can a validation layer, type system, or schema contract prevent this at the source?
- Is this a "dual source of truth" problem? (two systems that can diverge)

Examples:
- Bug: text overlap in PPTX → Architecture: measurement-first layout solver (not post-hoc QA)
- Bug: environment config wrong → Architecture: single env detection function (not 6 scattered if/else)
- Bug: message duplicated in streaming → Architecture: formalized merge semantics (not per-module patches)

### Check 5: Similar Issues Search

**Have you checked if this problem exists elsewhere in the codebase?**

```bash
# Search for similar patterns that might have the same bug
grep -rn "pattern_that_caused_the_bug" --include="*.py" src/
```

- If the bug is in module A, check if module B (which uses the same pattern) has the same bug
- If the bug is environment-related, check all environment-dependent code
- If the bug is in a streaming merge, check all streaming paths

**Finding the bug in one place and not checking others = guaranteed recurrence.**

## Triage Report Output

Before starting to fix, output this report:

```markdown
# Issue Triage Report

## Symptom
- Error: [exact error message]
- Trigger: [what action causes it]
- Expected: [what should happen]
- Actual: [what actually happens]

## Root Cause
- Surface cause: [where the error appears]
- Root cause: [why it actually happens — the "why" chain]
- Root cause type: [coding bug / design flaw / config error / systemic pattern]

## Impact Scope
- Directly affected: [files/modules]
- Lateral migration risk: [other modules with same pattern — list them]
- Downstream impact of fix: [what the fix might break]

## Architecture Prevention
- Is this systemic? [yes/no]
- Can architecture prevent this class? [yes — how / no — why not]
- Recommended approach: [root-cause fix / architecture change / targeted fix]

## Similar Issues Found
- [module B]: [same pattern, same risk — needs check]
- [module C]: [checked, no issue]

## Triage Decision
✅ Root cause identified, scope understood — ready to fix
❌ Need more investigation: [what's still unclear]
⚠️ This is systemic — recommend [architecture change] before fixing individual instances
```

## Execution Principles

1. **Diagnose before fix**: The instinct to "make the error go away" is wrong. The error message is your best clue — read it, understand it, trace it to the source. A fast patch that doesn't address root cause means the bug comes back (seen in 4+ recurrence cases across sessions).

2. **Two failures = change direction**: If you've tried to fix this same issue twice and it came back, stop patching. The root cause is deeper than your current fix addresses. Re-run this gate from scratch.

3. **Lateral check is mandatory**: A bug in module A that's caused by pattern X will also exist in module B that uses pattern X. Always grep for the pattern and check all instances. This is the difference between "fixing a bug" and "eliminating a bug class".

4. **Architecture > patch**: If the architecture can prevent an entire class of bugs, fix the architecture. Post-hoc QA and try-catch are band-aids, not solutions. The user explicitly said "先思考架构能否完全规避" (think about whether architecture can completely avoid this).

5. **Systemic problems need systemic solutions**: If the same type of bug appears in multiple sessions/modules, it's not a coding error — it's a design pattern problem. Document it as a systemic issue and propose an architecture-level fix.
