# Detailed Check Criteria Reference

This file defines the detailed criteria and check methods for all eight checks.

## Check 1: Zombie Files

### Check Method

#### 1.1 Extract SKILL.md references

```bash
# Extract all file references
grep -oP "(scripts|references|templates|assets)/[a-zA-Z0-9_/-]+\.(py|md|yaml|json|ttf|png)" SKILL.md | sort -u
```

#### 1.2 Extract reference cross-references

```bash
for ref in references/*.md; do
    grep -oP "references/[a-zA-Z0-9_-]+\.md" "$ref" | sort -u
done
```

#### 1.3 Extract script import relationships

```bash
grep -rn "import\|from " scripts/*.py | grep -v __pycache__
```

#### 1.4 Comparative analysis

Compare the file inventory with the reference inventory:
- In file inventory but not in reference inventory → candidate zombie
- In reference inventory but not in file inventory → missing file (error)

#### 1.5 Zombie cause analysis

For each candidate zombie, analyze:
1. **Explicitly superseded**: Does SKILL.md have "don't use X, use Y instead" phrasing?
2. **Made obsolete by simplified workflow**: Does it belong to a more complex multi-step workflow that has since been simplified?
3. **Development tool**: Is it a skill development/validation tool, not part of the production workflow?
4. **Content still valuable**: Read file contents, determine whether it contains unique information

### Classification Criteria

| Classification | Conditions | Action |
|---------------|-----------|--------|
| Safe to delete | Explicitly superseded (has replacement) or no references and no unique content value | Add to deletion list |
| Needs reference added | Content has unique value but SKILL.md doesn't reference it | Suggest adding reference in SKILL.md |
| Needs judgment | May still have value but uncertain | List content summary for user judgment |

## Check 2: Description Trigger Accuracy

### Evaluation Criteria

**Good description**:
- Starts with "Use when," describing trigger scenarios
- Includes specific user statement/context examples
- "What it does" is briefly summarized (1-2 sentences)
- Appropriate length (recommended <150 Chinese characters)

**Poor description**:
- Long paragraphs describing implementation details
- Includes script commands, parameter values
- Only describes "what it does" without "when to use"
- Too long (>200 characters)

### Check Method

1. Read SKILL.md frontmatter
2. Extract description field
3. Evaluate against criteria
4. If issues found, provide modification suggestions

## Check 3: SKILL.md Unnecessary Content

### Problem Patterns

#### 3.1 when-to-use repetition
**Pattern**: Body contains "When the user needs...use this skill" or similar
**Reason**: Skill is already activated, no need to repeat trigger conditions in body
**Action**: Delete the paragraph

#### 3.2 why explanations
**Pattern**: Body contains "because...therefore..." or "the purpose of this is..."
**Reason**: Skill describes how to complete the task, not why
**Action**: Delete why explanations, keep how steps

#### 3.3 version history
**Pattern**: Body contains "v1 used method X, v2 changed to method Y" or "original approach was A, optimized to B"
**Reason**: Skill should be a snapshot of the current best approach, without history
**Action**: Delete historical descriptions, keep only current approach

#### 3.4 iteration details
**Pattern**: Body contains "this optimization added X," "improved Y," "fixed Z"
**Reason**: Same as above
**Action**: Delete iteration details, keep only current implementation

### Check Method

Read SKILL.md body paragraph by paragraph, searching for keywords of the above patterns:
- "when the user needs," "use this skill," "trigger conditions"
- "because," "therefore," "purpose is," "in order to"
- "v1," "v2," "original approach," "before," "old version"
- "this optimization," "added," "improved," "fixed"

## Check 4: QA Layering Rationality

### Evaluation Criteria

**Good QA layering**:
```
Step 1: Generate background → Background QA (blocking, script-implemented)
Step 2: Generate containers → Container QA (blocking, script-implemented)
Step 3: Compose long image → Final QA (blocking, script-implemented)
```

**Poor QA layering**:
```
Step 1: Generate background
Step 2: Generate containers
Step 3: Compose long image
Step 4: Final QA (all checks stacked here, some described in text)
```

### Check Items

1. **Position**: Does each QA immediately follow its corresponding generation step?
2. **Layering**: Are there intermediate QAs (between steps) rather than all at the end?
3. **Blocking vs. advisory**: Is there a distinction between "must fix to continue" and "note but don't block"?
4. **Scripted**: Is QA implemented via scripts (e.g., `python3 scripts/xxx_qa.py`) rather than text descriptions (e.g., "check if X is Y")?

### Check Method

1. Extract all paragraphs in SKILL.md containing "QA," "check," or "verify"
2. Record each QA's position (after which step)
3. Check whether any QAs use only text descriptions
4. Check whether blocking vs. advisory distinction is made

## Check 5: Scriptability Potential

### Evaluation Criteria

**Content that should be scripted**:
- Parameter calculation (e.g., font size calculation, height estimation, spacing calculation)
- Rule checking (e.g., consistency validation, format validation, file existence checks)
- Instruction assembly (e.g., prompt template assembly, config file generation)
- Repetitive operations (e.g., batch rename, batch convert)

**Content that should NOT be scripted**:
- Creative decisions requiring AI judgment (e.g., visual scheme selection, content planning)
- Steps requiring user interaction (e.g., ask-user)
- One-time configuration (e.g., render_spec initial setup)

### Check Method

Read SKILL.md paragraph by paragraph, marking:
- Paragraphs containing specific parameter calculation formulas
- Paragraphs containing rule checking logic
- Paragraphs containing instruction template assembly
- Assess whether each marked paragraph could be replaced by a script

## Check 6: Content Redundancy

### Evaluation Criteria

**Redundant content**:
- SKILL.md reproduces detailed steps from references
- SKILL.md duplicates parameter details from references
- SKILL.md and references have the same content in different wording

**Non-redundant content**:
- SKILL.md briefly summarizes and points to references for details
- SKILL.md contains workflow overview, references contain step details
- Each location has unique content

### Check Method

1. Extract all file path references from SKILL.md
2. For each referenced file, compare SKILL.md content with the reference file content
3. Identify paragraphs with high overlap (>70% similar)
4. For each redundancy, provide specific comparison and retention recommendation

## Check 7: Pitfall Effectiveness

### Classification Criteria

| Pitfall Type | Characteristics | Recommended Action |
|-------------|----------------|-------------------|
| Can be QA-covered | The error described can be mechanically detected by a script (e.g., "don't change background color" → already checked by hard_contract audit) | Convert to QA gate, delete pitfall. QA scripts are proactive defense; pitfalls are passive reminders; when both overlap, keep QA |
| Describes constraint + solution | Pitfall includes problem description and solution (e.g., "float(v) doesn't support % → use value_label field") | Move into corresponding step or reference as a constraint. In-step constraints are visible during execution; pitfalls require the model to actively recall |
| Warning only, no solution | Pitfall only says "don't do X" without explaining the correct approach | Either supplement a solution and move into corresponding step, or delete. Warnings without solutions have no actionable guidance value for the model |

### Evaluation Dimensions

For each pitfall, evaluate:

1. **Has a solution**: Does it explain the correct approach, or just say "don't do X"?
2. **Can be QA-covered**: Is the error described already checked by a corresponding QA script?
3. **Duplicates reference/step**: Is the pitfall's content already described in the corresponding step or reference?
4. **Generalizable**: Is the pitfall a universal rule or specific to a single incident? If incident-specific, has the lesson been codified into step constraints or QA?
5. **Would the model naturally make this error**: Would a sufficiently intelligent model naturally make this error without this pitfall? If not, the pitfall is redundant.

### Check Method

1. Extract all pitfalls from SKILL.md (typically in "Common pitfalls" or "Notes" sections)
2. Evaluate each pitfall against the above 5 dimensions
3. Provide classification (can be QA-covered / describes constraint + solution / warning only) and handling recommendation (keep / convert to QA gate / move to step constraint / delete)
4. Provide rationale for each

## Check 8: Absolute Paths

### Core Principle

Skills need to be deployed and used in different environments. Any environment-bound absolute paths (containing usernames, session IDs, specific mount points like `/storage/`, `/home/`, `/usr/local/`) will cause the skill to fail in other environments. When referencing other skills, use `<skill_name_path>/relative_path` placeholders; don't hardcode paths.

### Evaluation Criteria

**Content that must NOT appear**:
- Any environment-bound absolute paths (e.g., `/storage/skills/...`, `/home/user/...`, `/usr/local/...`)
- Absolute paths containing usernames, session IDs, or other environment-specific info (e.g., `/storage/lixiang/h3m6g1sb6lmsmtla8k/...`)
- Environment absolute paths in any file: SKILL.md, references, scripts, prompts
- Hardcoded paths when referencing other skills (e.g., `python /storage/skills/image_gen/script.py`)

**Content that SHOULD appear**:
- When referencing other skills, use `<skill_name_path>/relative_path` placeholder, e.g., `python <image_gen_skill_path>/image_gen/script.py --mode file --prompt-file ...`
- When referencing this skill's directory, use `<current_skill_dir>`, e.g., `python <current_skill_dir>/scripts/xxx.py`
- When referencing working directory, use `<current_working_dir>`, e.g., `--output <current_working_dir>/outputs/xxx.png`
- Declare each placeholder's meaning and referenced skill names+functions in a path convention paragraph (e.g., "This skill calls the image generation script from the 'image_gen' skill, using `<image_gen_skill_path>` to denote that skill's directory")

### Placeholder Naming Convention

| Scenario | Placeholder | Description |
|----------|-----------|-------------|
| Reference this skill's directory | `<current_skill_dir>` | Refers to the directory containing the current skill |
| Reference current task working directory | `<current_working_dir>` | Refers to the current task's working directory |
| Reference other skill's scripts | `<skill_name_path>/relative_path` | e.g., `<image_gen_skill_path>/image_gen/script.py` |

### Check Method

1. Use grep to scan all `.py` and `.md` files in the skill directory for absolute paths:
   ```bash
   grep -rn "/storage/\|/usr/\|/home/\|/opt/" <skill_path> --include="*.py" --include="*.md" | grep -v __pycache__
   ```
2. For each match, determine:
   - Environment-bound absolute path → must replace
   - Reasonable system path (e.g., `#!/usr/bin/env python3`) → normal, no replacement needed
3. Check whether references to other skills use hardcoded paths instead of `<skill_name_path>` placeholder
4. Check placeholder naming consistency: this skill's directory uniformly uses `<current_skill_dir>`, working directory uniformly uses `<current_working_dir>`, other skills uniformly use `<skill_name_path>`
5. Check whether the path convention paragraph declares each placeholder's meaning and referenced skill names+functions
6. Check for residual environment-specific paths (e.g., containing usernames, session IDs)

### Replacement Suggestions

| Scenario | Should NOT Appear | Should Replace With |
|----------|------------------|-------------------|
| Reference other skill's script | `/storage/skills/image_gen/script.py` | `<image_gen_skill_path>/image_gen/script.py` |
| Reference this skill's directory | `/storage/lixiang/skills/xxx/` | `<current_skill_dir>` |
| Reference working directory | `/storage/lixiang/h3m6g1sb6lmsmtla8k/workspace/xxx/` | `<current_working_dir>` |
| Script docstrings/print statements | `/storage/skills/...` | `<skill_name_path>/...` or `<current_skill_dir>` |
| shebang line | `#!/usr/bin/env python3` | Normal, no replacement needed |
