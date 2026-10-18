# Skill Alchemy 健康检查优化记录

日期：2026-09-05

## 背景

项目内 `skill_health_check` 审计发现当前技能存在 last-n 非法值未阻断、最近 session 排序不稳定、技能正文与生成指令重复、阶段编号漂移及 README 过时等问题。

## 计划

- [x] 同步 `docs/02` 至 `docs/05` 的现行设计。
- [x] 固化提取时间戳并修复跨工具 session 排序。
- [x] 校验 `--recent` 和 `--max-sessions` 为正整数。
- [x] 增加组织阶段和第一层产物自动 QA。
- [x] 精简 `SKILL.md`，将详细分析合同移至模板。
- [x] 同步英文和中文 README。
- [x] 删除 n-turn 和旧关键词方案实验报告及对应本地测试产物。
- [x] 修复 `skill_health_check` 在 Python 3.7 下的兼容性。
- [x] 执行正常、异常、兼容和全链路回归。

## 兼容策略

- 保留现有 JSONL 字段；只把原本可能为空的 `created_at` 固化为有效时间。
- 保留 `--recent`、`--max-sessions` 和输出文件名。
- `last-n` 超过可用 session 数时继续使用全部可用 session，并报告实际数量。
- 非法的零或负数由静默错误改为明确 CLI 参数错误。

## 验证结果

- 标准库回归测试：8 项通过。
- 真实 Codex session 提取：成功，`created_at` 非空。
- 269-session 组织链路：10 个锚点、259 个历史 session、269 条索引，自动 QA 通过。
- `--max-sessions 3 --recent 10`：使用 3 个可用 session，自动 QA 通过。
- `quick_validate.py`：通过。
- `skill_health_check` 僵尸文件检测：0 个候选。
