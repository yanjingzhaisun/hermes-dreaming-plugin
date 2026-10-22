# merge 单：holographic-plus 两份副本合并 → 定正典 → 提交 git

> 历史任务说明（2026-10-13），于 2026-10-23 归档。下文的 A 为当时的导入来源；当前代码正典是 `/vol1/1000/hermes-new/data/projects/holographic-plus`（Gitea `zijianzhou/holographic-plus`），生产目录仅是部署副本。
> 内嵌合并方案由 [独立仓与 submodule 任务](phase-submodule-prompt.md) 取代；不要重跑其中的复制、删除或提交命令。历史报告没有执行这里要求的五套回归测试，也没有交付 `work_report_merge_20261013.md`，不能据此声称本单全部验收通过。现状与复核边界见 [迁移报告的 2026-10-23 补记](work_report_submodule_20261013.md#2026-10-23-归档复核补记)。

## 两份副本
- **A（生产，本机实际运行、最新）**：`/vol1/1000/hermes-new/data/plugins/holographic-plus`
  今天经过三轮验证：① entities 字符串崩溃修复与硬化（含 `test_entities_p0.py` 13 项）；② phase104 分段计时（`test_timing_phase104.py` 6 项）；③ phase106 语义候选 numpy 向量化 + 快照缓存（`test_semantic_phase106.py` 5 项）。另有 `test_p0.py` 4 项、`test_rebuild_p0.py` 1 项。
- **B（git 仓，有版本管理，落后）**：`/vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin`
  git 仓，远端 `github.com/yanjingzhaisun/hermes-dreaming-plugin`；插件在 `plugin/holographic-plus/`。已知 `embeddings.py`、`__init__.py`、`retrieval.py`、`store.py` 四个文件与 A 不一致；仓里另有 A 没有的 `NOTICE`（及 LICENSE/README/docs 等仓级文件）。

## 目标（按顺序做）
1. **逐文件判正典**：对 `plugin/holographic-plus/` 下每个文件判定「以哪边为准」，并给出理由。原则：
   - A 是本机实际运行且今天三轮验证过的最新代码 ⇒ **代码以 A 为正典**（除非某个文件 B 侧有 A 没有的、且属于该插件运行时必需的内容——那种情况逐条列出、说明取舍）；
   - B 侧独有的仓级文件（LICENSE / NOTICE / README / docs / 三语文档）一律保留，不删。
2. **合并写进 git 仓**（只改 B 的工作区）：让 `plugin/holographic-plus/*.py` 与 A **逐字节一致**（这是硬验收标准），同时保留 B 的仓级文件。
3. **清理**：不要把生产目录 A 里的杂物带进仓：`.bak-*`、`__pycache__/`、`.entities-validation`、`work_report_*.md`、`phase10*_tmp_path`、`*.db`。必要时补 `.gitignore`。
4. **文档一致性**：若 B 的 README/文档里对检索行为、性能、依赖有描述且因本次合并而失真，**同一提交里更新**（英文为准，三语同步；不要重写无关段落）。
5. **跑测试**：在 B 的合并结果上跑 `test_p0.py` / `test_rebuild_p0.py` / `test_entities_p0.py` / `test_timing_phase104.py` / `test_semantic_phase106.py`，全部必须绿，原始输出写进报告。
6. **提交 git**（一次性提交，信息用英文，说清「sync plugin code from live production copy: entities hardening + retrieval timing + semantic vectorization/cache」之类）。**不要 push**（远端是公开仓，推送要主人点头）。

## 红线
- **不许改 A**（`data/plugins/holographic-plus` 的任何文件都不得被写入）：开工前记录 A 下所有 `.py` 的 sha256，收工时再记一次，必须完全一致，把两张表写进报告。
- 不许改 `data/memory_store.db` 或任何生产数据；不许重启 gateway；不许 `git push`；不许改 `runtime/`。
- 不许删 B 的任何现有文件（除明确属于杂物的：`__pycache__` 等）。
- 不动 B 的既有 git 历史（不 rebase、不 force、不 amend 历史提交）。

## 交付
1. 报告 `work_report_merge_20261013.md`（放 B 根目录）：
   - 逐文件正典判定表（文件 → 以哪边为准 → 理由 → 是否逐字节相同）
   - A 的 sha256 开工/收工对照表（证明 A 未被写入）
   - 五个测试文件的原始输出
   - 本次提交的 hash 与 `git show --stat` 输出
   - 若发现某些差异**不该合并**（例如 B 侧有意为之的差异），单独列一节说明
2. `git log -1 --stat` 的原文放报告里；提交信息用英文。
