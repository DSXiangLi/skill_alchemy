# Conversation Analysis Instruction

The organizer selected {recent_count} recent sessions as anchors. Keep every session as an independent evidence unit.

## Inputs

- `anchor_recent.md`: complete anchor conversations with explicit session boundaries.
- `session_index.md`: searchable index of all available sessions.
- Extracted JSONL supplied to `distill.py`: historical conversation content.

## Phase 3: Anchor Semantic Analysis

Read every anchor turn in context and classify it as genuine correction, effective guidance, redundant confirmation, or pure progression. Extract only genuine corrections and effective guidance.

For every extracted item, record the session id, turn index, behavior before the intervention, and behavior after it. Missing before/after evidence is blocking.

## Phase 4: Integrated Correlation Search

Derive search targets from anchor findings rather than from a predefined keyword list. Use project, component, symptom, API, file path, constraint, and architecture patterns to inspect candidate history.

Analyze five dimensions:

1. Historical root cause and whether the problem was preventable when introduced.
2. Related modules, adapters, UI paths, and projects with the same risk.
3. Fix, validation, abstraction, or optimization patterns that should propagate.
4. Requirements repeated after the AI violated or omitted them.
5. Existing AGENTS.md rules or skills whose triggers or checks were ineffective.

Use `session_index.md` before opening historical content. Cite each source as session id plus turn index. Never combine evidence from different sessions without stating the cross-session relationship. Missing or ambiguous source boundaries are blocking.

## Phase 5: Distill and Generalize

Cluster and deduplicate evidence at a reusable but executable abstraction level. Separate general action guides, project-specific knowledge, systemic error patterns, repeated requirements, changed or conflicting requirements, and related findings.

Before continuing, verify that every item is evidence-backed and routed to exactly one primary category. Ambiguous categorization is advisory; missing evidence is blocking.

## Phase 6: First-Layer Artifacts

Write these directories inside the current run directory:

```text
action-guides/
error-patterns/
repeated-requirements/
conflicting-requirements/
related-findings/
```

Requirements:

- action guides include source frequency;
- error patterns include trigger, behavior, root cause, and systemic status;
- repeated requirements include first statement, intervening violation or omission, and later repetition;
- changed requirements identify the currently valid rule and its evidence;
- related findings cover all five correlation dimensions or explicitly record that no evidence was found;
- every artifact cites session ids and turn indexes or a structured evidence file.

Do not begin skill synthesis until this completeness gate passes.

## Phase 7: Skill Synthesis

Treat skill synthesis as a separate second layer:

1. Read all first-layer artifacts.
2. Cluster findings by trigger moment.
3. Check existing skills and AGENTS.md before proposing a new skill.
4. Prefer updating an existing skill when its trigger and responsibility already match.
5. Use the `skill-creator` skill and follow its best practices.
6. Run `quick_validate.py` and, when available, `skill_health_check` or an equivalent checker.

For each cluster, report one decision: update an existing skill, create a distinct new skill, or keep the finding as project knowledge/passive guidance. Keep evidence details in the synthesis report or a reference file rather than bloating generated `SKILL.md` files.
