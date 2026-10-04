# Hermes 记忆栈

一套 Hermes Agent 记忆系统的两半，都做成可移植、可直接接入另一个实例的形状：**fact store 后端**（`holographic-plus` 记忆 provider）与**夜间自动整理管线**（dreaming）。两者都从一台单人生产的部署里抽出并参数化。

English: [README.md](README.md) ｜ 日本語：[README.ja.md](README.ja.md)

## 包里有什么

| 半边 | 是什么 | 位置 |
| --- | --- | --- |
| **fact store** | SQLite 结构化记忆：事实、实体、信任分、HRR 组合检索、可选语义（embedding）检索。对外提供 `fact_store` / `fact_feedback` 工具，并按轮注入检索到的事实。 | [`plugin/holographic-plus/`](plugin/holographic-plus/) ＋ [docs/factstore.md](docs/factstore.md) |
| **dreaming** | 无人值守的夜间运行：捕获会话事实与用户纠错，只对「结构上可证明安全」的部分对账，按水位瘦身 `MEMORY.md` / `USER.md`，审核后台 staged 改写。fail-closed，成功时静默。 | [`cron/`](cron/)、[`skills/`](skills/)、[`scripts/`](scripts/) ＋ [docs/design.md](docs/design.md) |

两半互相独立：没有夜间 job，store 照样能用；夜里涉及 store 的步骤则需要有个 store。Hermes 自带 `holographic` provider、schema 相同——本包里的 fork 在它之上加了语义检索、语义实体归并、CJK 实体抽取三条（见 [docs/holographic-plus.md](docs/holographic-plus.md)）。

## 架构

```text
                    ┌─ fact_store(add)         ─┐
写入路径 ───────────┼─ memory 工具镜像          ─┼─→ memory_store.db  ── 读取方 ──→  系统提示状态块
                    ├─ 会话结束 hook           ─┤     facts / entities /           每轮 prefetch
                    └─ 夜间 dreaming           ─┘     FTS5 / HRR banks /            search / probe / related /
                                                      embedding sidecar              reason / contradict
```

```text
Hermes cron（本地投递，固定低成本模型）
  → fact_extract_sweep（纠错捕获＋普通抽取）
  → 纠错对账（有结构证据才应用，否则内部 deferred）
  → pending staged 写审核（逐项判断、应用或丢弃）
  → MEMORY / USER 独立水位评估（达到阈值才例行瘦身）
  → 保护集校验、逐操作回执
```

判断类工作由模型完成，脚本负责机械校验、执行与回执。运行成功且无需用户动作时保持静默。

## 快速接入五步

1. 准备 Hermes 实例：启用 holographic 记忆 provider（自带 `holographic`，或本仓库的 fork）、memory 工具与 cron；运行时 Python 可导入 `tools.memory_tool` 与 `tools.write_approval`。
2. 设置 `HERMES_HOME`：`scripts/` 放到 `$HERMES_HOME/scripts/`，skill 放到 `$HERMES_HOME/skills/<category>/memory-consolidation/`；要用 fork 就把 `plugin/holographic-plus/` 放到 `$HERMES_HOME/plugins/`。
3. 为目标实例初始化保护集 EXPECTED，核对冻结块后再允许夜间写入——EXPECTED 为空时检查通过**不代表**保护存在。
4. 按 [docs/porting.md](docs/porting.md) 配置权限与水位，创建每日 cron：`deliver=local`，显式固定便宜模型（例如 DeepSeek flash 档）。
5. 首夜在隔离副本里 dry-run：核对逐项回执 JSONL 与保护检查，确认无推送，再启用正式写入。

## 移植要点摘要

不同 Hermes 部署在工具 API、审批门、fact_store schema、会话数据库与 cron 字段上会有差异，逐项映射；不要复用别的实例的保护内容。完整清单见 [docs/porting.md](docs/porting.md)，设计约束见 [docs/design.md](docs/design.md)。

最容易咬人的四条：

1. 脚本必须在 Hermes 运行时 Python 下跑（要 import `tools.memory_tool` 和 store），系统 Python 不行。
2. `memory.write_approval` 只管前台写入——后台破坏性操作的 staging 闸在运行时代码里，没有配置开关。包里的 `memory_pending_review.py` 把这个审批接进了夜间流程。
3. `fact_extract_sweep.py` 需要外部的 `session_fact_extract.py`（LLM 抽取链）。那是每个部署自己的模型选择，包里有意不带——没有它，sweep 退化成空转。
4. 任何写 `hrr_vector` 的东西都必须从**唯一**来源（插件配置）读 HRR 维度。旁路脚本各自硬编码维度会污染库：写入被判维度不符而拒绝，或异形 blob 静默落库。

## 目录导览

- [plugin/holographic-plus/](plugin/holographic-plus/)：记忆 provider（自带 `holographic` 的 fork）。
- [docs/factstore.md](docs/factstore.md)：fact store 的数据模型、读写路径、打分、HRR、信任分。
- [docs/holographic-plus.md](docs/holographic-plus.md)：fork 加了什么、配置键、安装/回滚、HRR 维度纪律。
- [cron/nightly-prompt.md](cron/nightly-prompt.md)：参数化夜间执行 prompt 模板。
- [skills/memory-consolidation/SKILL.md](skills/memory-consolidation/SKILL.md)：运行规则与决策边界。
- [skills/memory-consolidation/references/](skills/memory-consolidation/references/)：裁决模板、瘦身 SOP、pending 审批 SOP、判官标定方法。
- [scripts/](scripts/)：会话事实抽取、共享状态、保护集校验、后台 staged 写审核。

## 许可

MIT — 见 [LICENSE](LICENSE)。`plugin/` 目录派生自 Hermes Agent 自带的 `holographic` provider（MIT，© 2025 Nous Research；原作者 dusterbloom）——见 [plugin/holographic-plus/NOTICE](plugin/holographic-plus/NOTICE)。
