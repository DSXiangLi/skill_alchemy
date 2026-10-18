---
name: skill-alchemy
description: Use when mining local AI sessions for recurring corrections, related failures, repeated constraints, or evidence-backed skill updates.
---

# Skill Alchemy

Extract durable lessons from local AI sessions through semantic correlation, then synthesize validated skill updates in a separate second layer.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/extract.py` | Normalize Kimi Code, Codex CLI, Claude Code, and Hermes Agent sessions into JSONL |
| `scripts/distill.py` | Select recent anchors and generate the session index and analysis instruction |
| `scripts/validate_run.py` | Validate generated files, session boundaries, index coverage, and phase numbering |

`templates/analysis_instruction.md` is the detailed Phase 3-7 analysis contract. `distill.py` renders it into each run directory; follow the rendered copy during analysis.

## Workflow

### Phase 1: Extract Sessions

Run from the skill directory:

```bash
python3 scripts/extract.py --tool all --min-turns 3 --output output/extracted --format jsonl
```

Treat each JSONL record as one session. Preserve `source_tool`, `source_file`, `session_id`, `workspace`, `created_at`, and ordered turns.

Blocking QA:

- every retained record has a non-empty session id, source file, and stable creation time;
- system injections and tool results are absent from user turns;
- turn indexes increase within each session.

### Phase 2: Build Anchors

Use 10 recent sessions by default:

```bash
python3 scripts/distill.py output/extracted -o output/run
```

Use another positive last-n when session length or topic density requires it:

```bash
python3 scripts/distill.py output/extracted -o output/run --recent 20
```

`--recent` and `--max-sessions` accept positive integers only. If last-n exceeds the available sessions, all available sessions become anchors and the actual count is reported.

The organizer automatically runs `scripts/validate_run.py`. Any missing file, mismatched boundary, duplicate anchor id, missing index entry, or invalid phase contract blocks analysis.

Expected files:

```text
output/run/
├── anchor_recent.md
├── session_index.md
└── ANALYSIS_INSTRUCTION.md
```

### Phase 3: Analyze Anchors

Read the rendered `ANALYSIS_INSTRUCTION.md`. Use semantic before/after comparison to extract only genuine corrections and effective guidance. Do not classify corrections by keywords.

Blocking QA: every extracted item cites session id, turn index, behavior before, and behavior after.

### Phase 4: Search Related History

Derive search targets from anchor findings and use `session_index.md` before inspecting extracted history. Search across historical root causes, related modules/projects, pattern propagation, repeated requirements, and existing rule/skill effectiveness.

Blocking QA: keep each session as a separate evidence unit and cite every cross-session source independently.

### Phase 5: Distill Findings

Cluster and deduplicate evidence. Separate general guidance, project knowledge, systemic error patterns, repeated requirements, changed requirements, and related findings.

Advisory QA: resolve ambiguous categories before writing final artifacts. Missing evidence remains blocking.

### Phase 6: Produce First-Layer Artifacts

Write evidence-backed results under the run directory:

```text
action-guides/
error-patterns/
repeated-requirements/
conflicting-requirements/
related-findings/
```

Apply the completeness gate in `ANALYSIS_INSTRUCTION.md`. Do not synthesize skills until it passes.

Run the blocking first-layer check:

```bash
python3 scripts/validate_run.py output/run --first-layer
```

The check requires every artifact directory to contain a non-empty file and every file to cite session/turn evidence or explicitly state that no evidence was found.

### Phase 7: Synthesize Skills

Use the first-layer artifacts as evidence, then:

1. Cluster findings by trigger moment.
2. Check existing skills and AGENTS.md before creating anything.
3. Prefer updating a matching skill over creating a duplicate.
4. Use `skill-creator` and follow its best practices.
5. Run `quick_validate.py` and, when available, `skill_health_check` or an equivalent checker.
6. Write synthesis decisions and validation results to `skill-synthesis/`.

Keep source-frequency details in the synthesis report or references. Generated `SKILL.md` files should contain concise triggers, workflow, executable checks, pass/fail criteria, and necessary resource links rather than experiment history.
