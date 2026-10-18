# 🧪 Skill Alchemy

> Turn raw conversation history into executable skills — not passive rules.

You chat with AI every day. Those conversations pile up like ore in a mine. Skill Alchemy extracts the gold — the corrections you made that genuinely changed AI's direction — and forges them into skills with checklists, grep commands, and pass/fail criteria. Skills that trigger at the right moment, not rules that sit passively in a file.

This repository contains Skill Alchemy itself (the meta-skill) and the 9 skills it has forged from real conversations.

---

## The Problem

You've felt this: **AI makes the same mistake across sessions.**

Last week you told it "start the service and test for real." This week it runs `pytest`, says "done," and the feature doesn't work. Last month you corrected "don't change unrelated code." This month it changes A and silently refactors B, C, D.

You corrected it. AI listened — for that session. Next session is a blank slate.

You might write it into AGENTS.md. But is that enough? We verified: **across 88 sessions, the user repeatedly demanded "start the service for real testing" — and that rule was already in AGENTS.md.** The rule exists; AI still doesn't follow it.

The gap: **"should do" ≠ "will do."** AGENTS.md says "verify before claiming done." But it doesn't say *when to trigger, what to check, how to check, what counts as pass.* AI reads the rule but doesn't know how to execute it.

Skill Alchemy closes that gap — **turning "should do" into "will do"** by forging rules into executable skills.

---

## How It Works

Six stages, like an alchemy pipeline:

```
Raw Conversations                    Executable Skills
─────────────────                     ──────────────────
                    ┌──────────┐
  Kimi Code ──────▶│  Extract  │  Parse 3 CLI tools' session
  Codex CLI ──────▶│  (mine)   │  formats into user-assistant pairs
  Claude Code ────▶└─────┬─────┘
                         │
                  ┌──────▼──────┐
                  │  Organize   │  Batch into AI-readable format
                  │  (sort)     │  + keyword search for initial leads
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  Analyze    │  AI reads conversations, identifies
                  │  (identify) │  genuine corrections (no keywords!)
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  Correlate  │  AI self-directed search: trace
                  │  (connect)  │  root causes, migrate, propagate
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  Track      │  Find constraints AI keeps
                  │  (repeated) │  violating across sessions
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  Forge      │  Turn rules into executable skills
                  │  (skills)   │  with triggers, checklists, gates
                  └─────────────┘
```

### Key Innovation: AI Semantic Analysis (Not Keywords)

We tried keywords first. Result: 39% false positives. "Good, continue" was counted as a correction. "I think we should use B" was flagged — but AI was already using B.

Now AI reads full conversations and judges for itself: **was AI's behavior before ≠ behavior after?** If yes, the correction was effective. If no, AI was already doing it — don't extract.

### Key Innovation: Cross-Session Correlation

Sessions are not isolated logs. They have structural relationships:

- **Temporal** (past → present): trace bug fixes back to coding sessions — could the bug have been prevented at writing time?
- **Spatial** (here → there): check whether the same problem exists in other modules
- **Solution** (this method → that method): check whether an optimization can spread to related modules

This reveals patterns invisible to single-session analysis — like a streaming bug that appeared in 4 independent modules over 30+ sessions, which was actually one disease treatable by a single merge-semantics audit.

---

## Forged Skills (The Output)

Skill Alchemy processed 240 sessions, 3,531 turns, 675 user corrections. Here's what it forged — 9 skills covering the full development workflow, ordered by when they trigger:

```
Requirement → simplification_gate → change_scope_control → fix_plan_review → design_doc_review
            → [Implementation]
            → issue_triage_gate → code_fix_acceptance → pre_completion_gate
            → pre_commit_doc_rescan
            → skill_health_check (meta: for creating/auditing skills)
```

| # | Skill | Trigger Moment | What It Does | Source |
|---|-------|----------------|-------------|:------:|
| 1 | [simplification_gate](skills/simplification_gate/) | Before designing | Necessity challenge, reuse-first, simplest approach, complexity budget | 30 sessions |
| 2 | [change_scope_control](skills/change_scope_control/) | Before coding | Confirm file list, exclude "while I'm at it", check existing impl, confirm environment, check compatibility | 57 sessions |
| 3 | [fix_plan_review](skills/fix_plan_review/) | When proposing solution | 6-dimension risk review + supplementary checks (scope necessity, dual-system, measurement, goal alignment) | 28 sessions |
| 4 | [design_doc_review](skills/design_doc_review/) | After writing design doc | 9-dimension review: completeness, clarity, implementability, simplicity, dual-system, real measurement | 271 sessions |
| 5 | [issue_triage_gate](skills/issue_triage_gate/) | When bug reported | Symptom documentation, root-cause tracing, impact scope, architecture prevention, lateral search | 23 sessions |
| 6 | [code_fix_acceptance](skills/code_fix_acceptance/) | After fix complete | 3-step acceptance + 11 production-omission principles + visual/entry-point/goal-alignment checks | 88 sessions |
| 7 | [pre_completion_gate](skills/pre_completion_gate/) | Before saying "done" | 6 gate checks: service running? real request? visual output? adjacent modules? restarted? test complexity? | 88 sessions |
| 8 | [pre_commit_doc_rescan](skills/pre_commit_doc_rescan/) | Before git commit | 4+4 checks: doc sync + commit authorization + file completeness + localization + artifact cleanup | 12 sessions |
| 9 | [skill_health_check](skills/skill_health_check/) | After skill creation | 10-point audit: zombie files, description, QA layering, scriptability, redundancy, paths, localization, command compat | 30 sessions |

### The Meta-Skill

| Skill | Trigger | What It Does |
|-------|---------|-------------|
| [skill-alchemy](meta_skill/skills/skill-alchemy/) | `distill conversations` | Extract gold from conversations, forge into skills. 8-phase pipeline. Sits above Memory Curator. |

> 📖 **Full story**: Read the [Skill Alchemy README](meta_skill/skills/skill-alchemy/README.md) (EN) or [中文说明](meta_skill/skills/skill-alchemy/README_ZH.md) for the complete 6-stage pipeline, experiment results, and design rationale.

---

## Real-World Results

From 240 sessions, 3,531 turns, 675 user corrections:

| Output | Count |
|--------|:-----:|
| Action guides (6 categories) | 25 |
| AI error patterns | 18 |
| Repeated user requirements (high-priority) | 8 |
| Cross-module systemic issues | 4 |
| Preventable bugs (backward tracing) | 3 |
| Optimization propagation opportunities | 5 |
| New skills forged | 4 |
| Existing skills enhanced | 5 (19 addon checks + 15 updates) |

**100% coverage** of the 8 highest-frequency correction patterns. **96% coverage** of AGENTS.md guidelines. 9 skills cover the full development workflow with zero gaps.

---

## Key Finding: Rules Are Not Enough

The most important discovery from analyzing 477 sessions:

| Constraint User Repeatedly Stated | Sessions | AI Still Erred | Already in AGENTS.md? |
|------------------------------------|:--------:|:--------------:|:---------------------:|
| Start real service, not just pytest | 88 | ✅ | ✅ (but still violated) |
| Simplify, don't over-engineer | 30 | ✅ | ✅ |
| Plan before coding | 28 | ✅ | ✅ |
| Diagnose before fixing | 23 | ✅ | ⚠️ Partial |
| Only change what's asked | 23 | ✅ | ✅ |
| Confirm environment (local/test/prod) | 34 | ✅ | ✅ |
| Wait for user confirmation before commit | 12 | ✅ | ✅ |
| Root-cause fix, not patch | 3 | ✅ | ✅ |

**All 8 rules already existed in AGENTS.md. AI still violated them.** Rules say "should." Skills say "how." This is why Skill Alchemy forges rules into executable skills with triggers, checklists, and pass/fail criteria.

---

## Quick Start

### Use the Skills

```bash
# Clone the repository
git clone git@github.com:DSXiangLi/Skill-Alchemy.git
cd Skill-Alchemy

# Copy skills to your CLI tool's skill directory
cp -r skills/* ~/.codex/skills/        # Codex
cp -r skills/* ~/.kimi-code/skills/     # Kimi Code
cp -r skills/* ~/.claude/skills/        # Claude Code
```

Skills auto-activate based on trigger words in your conversation. No manual invocation needed.

### Run Skill Alchemy on Your Own Conversations

```bash
# 1. Extract conversations from all CLI tools
python3 meta_skill/skills/skill-alchemy/scripts/extract.py \
  --tool all --min-turns 3 --output output/extracted --format jsonl

# 2. Organize into batches (related-analysis mode recommended)
python3 meta_skill/skills/skill-alchemy/scripts/distill.py \
  output/extracted -o output/batches --mode recent --recent 5

# 3. AI reads batches and analyzes
#    Read anchor_recent.md + session_index.md
#    Identify genuine corrections / effective guidance
#    Perform correlation analysis
#    Detect repeated requirements
#    Forge into executable skills
```

### Audit Your Own Skills

```bash
python3 skills/skill_health_check/scripts/zombie_detector.py <your_skill_path> --print
```

Then ask your AI: *"Run a health check on this skill"* — it will follow the full 10-point audit.

---

## Project Structure

```
Skill-Alchemy/
├── meta_skill/                      # THE CORE: meta-skills that create skills
│   └── skills/
│       └── skill-alchemy/           # Extract gold from conversations → forge into skills
│           ├── SKILL.md              # 8-phase pipeline definition
│           ├── scripts/
│           │   ├── extract.py        # Parse 3 CLI tools' session formats
│           │   └── distill.py        # Organize into AI-analyzable batches
│           ├── README.md            # Full story (EN)
│           └── README_ZH.md         # Full story (中文)
│
├── skills/                          # FORGED OUTPUT: quality gate skills
│   ├── simplification_gate/         # Anti-over-engineering gate (30 sessions)
│   ├── change_scope_control/        # Scope control gate (57 sessions)
│   ├── fix_plan_review/             # Solution risk review (28 sessions)
│   ├── design_doc_review/           # Design document review (9 dimensions)
│   ├── issue_triage_gate/           # Bug triage before fixing (23 sessions)
│   ├── code_fix_acceptance/         # Post-fix acceptance gate (88 sessions)
│   ├── pre_completion_gate/         # Pre-"done" verification gate (88 sessions)
│   ├── pre_commit_doc_rescan/       # Pre-commit doc sync gate (12 sessions)
│   └── skill_health_check/          # Skill quality audit (10-point)
│
├── AGENTS.md                        # AI behavioral guidelines (from real corrections)
├── README_ZH.md                     # 中文说明
└── docs/                            # Research & design documents
```

---

## Origin Story

This project started with a simple question: **why does AI keep making the same mistakes?**

We had AGENTS.md rules. We had design docs. We had code reviews. Yet across 240 sessions, the same 8 failure patterns kept recurring — 88 times for "didn't start the service" alone.

The answer: rules are passive. They say "should" but don't enforce. Skills are active — they trigger at the right moment, run grep commands, check pass/fail criteria, and produce structured reports.

So we built Skill Alchemy: a meta-skill that reads your conversation history, identifies what AI keeps getting wrong, and forges those lessons into executable skills. The 9 skills in this repository are its output — each one traces back to real corrections in real sessions.

They're not theory. They're scar tissue, systematically extracted and forged into tools.

---

## Relationship with Memory Curator

```
Memory Curator (the Steward)              Skill Alchemy (the Alchemist)
────────────────────────────              ────────────────────────────────
Manages memory files                      Extracts gold from raw conversations
Maintenance, cleanup, expiry              Corrections → Rules → Executable skills
"Are memory files healthy?"               "Is AI actually learning?"
Daily operations                           Periodic deep distillation
```

Curator manages memory files (CRUD). Alchemy reads raw conversations and forges them into skills. Different layers, complementary roles.

---

## Contributing

Found a recurring AI failure pattern? Two ways to contribute:

### Option 1: Let Skill Alchemy find it

Run Skill Alchemy on your conversation history. It will systematically scan all sessions, cluster by frequency, and surface patterns you might have missed.

### Option 2: Build a skill manually

1. Identify the specific incident and root cause
2. Define the systematic check that would prevent recurrence
3. Separate deterministic logic (script) from judgment-based logic (SKILL.md)
4. Test against real scenarios until the skill reliably catches the pattern
5. Run `skill_health_check` to audit the result

---

## License

MIT
# skill_alchemy
