# 任务：holographic-plus 独立成仓（Gitea）+ dreaming 仓改为 submodule

> 历史任务说明（2026-10-13），于 2026-10-23 归档。新仓初始化和 submodule 迁移已完成；“空仓”“尚未推送”“要删掉 github”等是当时的前置状态。不要再次执行下文的删除或 push 命令。
> 当前正典为 `/vol1/1000/hermes-new/data/projects/holographic-plus`；本仓通过 `plugin/holographic-plus` 固定已发布提交，生产目录是独立部署副本。原文“报告不必提交”保留为历史要求；本次按用户明确要求提交三份历史文档。复核结论见 [迁移报告补记](work_report_submodule_20261013.md#2026-10-23-归档复核补记)。

## 现状（已核实）
- **生产插件（内容正典）**：`/vol1/1000/hermes-new/data/plugins/holographic-plus`
  本机实际在跑；含 ① entities 字符串硬化 ② phase104 分段计时 ③ phase106 语义候选 numpy 向量化+快照缓存；测试 5 个文件（`test_p0.py` / `test_rebuild_p0.py` / `test_entities_p0.py` / `test_timing_phase104.py` / `test_semantic_phase106.py`）+ `test_sweep_p0.py`、`validate_entities_mutations.py`。
  注意目录里有杂物，**不要带**：`.bak-*`、`__pycache__/`、`.entities-validation`、`work_report_*.md`、`*.db`、`phase10*_tmp_path`。
- **dreaming 工作区**：`/vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin`（git；`origin` = Gitea `http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git`；另有 `github` 远程 —— **要删掉**）
- **新建的 Gitea 空仓**：`http://192.168.71.67:4100/zijianzhou/holographic-plus.git`（私有，已创建，**尚未初始化/未推送**）

## 目标（按顺序，每步都要原始输出）
1. **克隆插件新仓**到 `/vol1/1000/hermes-new/data/projects/holographic-plus`（clone 上面那条 Gitea URL）。
2. **灌入生产插件内容**：`*.py`（含各个 `test_*.py` 与 `validate_entities_mutations.py`）、`plugin.yaml`、插件 README（生产目录若有就用它；没有就从 dreaming 仓 `plugin/holographic-plus/README.md` 取）、`LICENSE`（从 dreaming 仓根目录取，MIT，内容一致）。补 `.gitignore`（`__pycache__/`、`*.pyc`、`*.bak-*`、`*.db`、`work_report_*.md`）。
   - 硬要求：带过去的每个 `.py` 的 sha256 必须与生产目录**逐个一致**，写进报告对照表。
3. **提交并推送插件仓**：一次提交，英文信息（例：`Initial import: holographic-plus memory provider (live production copy)`），push 到 Gitea，默认分支 `main`。
4. **改造 dreaming 仓**：
   a. `git remote remove github`（去掉 GitHub 远程）
   b. 清掉工作区里内嵌的插件目录：`git rm -r --cached plugin/holographic-plus`，然后把磁盘上的 `plugin/holographic-plus` 整目录删掉（**只允许删这一个路径**）
   c. `git submodule add http://192.168.71.67:4100/zijianzhou/holographic-plus.git plugin/holographic-plus`
   d. 确认 `.gitmodules` 里的 URL 就是上面那条 Gitea http URL（不要 https、不要别的地址）
   e. 一次提交（英文，例：`Move holographic-plus into its own repo as a git submodule`）+ `git push origin`（Gitea）
5. **报告** `work_report_submodule_20261013.md`（放 dreaming 仓根，不必提交）：
   - 两个仓的 HEAD hash + push 的原始输出
   - 生产目录**全部 `.py` 的 sha256 开工/收工对照表**（证明生产未被写入）
   - `git submodule status` 原始输出、插件仓 `git ls-files` 清单
   - 任何取舍（哪个文件没带、README/LICENSE 来源）逐条说明

## 红线
- **不许改** `/vol1/1000/hermes-new/data/plugins/holographic-plus` 里任何文件：开工前、收工后各记一次全部 `.py` 的 sha256，两边必须完全一致。
- 不许动 `data/memory_store.db`、`config.yaml`、`runtime/` 或任何生产数据；不许重启 gateway。
- **不许 push 到 GitHub**（远程要删掉）。
- 不许改写既有提交历史（不 rebase / 不 amend / 不 force push）。
- 破坏性命令（`rm`、`git clean`）只允许严格限定在 `plugin/holographic-plus` 或新建的插件仓目录内；禁 `git clean -fdx` 之类的通配清理。
