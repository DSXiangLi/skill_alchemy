# 🧪 Skill Alchemy（技能炼金术）

> 从原始对话中提炼可执行技能——不是被动规则。

你每天都在跟 AI 聊天写代码，对话记录堆成山。Skill Alchemy 从这些"废矿"里提炼"金子"——你反复纠正 AI 的经验——锻造成带检查清单、grep 命令和通过/失败标准的技能。技能会在关键时刻主动触发，而不是像规则一样被动躺在文件里。

本仓库包含 Skill Alchemy 本身（元技能）和它从真实对话中锻造出的 9 个技能。

---

## 问题

你一定有过这种感觉：**AI 在不同 session 中犯同样的错。**

上周你跟它说"改完要启动服务测试"，这周它又只跑了 pytest 就说"完成了"。上个月你纠正"不要顺手改无关代码"，这个月它改 A 顺手又把 B/C/D 也改了。

你纠正了，AI 当时听了，下次对话全忘了——因为每次新 session 都是白纸一张。

你可能会想写进 AGENTS.md，但写进去就够了吗？我们验证过：**88 个 session 中，用户反复要求"启动服务真实验证"——而这条规则已经写在 AGENTS.md 里了。** 规则存在，AI 依然不遵守。

原因很简单：**"应该做"不等于"会做"。** AGENTS.md 写的是"要验证"，但没写"什么时候触发、检查什么、怎么检查、什么算通过"。AI 读了规则，但不知道怎么执行。

Skill Alchemy 解决的就是这个断层——**把"应该做"变成"会做"**，把规则锻造成可执行技能。

---

## 工作原理

六道工序，像一座炼金工厂：

```
原始对话                              可执行技能
─────────────                        ──────────────
                    ┌──────────┐
  Kimi Code ──────▶│  挖矿     │  解析 3 种 CLI 工具的
  Codex CLI ──────▶│  (extract)│  session 格式为 user-assistant 对
  Claude Code ────▶└─────┬─────┘
                         │
                  ┌──────▼──────┐
                  │  选矿       │  组织成 AI 可读批次
                  │  (distill)  │  + 关键词搜索提供初始线索
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  识金       │  AI 通读对话，识别真正纠正
                  │  (analyze)  │  （不用关键词！）
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  关联       │  AI 自主搜索历史 session：
                  │  (correlate)│  追溯根因、迁移同类、扩散优化
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  追查       │  找出 AI 反复违反的约束
                  │  (track)    │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  锻造       │  把规则锻造成带触发条件、
                  │  (forge)    │  检查清单、门禁的技能
                  └─────────────┘
```

### 核心创新：AI 语义分析（不用关键词）

我们一开始试过关键词。结果 39% 是误报：用户说"很好继续"被当成纠正；用户说"我认为应该用 B"被标记，但 AI 之前已经在用 B 了。

现在 AI 通读对话自己判断：**纠正前 AI 的行为 ≠ 纠正后 AI 的行为？** 变了才算真正纠正；没变说明 AI 本来就在做，不提取。

### 核心创新：跨 Session 关联

session 不是孤立日志，它们有结构性关联：

- **时间关联**（过去 → 现在）：追溯 bug 到编写 session——编写时能否预防？
- **空间关联**（此处 → 彼处）：检查其他模块是否有同样问题
- **方案关联**（此法 → 彼法）：检查优化能否推广到其他模块

这能发现单 session 分析永远看不到的模式——比如同一个流式 bug 在 4 个独立模块重复出现 30+ 个 session，实际上是一个病，一次 merge 语义审计就能预防全部。

---

## 锻造出的技能（产物）

Skill Alchemy 处理了 240 个 session、3531 轮对话、675 条用户纠正。以下是它的产出——9 个技能覆盖完整开发工作流，按触发顺序排列：

```
需求收到 → simplification_gate → change_scope_control → fix_plan_review → design_doc_review
         → [实现阶段]
         → issue_triage_gate → code_fix_acceptance → pre_completion_gate
         → pre_commit_doc_rescan
         → skill_health_check（元技能：创建/审计技能时）
```

| # | 技能 | 触发时机 | 做什么 | 来源 |
|---|------|---------|-------|:----:|
| 1 | [simplification_gate](skills/simplification_gate/) | 收到需求、设计方案前 | 必要性挑战、复用优先、搜索标准答案、最简方案、复杂度预算 | 30 session |
| 2 | [change_scope_control](skills/change_scope_control/) | 收到编码任务时 | 确认文件清单、排除"顺手优化"、检查已有实现、确认环境、检查兼容性 | 57 session |
| 3 | [fix_plan_review](skills/fix_plan_review/) | 输出技术方案时 | 6 维度风险审查 + 补充检查（范围必要性、双系统、测量、目标对齐） | 28 session |
| 4 | [design_doc_review](skills/design_doc_review/) | 编写设计文档后 | 9 维度审核：完整性、清晰度、可实施性、简化、双系统、真实测量 | 271 sessions |
| 5 | [issue_triage_gate](skills/issue_triage_gate/) | 遇到 bug/报错时 | 症状文档化、根因追溯、影响范围、架构预防、同类搜索。先诊断再修复 | 23 session |
| 6 | [code_fix_acceptance](skills/code_fix_acceptance/) | 修复完成后 | 3 步验收 + 11 条线上遗漏防范原则 + 视觉/入口/目标对齐检查 | 88 session |
| 7 | [pre_completion_gate](skills/pre_completion_gate/) | 声称完成前 | 6 项门禁：服务启动了吗？发了真实请求吗？UI 看了吗？相邻模块测了吗？重启了吗？测试够复杂吗？ | 88 session |
| 8 | [pre_commit_doc_rescan](skills/pre_commit_doc_rescan/) | 提交前 | 4+4 类检查：文档同步 + 提交授权 + 文件完整性 + 本地化 + 测试产物清理 | 12 session |
| 9 | [skill_health_check](skills/skill_health_check/) | 技能创建后 | 10 项审计：僵尸文件、描述、QA 分层、可脚本化、冗余、路径、本地化、命令兼容 | 30 sessions |

### 元技能

| 技能 | 触发词 | 做什么 |
|------|--------|-------|
| [skill-alchemy](meta_skill/skills/skill-alchemy/) | `提炼对话`、`distill conversations` | 从对话中炼金，锻造成技能。8 阶段管道。位于 Memory Curator 之上。 |

> 📖 **完整故事**：阅读 [Skill Alchemy README](meta_skill/skills/skill-alchemy/README.md)（英文）或 [中文说明](meta_skill/skills/skill-alchemy/README_ZH.md) 了解完整的 6 阶段管道、实验结果和设计原理。

---

## 实际效果

从 240 个 session、3531 轮对话、675 条用户纠正中：

| 产出 | 数量 |
|------|:----:|
| 行动指南（6 大类） | 25 条 |
| AI 错误模式 | 18 个 |
| 重复用户要求（高优先级） | 8 条 |
| 跨模块系统性问题 | 4 个 |
| 可预防的 bug（纵向追溯） | 3 个 |
| 优化扩散机会 | 5 个 |
| 锻造的新技能 | 4 个 |
| 增强的现有技能 | 5 个（19 项新增检查 + 15 项更新） |

覆盖 8 个最高频纠正模式的 **100%**，覆盖 AGENTS.md 指南的 **96%**。9 个技能覆盖完整开发工作流，零盲区。

---

## 核心发现：规则不够

分析 477 个 session 最重要的发现：

| 用户反复要求的约束 | 重复 session 数 | AI 仍然犯错 | 已在 AGENTS.md？ |
|--------------|:------------:|:-----------:|:--------------:|
| 启动服务真实验证，别只跑 pytest | 88 | ✅ | ✅（但仍然违反） |
| 简化，别过度工程 | 30 | ✅ | ✅ |
| 先出方案再写代码 | 28 | ✅ | ✅ |
| 先定位问题再修复 | 23 | ✅ | ⚠️ 部分覆盖 |
| 只改我要求的，别扩展 | 23 | ✅ | ✅ |
| 确认环境（本地/测试/生产） | 34 | ✅ | ✅ |
| 提交前等用户确认 | 12 | ✅ | ✅ |
| 根因修复，别打补丁 | 3 | ✅ | ✅ |

**8 条规则全部已存在于 AGENTS.md 中。AI 仍然持续违反。** 规则说"应该"，技能说"怎么做"。这就是 Skill Alchemy 把规则锻造成带触发条件、检查清单和通过/失败标准的可执行技能的原因。

---

## 快速开始

### 使用技能

```bash
# 克隆仓库
git clone git@github.com:DSXiangLi/Skill-Alchemy.git
cd Skill-Alchemy

# 复制技能到你的 CLI 工具的技能目录
cp -r skills/* ~/.codex/skills/        # Codex
cp -r skills/* ~/.kimi-code/skills/     # Kimi Code
cp -r skills/* ~/.claude/skills/        # Claude Code
```

技能根据对话中的触发词自动激活，无需手动调用。

### 对你自己的对话运行 Skill Alchemy

```bash
# 1. 从所有 CLI 工具提取对话
python3 meta_skill/skills/skill-alchemy/scripts/extract.py \
  --tool all --min-turns 3 --output output/extracted --format jsonl

# 2. 组织成批次（推荐关联分析模式）
python3 meta_skill/skills/skill-alchemy/scripts/distill.py \
  output/extracted -o output/batches --mode recent --recent 5

# 3. AI 读取批次并分析
#    读取 anchor_recent.md + session_index.md
#    识别真正纠正 / 有效指引
#    执行关联分析
#    检测重复要求
#    锻造成可执行技能
```

### 审计你自己的技能

```bash
python3 skills/skill_health_check/scripts/zombie_detector.py <your_skill_path> --print
```

然后跟 AI 说："对这个技能做一次健康检查"——它会执行完整的 10 项审计。

---

## 项目结构

```
Skill-Alchemy/
├── meta_skill/                      # 核心：创建技能的元技能
│   └── skills/
│       └── skill-alchemy/           # 从对话中炼金 → 锻造成技能
│           ├── SKILL.md              # 8 阶段管道定义
│           ├── scripts/
│           │   ├── extract.py        # 解析 3 种 CLI 工具的 session 格式
│           │   └── distill.py        # 组织成 AI 可分析的批次
│           ├── README.md            # 完整故事（英文）
│           └── README_ZH.md         # 完整故事（中文）
│
├── skills/                          # 锻造产物：质量门禁技能
│   ├── simplification_gate/         # 反过度工程门禁（30 session）
│   ├── change_scope_control/        # 范围控制门禁（57 session）
│   ├── fix_plan_review/             # 方案风险审查（28 session）
│   ├── design_doc_review/           # 设计文档审核（9 维度）
│   ├── issue_triage_gate/           # 问题定位门禁（23 session）
│   ├── code_fix_acceptance/         # 修复验收门禁（88 session）
│   ├── pre_completion_gate/         # 完成前门禁（88 session）
│   ├── pre_commit_doc_rescan/       # 提交前文档同步门禁（12 session）
│   └── skill_health_check/          # 技能质量审计（10 项）
│
├── AGENTS.md                        # AI 行动指南（从真实纠正中提炼）
├── README.md                        # 英文说明
└── docs/                            # 调研和设计文档
```

---

## 来源故事

这个项目源于一个简单的问题：**AI 为什么总是犯同样的错？**

我们有 AGENTS.md 规则。我们有设计文档。我们有代码审查。但在 240 个 session 中，同样的 8 种失败模式反复出现——光"没启动服务"就有 88 次。

答案是：规则是被动的。它们说"应该"但不强制。技能是主动的——在正确的时机触发，运行 grep 命令，检查通过/失败标准，输出结构化报告。

所以我们构建了 Skill Alchemy：一个读取你的对话历史、识别 AI 反复犯的错、把教训锻造成可执行技能的元技能。本仓库中的 9 个技能就是它的产出——每个都追溯到真实 session 中的真实纠正。

不是理论——是伤疤，系统化提取并锻造成工具。

---

## 与 Memory Curator 的关系

```
Memory Curator（管家）              Skill Alchemy（炼金术士）
─────────────────────              ──────────────────────────────
管理记忆文件                         从原始对话中提炼金子
维护、清理、过期淘汰                 纠正 → 规则 → 可执行技能
"记忆文件是否健康？"                  "AI 是否真的在学习？"
日常运维                            周期性深度提炼
```

Curator 管理记忆文件（CRUD）。Alchemy 读取原始对话并锻造成技能。不同层级，互补角色。

---

## 贡献

发现了 AI 反复犯的失败模式？两种贡献方式：

### 方式一：让 Skill Alchemy 自动发现

在你自己的对话历史上运行 Skill Alchemy。它会系统化扫描所有 session，按频率聚类，帮你发现可能遗漏的模式。

### 方式二：手动构建技能

1. 识别具体事故和根因
2. 定义能防止复发的系统性检查
3. 分离确定性逻辑（script）和判断性逻辑（SKILL.md）
4. 用真实场景测试直到技能可靠地抓住该模式
5. 运行 `skill_health_check` 审计结果

---

## 许可证

MIT
