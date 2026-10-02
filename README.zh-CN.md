# Hermes 夜间记忆整理管线（dreaming v2）

一个可移植的 Hermes 插件包，用于在夜间整理 `MEMORY.md`、`USER.md` 与 holographic fact_store：捕获会话事实和用户纠错，处理可安全自动化的对账，按水位压缩记忆，并审核后台 staged 改写。

English: [README.md](README.md) ｜ 日本語：[README.ja.md](README.ja.md)

## 架构图（文字版）

```text
Hermes cron（本地投递，固定低成本模型）
  → fact_extract_sweep（捕获＋普通抽取）
  → 纠错对账（有证据且结构可验证才应用，否则内部 deferred）
  → pending staged 写审核（逐项判断、应用或丢弃）
  → MEMORY / USER 独立水位评估（达到阈值才例行瘦身）
  → 保护集及写后校验、逐操作回执
```

判断类工作由模型完成，脚本负责机械校验、执行与回执。运行成功且无需用户动作时保持静默。

## 快速接入五步

1. 准备 Hermes 实例：启用 holographic 记忆 provider、memory 工具与 cron；运行时 Python 可导入 `tools.memory_tool` 和 `tools.write_approval`。
2. 设置 `HERMES_HOME`，将 `scripts/` 放到 `$HERMES_HOME/scripts/`，将 skill 放到 `$HERMES_HOME/skills/<category>/memory-consolidation/`。
3. 为目标实例初始化保护集 EXPECTED，核对 D 类块及顺序后再允许夜间写入。
4. 按 `docs/porting.md` 配置权限与水位参数，并创建每日 cron：`deliver=local`，显式固定便宜模型（例如 DeepSeek flash 档）。
5. 首夜用 dry 模式验收，核对逐项回执 JSONL 与保护检查，确认没有推送，再启用正式写入。

## 移植要点摘要

不同 Hermes 部署在工具 API、审批门、fact_store schema、会话数据库和 cron 字段上会有差异。移植时逐项映射，不能直接复用源实例保护内容。完整清单见 [docs/porting.md](docs/porting.md)，设计约束见 [docs/design.md](docs/design.md)。四个脚本的保护 EXPECTED 初始为空，必须在目标实例人工审定后填充。

## 目录导览

- [cron/nightly-prompt.md](cron/nightly-prompt.md)：参数化夜间执行 prompt 模板。
- [skills/memory-consolidation/SKILL.md](skills/memory-consolidation/SKILL.md)：运行规则与决策边界。
- [skills/memory-consolidation/references/](skills/memory-consolidation/references/)：裁决模板、瘦身 SOP、pending 审批 SOP、判官标定方法。
- [scripts/](scripts/)：会话事实抽取、共享状态、保护集校验、后台 staged 写审核。
