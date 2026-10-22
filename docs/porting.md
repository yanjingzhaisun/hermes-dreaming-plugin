# 移植清单

## Hermes 内部依赖映射

| 依赖点 | 目标部署需要核对的内容 |
| --- | --- |
| `tools.memory_tool` | `load_on_disk_store`、`apply_memory_pending`、`destructive_ops` 的签名和副作用与 `memory_pending_review.py` 一致；后台删除闸的行为须实测。 |
| `tools.write_approval` | pending 列表、丢弃与存储常量 API；确认其 pending 目录和锁语义。 |
| holographic fact_store | 数据库位置、schema、活动/废弃事实读取方式、检索验证方式；本包不实现 fact_store 物理删除。 |
| `state.db` 的 `messages` 表 | `session_id`、`id`、`role`、`content`、`timestamp`、`active` 等列存在；会话表含 `id` 与 `source`，抽取器使用的筛选条件适配本地 schema。纠错捕获还须识别用户消息和工具来源，尤其 `tool_name='clarify'` 的消息语义。 |
| 会话抽取器 | `fact_extract_sweep.py` 调用 `$HERMES_HOME/scripts/session_fact_extract.py`；此辅助模块不在本包内，需从目标部署提供并审查。 |
| kanban 数据库 | 若实例启用了 queued/retryable 工作项，按其真实 schema 接入；本包不携带 kanban writer，不能假设源库字段兼容。 |
| 配置 | 映射 `memory.memory_char_limit`、`memory.user_char_limit`；确认 exact-match 修改能只触及目标键。 |
| 记忆文件 | `memories/MEMORY.md`、`memories/USER.md` 与实际存储位置一致；统一使用 UTF-8。 |

脚本默认 `HERMES_HOME=~/.hermes`（展开后）。所有目标环境路径应从该根目录派生。运行脚本的 Python 必须是 Hermes 运行时本体所在环境，并已将运行时加入 `sys.path`；普通系统 Python 通常不能导入上述模块。

## fact store 后端

夜间流程的 fact-store 步骤需要一个可用的记忆 provider。两条路：

- **用 Hermes 自带的 `holographic`**：无需安装。`memory.provider: holographic`，库落在 `db_path`（默认 `$HERMES_HOME/memory_store.db`）。
- **用本仓库的 fork `plugin/holographic-plus/`**：整目录放到 `$HERMES_HOME/plugins/`，`memory.provider: holographic-plus`。三条增强（语义检索/语义实体归并/CJK 实体抽取）与 bundled 共用同一个库，sidecar 表 additive；回滚＝把 provider 改回 `holographic`，不需要迁移数据。

安装 fork 时逐项核对：

| 项 | 要求 |
| --- | --- |
| embedding 凭据 | 语义检索需要；缺失时自动降级为纯文本检索，不影响写入与可用性。配置键 `plugins.holographic-plus.embedding_api_key`，或环境变量 `DASHSCOPE_API_KEY`。 |
| numpy | HRR 持久化写入需要；缺失时是**可诊断降级**：事实照写，但该条不带 `hrr_vector`（provider 记 warn 并给出本轮丢弃计数），在 `probe`/`related`/`reason` 路径里不可见，需事后回填。注意 ABI：解释器 3.14 配 cp313 的 vendor numpy 会被判「无 numpy」——`_HAS_NUMPY` 在首次 import 时缓存，所以不要盲目把第三方目录塞到 `sys.path` 最前面。 |
| `hrr_dim` | 建库形状的一部分。所有直连 store 的脚本（抽取 hook、日抽、夜间桥）必须从同一配置读维度，不要各写常量。改维度＝全量 `rebuild_all_vectors(dim=N)`。 |
| 库文件 | 必须是同一个绝对路径 `memory_store.db`；换 provider 不迁移数据。 |

数据模型、打分与读写路径见 [factstore.md](factstore.md)；fork 的差异、配置键与重建流程见 [holographic-plus.md](holographic-plus.md)。


## 配置与写权限

- 检查 `memory.write_approval` 的前台含义。此键通常不会关闭后台 `background_review` 的 destructive staging 门；不要将其误作夜间写入总开关。
- 明确 USER.md 非保护内容是否允许夜间写入。身份类内容夜间一律 deferred。
- MEMORY、USER 分开设置正整数水位。参考触发值为 `ceil(limit * 0.85)`；若采用不同值，须同步 prompt 与 SOP。
- 提额自决公式：`new_limit = max(old_limit, ceil(chars / 0.80 / 100) * 100)`。只允许修改目标限额键，修改后重读配置并复测水位。
- 不授予夜间 fact_store 物理删除权限。归档/删除边界由 owner 裁决；本包的 pending 自动审批只覆盖 MEMORY/USER staged 写。

## 保护集初始化

1. 先由部署维护者识别 MEMORY.md 和 USER.md 中不可压缩、不可重排的保护块。
2. 将每块的完整预期 SHA-256、稳定标签和文件名登记到 `scripts/dream_protected_check.py` 的 `EXPECTED`，按保护块在文件中的相对顺序排列；标签必须唯一匹配该块开头。检查器验证哈希与顺序，异常时以非零状态退出。
3. 在启用夜间写之前运行保护检查，验证全部条目均为 OK；EXPECTED 为空时检查通过不代表实例已建立保护集，必须由运维流程显式确认初始化完成。
4. 检查器不会复制任何其他部署的保护内容。保护块增加/改变只通过独立的主会话审定流程更新 EXPECTED。

## Cron job 建法

- 新建一个每日夜间 job，提示词使用 [../cron/nightly-prompt.md](../cron/nightly-prompt.md) 并填全参数。
- 设 `deliver=local`，避免 scheduler 重复投递；显式固定低成本模型档（例如 DeepSeek flash 系列），不要依赖用户默认模型漂移。
- 配置 skill 为 `memory-consolidation`，执行超时需覆盖实际工作量；job 建立后读回字段、prompt、时区、下一次运行时间。
- 不要复活旧 job 或复制旧 ID；测试应在隔离 cron store 完成。

## 验收方法

1. 在隔离副本首夜干跑：先检查脚本 `--dry-run`/`--dry` 参数是否支持当前运行分支，dry 不应写 DB、文件或审批队列。
2. 检查 run receipt 和 `state/pending-memory-review.jsonl` 中每条 `PENDING_REVIEW` 结果、run_id 与目标状态相符。
3. 对 MEMORY/USER 运行字符数测量与保护检查，并对比输入文件哈希。
4. 确认运行成功无 stdout、无消息推送；失败告警也不包含原文、私密路径或行动项。
5. 经人工验收后才打开生产写入；首轮逐项检查 before/after 与备份记录。

## 已知边界

- pending 审批只覆盖 MEMORY/USER staged 写；fact_store 的物理删除仍需 owner 裁决。
- 身份类内容不由夜间流程落地。
- `fact_extract_sweep.py` 依赖外置 `session_fact_extract.py` 和若干同目录模块；该最小包仅包含指定四个脚本，需逐项核对这些运行时依赖。
- LLM 事实抽取链（会话结束 hook + 抽取 prompt/模型路由）与冲突确认队列**有意不同捆**：模型供应商、语言、transcript schema、成本策略都是部署特定的。没有抽取链时，fact store 仍可由模型的 `fact_store(add)` 与内置 memory 工具的 `add` 镜像写入，但夜间 sweep 会退化成空转，并在正常运行回执中记录 `extractor_unavailable`；缺少可选语义复核模块时记录 `disabled`。`--dry-run` 只在内存中保留统计，不创建回执文件。
- 各 Hermes 版本的工具 API、表结构与 scheduler schema 可能变化；必须在隔离环境验证。
