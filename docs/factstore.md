# fact_store：数据结构与读写机制

本档描述 holographic 记忆 provider 的**数据结构与读写路径**——即「fact store」这一层。它是 recall 型记忆：与每轮注入的 `MEMORY.md` / `USER.md`（always-on 层）分工，不替代它们。

参考实现：[plugin/holographic-plus/](../plugin/holographic-plus/)（bundled `holographic` 的 fork，见 [holographic-plus.md](holographic-plus.md)）。bundled 版本结构相同，只是没有语义检索/语义实体归并/CJK 实体三条增强。

## 1. 数据模型

存储是单个 SQLite 库（默认 `$HERMES_HOME/memory_store.db`）。bundled 与 fork 共用同一库。

### 基表

| 表 | 字段 | 说明 |
| --- | --- | --- |
| `facts` | `fact_id` PK、`content` TEXT **UNIQUE**、`category`（`user_pref`/`project`/`tool`/`general`，默认 `general`）、`tags`（逗号分隔）、`trust_score` REAL（默认 0.5）、`retrieval_count`、`helpful_count`、`created_at`、`updated_at`、`hrr_vector` BLOB | `content` 的 UNIQUE 约束就是文本级去重入口：同文本 add 不会产生第二条。 |
| `entities` | `entity_id` PK、`name`、`entity_type`（默认 `unknown`）、`aliases`（逗号分隔）、`created_at` | 实体是召回路径，不是装饰：`probe`/`related`/`reason` 都走它。 |
| `fact_entities` | `(fact_id, entity_id)` 复合主键，双向外键 | 事实↔实体多对多。 |
| `memory_banks` | `bank_id` PK、`bank_name` UNIQUE、`vector` BLOB、`dim`、`fact_count`、`updated_at` | 每个 category 一个 HRR 束（bundle），用于组合式检索。**`dim` 必须与写入方一致**，混维会直接拒绝写入。 |
| `facts_fts` | FTS5 虚表（`content`、`tags`，`content=facts`、`content_rowid=fact_id`） | 由 `facts_ai`/`facts_ad`/`facts_au` 三个触发器与主表同步；直接改 `facts` 不会绕过 FTS。 |

索引：`idx_facts_trust(trust_score DESC)`、`idx_facts_category(category)`、`idx_entities_name(name)`。

### 惰性迁移

初始化时按需 `ALTER TABLE` 补齐：`facts.hrr_vector`（HRR 升维前的老库）、`facts.deprecated_at`（软废弃标记；不存在时读取路径自动降级为不过滤）、sidecar 表的 `content_hash`。**没有 `status` 列**：废弃只是文本或 `deprecated_at` 标记，归档不等于删行。

### 语义 sidecar（holographic-plus 新增，additive）

| 表 | 字段 |
| --- | --- |
| `fact_embeddings` | `fact_id` PK→`facts`、`model`、`dim`、`vector` BLOB、`content_hash`、`created_at` |
| `entity_embeddings` | `entity_id` PK→`entities`、`model`、`dim`、`vector` BLOB、`content_hash` |

`content_hash` 让「文本变了但向量没重算」可被判为 stale。`embedding_index.py` 提供**只读体检**：对每张 sidecar 报 `missing` / `stale` / `orphan`，不回写、不初始化主 schema。写入走 `save_if_current()` —— 用 `INSERT ... SELECT ... WHERE id=? AND content=?` 保证「写入时源文本与取向量时一致」，源已变的写入直接落空（rowcount=0），不会存进对不上的向量。

## 2. 写入路径（谁往里写）

1. **模型显式写入**：`fact_store(add)` 工具调用。`entities` 参数可显式给（优先于正则抽取）。
2. **always-on 记忆镜像**：Hermes 内置 memory 工具的 `add` 经 `on_memory_write` 镜像成一条 fact。注意：`replace`/`remove` **不镜像**——所以 fact store 里会留下被取代的旧副本，去重必须自己reconcile。
3. **会话结束自动抽取**（可选、部署自带）：`on_session_finalize` hook → LLM 抽取链（本仓库另见 README 的 write-path 说明）→ `MemoryStore.add_fact`。抽取器**逐字校验**：模型给的 `quote` 必须能在原始 transcript 中确认（NFC + 空白归一化后子串命中），否则整批判失败，不落库。
4. **夜间 dreaming**：cron 会话是 `skip_memory` 建的，用不了 `fact_store` 工具，走同库直连的桥脚本（nightly cron 的 add/定点删）。夜间只允许「可追溯来源的独立事实 add」与「严格重复的定点删」；语义合并/物理删除需 owner 裁决。

所有写入路径共享 `add_fact` 的 UNIQUE 去重与实体链接。

## 3. 读路径（怎么被读到）

- **状态块**：`system_prompt_block()` 把库的规模/健康摘要注入系统提示（部署可关）。
- **每消息 prefetch**：`prefetch(query, session_id)` 按当轮用户消息检索，命中结果注入上下文；读侧全自动，不需要模型主动调用。
- **工具查询**：`search`（词面检索）、`probe`（对某实体做 HRR 代数打分后排序，返回 top-`limit`——**是排序召回，不是严格过滤**；无 numpy 时退化为对该实体名的关键词检索）、`related`（结构邻接）、`reason`（同时连到多个实体的事实）、`contradict`（互相冲突的事实）、`list`/`update`/`remove`（CRUD）。

## 4. 检索打分

`FactRetriever.search()` 的流程：

```text
FTS5(BM25) 候选  ─┐
语义向量候选      ─┼→ 逐条打分 → 信任加权 → 排序取 limit
(可选)           ─┘
```

逐条相关性：

```text
relevance = w_fts * fts_score + w_jaccard * jaccard
          + w_hrr * hrr_sim + w_semantic * sem_sim

final_score = relevance * trust_score      # 信任加权，不是加法
```

参考部署权重：`fts 0.25 / jaccard 0.15 / hrr 0.15 / semantic 0.45`，全部可按实例配置。

**降级是自动的**：numpy 不可用 → `w_hrr → 0`，其权重对半分给 FTS/Jaccard；embedding 客户端不可用 → `w_semantic → 0`，同样再分配。也就是缺任一增强，检索仍能工作，只是退化成纯文本匹配。

`min_trust` 默认 0.3，低于阈值的事实不进结果集（读取侧默认只读未被 `deprecated_at` 标记的行）。

## 5. HRR 组合检索

`holographic.py` 用相位编码实现 HRR：概念是 `[0, 2π)` 上的角度向量，`bind` = 圆周卷积（相位相加）、`unbind` = 圆周相关（相位相减）、`bundle` = 打包成一条叠加向量。每个 category 一条 bank（`memory_banks`），用于「同时连到多个实体」这类组合查询。

**维度是全局不变量**：`hrr_dim` 由配置给（参考部署 8192，早期 1024）。维度改变必须一次性做完：备份 → 改配置 → `rebuild_all_vectors(dim=N)` 全量重算 facts 与 banks → **所有直连 MemoryStore 的旁路脚本同步引用同一个维度来源** → 重启 → 补算窗口期写入。历史事故：旁路脚本各自硬编码旧维度，导致新事实 insert 被拒（`expected 4100 ... for dim=1024`）并混入异维 blob。做法上只需要一条：**维度只从配置读**（细节见 [holographic-plus.md](holographic-plus.md#4-维度与依赖)），任何写 `hrr_vector` 的新脚本都一样。

## 6. 实体抽取与归并

`_extract_entities()` 的正则规则（按序）：大写多词短语、双引号、单引号、`X aka Y`；holographic-plus 追加 CJK 引号跨度（`「」`、《》、中文双引号）。抽取结果先去重（大小写不敏感、保持首次出现顺序），再 `_resolve_entity()` 归并到已有实体：名字精确/别名命中即合并；配了 embedding 时，**高余弦相似的名字按 `entity_merge_threshold`（默认 0.88）合并为别名**。

## 7. 信任分

- 新事实 `trust_score = default_trust`（默认 0.5），写入时可带 `trust_delta`。
- `fact_feedback`：`helpful` → `+0.05` 且 `helpful_count += 1`；`unhelpful` → `-0.10`（**不对称**：负面反馈的权重是正面的两倍），值 clamp 在合法区间。
- 时间衰减：`temporal_decay_half_life`，默认 0 = 不衰减。衰减只在 recall telemetry 可信时执行，且**只调数值，不删事实、不改写内容**。

## 8. 与 dreaming 的边界

夜间流程对 fact store 的权限是收窄的：可以按可追溯来源 add 独立事实、按「原文完整连续包含于单一存活事实」做定点删；**语义合并（M2）与物理删除永远需要 owner 裁决**；「归档」是零 DB 操作（只记状态）。保护集与水位只管 `MEMORY.md` / `USER.md`，不构成对 fact store 的授权。

## 9. 部署清单

```yaml
memory:
  provider: holographic-plus        # 或 bundled: holographic
plugins:
  holographic-plus:
    db_path: $HERMES_HOME/memory_store.db
    embedding_enabled: true         # 无 embedding 凭据时自动降级为纯文本检索
    embedding_model: text-embedding-v4
    hrr_dim: 8192                   # 建库后不要随意改，改则全量重建
```

- 语义检索需要 embedding 凭据（参考实现用 DashScope，`embedding_api_key` 或 `DASHSCOPE_API_KEY`）。**没有凭据不影响可用性**，只是退化为 FTS/Jaccard/HRR。
- HRR 写入需要 numpy；缺 numpy 时该维度权重自动归零，但**持久化 HRR 写会失败或静默缺失**，所以生产环境应保证 numpy 可导入。
- 换 provider **不迁移数据**：同一个 `db_path` 才会看到同一批事实；切到别家 provider 会看到一个空库。
