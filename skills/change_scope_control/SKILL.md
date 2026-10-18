---
name: change_scope_control
description: >-
  Before AI starts coding, it must confirm the exact scope of changes with the user.
  Checks: did you list all files to be modified? Did you confirm each file is necessary
  (not "while I'm at it" optimization)? Did you grep for existing implementations before
  writing new ones? Did you check if existing capabilities already cover the requirement?
  Did you confirm the environment (local/test/prod) before touching config? This skill
  triggers when: AI is about to start coding after receiving a task, AI received a task
  with multiple requirements, user says "change X" (risk of AI changing X+Y+Z), or when
  AI detects it's about to modify files beyond the explicit request. Trigger words:
  "change", "fix", "update", "modify", "implement", "改", "修", "改一下", "实现", "更新",
  "优化", or when AI receives any coding task with 2+ requirements.
---

# Change Scope Control

## Why This Skill Exists

Across 23+ sessions, the user repeatedly said "change A" and AI changed A+B+C+D. The user's exact words: "你的修改过分了" (your changes are excessive), "只提交X相关的修改，撤回所有其他" (only commit X-related changes, revert everything else), "不对哈外层项目路径还是..." (no, the outer path should be...).

AI defaults to "while I'm at it, let me also optimize B" — but every extra change is a risk: it may break things the user didn't ask to change, it inflates the diff making review harder, and it makes rollback impossible.

## Scope

**Must gate**: Any task where AI is about to write/modify code.

**May skip**: Reading code to answer a question (no modification).

## Gate Checklist

Before writing any code, confirm ALL of the following:

### Check 1: Explicit File List

**Do you have a confirmed list of every file you will modify?**

Before touching any file:
```bash
# If the user said "change X", grep to find all files containing X
grep -rn "X" --include="*.py" --include="*.ts" --include="*.js" src/
```

- List every file you plan to modify
- For each file, state exactly what will change (function name, line range, what's added/removed)
- If you discover additional files need changes mid-work, STOP and inform the user before proceeding

**If you can't produce this list, you don't understand the scope yet.** Read more code first.

### Check 2: No "While I'm At It" Changes

**For each file in your list, is it truly necessary for the user's request?**

For each file, ask: "If I only do what the user explicitly asked, would this file need to change?"

- If YES → include it
- If "I think it would be better if..." → EXCLUDE it. The user asked for specific changes, not a refactoring session.
- If "This related function is also broken..." → Tell the user about it, don't fix it silently

### Check 3: Existing Implementation Check

**Did you grep for existing implementations of what you're about to write?**

```bash
# Before writing new code, check if similar already exists
grep -rn "similar_function_name\|similar_pattern" --include="*.py" src/
```

- If a similar implementation exists, USE IT (import/call it), don't write a new one
- If a config pattern exists in the project, FOLLOW IT, don't invent a new one
- If a utility function already does part of the work, EXTEND it, don't duplicate

### Check 4: Environment Confirmation

**Do you know which environment this code will run in?**

- Is this for local dev, test, or production?
- Are the config files, URLs, and proxy settings correct for that environment?
- Are you about to add local-only logic (like proxy bypass) to code that runs in production?

If you're not sure which environment, ASK THE USER before writing any config-dependent code.

### Check 5: Backward Compatibility

**Will this change break existing data/sessions/calls?**

- If renaming a field: will old data with the old field name still work?
- If changing a path: will existing references to the old path break?
- If modifying an API response: will consumers expecting the old format break?

If YES to any: you must either maintain backward compatibility or explicitly inform the user that existing data/calls will break.

## Scope Report Output

Before starting to code, output this report:

```markdown
# Change Scope Control Report

## Task
User request: [exact quote]

## Files to Modify

| File | Change | Why Necessary | "While I'm at it"? |
|------|--------|---------------|---------------------|
| src/a.py | Fix function X | User asked for this | No |
| src/b.py | Update call to X | Required because a.py changed | No |
| src/c.py | Refactor Z | "Would be better if..." | YES — EXCLUDED |

## Existing Implementation Check
- Searched for: [keywords]
- Found: [existing function/pattern] in [file] — will reuse
- Not found: no existing implementation — will write new

## Environment
- Target: [local/test/prod]
- Config file: [which config]
- Proxy strategy: [if applicable]

## Backward Compatibility
- Field/path changes: [list or "none"]
- Impact on existing data: [none / will break: X]

## Scope Decision
✅ Scope confirmed — [N] files to modify, all necessary
❌ Scope unclear — need user confirmation on: [questions]
```

## Execution Principles

1. **Minimal change is the default**: Every line you change that the user didn't ask for is a liability. The user can always ask for "also fix B" later — but they can't un-merge your surprise changes.

2. **Existing > new**: Before writing new code, always search for existing implementations. If the project already has a truncation strategy, retry logic, or config pattern, use it. Duplicating patterns creates maintenance debt.

3. **Environment matters**: "Local" is not "test" is not "prod". Config, URLs, proxy, and even available packages differ. Confirm before writing environment-dependent code.

4. **If you discover more needs changing, stop and report**: Finding additional issues during work is normal — silently fixing them is not. Report what you found, let the user decide whether to include it in this change or defer.

5. **Backward compatibility is not optional**: If your change breaks existing data or calls, that's a scope expansion — the user must approve it.
