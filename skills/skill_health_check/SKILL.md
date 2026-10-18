---
name: skill_health_check
description: "Use when the user completes skill creation or iteration and needs a skill health check. Checks for zombie files (unreferenced/outdated/unused scripts, references, assets), description trigger accuracy, SKILL.md unnecessary content (when-to-use repetition, why explanations, version history, iteration details), QA layering rationality (intermediate steps vs. end-stacking, blocking vs. advisory, scripted vs. textual), scriptability potential (whether fixable instructions are already scripted), content redundancy (SKILL.md vs. reference duplication with specific overlap and retention recommendations), pitfall effectiveness (whether QA can cover them, whether they provide solutions not just warnings), absolute path checks (skills must not contain environment-bound absolute paths; use `<skill_path>/relative_path` placeholders when referencing other skills), localization completeness (if localization is claimed, all files including references and scripts must be translated), and command environment compatibility (docker compose vs docker-compose, sudo behavior across distributions, python3 vs python, sudo tee vs sudo bash -c). Outputs a check report + pending-confirmation action list; after user confirmation, preserves state before modifying."
---

# Skill Health Check

Systematic health audit for completed skills, surfacing zombie files, description issues, redundant content, QA defects, scriptability opportunities, and pitfall effectiveness problems.

## Content Ownership Principle

When checking redundancy and pitfall effectiveness, use this principle to determine where content should reside:

| Layer | Should Contain | Should NOT Contain |
|-------|---------------|-------------------|
| **SKILL.md** | Workflow overview (step names + inter-step relationships), brief global constraint declarations, script invocation methods (command + args + expected output), inter-step references ("read references/xxx.md") | Single-step execution details, parameter calculation logic, reproduction of reference-specific steps, constraints exceeding 3 lines |
| **references/** | Detailed execution methods for single steps, parameter details, examples, detailed constraints, variant selection logic | Workflow overview, inter-step relationships |
| **scripts/** | Deterministically executable logic (parameter calculation, rule checking, template assembly, format conversion) | Creative decisions requiring AI judgment, steps requiring user interaction |

**Script coverage principle**: If a piece of logic is already implemented in a script, SKILL.md only needs to say "run script X, it does Y, expected output Z" — no need to reproduce the script's internal implementation logic. The script itself is the most accurate documentation — when modifying the script, there's no need to synchronously modify SKILL.md's reproduction of it.

## Workflow

### 1. Scan skill file structure

Read all files in the skill directory, build a complete file inventory:

```bash
find <skill_path> -type f | sort
```

Record: scripts (scripts/*.py), reference files (references/*.md), assets (assets/*), templates (templates/*), other files.

### 2. Execute eight checks

Execute the following checks one by one. Detailed criteria for each check are in `references/check-criteria.md`.

#### Check 1: Zombie Files

**Goal**: Find unreferenced, outdated, superseded scripts, references, and assets.

**Automated detection**: Run `scripts/zombie_detector.py` to automatically scan file reference relationships:

```bash
python3 scripts/zombie_detector.py <skill_path> --print
```

The script outputs a candidate zombie file list. zombie_detector.py only checks direct path string matching and cannot detect runtime assets loaded by filename in scripts (e.g., font files, icon files). For each candidate zombie, manually verify:

1. Search for filename (without path) in SKILL.md
2. grep filename in all scripts
3. Search for filename in all references
4. Confirm whether it's a runtime asset (font, icon, config file loaded by script by name)

**Classification output**:
- **Safe to delete**: Explicitly superseded (has replacement) or has no references and content has no unique value
- **Needs reference added**: Content has unique value but SKILL.md doesn't reference it — suggest adding reference in SKILL.md
- **Needs judgment**: May still have value but uncertain — list content summary for user to judge
- **False positive**: zombie_detector.py misreported, actually referenced at runtime by a script — note false positive reason

**Prohibited**: Do not directly delete any files. Only output analysis report for user to confirm and execute.

#### Check 2: Description Trigger Accuracy

**Goal**: Verify that description correctly describes "when to use," not "what it does."

**Criteria**:
- ✅ Description should focus on **when to use** (what scenarios, what user statements trigger it)
- ✅ "What it does" should be briefly summarized (1-2 sentences), not expanded into implementation details
- ❌ Should not include implementation steps, technical parameters, or script commands in description
- ❌ Should not be too long (recommended <150 characters)

**Check method**: Read SKILL.md frontmatter description field, evaluate against above criteria.

#### Check 3: SKILL.md Unnecessary Content

**Goal**: Remove content that should not appear in SKILL.md body.

**Criteria**:
- ❌ **when to use**: Skill is already activated, no need to repeat "when to use" in body — that's description's job
- ❌ **why do this**: Skill describes how to do the task, not why. Delete "because...therefore..." style explanations
- ❌ **version history**: e.g., "v1 used X, v2 changed to Y" — skill should be a snapshot of the current best approach, without history
- ❌ **iteration details**: e.g., "this optimization added X, improved Y" — same as above
- ✅ Keep: concrete steps, parameters, commands, expected outputs

#### Check 4: QA Layering Rationality

**Goal**: Confirm QA checks are distributed at appropriate positions in the workflow, not all stacked at the end.

**Criteria**:
- ✅ Each generation step should be immediately followed by a corresponding QA check
- ✅ QA should be layered: intermediate QA + final QA, not all checks stacked at the end
- ✅ QA should distinguish "blocking" (must fix to continue) vs. "advisory" (note but don't block)
- ❌ QA should not only appear in the final step
- ❌ QA should not be text-only descriptions (e.g., "check if X is Y") when it could be scripted

#### Check 5: Scriptability Potential

**Goal**: Identify SKILL.md content that could be fixed into scripts but is currently text instructions.

**Criteria**:
- ✅ Parameter calculation logic (font size, spacing, height estimation)
- ✅ Rule checking (consistency validation, format validation, file existence checks)
- ✅ Instruction assembly (prompt template assembly, config file generation)
- ✅ Repetitive operations (batch rename, batch convert)
- ❌ Creative decisions requiring AI judgment should NOT be scripted
- ❌ Steps requiring user interaction should NOT be scripted

#### Check 6: Content Redundancy

**Goal**: Identify content that appears in both SKILL.md and references, causing maintenance divergence.

**Criteria**:
- ❌ SKILL.md should not reproduce detailed steps from references
- ❌ SKILL.md should not duplicate parameter details from references
- ✅ SKILL.md may briefly summarize and point to references for details
- ✅ Unique content in each location is acceptable

**Output requirement**: For each redundancy, provide:
- Exact location in SKILL.md (line numbers)
- Exact location in reference (filename + line numbers)
- Degree of overlap (identical/highly similar/partial overlap)
- Retention recommendation (remove from SKILL.md / remove from reference / keep both)

#### Check 7: Pitfall Effectiveness

**Goal**: Evaluate whether each pitfall in SKILL.md is effective and properly placed.

**Classification criteria**:

| Pitfall Type | Characteristics | Recommended Action |
|-------------|----------------|-------------------|
| Can be QA-covered | The error described can be mechanically detected by a script (e.g., "don't change background color" → already checked by hard_contract audit) | Convert to QA gate, delete pitfall. QA scripts are proactive defense; pitfalls are passive reminders; when both overlap, keep QA |
| Describes constraint + solution | Pitfall includes problem description and solution (e.g., "float(v) doesn't support % → use value_label field") | Move into corresponding step or reference as a constraint. In-step constraints are visible during execution; pitfalls require the model to actively recall |
| Warning only, no solution | Pitfall only says "don't do X" without explaining the correct approach | Either supplement a solution and move into corresponding step, or delete. Warnings without solutions have no actionable guidance value for the model |

**Evaluation dimensions**:

For each pitfall, evaluate:

1. **Has a solution**: Does it explain the correct approach, or just say "don't do X"?
2. **Can be QA-covered**: Is the error described already checked by a corresponding QA script?
3. **Duplicates reference/step**: Is the pitfall's content already described in the corresponding step or reference?
4. **Generalizable**: Is the pitfall a universal rule or specific to a single incident? If incident-specific, has the lesson been codified into step constraints or QA?
5. **Would the model naturally make this error**: Would a sufficiently intelligent model naturally make this error without this pitfall? If not, the pitfall is redundant.

#### Check 8: Absolute Paths

**Goal**: Ensure the skill contains no environment-bound absolute paths.

**Criteria**:
- ❌ No environment-bound absolute paths (e.g., `/storage/skills/...`, `/home/user/...`, `/usr/local/...`)
- ❌ No absolute paths containing usernames, session IDs, or environment-specific info
- ✅ When referencing other skills, use `<skill_name_path>/relative_path` placeholder
- ✅ When referencing this skill's directory, use `<current_skill_dir>`
- ✅ When referencing working directory, use `<current_working_dir>`
- ✅ Declare placeholder meanings and referenced skill names+functions in a path convention paragraph

**Check method**:
1. Use grep to scan all `.py` and `.md` files in the skill directory for absolute paths:
   ```bash
   grep -rn "/storage/\|/usr/\|/home/\|/opt/" <skill_path> --include="*.py" --include="*.md" | grep -v __pycache__
   ```
2. For each match, determine if it's an environment-bound absolute path or a reasonable system path (e.g., `/usr/bin/env python3`)
3. Check whether references to other skills use hardcoded paths instead of `<skill_name_path>` placeholder
4. Check placeholder naming consistency: this skill's directory uses `<current_skill_dir>`, working directory uses `<current_working_dir>`, other skills use `<skill_name_path>`
5. Also check whether scripts call absolute paths of other skills' scripts via `subprocess` or `os.system` (e.g., `/home/user/.agents/skills/other_skill/scripts/xxx.py`). Such cross-skill absolute path dependencies break when the skill is moved to a different machine.

**Output requirement**: List each absolute path's file, line number, original text, and replacement suggestion (`<skill_name_path>/relative_path` or `<current_skill_dir>` or `<current_working_dir>`).

### 3. Output check report

Generate check report in the following format:

```markdown
# Skill Health Check Report: <skill_name>

## Check 1: Zombie Files

### Safe to Delete (X files)
| File | Type | Reason for becoming zombie | Replaced by |
|------|------|---------------------------|-------------|

### Needs Reference Added (X files)
| File | Content Summary | Suggested Reference Location |
|------|----------------|---------------------------|

### Needs Judgment (X files)
| File | Content Summary | Judgment Points |
|------|----------------|----------------|

### False Positives (X files)
| File | False Positive Reason |
|------|----------------------|

## Check 2: Description
- Current description: "..."
- Assessment: ...
- Suggested modification: "..."

## Check 3: SKILL.md Unnecessary Content
| Line | Content Summary | Issue Type | Suggested Action |
|------|----------------|-----------|-----------------|

## Check 4: QA Layering
- QA step positions: ...
- Issues: ...
- Suggestions: ...

## Check 5: Scriptability
| Line | Current Text Description | Suggested Script Approach |
|------|------------------------|--------------------------|

## Check 6: Content Redundancy

For each redundancy, provide specific comparison:

### Redundancy 1: <Brief description>
- **SKILL.md**: Lines X-Y
  > Original text excerpt...
- **reference**: Filename, Lines X-Y
  > Original text excerpt...
- **Overlap degree**: Identical / Highly similar / Partial overlap
- **Retention recommendation**: <Action>
- **Retention rationale**: <Per content ownership principle>

### Redundancy 2: ...

## Check 7: Pitfall Effectiveness

For each pitfall:

### Pitfall #N: <Brief description>
- **Original text**: Line X "..."
- **Has solution**: Yes/No
- **Can be QA-covered**: Yes (which QA script) / No
- **Duplicates reference/step**: Yes (where) / No
- **Recommendation**: Keep / Convert to QA gate / Move to step constraint / Delete
- **Rationale**: ...

## Check 8: Absolute Paths

| File | Line | Original Text | Suggested Replacement |
|------|------|--------------|----------------------|
```

### 4. Output pending-confirmation action list

Organize all actions requiring user confirmation into a list:

```markdown
## Pending Confirmation Action List

### Delete Files
- [ ] Delete scripts/xxx.py (superseded by yyy.py)

### Add References
- [ ] Add reference to references/xxx.md in SKILL.md step X

### Modify Content
- [ ] Modify description: "old" → "new"
- [ ] Delete SKILL.md lines X-Y (version history language)

### Script
- [ ] Fix SKILL.md lines X-Y text description into scripts/xxx.py

### Absolute Path Fixes
- [ ] Replace `/storage/...` in SKILL.md line X with `<current_skill_dir>/...` or `<current_working_dir>/...`
- [ ] Replace `/storage/skills/other_skill/...` in references/xxx.md line X with `<other_skill_name_path>/...`
- [ ] Replace `/storage/...` in scripts/xxx.py line X with corresponding placeholder

### Redundancy Handling
- [ ] Replace SKILL.md lines X-Y reproduction with reference to references/xxx.md

### Pitfall Handling
- [ ] Convert pitfall #N to QA gate (already checked by xxx.py)
- [ ] Move pitfall #N into step X as a constraint
- [ ] Delete pitfall #N (warning only, no solution, and model wouldn't naturally make this error)
```

### 5. Execute after user confirmation

**Key principle**: After user confirmation, **preserve state first, then modify**.

1. **Preserve state**: Package or git-push the current skill version
   ```bash
   cd <skill_parent_dir>
   python3 -c "
   import zipfile, os
   with zipfile.ZipFile('<skill_name>_backup.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
       for root, dirs, files in os.walk('<skill_name>'):
           dirs[:] = [d for d in dirs if d != '__pycache__']
           for f in files:
               path = os.path.join(root, f)
               zf.write(path, os.path.relpath(path, '.'))
   "
   ```
   Or if the skill is in a git repository:
   ```bash
   cd <skill_path>
   git add -A && git commit -m "checkpoint: pre-audit-fix snapshot"
   ```

2. **Execute modifications**: Execute each item per the user-confirmed action list

3. **Verify modifications**: After modifications, rerun the check to confirm issues are resolved

## Output Format

1. Check report (markdown format, containing complete analysis of all ten checks)
2. Pending-confirmation action list (user confirms each item before execution)
3. Verification report after modifications are complete
