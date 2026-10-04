# holographic-plus：相对 bundled provider 的差异

参考实现目录：[../plugin/holographic-plus/](../plugin/holographic-plus/)，共 6 个文件（`__init__.py`、`store.py`、`retrieval.py`、`holographic.py`、`embeddings.py`、`embedding_index.py`）+ `plugin.yaml`。

它是 Hermes 自带 `holographic` provider（MIT，原作者 dusterbloom）的 fork，**共用同一个 SQLite 库**，sidecar 表全部 additive。

## 1. 三条增强

| 增强 | 做了什么 | 少了它会怎样 |
| --- | --- | --- |
| 语义检索 | DashScope `text-embedding-v4`（1024 维，OpenAI 兼容端点）写 `fact_embeddings` / `entity_embeddings` sidecar；检索时与 FTS5 候选池合并，按 `semantic_weight` 混合打分 | 退化为纯词面匹配：换个说法问同一件事就召不回 |
| 语义实体归并 | 实体名高余弦（阈值默认 0.88）合并为别名 | 同一实体的不同写法各成一条实体，`probe` 会漏 |
| CJK 实体抽取 | 在原正则（大写短语/引号/aka）之外增加 `「」`、《》、中文双引号的跨度 | 中文对话里实体几乎抽不出来，事实等于没挂索引 |

## 2. 失败即降级（fail-open）的设计

- 任何 embedding API/网络失败只记日志并返回 `None`，**不影响事实写入与检索**。
- 检索器构造时按能力自动再分配权重：无 numpy → `w_hrr` 归零并对半分给 FTS/Jaccard；无 embedder → `w_semantic` 同样再分配。所以三档能力（纯 FTS / +HRR / +语义）都能跑。
- 查询侧有 256 条的 LRU 缓存（prefetch 每轮用户消息触发一次，不缓存会打爆 API）。

## 3. 配置键

写在 `$HERMES_HOME/config.yaml` 的 profile 作用域：

```yaml
plugins:
  holographic-plus:
    db_path: $HERMES_HOME/memory_store.db
    auto_extract: false              # 内置英文正则抽取，默认关；生产建议用自带抽取链
    default_trust: 0.5
    min_trust_threshold: 0.3
    temporal_decay_half_life: 0
    embedding_enabled: true
    embedding_model: text-embedding-v4
    embedding_dim: 1024
    embedding_api_key: ""            # 留空则读 DASHSCOPE_API_KEY；两者都无 → 语义检索自动关闭
    embedding_timeout_s: 3.0
    semantic_weight: 0.45
    fts_weight: 0.25
    jaccard_weight: 0.15
    hrr_weight: 0.15
    entity_merge_threshold: 0.88
    hrr_dim: 8192
```

`hrr_dim` 只在建库/重建时决定数据形状，日常不要动它。

## 4. 维度与依赖

- **`hrr_dim` 只能有一个来源**：配置。任何直连 `MemoryStore` 的旁路脚本（抽取 hook、日抽、夜间桥）都必须从同一处读维度，不要各自写死常量——历史上正是旁路脚本硬编码旧维度，导致新事实 `insert` 被拒并把异维 blob 混进库。参考部署为此抽了一个 20 行的 `hmem_common.hrr_dim_from_config()`（读 config.yaml），所有脚本引用它。
- **numpy 的坑是导入顺序与 ABI，不是装没装**：`holographic.py` 在**首次 import** 时缓存 `_HAS_NUMPY`，所以「先把某个第三方目录塞进 `sys.path` 最前面」这种老经验反而会打坏它——如果那个目录里的 numpy 是给别的 Python 小版本编译的（实测：解释器 3.14、vendor 目录里是 cp313 的 numpy），它会先被找到并导入失败，于是整个进程被判「无 numpy」。做法：**保证与解释器版本匹配的 numpy 能正常 import，再在它之前不要放 ABI 不匹配的副本**；需要把某个目录的 numpy 降级到后面时，先把版本匹配的那份放前面，用完再恢复原顺序。
- numpy 缺失时的行为是**可诊断的降级**，不是静默：provider 会记一条 warn（事实已写入但不带 `hrr_vector`，本轮丢弃计数一并给出），后果是该事实在 HRR 路径（`probe`/`related`/`reason`）里不可见，直到回填。所以生产环境要保证 numpy 可用，并且**回填一次**补上这段窗口的数据。
- Python 版本与 numpy ABI 必须对齐：参考实现里 vendor 目录（`pylibs`）与解释器小版本脱节过，脚本为此在导入 store 前临时调整 `sys.path` 顺序再恢复。

## 5. 安装与回滚

```bash
# 安装：整目录放到 $HERMES_HOME/plugins/<name>/
cp -r plugin/holographic-plus "$HERMES_HOME/plugins/"

# config.yaml 指向它（这些键只能通过 hermes CLI 或直接编辑 config 生效，见 porting 文档）
#   memory.provider: holographic-plus
```

回滚 = 把 `memory.provider` 改回 `holographic`。两个 provider 共用同一个库；sidecar 表留着不影响 bundled provider，不需要 drop。**不存在数据迁移步骤**，也不需要导出/导入。

## 6. 重建与体检

- 语义向量体检（只读，报 missing/stale/orphan）：`embedding_index.inspect(conn, model, dim)`。
- 全量重算 HRR：`MemoryStore.rebuild_all_vectors(dim=N)`（facts + 所有 category banks）。
- 语义向量回填：按 sidecar 体检结果，用批量接口（DashScope 单次最多 10 条输入）补 missing/stale，写入走 `save_if_current()`，源文本已变的写入会被拒而不是写歪。
- 升级 bundled 版本后重做 fork 时：注意上游可能已修 bug，先 diff 上游 `plugins/memory/holographic/` 再决定是否保留本目录的同名文件。

## 7. 已知边界

- 语义检索依赖外部 embedding 服务；离线部署只能跑前两档。
- `auto_extract` 是英文正则，中文场景不要开它当作抽取方案。
- sidecar 表在 bundled provider 下不会更新：切回 `holographic` 后新增事实没有向量，切回来需先回填。
