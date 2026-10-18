---
name: fix_plan_review
description: "Six-dimension systematic review of AI-proposed technical solutions: blast radius, performance impact, maintenance cost, root cause resolution, backward compatibility, and edge case coverage. Auto-triggers self-review before AI outputs a technical solution; also supports user-initiated review of existing solutions. Use when the user mentions 'review solution', 'evaluate plan', 'plan review', 'what's wrong with this plan', 'solution audit', 'check technical plan', 'is this design sound', or when AI is about to output a technical solution with implementation steps. Even without explicit review request, when AI is formulating a technical solution involving multiple steps, multi-file changes, or architectural adjustments, it should self-review before outputting."
---

# Technical Solution Reviewer

## Overview

Systematic six-dimension review of technical solutions, surfacing potential risks before the solution is presented to the user, or providing independent review of existing solutions upon request.

Reviewing is not about negating solutions, but about exposing hidden costs and risks before they land. A good technical solution must solve the current problem while also being responsible to the system's future.

## Two Usage Modes

### Mode 1: Self-Review (Before AI Outputs Solution)

When AI is formulating a technical solution (involving multiple steps, multi-file changes, architectural adjustments, data model changes, etc.), self-review before outputting:

1. Complete solution formulation internally
2. Check each of the six dimensions
3. Integrate self-review findings directly into the solution — fix the solution itself or annotate risks within it
4. Output the self-review-enhanced solution

In self-review mode, review results don't need a separate report; they are reflected in the final solution's completeness and risk annotations.

### Mode 2: Independent Review (User-Triggered)

When the user requests review of an existing solution (whether AI-generated or human-written), perform an independent structured review:

1. Read the entire solution, understanding the problem context and solution intent
2. When needed, read related code files to confirm the actual state of modules, interfaces, and data flows mentioned in the solution
3. Review dimension by dimension, output structured report

---

## Six Review Dimensions

### Dimension 1: Blast Radius

**Core question**: Which currently working modules will the solution's changes affect?

A seemingly local modification can propagate to unexpected places through shared interfaces, common modules, data models, event buses, and other channels. Blast radius is the most easily overlooked risk in technical solutions — because the solution designer's attention is focused on the problem being solved and rarely proactively checks "what will my change break."

**Checklist**:

- **Shared interface changes**: Does the solution modify interface signatures, return structures, or field semantics that other modules depend on? If so, do downstream consumers need synchronous modifications?
- **Common module/base class changes**: Does the solution modify common classes, utility functions, or middleware that are inherited or called from multiple places? Will other callers' behavior change after the modification?
- **Data model changes**: Does the solution change database table structures, serialization formats, or message body structures? Do existing data need migration? How is dual-write compatibility ensured during migration?
- **Configuration/environment dependencies**: Does the solution introduce new environment variables, configuration items, or infrastructure dependencies? Do other environments (test, staging, production) need synchronous changes?
- **Deployment coupling**: Does the solution's deployment require multiple services to be released simultaneously? Are deployment order dependencies introduced?
- **Implicit contract breaking**: Does the solution break conventions that aren't explicitly declared but actually exist in the code (e.g., callers of a function relying on undocumented side effects)?
- **Scope necessity**: Is every proposed change directly required by the user's request? Any "while I'm at it" changes should be flagged and excluded.

**Assessment method**: Trace each change point in the solution, follow the dependency chain outward one to two levels, and check for affected modules not addressed in the solution.

### Dimension 2: Performance Impact

**Core question**: After the solution lands, can the system handle normal and peak loads?

Performance issues typically don't surface in functional testing but suddenly erupt when traffic grows after deployment. During review, focus on whether the overhead introduced by the solution is within acceptable limits and whether there are hidden degradation risks as data volume grows.

**Checklist**:

- **Time complexity**: What is the time complexity of newly added or modified logic? Are there O(n²) or worse nested loops? What is the scale of n now and in the future?
- **Database pressure**: Are N+1 queries introduced? Are database operations executed inside loops? Are excessive indexes added or necessary indexes missing? Is there a full table scan risk?
- **Memory usage**: Is large amounts of data loaded into memory at once? Is caching introduced without an eviction strategy? Is there a memory leak risk?
- **Concurrency and locks**: Are new lock contentions introduced? Is lock granularity reasonable? Is there a deadlock risk? Are distributed lock scenarios considered?
- **I/O blocking**: Is synchronous I/O introduced on the critical path? Are there operations that could be async but are designed as sync?
- **Network overhead**: Are additional network calls added (e.g., cross-service calls)? Does call volume grow linearly with data volume?
- **Capacity estimation**: Under expected data growth (1x, 10x, 100x), will the solution's performance degradation be within acceptable limits?

### Dimension 3: Maintenance Cost

**Core question**: Six months from now, will a new team member be able to understand and modify this code?

The cost of a solution isn't just in writing it — it includes every future read, modification, and debugging session. Review must assess whether the solution increases cognitive load or introduces hard-to-maintain patterns.

**Checklist**:

- **Code complexity**: Does the solution introduce overly complex logic (deep nesting, multi-layer callbacks, complex state machines)? Can complexity be reduced through decomposition? Does the solution add abstraction layers, config options, or extension points that have only one known use case? Is the approach the simplest possible, or is it additive by default — adding capability the user didn't ask for?
- **Implicit dependencies**: Does the solution rely on undocumented assumptions (execution order, external state, specific data formats)?
- **Naming clarity**: Are new variables, functions, and classes named accurately? Can the purpose be understood without reading the implementation?
- **Comment sufficiency**: Are complex logic sections commented? Do comments explain "why" rather than "what"?
- **Pattern consistency**: Does the solution follow existing codebase patterns? If new patterns are introduced, is there sufficient justification?
- **Test difficulty**: Is the solution easy to write unit tests for? Does it introduce hard-to-mock dependencies or hard-to-reproduce states?
- **Documentation sync**: Does the solution require synchronous updates to design docs, API docs, or operational guides?

### Dimension 4: Root Cause Resolution

**Core question**: Does the solution address the root cause of the problem, or just the symptoms?

Patch-style fixes (making errors not occur by adding special handling) are reasonable in emergencies but create recurring maintenance burden. Review must assess whether the solution resolves the root cause.

**Checklist**:

- **Problem definition**: Does the solution clearly state the root cause of the problem? If the solution only describes "what to do" without "why the problem occurs," it's likely patching symptoms
- **Patch vs. root fix**: Is the solution patch-style (special handling when the problem occurs) or root-fix (eliminating the conditions that cause the problem)?
- **Recurrence risk**: Under what conditions could this problem recur? Does the solution cover these conditions?
- **Similar problems**: Could the same root cause trigger similar problems elsewhere? Does the solution only fix one manifestation?
- **Technical debt labeling**: If the solution is a patch, does it clearly mark the technical debt and the trigger conditions for future refactoring?

### Dimension 5: Backward Compatibility

**Core question**: After the solution is deployed, will existing functionality, existing data, and existing integrations continue to work?

Backward compatibility issues are among the most dangerous changes — they don't trigger errors but produce "silent failures." Existing users, existing data, and existing integration code may all be affected.

**Checklist**:

- **API compatibility**: Do interface signatures, parameter names, parameter types, or return structures change? Do old callers still work?
- **Data format compatibility**: Are storage formats, serialization formats, or message body structures changed? Can existing data still be parsed?
- **Behavioral compatibility**: Does the same input produce different output? Will callers relying on the original behavior be affected?
- **Configuration compatibility**: Are configuration items deleted or renamed? Do old configuration files still work?
- **Dependency compatibility**: Are dependency versions upgraded? Does the new version have breaking changes?
- **Deprecation strategy**: For incompatible changes, is a deprecation strategy provided (dual-version coexistence, migration tools, migration guide)?

### Dimension 6: Edge Case Coverage

**Core question**: Does the solution consider abnormal scenarios (edge cases, error paths, concurrency, timeouts, retries)?

Functional correctness in normal paths is basic; how abnormal scenarios are handled determines system robustness. During review, systematically check whether the solution covers common abnormal scenarios.

**Checklist**:

- **Null/empty values**: How does the solution handle null, empty strings, empty arrays, empty objects?
- **Boundary values**: How are zero, negative numbers, maximum values, special characters handled?
- **Error paths**: If external dependencies fail (database, cache, message queue, external service), are there fallback strategies?
- **Timeout handling**: What happens when operations timeout? Are there retries? What is the retry strategy?
- **Concurrency scenarios**: What is the behavior under concurrent access? Is there a race condition risk?
- **Partial failures**: If a multi-step operation fails partway through, what is the state? Is there compensation/rollback?
- **Permission/authentication**: Have permission verification and authentication token expiration been considered?

---

## Supplementary Checks

### Product Entry Point Integration

**Core question**: When the solution adds a new feature, template, or component, does it explicitly specify how it integrates into existing product entry points (default configuration, routing, menu)?

**Checklist**:

- **Entry point specification**: Does the solution state which product entry point (route, menu item, default config) the new feature is wired into? Or does it only implement the feature in isolation, leaving it unreachable by end users?
- **Default configuration**: If the feature requires configuration to be active, is the default value set so it is discoverable without manual intervention?
- **Routing/menu integration**: If the feature is a page, component, or tool, is it registered in the routing table or menu system? Or does it exist only as a standalone module that users cannot navigate to?

**Assessment method**: After reading the solution, trace from the feature implementation back to the product entry point. If no integration path is specified, flag it.

### Dual System Consistency

**Core question**: Does the solution introduce or maintain two parallel rendering/processing paths? If so, is there a consistency plan or a unification roadmap?

**Checklist**:

- **Dual path detection**: Does the solution create a new rendering or processing path alongside an existing one (e.g., a new template engine while the old one remains active)?
- **Consistency guarantee**: If two paths coexist, is there an explicit plan to keep their output consistent? Or will they silently diverge over time?
- **Unification roadmap**: If two paths exist, does the solution specify which one is the target and when the other will be deprecated? Or is the dual system treated as permanent without justification?

**Assessment method**: Identify all rendering/processing paths the solution touches. If more than one path exists for the same concern, verify that a consistency or unification plan is documented.

### Real Measurement vs Estimation

**Core question**: Does the solution rely on estimation rather than real measurement for layout, sizing, performance, or capacity claims? Does it specify a measurement method?

**Checklist**:

- **Estimation vs measurement**: Are sizing, spacing, performance, or capacity claims based on actual measurement (real data, real rendering, real benchmarks) or on estimation ("should be fine", "roughly X")?
- **Measurement method specification**: Does the solution specify how the claim will be verified? E.g., does it name the tool, the data set, or the test scenario used to produce the measurement?
- **Layout correctness**: For UI/layout changes, does the solution verify rendered output against real content rather than assuming dimensions will "just work"?

**Assessment method**: For each quantitative claim in the solution (size, performance, capacity, layout), check whether a real measurement is cited or a measurement method is specified. Flag any claim that relies solely on estimation.

### Core Goal Alignment

**Core question**: Does the solution directly solve the original problem, or has it drifted to a sub-module or a tangential concern? Re-read the original problem statement and confirm.

**Checklist**:

- **Original problem re-read**: Re-read the user's original problem statement. Does the solution address that problem directly, or has it pivoted to solving a different (possibly related but not equivalent) problem?
- **Sub-module drift**: Has the solution's focus shifted to refactoring, optimizing, or fixing a sub-module that is not the core of the user's request? While the sub-module work may be valid, it should not replace the core deliverable.
- **Direct path verification**: Is there a direct, traceable line from the solution's main deliverable back to the original problem? Or does the solution solve the problem indirectly through a chain of prerequisites that may not all be necessary?

**Assessment method**: After reviewing the entire solution, re-read the original problem statement. Explicitly confirm whether the solution's primary output addresses that problem. If the solution's main effort is on something other than the original problem, flag the misalignment.

---

## Output Formats

### Independent Review Mode Output

```markdown
# Technical Solution Review Report

## Solution Overview
- Problem: [One-line description]
- Solution: [One-line description]
- Scope of changes: [Files/modules involved]

## Dimension Review

### Dimension 1: Blast Radius
**Assessment**: Low / Medium / High
**Findings**: ...
**Improvement suggestions**: ...

### Dimension 2: Performance Impact
**Assessment**: Low / Medium / High
**Findings**: ...
**Improvement suggestions**: ...

### Dimension 3: Maintenance Cost
**Assessment**: Low / Medium / High
**Findings**: ...
**Improvement suggestions**: ...

### Dimension 4: Root Cause Resolution
**Assessment**: Root cause / Patch
**Findings**: ...
**Improvement suggestions**: ...

### Dimension 5: Backward Compatibility
**Assessment**: Compatible / Incompatible / Needs evaluation
**Findings**: ...
**Improvement suggestions**: ...

### Dimension 6: Edge Case Coverage
**Assessment**: Sufficient / Insufficient
**Findings**: ...
**Improvement suggestions**: ...

## Summary

### Must-Resolve Issues (Before Deployment)
1. ...
2. ...

### Recommended Improvements (Can iterate later)
1. ...
2. ...

### Trade-offs Requiring User Decision
1. [Issue] → Option A (low cost/short-term) vs Option B (high cost/long-term)
```

### Self-Review Mode Output Requirements

In self-review mode, the full report above is not needed, but:

1. **Integrate review findings into the solution**: Annotate risks and notes alongside corresponding solution steps
2. **Append risk alert at end of solution**: List key risks found during self-review in the following format:

```markdown
## Solution Risk Alert (Self-Review)

| Dimension | Risk Level | Description |
|-----------|-----------|-------------|
| Blast Radius | Low/Medium/High | ... |
| Performance Impact | Low/Medium/High | ... |
| Maintenance Cost | Low/Medium/High | ... |
| Root Cause Resolution | Low/Medium/High | ... |
| Backward Compatibility | Low/Medium/High | ... |
| Edge Case Coverage | Low/Medium/High | ... |
```

---

## Review Principles

### General Principles

The following principles apply to all reviews, regardless of solution type or change scope:

1. **Review the solution on its merits**: Reviewing the solution's risks, not the solution designer's capability. No "should have" lecturing — only point out specific risks and specific fixes.

2. **Differentiate severity**: Not all issues are equally important. Categorize issues as "must resolve" (will cause production incidents or data loss if unresolved) and "recommended improvement" (optimization but non-blocking for deployment).

3. **Give actionable improvement suggestions**: Don't just point out issues and stop there. Each issue should come with a specific improvement direction — no need for a complete solution, but the recipient should know "which direction to fix."

4. **Respect engineering reality**: Sometimes "patching" is the right choice — when root-cause fix costs far exceed the problem's impact. Reviews should annotate these trade-offs for the decision-maker's awareness, not blindly pursue "perfect solutions."

5. **Avoid over-reviewing**: If a solution genuinely has no issues in a certain dimension, don't fabricate issues just to fill space. Explicitly writing "no obvious risks found" is more valuable than listing a bunch of equivocal concerns.

### Scenario-Specific Supplementary Rules

The following rules only activate when the solution matches specific scenarios. During review, first determine which scenarios the solution involves, then execute the corresponding supplementary rules.

#### Scenario 1: A specific-type issue found during review

When a specific issue is found in a dimension during review (e.g., parameter filter omission, uncovered path, unreferenced constant, incorrect behavior definition for a file type), don't just record this one issue and move on. The appearance of one issue often means similar defects exist elsewhere.

**Supplementary rules**:
1. **Same-type full scan**: grep all related code paths to confirm whether the same issue exists
2. **Logical abstraction scan**: Abstract the underlying pattern from the specific issue, then check other locations exhibiting the same pattern but with different code forms. For example, if markdown download opened a web page instead of a download page — the abstracted pattern is "incorrect download behavior definition for specific file types"; should then check text, csv, json, and other text types for the same issue, rather than just grepping the keyword "markdown"
3. **Record to AGENTS.md**: Add the investigation conclusion as a development standard entry to prevent future recurrence

#### Scenario 2: Solution involves code/variable deletion

When deleting code blocks, it's easy to accidentally delete adjacent variable definitions that subsequent code depends on. `UnboundLocalError` only triggers at runtime, and neither import checks nor diff reviews can catch it.

**Supplementary rules**:
- For each variable defined in the deleted code block, run grep across the entire project to confirm no remaining references
- If remaining references exist, the solution must include handling for those reference points

#### Scenario 3: Solution involves interface/data model changes

Interface signatures, return structures, field semantics, and database table structure changes propagate along the dependency chain. The blast radius of such changes is most easily underestimated.

**Supplementary rules**:
- List all downstream consumers (grep interface name/field name), confirm each one's need for synchronous modification
- If existing data exists, confirm data migration plan and dual-write compatibility strategy
- If interface semantics change (signature unchanged but behavior changed), confirm whether there's a transition period and notification mechanism

#### Scenario 4: Solution involves concurrency/distributed scenarios

When a solution introduces new concurrency paths, locking mechanisms, cross-service calls, or distributed coordination, standard functional tests have difficulty covering race conditions and timing issues.

**Supplementary rules**:
- Check whether lock granularity is reasonable and whether deadlock risk exists
- Check whether retries are idempotent and whether repeated execution is safe
- Check behavior under message reordering, delayed arrival, and duplicate consumption
- Check consistency windows and dirty-read risks in distributed scenarios

#### Scenario 5: Solution is labeled as technical debt or expedient measure

When the solution includes content like "do this for now, optimize later" or "temporary solution," these debts, if only verbal, are often never repaid.

**Supplementary rules**:
- Confirm whether the solution explicitly labels the trigger conditions for refactoring (e.g., "refactor when data volume exceeds X")
- Confirm whether the refactoring direction is recorded, not just "needs refactoring"
- Confirm whether the debt is recorded in AGENTS.md or the technical debt list
