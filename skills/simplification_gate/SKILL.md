---
name: simplification_gate
description: >-
  Before AI starts designing or implementing a solution, it must pass this gate.
  Checks: did you ask "can we not do this at all?" before "how to do this?" Did you
  identify parts that can be cut, deferred, or reused? Is the proposed approach the
  simplest possible (one function, one path)? Are you adding abstraction, configuration,
  or flexibility for "future needs" that don't exist yet? Did you search for standard
  answers before designing your own? This skill triggers when: AI receives a new
  requirement, AI is about to design a solution, AI is about to add a new feature/config/
  abstraction layer, or user hints at simplification. Trigger words: "实现", "设计",
  "新增", "加一个", "做一个", "方案", "approach", "implement", "design", "add feature",
  or when AI is about to start any non-trivial implementation task.
---

# Simplification Gate

## Why This Skill Exists

Across 30+ sessions, the user repeatedly had to say "简化" (simplify), "不要加这么多", "先问能不能不做", "一个功能一个路径". AI's default behavior is additive — when given a requirement, it designs a flexible, extensible, future-proof solution with configuration options, abstraction layers, and multiple code paths. The user's actual need is usually the simplest thing that works.

This is the 3rd most frequent correction (after "功能验收≠语法检查" at 88 and "环境混淆" at 34). At 30 occurrences, it's more frequent than "先定位再修复" (23), "只改要求" (23), or "先出方案" (28).

The gap: AI's instinct is "add capability", the user's instinct is "remove complexity". These are opposite directions.

## Scope

**Must gate**: Any non-trivial implementation task — new feature, new config item, new abstraction, new module, solution design.

**May skip**: Trivial fixes (typo, one-line bug fix with obvious solution), pure documentation, reading code to answer a question.

## Relationship to Other Skills

| Skill | What it checks | When it triggers |
|-------|---------------|-----------------|
| change_scope_control | WHICH files to change (horizontal scope) | Before writing code |
| fix_plan_review | HOW GOOD the solution is (6 dimensions) | After solution is formulated |
| **simplification_gate** | **WHETHER and HOW SIMPLY to do it** | **Before solution design** |

This gate runs BEFORE fix_plan_review. First ask "is this the simplest approach?", then review the simplified solution's quality.

## Gate Checklist

Before designing or implementing, answer ALL of the following:

### Check 1: Necessity Challenge

**Can any part of this requirement be eliminated or deferred?**

For each sub-requirement, ask:
- "If I only do the core ask, would the user's actual need be met?"
- "Is this sub-requirement real now, or am I imagining a future need?"
- "Can this part be deferred until someone actually needs it?"

```
Requirement decomposition:
  [Core need]      → Must do now
  [Implied need]   → Verify with user before doing
  [Future need]    → DEFER — don't build for hypothetical scenarios
  [Nice to have]   → CUT
```

**Source evidence**: B2 "先问能不能不做再问怎么做" (AGENTS.md); 简化 30 sessions.

**Fail condition**: You cannot produce the decomposition, or >50% of the work is "implied/future/nice-to-have" without user confirmation.

### Check 2: Reuse Before Build

**Does the project already have something that does this?**

```bash
# Search for existing implementations of what you're about to build
grep -rn "similar_functionality\|similar_pattern" --include="*.py" --include="*.ts" --include="*.js" src/
# Check if an existing config pattern can be extended
grep -rn "config_pattern" src/config/
# Check if an existing utility function covers the need
grep -rn "def utility_" src/utils/
```

- If an existing implementation covers 80%+ of the need → EXTEND it, don't build new
- If an existing config pattern exists → FOLLOW it, don't invent a new one
- If a standard library/framework provides this → USE it, don't reimplement

**Source evidence**: A5 "优先检查已有能力是否满足需求", B3 "同项目内已有方案直接复用" (AGENTS.md).

**Fail condition**: You started designing without grepping the codebase for existing solutions.

### Check 3: Search Before Experiment

**Is this a standard technical problem with a known solution?**

Before designing your own solution, check:
- Is this a common pattern with a standard approach? (e.g., rate limiting, caching, retry)
- Does the framework documentation address this?
- Does a community solution exist?

```bash
# Check project docs first
grep -rn "keyword" docs/
# Check if framework docs mention this pattern
```

If a standard solution exists → USE it. Don't design your own experiment from scratch.

**Source evidence**: F6 "搜索标准答案优先于自行实验", A1 "先读文档和参考代码" (AGENTS.md).

**Fail condition**: You're designing a custom solution for a problem that has a well-known standard approach, without checking docs first.

### Check 4: Simplest Approach

**Is this the simplest possible approach? Not "a good approach" — the SIMPLEST.**

For each design decision, ask:
- "Can this be done with fewer moving parts?"
- "Am I adding an abstraction layer that isn't needed yet?"
- "Am I creating a configuration option when a hardcoded value would work?"
- "Am I building for extensibility when there's only one known use case?"

Anti-patterns to flag:
| Anti-pattern | Simpler alternative |
|---------------|---------------------|
| Abstract base class with 1 implementation | Just write the class directly |
| Config option for something with 1 known value | Hardcode it, branch later if needed |
| Plugin/strategy pattern for 1 strategy | Just write the function |
| Factory method when there's 1 product | Just construct directly |
| "Flexible" parameter that's always called with same value | Remove the parameter |
| Multi-layer architecture for a single-file feature | One file, one function |

**Source evidence**: B4 "默认值用最简方案，不为未来可能的需求预留扩展点", 简化 30 sessions.

**Fail condition**: The solution has abstraction layers, config options, or extension points that have only one known use case.

### Check 5: Complexity Budget

**Does the solution's complexity match the problem's complexity?**

- Simple problem (1-step, local) → Should be 1 function, no new files, no new config
- Medium problem (multi-step, single module) → Should be 1 file, minimal new config
- Complex problem (cross-module, architectural) → Justifies new abstractions, but still challenge each one

If a "simple problem" is getting a "complex solution", STOP and simplify.

**Source evidence**: B4 "一个功能一个路径，等真有第二种需求时再分支" (AGENTS.md).

**Fail condition**: Solution complexity >> problem complexity (e.g., adding a config system for a feature that has one setting).

## Gate Report Output

```markdown
# Simplification Gate Report

## Requirement
User request: [exact quote]
Core need: [one sentence]

## Necessity Decomposition
| Part | Classification | Action |
|------|---------------|--------|
| Core feature | Must do now | Include |
| Config option | Future need | DEFER |
| Error handling for edge X | Real need | Include |
| Extensibility layer | Future need | CUT |

## Reuse Check
- Searched for: [keywords]
- Found existing: [function/pattern] in [file] — will reuse
- Not found: no existing implementation — will write new (simplest version)

## Search Check
- Standard solution exists: [yes — which / no — confirmed not standard]
- Decision: [use standard / write minimal custom]

## Simplest Approach
- Proposed approach: [one paragraph]
- Abstraction layers: [count] — [justified / can be removed]
- Config options: [count] — [justified / can be hardcoded]
- New files: [count] — [justified / can be fewer]

## Complexity Budget
- Problem complexity: [simple / medium / complex]
- Solution complexity: [simple / medium / complex]
- Match: ✅ / ❌ (solution over-engineered)

## Gate Decision
✅ SIMPLIFIED — approach is the simplest that meets the core need
❌ OVER-ENGINEERED — must simplify before proceeding: [what to cut/defer]
```

## Execution Principles

1. **Subtraction before addition**: The default question is "can we not do this?", not "how should we do this?". Every line of code you don't write is a line that can't break.

2. **One path until proven otherwise**: Build one code path. When a second, genuinely different requirement arrives, THEN branch. Don't pre-branch for hypothetical variations.

3. **Hardcode until proven configurable**: Start with hardcoded values. Add configuration only when there's a demonstrated second value. "It might need to be configurable" is not a reason — it's an assumption.

4. **Existing > new > custom**: First check if the project already has it. Then check if a standard solution exists. Only then write custom code — and make it the minimum custom code possible.

5. **Complexity must be earned**: Every abstraction layer, config option, and extension point must be justified by a real, current need — not a future possibility. "We might need this later" means "we won't need it now."
