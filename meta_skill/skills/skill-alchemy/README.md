# Skill Alchemy

> Turn raw conversation history into executable skills — not passive rules.

Skill Alchemy mines local AI conversation history for corrections and recurring failures, correlates them across sessions, and turns evidence-backed findings into skill updates.

You chat with AI every day. Those conversations pile up like ore in a mine. Skill Alchemy extracts the gold — the corrections you made that genuinely changed AI's direction — and forges them into skills with checklists, grep commands, and pass/fail criteria. Skills that trigger at the right moment, not rules that sit passively in a file.

Sits above [Memory Curator](#relationship-with-memory-curator). Curator manages memory files; Alchemy extracts gold from raw conversations.

---

## Why It Exists

You've felt this: **AI makes the same mistake across sessions.**

Last week you told it "start the service and test for real." This week it runs `pytest`, says "done," and you find the feature doesn't work. Last month you corrected "don't change unrelated code." This month it changes A and silently refactors B, C, D.

You corrected it. AI listened — for that session. Next session is a blank slate.

You might write it into AGENTS.md. But is that enough? We verified: **across 88 sessions, the user repeatedly demanded "start the service for real testing" — and that rule was already in AGENTS.md.** The rule exists; AI still doesn't follow it.

The gap: **"should do" ≠ "will do."** AGENTS.md says "verify before claiming done." But it doesn't say *when to trigger, what to check, how to check, what counts as pass.* AI reads the rule but doesn't know how to execute it.

Skill Alchemy closes that gap — **turning "should do" into "will do."**

---

## Workflow

The current workflow has one analysis path and seven phases:

1. Extract sessions into a unified JSONL format.
2. Select recent sessions as anchors; the default is last10.
3. Identify genuine corrections and effective guidance semantically.
4. Search related history across five correlation dimensions.
5. Cluster and generalize evidence.
6. Produce first-layer analysis artifacts and pass completeness QA.
7. Synthesize or update skills with `skill-creator`, then run skill validation.

Keyword matching may help locate candidate text during historical search, but it never determines whether a user turn is a correction.

### How It Works — Stage by Stage

**Stage 1 (Extract):** Every AI conversation is stored locally, but four CLI tools use completely different formats. `extract.py` is the mining machine — regardless of format, it digs out two things: **what you asked** and **what AI finally answered**. Tool calls, thinking, system injections — all discarded. Why only these two? Because judging "did AI do it right" only needs your input and AI's final reply. The intermediate process is noise.

**Stage 2 (Distill):** The mined ore can be 3,500+ turns — too much for AI to process at once. `distill.py` organizes it into readable batches. The insight: don't analyze everything — **anchor to current work, then trace backward.** If you're fixing an SSE bug, it searches history for "SSE", "compact", "streaming", finds the session where that code was originally written, and asks whether the bug could have been prevented at writing time.

**Stage 3 (Semantic Analysis):** This is the core — **no keyword matching, let AI judge for itself.** We tried keywords first. Result: 39% false positives. "Good, continue" was counted as a correction. "I think we should use B" was flagged — but AI was already using B. Now AI reads full conversations and classifies each user turn:

| Type | Meaning | Extract? |
|------|---------|:--------:|
| **Genuine correction** | AI was wrong, user pointed it out, AI actually changed direction | ✅ |
| **Effective guidance** | User provided a direction AI hadn't considered, AI adopted it | ✅ |
| **Redundant confirmation** | AI was already doing it, user merely confirmed | ❌ |
| **Pure progression** | "continue", "next step" | ❌ |

One criterion: **was AI's behavior before ≠ behavior after?** If yes, the correction was effective. If no, AI was already doing it — don't extract.

| Problem | Keyword Approach | AI Semantic Understanding |
|---------|-----------------|--------------------------|
| Redundant confirmations | "Good, continue" counted as correction | AI judges it was already doing it, skips |
| Corrections without signal words | Corrections without "wrong"/"should" missed | AI understands semantics, no keyword dependency |
| Fixed context window | Only looks at ±1 turn | AI reads full text, understands long-range changes |
| No effect verification | Only checks for context presence | AI compares before/after behavior direction |

**Stage 4 (Correlation):** This is what separates Skill Alchemy from "simple summarization." While analyzing the batch, if AI discovers a problem that may relate to other historical sessions, **it autonomously uses grep/read tools to search `output/extracted/` for more historical sessions**. What to search and how deep is entirely driven by AI's semantic understanding, unconstrained by predefined keywords.

**Stage 5 (Repeated Requirements):** Similar to Stage 4, AI autonomously searches historical sessions. But the purpose differs — Stage 4 discovers correlations between problems and optimizations; Stage 5 validates **whether the same constraint was repeatedly stated by the user across sessions and AI actually erred**. Three conditions, ALL must be met: (1) you stated a constraint in some turn, (2) you re-stated it in a later turn or session, (3) between the two, AI actually violated it. **Only counts if AI actually erred.**

**Stage 6 (Forging):** The final stage — forge rules into skills. Rules say "should verify before claiming done." Skills say: trigger when AI is about to say "done", check if the service is running (`curl http://localhost:port/health`), check if you sent a real request (not just pytest), check if UI changes have actual rendered output, check if you tested downstream module B that calls changed module A, check if service was restarted after code changes, check if test cases are complex enough. **ALL ✅ before saying "done."** Rules are passive; skills trigger at the right moment with executable steps.

---

## Supported Sources

| Tool | Default storage |
|---|---|
| Kimi Code | `~/.kimi-code/sessions/*/session_*/agents/main/wire.jsonl` |
| Codex CLI | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` |
| Claude Code | `~/.claude/projects/*/*.jsonl` |
| Hermes Agent | `~/.hermes/sessions/*.json` |

## Quick Start

Run commands from this directory:

```bash
python3 scripts/extract.py \
  --tool all \
  --min-turns 3 \
  --output output/extracted \
  --format jsonl

python3 scripts/distill.py output/extracted -o output/run
```

The default anchor size is 10. Select a different positive value when the sessions are unusually short, long, or topically dense:

```bash
python3 scripts/distill.py output/extracted -o output/run --recent 20
```

If the requested value exceeds the available session count, all available sessions are used. Zero and negative values are rejected.

`distill.py` automatically validates the generated files. You can rerun the same check explicitly:

```bash
python3 scripts/validate_run.py output/run
```

## Generated Files

The organizer produces:

```text
output/run/
├── anchor_recent.md
├── session_index.md
└── ANALYSIS_INSTRUCTION.md
```

The analysis then produces two layers:

```text
output/run/
├── action-guides/
├── error-patterns/
├── repeated-requirements/
├── conflicting-requirements/
├── related-findings/
└── skill-synthesis/
```

The first five directories contain evidence and analysis. `skill-synthesis/` is created only after the first layer passes its completeness gate.

Validate the first layer before synthesis:

```bash
python3 scripts/validate_run.py output/run --first-layer
```

## Correlation Dimensions

- historical root-cause tracing;
- related module and project analysis;
- pattern and optimization propagation;
- repeated requirement validation;
- existing rule and skill effectiveness.

Every cross-session conclusion must cite each source session and turn separately. Similar project names do not permit session merging.

### Detailed Explanations with Real Examples

Isolated per-session analysis yields isolated lessons. AI's self-directed correlation of sessions reveals deeper patterns:

#### Backward Root-Cause Tracing (look to the past)

AI discovers a bug fix in the current session, then autonomously searches history for the session where that code was originally written. Found it? Then: **was there a signal at writing time that could have prevented this bug?** If yes, distill into "coding-time prevention guide."

Real example from our data: A "tool name duplication" bug (`bash` → `bashbash`). Root cause: LangChain's `merge_dicts` already concatenates string fields, but the implementer used `+=` again. If they had read the upstream merge logic (5 minutes), this would never have happened. Instead, the same class of bug appeared in 4 different modules over 30+ sessions — a single merge-semantics audit after the second occurrence would have prevented all the rest.

#### Related Module and Project Analysis (look sideways)

AI discovers a problem in module A, then autonomously searches: **does module B have the same problem?** Same developer, same patterns, same blind spots.

Real example: "environment confusion" — SproutHarness had 6 independent environment-mapping implementations, all with different bugs. Fixing one didn't fix the others because nobody checked.

#### Pattern and Optimization Propagation (look to the future)

AI discovers an optimization in the current session, then autonomously searches: **can this optimization spread to related modules?**

Real example: One session introduced `normalize_env()` as a single environment detection function. Three other projects independently implemented their own — if `normalize_env()` had been promoted to a shared utility, those projects would have been a one-line import instead of multi-file refactoring.

#### Repeated Requirement Validation

AI identifies constraints from anchor sessions, then autonomously uses grep to search all historical sessions for the same constraint, and verifies whether AI actually made related errors.

Across 477 sessions, we found 8 high-frequency repeated requirements:

| Repeated Constraint | Sessions | AI Erred Each Time | Already in AGENTS.md? |
|---------------------|:--------:|:------------------:|:---------------------:|
| Start real service, not just pytest | 88 | ✅ | ✅ (but still violated) |
| Simplify, don't over-engineer | 30 | ✅ | ✅ |
| Plan before coding | 28 | ✅ | ✅ |
| Diagnose before fixing | 23 | ✅ | ⚠️ Partial |
| Only change what's asked | 23 | ✅ | ✅ |
| Confirm environment (local/test/prod) | 34 | ✅ | ✅ |
| Wait for user confirmation before commit | 12 | ✅ | ✅ |
| Root-cause fix, not patch | 3 | ✅ | ✅ |

**All 8 already exist in AGENTS.md. AI still violates them.** Rules exist; enforcement is insufficient. This dimension doesn't just find "what AI does wrong" — it finds **"what AI was corrected for but still does wrong again"** — a direct effectiveness test of existing rules.

#### Existing Rule and Skill Effectiveness

This dimension checks whether rules already written in AGENTS.md or existing skills actually prevent the errors they target. The repeated-requirement table above is the proof: all 8 constraints have AGENTS.md entries, yet AI continues to violate them across sessions. This validates the core thesis — **writing rules is necessary but not sufficient; rules need to be forged into executable skills with triggers, checklists, and pass/fail criteria.**

In the worst case (Session 242/243), the user had to say "don't commit, only check" **three consecutive times** (turns 6, 7, 8) because AI kept trying to commit.

---

## Experiment Results

We ran two rounds of experiments to validate the approach.

### Round 1: Different Session Counts (1 / 5 / 10)

**Goal**: Determine how many sessions are needed for effective distillation, and compare keyword matching vs. AI semantic understanding.

**Setup**: Tested with 1, 5, and 10 sessions across three CLI tools (Kimi Code, Codex, Claude Code). All three groups used **standard mode** (full batched analysis) — meaning all sessions were fed to AI as input for analysis. This is different from related-analysis mode, where only recent N sessions serve as anchors and the rest are searched on demand.

**What this experiment actually tests**: the effect of **input volume** on principle quality. It does NOT test the effect of correlation search range — that was Round 2.

#### Extraction Results

| Metric | 1 Session | 5 Sessions | 10 Sessions |
|--------|-----------|------------|-------------|
| Total turns | 167 | 538 | 860 |
| Signal matches (keyword) | 31 | 149 | 151 |
| AI-identified real corrections | 35 | 52 | 73 |
| False positive rate (keyword) | ~39% | ~39% | ~39% |

> **Note**: Keyword matching numbers (31/149/151) are from the earlier `scan.py` approach which has since been removed. AI-identified correction numbers (35/52/73) are from sub-agent analysis of batch files. The exact numbers may shift slightly on re-run, but the proportional relationship (AI semantic analysis < keyword matching due to false-positive filtering) and all core conclusions hold.

**Key finding**: AI semantic analysis consistently filtered out ~39% false positives that keyword matching would have included. AI also caught corrections that had no signal words at all.

#### What Each Scale Produces

| Scale | Correction Types Covered | Guide Specificity | Recommendation |
|-------|:------------------------:|:-----------------:|----------------|
| 1 session | 4/6 types | Project-specific, not generalizable | For testing only |
| **5 sessions** | **5/6 types** | **Generalizable across projects** | **Sweet spot** |
| 10 sessions | 5/6 types | Marginal improvement over 5 | Diminishing returns |

**5 sessions is the sweet spot** — enough to cover multiple projects and tools, diverse correction types, but not so much that analysis becomes redundant.

#### Window Size Doesn't Just Affect Quantity — It Changes Principle Quality

This is often overlooked: different window sizes don't produce "more or fewer principles" — they produce **principles of different quality and nature**.

| Dimension | 1 Session | 5 Sessions | 10 Sessions |
|-----------|-----------|------------|-------------|
| **Correction type coverage** | 4/6 types | 5/6 types | 5/6 types |
| **Principle generalizability** | All from one project, can't generalize | Cross-project validated, generalizable | Same as 5 |
| **Error pattern recognition** | Only sees "this time was wrong" | Can see "this pattern repeats across projects" | Can confirm "this pattern is systemic" |
| **Actionability** | Biased toward project-specific operations | Extracts cross-scenario executable checklists | Same as 5, marginal gain |
| **Overfitting risk** | High — may treat project-specific conventions as universal principles | Low — multi-project cross-validation filters project noise | Low, but limited new information |

**Key finding**: Principles from 1 session look reasonable but are essentially overfitted — they mistake "this project's specific convention" for "AI's universal error pattern." Only cross-validation across 5+ sessions and multiple projects can distinguish "project-specific knowledge" from "general behavior guide." And 10 sessions vs. 5 mainly adds repetitive corrections from similar project types — after clustering, no new principle entries are generated.

#### What Keyword Matching Missed (AI Found)

1. "Forgot to restart service after code changes" — no signal word, but AI semantics caught it
2. "Command doesn't work on target environment" (docker compose vs docker-compose) — no "wrong" keyword
3. "Give options instead of just executing" — user said "just deploy it, don't give me choices"
4. "Claimed localization done but only changed main file" — no signal word
5. "Built feature but didn't wire into product entry point" — no signal word
6. "Core goal drifted without AI noticing" — gradual drift, not a single correction

#### What Keyword Matching Falsely Included (AI Filtered)

1. "Good, please write the progress doc" — AI was already writing docs, user just confirmed direction
2. "Yes, I think L1 and L3 should also be stored" — AI's prior solution already included L1/L3
3. "A few suggestions, I think charts should go in HTML" — AI had already proposed similar
4. "Continue, but note each step needs complete testing" — first half is progression, second half is constraint

### Round 2: Related-Session Correlation

**Goal**: Test whether cross-session correlation reveals insights that isolated analysis misses.

**Setup**: Used recent 5 sessions as anchors, searched 472 historical sessions for related content via keywords and project matching. AI performed three-dimensional correlation analysis.

**Relationship to Round 1**: Round 1 tested "how much input volume affects principle quality" (standard mode, all sessions fed as input). Round 2 tests "whether correlation search changes principle nature" (related mode, only 5 sessions as input + historical sessions searched on demand). The key difference: Round 1's 10-session group fed all 10 sessions to AI; Round 2's approach only feeds 5 sessions to AI but searches 472 historical sessions for correlation evidence. This is more efficient (smaller input → lower token cost) and more targeted (search is driven by current work context, not random inclusion).

#### Why Correlation Matters — The Principle

Sessions are not isolated logs. They have three types of structural relationships. Leveraging these relationships reveals patterns that single-session analysis can never discover:

**Temporal correlation (past → present)**: A causal link exists between the "coding session" and the "fixing session" for the same code. If the bug had been prevented at coding time, the fixing session wouldn't need to exist at all. This correlation answers "could this bug have been prevented at the source" — a question single-session analysis can't answer because it requires seeing both the coding and fixing sessions simultaneously.

**Spatial correlation (here → there)**: Different modules from the same developer, same project, or same architecture pattern often share the same blind spots. A bug in module A likely exists in module B too. This correlation answers "is this problem systemic" — single-session analysis only sees "fixed A," not "do B/C/D have the same hole."

**Solution correlation (this method → that method)**: An optimization, architecture pattern, or verification method from one module can often be transferred to other modules. This correlation answers "can this optimization propagate" — single-session analysis only sees "did it in this module," not "other modules could use the same approach."

These three correlations are not "searching more sessions" — they leverage the **structural relationships** between conversations to discover patterns invisible to single-session analysis. Without correlation, you only see "what happened this time." With correlation, you see "under what conditions this class of problem occurs and how to prevent it systemically."

#### Backward Tracing Findings

| Bug | Original Session | Could Have Been Prevented? | Signal Missed |
|-----|-----------------|:------------------------:|---------------|
| Tool name duplication (bashbash) | Session where merge logic was written | ✅ | LangChain `merge_dicts` source code |
| Network error during long bash | Session where SSE heartbeat was implemented | ✅ | Git log entry of prior heartbeat fix |
| Compact token counting chain | Session where compact hook was integrated | ✅ | State writeback integration gap |

**Key insight**: All 3 bugs had clear preventive signals at coding time. If the original implementer had checked one more thing (upstream merge logic, git history, integration endpoint), the bug would never have existed.

#### Lateral Migration Findings

| Systemic Pattern | Modules Affected | Sessions Wasted |
|-----------------|:----------------:|:---------------:|
| Streaming message duplication | 4 independent modules | 30+ |
| Environment confusion | 6 independent implementations | 34+ |
| `finish_reason` anomaly handling | 5 sessions | 5+ |
| Fix recurrence (declared fixed but came back) | 4 bugs | 12+ |

**Key insight**: The streaming duplication bug was treated as 4 separate incidents. In reality, it was one disease — inadequate merge semantics. Fixing them one at a time over 30 sessions cost enormous time; a single merge-semantics audit after the second occurrence would have prevented the rest.

#### Optimization Propagation Findings

| Optimization | Origin | Could Spread To |
|-------------|--------|----------------|
| `normalize_env()` | SproutHarness session | ThinkSkillsHub, poster, image-studio, hermes |
| ContextVar structured logging | SproutHarness session | poster, ThinkSkillsHub, hermes |
| Agent effect testing protocol | SproutHarness session | poster, ThinkSkillsHub, mcp_checker |
| StreamBridge SSE design | SproutHarness session | DingTalk adapter, Dify plugin |
| Conversation compression pipeline | This project (turtle_skill) | SproutHarness memory system |

**Key insight**: The conversation compression pipeline (this very project) is the missing automation layer for the memory system designed in SproutHarness. The two were developed independently — correlation analysis revealed they should be connected.

#### What Correlation Reveals That Isolated Analysis Misses

| Dimension | Isolated Analysis Sees | Correlation Analysis Adds |
|-----------|----------------------|--------------------------|
| Problem frequency | Each session's corrections independently | Workspace bug reported 3 times before fix; "patch-first" across 3 projects — systemic, not incidental |
| Architecture similarity | Each session's technical issues look unrelated | "Dual source of truth" anti-pattern in 3 modules — one lesson could prevent the others |
| Verification method chain | User's verification demand in one session | "Real case reproduction", "plan before code" demanded across multiple sessions — AI won't do it spontaneously |
| Skill motivation | AGENTS.md rules exist independently | "Fix plan review" skill was created because of repeated corrections across sessions — rules aren't theoretical |
| Missed fix risk | Only sees current session's problems | Session 21 identified root cause but didn't fix — if it had, Session 3's 18-turn conversation wouldn't have been needed |

#### How Correlation Fundamentally Changes Principle Nature

This must be emphasized: correlation analysis doesn't just "find more problems" — it **changes the nature of the principles themselves**.

Take "patch-style fixing" as an example. In isolated analysis, it's just a rule: "AI tends to patch instead of fixing root causes." But in correlation analysis, when we see the same pattern corrected by users across 3 different projects (SproutHarness, pptx-composer, poster), it upgrades from "an individual correction in some session" to **"a systemic behavioral deficit in AI."**

| Same Principle | Isolated Analysis Statement | Correlation Analysis Statement |
|---------------|----------------------------|-------------------------------|
| Patch-style fixing | "AI tends to patch rather than fix root cause" | "AI's patch-first tendency is a cross-project systemic behavioral deficit; user created a dedicated 'fix plan review' skill to constrain it — AGENTS.md rules alone are insufficient" |
| Insufficient acceptance | "AI claims done but has problems" | "AI's acceptance downgrade recurred across 88 sessions, even with AGENTS.md rules in place — needs stronger executable gate skills" |
| Streaming message duplication | "Fixed streaming message duplication bug" | "Same merge semantics flaw appeared in 4 independent modules over 30+ sessions — fixing one by one is less effective than a single audit; this is a bug class, not a single bug" |

**Key finding**: Correlation analysis upgrades principles from "describing symptoms" to "revealing essence." Isolated analysis tells you "what AI did wrong." Correlation analysis tells you "whether the error is systemic or incidental, whether existing rules are effective, and whether a skill or a rule is the right constraint." This nature change directly determines the output form — a passive rule or an executable skill with triggers and checklists.

### Repeated-Requirement Validation

The repeated-requirement dimension was validated separately across all 477 sessions:

| Constraint | Search Keywords | Sessions Hit | AI Errors Confirmed | High-Priority? |
|-----------|----------------|:-----------:|:-------------------:|:--------------:|
| Real service testing | "启动服务", "start service", "端到端" | 88 | 3+ confirmed | ✅ |
| Don't commit yet | "不要提交", "先别提交", "don't commit" | 12 | 6+ confirmed | ✅ |
| Minimal scope | "只改", "不要修改", "撤回" | 23 | 3+ confirmed | ✅ |
| Environment confusion | "测试环境", "生产环境", "local" | 34 | 4+ confirmed | ✅ |
| Diagnose before fix | "先定位", "先不要修复", "locate" | 23 | 4+ confirmed | ✅ |
| Plan before code | "先出方案", "先写文档", "plan first" | 28 | 4+ confirmed | ✅ |
| Simplify | "简化", "太复杂", "simplify" | 30 | 3+ confirmed | ✅ |
| Root cause not patch | "根因", "补丁", "root cause" | 3 | 2 confirmed | Medium |

**Critical finding**: All 8 constraints already have corresponding entries in AGENTS.md. AI continues to violate them. This proves that **writing rules is necessary but not sufficient** — rules need to be forged into executable skills with triggers, checklists, and pass/fail criteria.

---

## Why This Is More Effective Than Alternatives

### vs. Keyword Matching

Keyword matching was our first approach. It failed on two fronts:
- **39% false positives**: "Good, continue" and "I think we should use B" (when AI was already using B) were counted as corrections
- **Missed real corrections**: "Forgot to restart service" has no signal word but is a real AI failure

AI semantic understanding fixes both: it understands context, compares before/after behavior, and only extracts corrections that actually changed AI's direction.

### vs. Per-Session Independent Analysis

Analyzing each session independently yields per-session lessons. But:
- It can't tell that the same bug was reported 3 times before being fixed
- It can't tell that the same anti-pattern exists in 4 modules
- It can't trace a bug back to its origin and ask "could this have been prevented?"

Cross-session correlation analysis reveals these systemic patterns — the difference between "fixing a bug" and "eliminating a bug class."

### vs. Writing Rules in AGENTS.md

AGENTS.md rules are necessary but insufficient. Our data proves it:
- 88 sessions of "start the service for real testing" — rule already in AGENTS.md
- 30 sessions of "simplify" — rule already in AGENTS.md
- 23 sessions of "only change what's asked" — rule already in AGENTS.md

Rules say "should." Skills say "how." Rules are passive text. Skills are executable checklists that trigger at the right moment with grep commands, pass/fail criteria, and structured reports.

**Skill Alchemy's output isn't more rules — it's skills that enforce rules.**

### vs. Manual Skill Creation

Manual skill creation works but:
- It's slow — you have to remember what went wrong and write it up
- It's incomplete — you remember the last incident, not the pattern across 30 sessions
- It's subjective — you write what bothered you most, not what the data shows is highest-frequency

Skill Alchemy processes 477 sessions systematically, clusters by frequency, and prioritizes by impact. The 4 skills it generated cover 100% of the 8 highest-frequency correction patterns.

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

All findings are grounded in real conversation evidence — nothing fabricated. Every guide, pattern, and skill references its source sessions and frequency.

---

## Skill Coverage

After Skill Alchemy ran, the resulting skills cover the full development workflow:

```
Requirement received → simplification_gate (should we do this? can it be simpler?)
                      → change_scope_control (which files? confirm scope)
                      → fix_plan_review (is the plan sound?)
                      → [Implementation]
                      → issue_triage_gate (bug found? diagnose first)
                      → code_fix_acceptance (fix done? verify properly)
                      → pre_completion_gate (claiming done? pass the gate)
                      → pre_commit_doc_rescan (committing? docs synced? user authorized?)
```

10 skills, each with trigger conditions, executable checklists, grep commands, and pass/fail criteria. Covering 100% of the 8 highest-frequency correction patterns and 96% of AGENTS.md guidelines.

**No additional skills needed** — 10 skills cover the full chain from "requirement received" to "commit complete." Continuing to add more has diminishing returns.

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

Curator ensures memory files don't bloat, don't expire incorrectly, and follow format conventions. Alchemy goes deeper — it reads raw conversations, identifies what AI keeps getting wrong, and forges that into skills that prevent recurrence.

They operate at different layers:
- **Curator** = file system management (CRUD on memory files)
- **Alchemy** = semantic analysis (what do conversations teach us?)

---

## Dependencies

- Python 3.7 or newer;
- `rg` for the documented manual search examples, or an equivalent text-search tool;
- at least one supported CLI tool with local session history.
