---
name: design_doc_review
description: "Systematically review design documents for completeness, clarity, and implementability. Triggered after a design document is written or updated. Also use when the user mentions 'review design doc', 'design review', 'check design doc', or 'is this design sound'. The review aims to surface omissions, ambiguities, contradictions, and points needing clarification — exposing issues that would cause rework before coding begins. Every design document must pass this skill's review before implementation is approved."
---

# Design Document Reviewer

## Purpose

Systematically evaluate design documents for completeness, clarity, and implementability. Surface omissions, ambiguities, contradictions, and points needing clarification before implementation begins.

## Core Principle

**Critical review, not rubber-stamping**

This is not a walk-through approval process. Maintain skepticism and critical thinking for every design document. The goal is to expose issues that would cause implementation failures, rework, or unclear outcomes.

## Review Dimensions

Systematically evaluate the following 9 dimensions:

### 1. Context
- **What to check**: Does the document clearly explain why this design is needed?
- **Omission signal**: No context, assumes reader knows the situation, no background history
- **Ambiguity signal**: Context too vague, not tied to specific project context
- **Follow-up**: What triggered this design? What is the current state? Why now?

### 2. Problem Definition
- **What to check**: Does the document clearly state what problem it aims to solve?
- **Omission signal**: Problem is implied but not stated, or is too broad
- **Ambiguity signal**: "Optimize X" without metrics, "fix performance" without baseline
- **Follow-up**: What is the specific pain point? How is it measured today? What is the target state? Does the problem statement include a success criterion that can be checked against the original request to prevent scope drift?

### 3. Solution
- **What to check**: Is the technical approach specific and achievable?
- **Omission signal**: Only high-level concepts, no technical details, no architecture diagram
- **Ambiguity signal**: "Use microservices" without details, "add caching" without strategy
- **Follow-up**: What specific components are involved? What is the data flow? What are the interfaces?

### 4. Boundaries
- **What to check**: Does the document clarify what's in scope and what's out of scope?
- **Omission signal**: Scope not mentioned, assumes reader knows the constraints
- **Ambiguity signal**: "Focus on X" but also mentions other features, priorities unclear
- **Follow-up**: What won't be implemented? What are the constraints? What's being deferred?

### 5. Integration
- **What to check**: Does the document explain how it integrates with existing systems?
- **Omission signal**: Existing code not mentioned, assumes standalone implementation
- **Ambiguity signal**: "Integrate with X" without details, no migration plan
- **Follow-up**: Which existing components will interact? What needs to be modified? What is the migration path? If the design adds new features/templates/components, how are they wired into existing product entry points (default config, routing, menus)? Will the new feature be accessible by default, or only in isolation?
- **Dual System Consistency**: Does the design introduce or maintain dual rendering/processing paths (e.g., HTML preview vs PPTX export)? If dual systems exist, is there a unification plan?

### 6. Expected Outcomes
- **What to check**: Does the document describe specific results after implementation?
- **Omission signal**: Outcomes not described, or only technical-level outcomes
- **Ambiguity signal**: "Better performance" without metrics, "improved experience" without specifics
- **Follow-up**: What will users see? Which metrics will change? What is the success criteria?

### 7. Verification Scope
- **What to check**: Does the document clarify what will be tested/verified?
- **Omission signal**: No verification plan, assumes "just make it work"
- **Ambiguity signal**: "Test functionality" without specifics, edge cases not mentioned. Does the verification plan specify test case complexity? Simple smoke tests (e.g., 4-page deck) are insufficient — must include realistic data density and edge cases.
- **Follow-up**: Which scenarios will be tested? Which edge cases? What won't be tested?

### 8. Acceptance Criteria
- **What to check**: Does the document provide measurable acceptance criteria?
- **Omission signal**: No criteria, or only subjective criteria ("looks good")
- **Ambiguity signal**: "Works correctly" without definition, "fast enough" without numbers. If UI/visual output is involved, are visual acceptance criteria specified (no text overlap, no misalignment, no blank areas)?
- **Real Measurement vs Estimation**: Does the design rely on estimation (e.g., font metrics estimating text width/height) rather than real measurement? Is a measurement method specified?
- **Follow-up**: Which metrics? What test pass rate? What is the review process?

### 9. Simplicity
- **What to check**: Does the design introduce unnecessary abstraction layers, configuration options, or extension points to satisfy hypothetical future needs? Is there a simpler approach that meets the core requirements?
- **Omission signal**: No consideration of simpler alternatives; over-engineered by default
- **Ambiguity signal**: "Flexible for future extension" without a concrete future need identified
- **Follow-up**: What is the simplest approach that satisfies the stated requirements? Which abstraction layers or config options can be removed without losing core functionality?

## Review Workflow

### Step 1: Read the full document

Read the design document completely. Note:
- Structure and organization
- Missing sections
- Assumptions made
- Unexplained terminology

### Step 2: Systematic dimension check

Check each dimension using the following markers:
- ✅ = Complete and clear
- ⚠️ = Present but vague/unclear
- ❌ = Missing or severely insufficient
- ❓ = Needs user clarification

### Step 3: Critical analysis

Identify and categorize the following types of issues:

- **Omissions**: What important aspects were not mentioned?
- **Ambiguities**: What content could be interpreted in multiple ways?
- **Contradictions**: What statements conflict with each other?
- **Points needing clarification**: What requires more explanation?

### Step 4: Clarification questions

**Critical: Must use AskUserQuestion tool ask questions; must NOT write questions into the output file.**

When unclear points requiring user input are found, you must:
- **Immediately call AskUserQuestion** (don't write questions into the review report)
- Ask specific questions (not vague ones)
- Explain why you're asking the question
- Limit to 1-4 questions per review
- Questions should address specific unclear points or contradictions

**Correct approach**:
Find contradiction → Immediately call AskUserQuestion → Wait for answer → Incorporate answer into final review report

**Wrong approach** (don't do this):
Find contradiction → Write question into review report → Review ends without getting an answer

**When to use AskUserQuestion**:
- Found contradictions in the design (goals vs. approach mismatch)
- Need to understand design intent to judge quality
- Found ambiguous statements that could have multiple meanings
- Need data/schema information to evaluate implementation feasibility

### Step 5: Actionable recommendations

For each issue found, provide:
- **Issue**: Specific problem description
- **Location**: Location in the document (section/paragraph)
- **Risk**: Why this is a problem (implementation failure risk)
- **Recommendation**: Specific fix recommendation

Format:
```
**Issue**: [Description]
**Location**: [Section name or paragraph]
**Risk**: [Why this matters]
**Recommendation**: [Specific fix — what to add/modify]
```

## Output Format

```
# Design Document Review: [Document Title/Path]

## Overall Assessment
- **Completeness**: [X/9 dimensions complete]
- **Clarity**: [High/Medium/Low]
- **Implementability**: [Ready to implement / Needs revision]

## Dimension Analysis
| Dimension | Status | Notes |
|-----------|--------|-------|
| Context | ✅/⚠️/❌/❓ | [Brief note] |
| Problem Definition | ✅/⚠️/❌/❓ | [Brief note] |
| Solution | ✅/⚠️/❌/❓ | [Brief note] |
| Boundaries | ✅/⚠️/❌/❓ | [Brief note] |
| Integration | ✅/⚠️/❌/❓ | [Brief note] |
| Expected Outcomes | ✅/⚠️/❌/❓ | [Brief note] |
| Verification Scope | ✅/⚠️/❌/❓ | [Brief note] |
| Acceptance Criteria | ✅/⚠️/❌/❓ | [Brief note] |
| Simplicity | ✅/⚠️/❌/❓ | [Brief note] |

## Issues Found

### Omissions
1. [Issue and recommendation]

### Ambiguities
1. [Issue and recommendation]

### Contradictions
1. [Issue and recommendation] (if any)

### Points Needing Clarification
1. [Questions needing user input — if not already asked via AskUserQuestion]

**Note**: If points needing clarification were found, you should have already used AskUserQuestion in Step 4. Don't just list "points needing clarification" without actually asking.

## Recommendations

### Must Fix Before Implementation
1. [Critical recommendations]

### Recommended Fixes
1. [Important but non-blocking]

### Optional Improvements
1. [Nice to have]

## Final Conclusion
- **Pass**: All critical dimensions complete, no blocking issues
- **Needs Revision**: Critical sections missing/unclear
- **Blocked**: Fundamental issues exist, need user clarification first
```

## Anti-Patterns

- **Rubber-stamping**: Don't say "looks fine" without critical analysis
- **Soft feedback**: Don't say "could be better" — specify what's wrong
- **Vague recommendations**: Don't suggest "add more detail" — say what detail to add
- **Skipping questions**: Don't guess at unclear points — ask the user

## Success Criteria

A successful review:
- Surfaces at least one actionable improvement point (even for good documents)
- Provides specific location for each issue
- Provides concrete fix recommendations (not vague suggestions)
- Asks clarification questions when genuinely uncertain
- Gives a clear conclusion: pass, needs revision, or blocked
