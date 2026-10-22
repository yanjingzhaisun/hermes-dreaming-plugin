# holographic-plus 独立成仓与 dreaming submodule 迁移报告

## 2026-10-23 归档复核补记

本节是本次复核的新说明；其后的日期、HEAD、push 输出、SHA256 表及完整 diff 均保留 2026-10-13 原文，不代表当前 HEAD，也不授权重跑历史命令。原文“报告不提交”已由本次用户明确要求归档提交所取代。

- **结构迁移已完成**：正典是 `/vol1/1000/hermes-new/data/projects/holographic-plus`，origin 为 Gitea `zijianzhou/holographic-plus`；`/vol1/1000/hermes-new/data/plugins/holographic-plus` 是部署副本。本仓的 `plugin/holographic-plus` 是 `160000` gitlink，`.gitmodules` 的 HTTP URL 正确，GitHub remote 已不存在。
- **历史证据得到复核**：13 个原始 Python SHA256 均匹配初始提交 `3521896162c86d6beced36820cae62753f0c3239` 的 Git blob；报告中的完整 staged diff 与 `1119d535..68215762` 的实际 diff 逐字节一致；LICENSE 与 NOTICE 来源得到保留。哈希对照证明两次观测相同，不能独立证明历史期间没有任何临时写入或进程操作。
- **安全修正 pin**：本次从 `c23a9bd91e970aec6e0411919942f9bb98c9e1be` 更新到 `b1734859fb9ebfd1bf184040e5370b63d478fc6b`；更新前 `git ls-remote --symref origin HEAD refs/heads/main` 已确认后者是 Gitea 已发布的 main。正典工作区 HEAD 为 `2cf914cf0ba6efafdea594e44275e102e1abff75`，另有 4 个尚未发布的提交，未将其写入本仓 gitlink。
- **历史验收缺口保留**：此前合并单要求的五套回归测试当时没有运行，也未找到 `work_report_merge_20261013.md`。本次在 `b173485` 的隔离导出副本运行五个指定测试模块，29 项通过；这是当前验证，不能补称为 2026-10-13 的测试结果。实体 mutation 验证脚本保留但本次未执行。
- **当前部署仍有差异**：发布版本的 `retrieval.py` 与生产不同；正典 HEAD 还在 `store.py` 上不同。没有从生产反向覆盖正典，也没有部署或修改生产。是否发布正典额外提交、何时部署，需要另行决定。
- **文档已同步修正**：三语 README 补充 submodule 初始化与固定版本说明；安装文档改为导出已提交文件，避免复制 `.git` 指针；删除已失真的“无需迁移即可切回 bundled provider”和旧阈值自动合并承诺，指向所固定插件版本的迁移与身份解析说明。
- **副本范围**：projects 目录深度不超过 5 的源码布局检查只找到预期正典/submodule，以及有来源说明的 `holographic-cn-fork` 和 bundled 上游源码。未发现遗留的 holographic-plus 内嵌副本；未删除这些有明确用途的目录。

完整验收表、实际命令输出、测试原始输出、本次提交清单与最终状态见本机审计产物 `/vol1/1000/hermes-new/data/work/codex-sweep-2026-10-23/reports/legacy-hermes-dreaming-plugin.md`；该审计产物和隔离测试文件不纳入本仓。下文开始为原始迁移报告。

日期：2026-10-13（Asia/Shanghai）。

## 结果

- 插件仓：`/vol1/1000/hermes-new/data/projects/holographic-plus`；HEAD：`3521896162c86d6beced36820cae62753f0c3239`。
- dreaming 仓：`/vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin`；HEAD：`68215762663fe390f257b2003aeb6818d4faa634`。
- 两个仓库均为 `main`，均已推送并通过 `git ls-remote` 核对远程 main 与本地 HEAD 一致。新插件仓远程 HEAD 默认指向 main。
- 插件仓仅一个初始提交；dreaming 新提交的父提交仍为 `1119d53554570b93addaac140e0af3065816c00f`，没有改写历史。
- dreaming 的 `plugin/holographic-plus` 已为模式 `160000` 的 gitlink，指向插件 HEAD。`.gitmodules` URL 精确为 `http://192.168.71.67:4100/zijianzhou/holographic-plus.git`。
- dreaming 的 GitHub 远程已删除，只保留 Gitea origin；所有 push 均发往 Gitea。
- 生产目录全部 13 个 `.py` 的开工与收工路径集合及 SHA256 完全一致；独立仓工作副本、已提交 Git blob 与 submodule 工作副本也逐个一致。
- 本任务没有修改生产插件文件、生产数据库、config.yaml 或 runtime，没有重启 gateway。报告不提交。

## Push 原始输出

### 步骤 3：推送插件仓到 Gitea

时间（UTC）：2026-10-13T10:56:57.983892+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git push -u origin main
remote: . Processing 1 references        
remote: Processed 1 references in total        
To http://192.168.71.67:4100/zijianzhou/holographic-plus.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
````

### 步骤 4e：推送 dreaming 到 Gitea

时间（UTC）：2026-10-13T10:57:24.378336+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git push origin
remote: . Processing 1 references        
remote: Processed 1 references in total        
To http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git
   1119d53..6821576  main -> main
````

## 全部生产 Python 文件 SHA256 对照

生产目录：`/vol1/1000/hermes-new/data/plugins/holographic-plus`。递归枚举全部 `*.py`，每次直接读取字节并计算 SHA256。没有运行或导入生产插件代码。

| 相对文件名 | 生产开工 SHA256 | 导入副本 SHA256 | 生产收工 SHA256 | 结果 |
| --- | --- | --- | --- | --- |
| `__init__.py` | `13985c6ee52d543f981f20d96d0af5a855f642b9c39ab018f71dbe3fe54eb56e` | `13985c6ee52d543f981f20d96d0af5a855f642b9c39ab018f71dbe3fe54eb56e` | `13985c6ee52d543f981f20d96d0af5a855f642b9c39ab018f71dbe3fe54eb56e` | 一致 |
| `embedding_index.py` | `0d806068ca22c46512e5733a702f0c70553c0a7601cad94412facb2d84925272` | `0d806068ca22c46512e5733a702f0c70553c0a7601cad94412facb2d84925272` | `0d806068ca22c46512e5733a702f0c70553c0a7601cad94412facb2d84925272` | 一致 |
| `embeddings.py` | `3659df156e67721e5af0b76752a1872e2944e44ef05d9af007b860434643d658` | `3659df156e67721e5af0b76752a1872e2944e44ef05d9af007b860434643d658` | `3659df156e67721e5af0b76752a1872e2944e44ef05d9af007b860434643d658` | 一致 |
| `holographic.py` | `ffc27abd0f1ffe1ffa01c79c34dbbbb5b7a99ba72b7a75c8e9a0d1b7cbb94315` | `ffc27abd0f1ffe1ffa01c79c34dbbbb5b7a99ba72b7a75c8e9a0d1b7cbb94315` | `ffc27abd0f1ffe1ffa01c79c34dbbbb5b7a99ba72b7a75c8e9a0d1b7cbb94315` | 一致 |
| `retrieval.py` | `e4fd2162452937812136d107c7d2c7c4472a1220433d972a3199ceebc9d183e1` | `e4fd2162452937812136d107c7d2c7c4472a1220433d972a3199ceebc9d183e1` | `e4fd2162452937812136d107c7d2c7c4472a1220433d972a3199ceebc9d183e1` | 一致 |
| `store.py` | `98e1de5f2efdfb4ef617386aa45fabfd7c0f972763907f44623ad849a18030f2` | `98e1de5f2efdfb4ef617386aa45fabfd7c0f972763907f44623ad849a18030f2` | `98e1de5f2efdfb4ef617386aa45fabfd7c0f972763907f44623ad849a18030f2` | 一致 |
| `test_entities_p0.py` | `75d33ea89b5bdd085307b3061efc53b156ca3fdf0bf23a48b4a79f1e60179c1b` | `75d33ea89b5bdd085307b3061efc53b156ca3fdf0bf23a48b4a79f1e60179c1b` | `75d33ea89b5bdd085307b3061efc53b156ca3fdf0bf23a48b4a79f1e60179c1b` | 一致 |
| `test_p0.py` | `d294d8d1925f0f6a8588c7799fccf8b9975a1a6afa228cdb5721b7ddc53b24f3` | `d294d8d1925f0f6a8588c7799fccf8b9975a1a6afa228cdb5721b7ddc53b24f3` | `d294d8d1925f0f6a8588c7799fccf8b9975a1a6afa228cdb5721b7ddc53b24f3` | 一致 |
| `test_rebuild_p0.py` | `4d7176fe6d4ba6b138d1d375c8cdc7bbe3ed365681681dab7b6f291ea3425366` | `4d7176fe6d4ba6b138d1d375c8cdc7bbe3ed365681681dab7b6f291ea3425366` | `4d7176fe6d4ba6b138d1d375c8cdc7bbe3ed365681681dab7b6f291ea3425366` | 一致 |
| `test_semantic_phase106.py` | `510669e538551ec8d9244955f5cb9b25baf5b954e2b5b57284e9e84d066c066b` | `510669e538551ec8d9244955f5cb9b25baf5b954e2b5b57284e9e84d066c066b` | `510669e538551ec8d9244955f5cb9b25baf5b954e2b5b57284e9e84d066c066b` | 一致 |
| `test_sweep_p0.py` | `a28775b8b30e6c07cfa3b291592de0fe54d31574323e6b2b5e00db281452446b` | `a28775b8b30e6c07cfa3b291592de0fe54d31574323e6b2b5e00db281452446b` | `a28775b8b30e6c07cfa3b291592de0fe54d31574323e6b2b5e00db281452446b` | 一致 |
| `test_timing_phase104.py` | `9822ea221e44ea5128690e0c5f63beac72a130c5d5a44c512341b449d2b5889c` | `9822ea221e44ea5128690e0c5f63beac72a130c5d5a44c512341b449d2b5889c` | `9822ea221e44ea5128690e0c5f63beac72a130c5d5a44c512341b449d2b5889c` | 一致 |
| `validate_entities_mutations.py` | `a77cd95ed27bab7552d83b4036a5d453a78e0491953d7bce5475ea485a8d2917` | `a77cd95ed27bab7552d83b4036a5d453a78e0491953d7bce5475ea485a8d2917` | `a77cd95ed27bab7552d83b4036a5d453a78e0491953d7bce5475ea485a8d2917` | 一致 |

## Submodule 与插件文件清单原始输出

### 最终 git submodule status

时间（UTC）：2026-10-13T10:58:07.697459+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git submodule status
 3521896162c86d6beced36820cae62753f0c3239 plugin/holographic-plus (heads/main)
````

### gitlink 模式核对

时间（UTC）：2026-10-13T10:58:07.703089+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git ls-tree HEAD plugin/holographic-plus
160000 commit 3521896162c86d6beced36820cae62753f0c3239	plugin/holographic-plus
````

### 插件仓 git ls-files

时间（UTC）：2026-10-13T10:58:07.700133+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git ls-files
.gitignore
LICENSE
NOTICE
README.md
__init__.py
embedding_index.py
embeddings.py
holographic.py
plugin.yaml
retrieval.py
store.py
test_entities_p0.py
test_p0.py
test_rebuild_p0.py
test_semantic_phase106.py
test_sweep_p0.py
test_timing_phase104.py
validate_entities_mutations.py
````

## 文件取舍与来源

1. 生产目录中的全部 13 个 `.py` 原样导入，包括 6 个 `test_*.py` 和 `validate_entities_mutations.py`；没有遗漏任何生产 `.py`，没有改动源码字节。
2. `plugin.yaml` 从生产目录复制并核对字节一致。
3. 两个指定 README 来源均不存在：生产目录无 README，dreaming 的 `plugin/holographic-plus/README.md` 在磁盘和当前提交中也不存在。已提出可选澄清，等待超过 60 秒未收到回复后，按需要插件 README 的目标补写英文 README。来源为导入源码及 dreaming 的 `docs/holographic-plus.md`，不是声称复制了一个不存在的文件。README 已明确注明来源。
4. `LICENSE` 从 dreaming 根目录复制；MIT 全文逐字节一致（Copyright (c) 2026 yanjingzhaisun）。
5. 额外保留旧嵌入插件的 `NOTICE`，包含 Nous Research 2025 署名及 upstream MIT 许可文本；迁移到独立仓根后，只将 `see ../../LICENSE` 改为 `see LICENSE`。
6. 新建 `.gitignore` 包含 `__pycache__/`、`*.pyc`、`*.bak-*`、`*.db`、`work_report_*.md`，与要求一致。采用源码文件白名单导入，未递归复制杂物目录。
7. 未导入 7 个备份文件：`__init__.py.bak-2026-10-13`、`__init__.py.bak-20261013`、`retrieval.py.bak-2026-10-13`、`retrieval.py.bak-20261013`、`store.py.bak-2026-10-13`、`store.py.bak-20261013`、`test_sweep_p0.py.bak-2026-10-13`。
8. 未导入 `__pycache__/` 及其所有 bytecode，也未导入 `.entities-validation/` 及其快照、日志、diff 和 tmp 子目录；完整原始排除清单见后面的执行记录。
9. 未导入 3 个旧工作报告：`work_report_holographic_entities.md`、`work_report_phase104.md`、`work_report_phase106.md`。
10. 开工生产清单没有 `*.db` 或 `phase10*_tmp_path`；白名单规则也不会导入这些文件或目录。
11. 旧嵌入目录的 7 个未跟踪测试/验证文件随获准删除的目录被移除；新仓及 submodule 内对应文件均采用生产副本。两份原有未跟踪提示文件 `phase-merge-prompt.md`、`phase-submodule-prompt.md` 保留，SHA256 未变。
12. 导入只保证指定的源码字节一致；源码以普通文本文件模式 `100644` 提交，不复制生产文件的执行权限。
13. 唯一磁盘删除命令为精确限定的 `rm -r -- /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin/plugin/holographic-plus`。执行前核对该目录不是符号链接，且路径不是生产目录；没有使用 git clean。

## 验证范围与执行说明

已完成所有导入 `.py` 的内存语法编译、Git diff 检查、源码/提交 blob/submodule 哈希一致性、远程默认分支及 HEAD 核对、提交父子关系、gitlink 模式、远程 URL、工作区状态核对。此次是原样迁移，没有运行回归测试或 mutation 脚本，也没有加载 provider，避免触发运行时或数据库行为。测试文件仍保留其生产环境路径，README 已说明这个边界。

准备阶段发现本机没有 `python` 命令（退出 127），随后使用 `python3`。首轮复制前置检查因 README 缺失停止（AssertionError，退出 1），未复制文件；随后按以上取舍完成导入。其余已记录步骤均成功。

## 全部步骤原始输出

所有以下业务命令均保留完整 stdout/stderr 合并原始输出与退出码；无输出命令保留空输出。复制、哈希等 Python 文件操作列出实际结果。完整 staged diff 也保留，没有使用终端截断后的版本。

### 开工生产 SHA256

时间（UTC）：2026-10-13T10:54:26.870728+00:00；退出码：0。

````text
$ SHA256 of every production *.py (recursive)
13985c6ee52d543f981f20d96d0af5a855f642b9c39ab018f71dbe3fe54eb56e  __init__.py
0d806068ca22c46512e5733a702f0c70553c0a7601cad94412facb2d84925272  embedding_index.py
3659df156e67721e5af0b76752a1872e2944e44ef05d9af007b860434643d658  embeddings.py
ffc27abd0f1ffe1ffa01c79c34dbbbb5b7a99ba72b7a75c8e9a0d1b7cbb94315  holographic.py
e4fd2162452937812136d107c7d2c7c4472a1220433d972a3199ceebc9d183e1  retrieval.py
98e1de5f2efdfb4ef617386aa45fabfd7c0f972763907f44623ad849a18030f2  store.py
75d33ea89b5bdd085307b3061efc53b156ca3fdf0bf23a48b4a79f1e60179c1b  test_entities_p0.py
d294d8d1925f0f6a8588c7799fccf8b9975a1a6afa228cdb5721b7ddc53b24f3  test_p0.py
4d7176fe6d4ba6b138d1d375c8cdc7bbe3ed365681681dab7b6f291ea3425366  test_rebuild_p0.py
510669e538551ec8d9244955f5cb9b25baf5b954e2b5b57284e9e84d066c066b  test_semantic_phase106.py
a28775b8b30e6c07cfa3b291592de0fe54d31574323e6b2b5e00db281452446b  test_sweep_p0.py
9822ea221e44ea5128690e0c5f63beac72a130c5d5a44c512341b449d2b5889c  test_timing_phase104.py
a77cd95ed27bab7552d83b4036a5d453a78e0491953d7bce5475ea485a8d2917  validate_entities_mutations.py
````

### dreaming 开工状态

时间（UTC）：2026-10-13T10:54:26.875273+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git status --short
?? phase-merge-prompt.md
?? phase-submodule-prompt.md
?? plugin/holographic-plus/test_entities_p0.py
?? plugin/holographic-plus/test_p0.py
?? plugin/holographic-plus/test_rebuild_p0.py
?? plugin/holographic-plus/test_semantic_phase106.py
?? plugin/holographic-plus/test_sweep_p0.py
?? plugin/holographic-plus/test_timing_phase104.py
?? plugin/holographic-plus/validate_entities_mutations.py
````

### dreaming 开工远程

时间（UTC）：2026-10-13T10:54:26.877923+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git remote -v
github	https://github.com/yanjingzhaisun/hermes-dreaming-plugin.git (fetch)
github	https://github.com/yanjingzhaisun/hermes-dreaming-plugin.git (push)
origin	http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git (fetch)
origin	http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git (push)
````

### dreaming 开工 HEAD

时间（UTC）：2026-10-13T10:54:26.880754+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git rev-parse HEAD
1119d53554570b93addaac140e0af3065816c00f
````

### 步骤 1：clone 插件新仓

时间（UTC）：2026-10-13T10:54:27.452117+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects && git clone http://192.168.71.67:4100/zijianzhou/holographic-plus.git /vol1/1000/hermes-new/data/projects/holographic-plus
Cloning into '/vol1/1000/hermes-new/data/projects/holographic-plus'...
warning: You appear to have cloned an empty repository.
````

### README 来源检查

时间（UTC）：2026-10-13T10:55:27.938587+00:00；退出码：0。

````text
$ exists production/README.md; exists dreaming/plugin/holographic-plus/README.md
production README.md: absent
dreaming plugin README.md: absent
Initial copy precondition stopped before copying files; preparing sources pending README clarification.
````

### 步骤 2：导入源码和授权文件

时间（UTC）：2026-10-13T10:55:27.941917+00:00；退出码：0。

````text
$ copy production *.py + plugin.yaml; copy LICENSE/NOTICE; create .gitignore
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/__init__.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/__init__.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/embedding_index.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/embedding_index.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/embeddings.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/embeddings.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/holographic.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/holographic.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/retrieval.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/retrieval.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/store.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/store.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/test_entities_p0.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/test_entities_p0.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/test_p0.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/test_p0.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/test_rebuild_p0.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/test_rebuild_p0.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/test_semantic_phase106.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/test_semantic_phase106.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/test_sweep_p0.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/test_sweep_p0.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/test_timing_phase104.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/test_timing_phase104.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/validate_entities_mutations.py -> /vol1/1000/hermes-new/data/projects/holographic-plus/validate_entities_mutations.py
copied /vol1/1000/hermes-new/data/plugins/holographic-plus/plugin.yaml -> /vol1/1000/hermes-new/data/projects/holographic-plus/plugin.yaml
copied /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin/LICENSE -> /vol1/1000/hermes-new/data/projects/holographic-plus/LICENSE
copied /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin/plugin/holographic-plus/NOTICE -> /vol1/1000/hermes-new/data/projects/holographic-plus/NOTICE
created .gitignore:
__pycache__/
*.pyc
*.bak-*
*.db
work_report_*.md

````

### 逐个导入 SHA256 核对

时间（UTC）：2026-10-13T10:55:27.943761+00:00；退出码：0。

````text
$ SHA256 copied *.py compared with production start snapshot
13985c6ee52d543f981f20d96d0af5a855f642b9c39ab018f71dbe3fe54eb56e  __init__.py  MATCH
0d806068ca22c46512e5733a702f0c70553c0a7601cad94412facb2d84925272  embedding_index.py  MATCH
3659df156e67721e5af0b76752a1872e2944e44ef05d9af007b860434643d658  embeddings.py  MATCH
ffc27abd0f1ffe1ffa01c79c34dbbbb5b7a99ba72b7a75c8e9a0d1b7cbb94315  holographic.py  MATCH
e4fd2162452937812136d107c7d2c7c4472a1220433d972a3199ceebc9d183e1  retrieval.py  MATCH
98e1de5f2efdfb4ef617386aa45fabfd7c0f972763907f44623ad849a18030f2  store.py  MATCH
75d33ea89b5bdd085307b3061efc53b156ca3fdf0bf23a48b4a79f1e60179c1b  test_entities_p0.py  MATCH
d294d8d1925f0f6a8588c7799fccf8b9975a1a6afa228cdb5721b7ddc53b24f3  test_p0.py  MATCH
4d7176fe6d4ba6b138d1d375c8cdc7bbe3ed365681681dab7b6f291ea3425366  test_rebuild_p0.py  MATCH
510669e538551ec8d9244955f5cb9b25baf5b954e2b5b57284e9e84d066c066b  test_semantic_phase106.py  MATCH
a28775b8b30e6c07cfa3b291592de0fe54d31574323e6b2b5e00db281452446b  test_sweep_p0.py  MATCH
9822ea221e44ea5128690e0c5f63beac72a130c5d5a44c512341b449d2b5889c  test_timing_phase104.py  MATCH
a77cd95ed27bab7552d83b4036a5d453a78e0491953d7bce5475ea485a8d2917  validate_entities_mutations.py  MATCH
````

### Python 语法验证

时间（UTC）：2026-10-13T10:55:27.973906+00:00；退出码：0。

````text
$ compile 13 copied *.py in memory (no bytecode/files written)
PASS: all 13 Python files compile; no code executed.
````

### 新仓文件状态

时间（UTC）：2026-10-13T10:55:27.976538+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git status --short
?? .gitignore
?? LICENSE
?? NOTICE
?? __init__.py
?? embedding_index.py
?? embeddings.py
?? holographic.py
?? plugin.yaml
?? retrieval.py
?? store.py
?? test_entities_p0.py
?? test_p0.py
?? test_rebuild_p0.py
?? test_semantic_phase106.py
?? test_sweep_p0.py
?? test_timing_phase104.py
?? validate_entities_mutations.py
````

### 未导入的生产目录内容

时间（UTC）：2026-10-13T10:56:14.685451+00:00；退出码：0。

````text
$ inventory minus production source allowlist
.entities-validation
.entities-validation/array-snapshot-fixed.json
.entities-validation/array-snapshot-original.json
.entities-validation/baseline-fixture-updated.log
.entities-validation/entities-tests.log
.entities-validation/full-suite.log
.entities-validation/mutation-retrieval.log
.entities-validation/mutation-store.log
.entities-validation/mutation-tool.log
.entities-validation/negative-controls.log
.entities-validation/source-changes.diff
.entities-validation/source-review.log
.entities-validation/tmp
__init__.py.bak-2026-10-13
__init__.py.bak-20261013
__pycache__
__pycache__/__init__.cpython-311.pyc
__pycache__/__init__.cpython-314.pyc
__pycache__/embedding_index.cpython-311.pyc
__pycache__/embedding_index.cpython-314.pyc
__pycache__/embeddings.cpython-311.pyc
__pycache__/embeddings.cpython-314.pyc
__pycache__/holographic.cpython-311.pyc
__pycache__/holographic.cpython-314.pyc
__pycache__/retrieval.cpython-311.pyc
__pycache__/retrieval.cpython-314.pyc
__pycache__/store.cpython-311.pyc
__pycache__/store.cpython-314.pyc
__pycache__/test_entities_p0.cpython-311.pyc
__pycache__/test_entities_p0.cpython-314.pyc
__pycache__/test_p0.cpython-311.pyc
__pycache__/test_p0.cpython-314.pyc
__pycache__/test_rebuild_p0.cpython-311.pyc
__pycache__/test_rebuild_p0.cpython-314.pyc
__pycache__/test_sweep_p0.cpython-311.pyc
__pycache__/test_sweep_p0.cpython-314.pyc
__pycache__/test_timing_phase104.cpython-314.pyc
__pycache__/validate_entities_mutations.cpython-314.pyc
retrieval.py.bak-2026-10-13
retrieval.py.bak-20261013
store.py.bak-2026-10-13
store.py.bak-20261013
test_sweep_p0.py.bak-2026-10-13
work_report_holographic_entities.md
work_report_phase104.md
work_report_phase106.md
````

### dreaming 待暂存检查

时间（UTC）：2026-10-13T10:56:14.688496+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git diff --cached --name-only

````

### dreaming 已跟踪插件文件

时间（UTC）：2026-10-13T10:56:14.691143+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git ls-files plugin/holographic-plus
plugin/holographic-plus/NOTICE
plugin/holographic-plus/__init__.py
plugin/holographic-plus/embedding_index.py
plugin/holographic-plus/embeddings.py
plugin/holographic-plus/holographic.py
plugin/holographic-plus/plugin.yaml
plugin/holographic-plus/retrieval.py
plugin/holographic-plus/store.py
````

### dreaming 本地与 origin/main

时间（UTC）：2026-10-13T10:56:14.694236+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git rev-list --left-right --count HEAD...origin/main
0	0
````

### .gitmodules 开工检查

时间（UTC）：2026-10-13T10:56:14.694438+00:00；退出码：0。

````text
$ exists dreaming/.gitmodules
absent
````

### 新仓 origin 配置

时间（UTC）：2026-10-13T10:56:14.696952+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git remote -v
origin	http://192.168.71.67:4100/zijianzhou/holographic-plus.git (fetch)
origin	http://192.168.71.67:4100/zijianzhou/holographic-plus.git (push)
````

### 新仓分支状态

时间（UTC）：2026-10-13T10:56:14.699244+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git symbolic-ref HEAD
refs/heads/main
````

### README 草稿准备

时间（UTC）：2026-10-13T10:56:14.699514+00:00；退出码：0。

````text
$ write standalone README draft in audit directory
Draft ready; based on copied code and dreaming/docs/holographic-plus.md.
````

### 步骤 2：README 与 NOTICE

时间（UTC）：2026-10-13T10:56:56.955628+00:00；退出码：0。

````text
$ copy prepared README; fix NOTICE license path for repository root
README.md: newly written from copied source and dreaming/docs/holographic-plus.md because both specified README sources are absent.
NOTICE: preserved upstream attribution/license; changed only "see ../../LICENSE" to "see LICENSE".
````

### 步骤 3：设置 main 分支

时间（UTC）：2026-10-13T10:56:56.960294+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git symbolic-ref HEAD refs/heads/main

````

### 步骤 3：暂存插件导入

时间（UTC）：2026-10-13T10:56:56.973304+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git add -- .gitignore __init__.py embedding_index.py embeddings.py holographic.py retrieval.py store.py test_entities_p0.py test_p0.py test_rebuild_p0.py test_semantic_phase106.py test_sweep_p0.py test_timing_phase104.py validate_entities_mutations.py plugin.yaml README.md LICENSE NOTICE

````

### 导入 diff 检查

时间（UTC）：2026-10-13T10:56:56.977394+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git diff --cached --check

````

### 插件仓待提交清单

时间（UTC）：2026-10-13T10:56:56.982978+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git diff --cached --stat
 .gitignore                     |   5 +
 LICENSE                        |  21 +
 NOTICE                         |  38 ++
 README.md                      |  75 ++++
 __init__.py                    | 629 ++++++++++++++++++++++++++
 embedding_index.py             |  65 +++
 embeddings.py                  | 239 ++++++++++
 holographic.py                 | 304 +++++++++++++
 plugin.yaml                    |   3 +
 retrieval.py                   | 995 +++++++++++++++++++++++++++++++++++++++++
 store.py                       | 936 ++++++++++++++++++++++++++++++++++++++
 test_entities_p0.py            | 141 ++++++
 test_p0.py                     |  84 ++++
 test_rebuild_p0.py             |  47 ++
 test_semantic_phase106.py      | 169 +++++++
 test_sweep_p0.py               |  46 ++
 test_timing_phase104.py        | 153 +++++++
 validate_entities_mutations.py | 110 +++++
 18 files changed, 4060 insertions(+)
````

### 步骤 3：插件初始提交

时间（UTC）：2026-10-13T10:56:56.993843+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git commit -m 'Initial import: holographic-plus memory provider (live production copy)'
[main (root-commit) 3521896] Initial import: holographic-plus memory provider (live production copy)
 18 files changed, 4060 insertions(+)
 create mode 100644 .gitignore
 create mode 100644 LICENSE
 create mode 100644 NOTICE
 create mode 100644 README.md
 create mode 100644 __init__.py
 create mode 100644 embedding_index.py
 create mode 100644 embeddings.py
 create mode 100644 holographic.py
 create mode 100644 plugin.yaml
 create mode 100644 retrieval.py
 create mode 100644 store.py
 create mode 100644 test_entities_p0.py
 create mode 100644 test_p0.py
 create mode 100644 test_rebuild_p0.py
 create mode 100644 test_semantic_phase106.py
 create mode 100644 test_sweep_p0.py
 create mode 100644 test_timing_phase104.py
 create mode 100644 validate_entities_mutations.py
````

### 步骤 3：推送插件仓到 Gitea

时间（UTC）：2026-10-13T10:56:57.983892+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git push -u origin main
remote: . Processing 1 references        
remote: Processed 1 references in total        
To http://192.168.71.67:4100/zijianzhou/holographic-plus.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
````

### 插件仓 HEAD

时间（UTC）：2026-10-13T10:56:57.988244+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git rev-parse HEAD
3521896162c86d6beced36820cae62753f0c3239
````

### 插件仓远程默认分支

时间（UTC）：2026-10-13T10:56:58.604938+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git ls-remote --symref origin HEAD
ref: refs/heads/main	HEAD
3521896162c86d6beced36820cae62753f0c3239	HEAD
````

### 步骤 4a：删除 GitHub 远程

时间（UTC）：2026-10-13T10:57:22.677395+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git remote remove github

````

### 步骤 4a：确认仅有 Gitea 远程

时间（UTC）：2026-10-13T10:57:22.679841+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git remote -v
origin	http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git (fetch)
origin	http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git (push)
````

### 步骤 4b：从索引移除内嵌插件

时间（UTC）：2026-10-13T10:57:22.683587+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git rm -r --cached -- plugin/holographic-plus
rm 'plugin/holographic-plus/NOTICE'
rm 'plugin/holographic-plus/__init__.py'
rm 'plugin/holographic-plus/embedding_index.py'
rm 'plugin/holographic-plus/embeddings.py'
rm 'plugin/holographic-plus/holographic.py'
rm 'plugin/holographic-plus/plugin.yaml'
rm 'plugin/holographic-plus/retrieval.py'
rm 'plugin/holographic-plus/store.py'
````

### 步骤 4b：删除唯一获准的插件路径

时间（UTC）：2026-10-13T10:57:22.686709+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && rm -r -- /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin/plugin/holographic-plus

````

### 步骤 4c：添加 Gitea submodule

时间（UTC）：2026-10-13T10:57:23.350052+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git submodule add http://192.168.71.67:4100/zijianzhou/holographic-plus.git plugin/holographic-plus
Cloning into '/vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin/plugin/holographic-plus'...
````

### 步骤 4d：.gitmodules 原始内容

时间（UTC）：2026-10-13T10:57:23.352031+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && cat .gitmodules
[submodule "plugin/holographic-plus"]
	path = plugin/holographic-plus
	url = http://192.168.71.67:4100/zijianzhou/holographic-plus.git
````

### 步骤 4d：核对 submodule URL

时间（UTC）：2026-10-13T10:57:23.354481+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git config -f .gitmodules --get submodule.plugin/holographic-plus.url
http://192.168.71.67:4100/zijianzhou/holographic-plus.git
````

### submodule HEAD

时间（UTC）：2026-10-13T10:57:23.357462+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin/plugin/holographic-plus && git rev-parse HEAD
3521896162c86d6beced36820cae62753f0c3239
````

### 独立插件 HEAD 核对

时间（UTC）：2026-10-13T10:57:23.360083+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git rev-parse HEAD
3521896162c86d6beced36820cae62753f0c3239
````

### submodule 源码核对

时间（UTC）：2026-10-13T10:57:23.362127+00:00；退出码：0。

````text
$ SHA256 every submodule *.py vs production start snapshot
PASS: all 13 submodule Python files match the production start snapshot.
````

### dreaming 暂存 diff 检查

时间（UTC）：2026-10-13T10:57:23.367229+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git diff --cached --check

````

### dreaming 暂存变更清单

时间（UTC）：2026-10-13T10:57:23.370405+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git diff --cached --summary
 create mode 100644 .gitmodules
 create mode 160000 plugin/holographic-plus
 delete mode 100644 plugin/holographic-plus/NOTICE
 delete mode 100644 plugin/holographic-plus/__init__.py
 delete mode 100644 plugin/holographic-plus/embedding_index.py
 delete mode 100644 plugin/holographic-plus/embeddings.py
 delete mode 100644 plugin/holographic-plus/holographic.py
 delete mode 100644 plugin/holographic-plus/plugin.yaml
 delete mode 100644 plugin/holographic-plus/retrieval.py
 delete mode 100644 plugin/holographic-plus/store.py
````

### dreaming 暂存 diff

时间（UTC）：2026-10-13T10:57:23.377050+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git diff --cached -- .gitmodules plugin/holographic-plus
diff --git a/.gitmodules b/.gitmodules
new file mode 100644
index 0000000..def8c6d
--- /dev/null
+++ b/.gitmodules
@@ -0,0 +1,3 @@
+[submodule "plugin/holographic-plus"]
+	path = plugin/holographic-plus
+	url = http://192.168.71.67:4100/zijianzhou/holographic-plus.git
diff --git a/plugin/holographic-plus b/plugin/holographic-plus
new file mode 160000
index 0000000..3521896
--- /dev/null
+++ b/plugin/holographic-plus
@@ -0,0 +1 @@
+Subproject commit 3521896162c86d6beced36820cae62753f0c3239
diff --git a/plugin/holographic-plus/NOTICE b/plugin/holographic-plus/NOTICE
deleted file mode 100644
index b7f2b61..0000000
--- a/plugin/holographic-plus/NOTICE
+++ /dev/null
@@ -1,38 +0,0 @@
-holographic-plus — attribution and derivation
-=============================================
-
-This directory is a fork of the `holographic` memory provider that ships
-with Hermes Agent (MIT License, Copyright (c) 2025 Nous Research; the
-original plugin was contributed by dusterbloom).
-
-Upstream: https://github.com/NousResearch/hermes-agent
-         plugins/memory/holographic/
-
-Changes made in this fork: semantic embedding sidecar tables and blended
-retrieval, semantic entity resolution, CJK entity extraction, and
-configuration-driven HRR dimension. The modifications are released under
-the same MIT License as the rest of this repository (see ../../LICENSE).
-
-The upstream MIT license text, as it applies to the derived files, is:
-
-  MIT License
-
-  Copyright (c) 2025 Nous Research
-
-  Permission is hereby granted, free of charge, to any person obtaining a copy
-  of this software and associated documentation files (the "Software"), to deal
-  in the Software without restriction, including without limitation the rights
-  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
-  copies of the Software, and to permit persons to whom the Software is
-  furnished to do so, subject to the following conditions:
-
-  The above copyright notice and this permission notice shall be included in all
-  copies or substantial portions of the Software.
-
-  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
-  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
-  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
-  SOFTWARE.
diff --git a/plugin/holographic-plus/__init__.py b/plugin/holographic-plus/__init__.py
deleted file mode 100644
index 1deb448..0000000
--- a/plugin/holographic-plus/__init__.py
+++ /dev/null
@@ -1,604 +0,0 @@
-"""holographic-plus — embedding-augmented fork of the bundled holographic memory plugin.
-
-PORTED: paths parameterized; the plugin itself reads only its own config keys.
-
-Built on top of Hermes' bundled `holographic` provider (MIT, original plugin by
-dusterbloom). Adds:
-
-- Semantic retrieval: an embedding sidecar table (provider configurable;
-  the reference deployment uses DashScope text-embedding-v4), cosine candidate
-  pool merged with FTS5, blended scoring
-- Semantic entity resolution: high-cosine entity names merge as aliases
-- CJK entity extraction (「」《》"" quoted spans) + explicit entities param
-  on fact_store(add)
-
-It shares the SAME SQLite database as the bundled provider (memory_store.db);
-sidecar tables are additive. Rolling back = set memory.provider: holographic.
-
-Config in $HERMES_HOME/config.yaml (profile-scoped):
-  plugins:
-    holographic-plus:
-      db_path: $HERMES_HOME/memory_store.db
-      auto_extract: false
-      default_trust: 0.5
-      min_trust_threshold: 0.3
-      temporal_decay_half_life: 0
-      embedding_enabled: true
-      embedding_model: text-embedding-v4
-      embedding_dim: 1024
-      embedding_timeout_s: 3.0
-      semantic_weight: 0.45
-      fts_weight: 0.25
-      jaccard_weight: 0.15
-      hrr_weight: 0.15
-      entity_merge_threshold: 0.88
-"""
-
-from __future__ import annotations
-
-import json
-import logging
-import os
-import hashlib
-import fcntl
-import uuid
-import threading
-import sys
-import re
-from datetime import datetime, timezone, timedelta
-from pathlib import Path
-from typing import Any, Dict, List
-
-from agent.memory_provider import MemoryProvider
-from tools.registry import tool_error
-from utils import is_truthy_value
-from .store import MemoryStore
-from .retrieval import FactRetriever
-from hermes_cli.config import cfg_get
-
-logger = logging.getLogger(__name__)
-
-
-_PROVIDER_CODE_HASH=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
-_TELEMETRY_INSTANCE=str(uuid.uuid4())
-_TELEMETRY_START=None
-_TELEMETRY_END=None
-_TELEMETRY_THREAD=None
-_TELEMETRY_GUARD=threading.RLock()
-
-
-def _telemetry_path():
-    from hermes_constants import get_hermes_home
-    return Path(get_hermes_home())/'state/fact-recalls.jsonl'
-
-
-def _telemetry_base(source):
-    start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]
-    return {'schema':'dream-decay-1','event_id':str(uuid.uuid4()),'occurred_at':datetime.now(timezone.utc).isoformat(),
-            'source':source,'provider_code_hash':_PROVIDER_CODE_HASH,'instance_id':_TELEMETRY_INSTANCE,
-            'process_id':os.getpid(),'process_start':start_ticks,'session_id':None,'fact_ids':[]}
-
-
-def _telemetry_append(event):
-    path=_telemetry_path();path.parent.mkdir(parents=True,exist_ok=True)
-    lock=Path(str(path)+'.lock');lock.touch(mode=0o600,exist_ok=True)
-    with lock.open('r+') as guard:
-        fcntl.flock(guard,fcntl.LOCK_EX)
-        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
-        with os.fdopen(fd,'ab') as out:out.write(json.dumps(event,sort_keys=True).encode()+b'\n');out.flush();os.fsync(out.fileno())
-        fcntl.flock(guard,fcntl.LOCK_UN)
-    os.chmod(path,0o600)
-
-
-def _telemetry_gap(source,exc):
-    # Independent sidecar: if the main log cannot be appended, persist a gap.
-    # If storage itself is unavailable, leases expire; never renew after failure.
-    global _TELEMETRY_END
-    _TELEMETRY_END=None
-    try:
-        path=Path(str(_telemetry_path())+'.gaps.jsonl');path.parent.mkdir(parents=True,exist_ok=True)
-        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
-        with os.fdopen(fd,'ab') as out:
-            out.write(json.dumps(dict(_telemetry_base('telemetry-gap'),failed_source=source,error=type(exc).__name__)).encode()+b'\n');out.flush();os.fsync(out.fileno())
-    except Exception:pass
-    logger.warning('Dreaming telemetry gap source=%s error=%s',source,type(exc).__name__)
-
-
-def _record_recall_event(facts, source, session_id=None):
-    try:
-        event=_telemetry_base(source);event['session_id']=session_id
-        event['fact_ids']=[{'fact_id':int(x['fact_id']),'content_hash':hashlib.sha256(x.get('content','').encode()).hexdigest()}
-                          for x in facts if isinstance(x,dict) and type(x.get('fact_id')) is int]
-        if event['fact_ids']:_telemetry_append(event)
-    except Exception as exc:_telemetry_gap(source,exc)
-
-
-def _coverage_heartbeat():
-    global _TELEMETRY_END
-    with _TELEMETRY_GUARD:
-        if _TELEMETRY_END is None:return
-        try:
-            event=_telemetry_base('telemetry-coverage')
-            event.update(coverage_start=event['occurred_at'],coverage_end=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat())
-            _telemetry_append(event);_TELEMETRY_END=event['coverage_end']
-        except Exception as exc:_telemetry_gap('telemetry-coverage',exc)
-
-
-def _record_telemetry_ready():
-    global _TELEMETRY_START,_TELEMETRY_END,_TELEMETRY_THREAD
-    with _TELEMETRY_GUARD:
-        if _TELEMETRY_START is not None:return
-        try:
-            event=_telemetry_base('telemetry-ready');_TELEMETRY_START=event['occurred_at']
-            event.update(coverage_start=_TELEMETRY_START,coverage_end=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat())
-            _telemetry_append(event);_TELEMETRY_END=event['coverage_end']
-            def heartbeat():
-                while True:
-                    threading.Event().wait(30)
-                    _coverage_heartbeat()
-            _TELEMETRY_THREAD=threading.Thread(target=heartbeat,name='dream-recall-coverage',daemon=True)
-            _TELEMETRY_THREAD.start()
-        except Exception as exc:_telemetry_gap('telemetry-ready',exc)
-
-
-# ---------------------------------------------------------------------------
-# Tool schemas (unchanged from original PR)
-# ---------------------------------------------------------------------------
-
-FACT_STORE_SCHEMA = {
-    "name": "fact_store",
-    "description": (
-        "Deep structured memory with algebraic reasoning. "
-        "Use alongside the memory tool — memory for always-on context, "
-        "fact_store for deep recall and compositional queries.\n\n"
-        "ACTIONS (simple → powerful):\n"
-        "• add — Store a fact the user would expect you to remember.\n"
-        "• search — Keyword lookup ('editor config', 'deploy process').\n"
-        "• probe — Entity recall: ALL facts about a person/thing.\n"
-        "• related — What connects to an entity? Structural adjacency.\n"
-        "• reason — Compositional: facts connected to MULTIPLE entities simultaneously.\n"
-        "• contradict — Memory hygiene: find facts making conflicting claims.\n"
-        "• update/remove/list — CRUD operations.\n\n"
-        "IMPORTANT: Before answering questions about the user, ALWAYS probe or reason first."
-    ),
-    "parameters": {
-        "type": "object",
-        "properties": {
-            "action": {
-                "type": "string",
-                "enum": ["add", "search", "probe", "related", "reason", "contradict", "update", "remove", "list"],
-            },
-            "content": {"type": "string", "description": "Fact content (required for 'add')."},
-            "query": {"type": "string", "description": "Search query (required for 'search')."},
-            "entity": {"type": "string", "description": "Entity name for 'probe'/'related'."},
-            "entities": {"type": "array", "items": {"type": "string"}, "description": "Entity names: for 'reason' (required); for 'add' (optional explicit entities, preferred over regex extraction)."},
-            "fact_id": {"type": "integer", "description": "Fact ID for 'update'/'remove'."},
-            "category": {"type": "string", "enum": ["user_pref", "project", "tool", "general"]},
-            "tags": {"type": "string", "description": "Comma-separated tags."},
-            "trust_delta": {"type": "number", "description": "Trust adjustment for 'update'."},
-            "min_trust": {"type": "number", "description": "Minimum trust filter (default: 0.3)."},
-            "limit": {"type": "integer", "description": "Max results (default: 10)."},
-        },
-        "required": ["action"],
-    },
-}
-
-FACT_FEEDBACK_SCHEMA = {
-    "name": "fact_feedback",
-    "description": (
-        "Rate a fact after using it. Mark 'helpful' if accurate, 'unhelpful' if outdated. "
-        "This trains the memory — good facts rise, bad facts sink."
-    ),
-    "parameters": {
-        "type": "object",
-        "properties": {
-            "action": {"type": "string", "enum": ["helpful", "unhelpful"]},
-            "fact_id": {"type": "integer", "description": "The fact ID to rate."},
-        },
-        "required": ["action", "fact_id"],
-    },
-}
-
-
-# ---------------------------------------------------------------------------
-# Config
-# ---------------------------------------------------------------------------
-
-def _load_plugin_config() -> dict:
-    try:
-        # Canonical loader: behavioral read now honors the managed-scope
-        # overlay + ${VAR} expansion (e.g. an api key template) too.
-        from hermes_cli.config import load_config_readonly
-        all_config = load_config_readonly()
-        return cfg_get(all_config, "plugins", "holographic-plus", default={}) or {}
-    except Exception:
-        return {}
-
-
-# ---------------------------------------------------------------------------
-# MemoryProvider implementation
-# ---------------------------------------------------------------------------
-
-class HolographicPlusMemoryProvider(MemoryProvider):
-    """Holographic memory + semantic embeddings (fork: holographic-plus)."""
-
-    def __init__(self, config: dict | None = None):
-        self._config = config or _load_plugin_config()
-        self._store = None
-        self._retriever = None
-        self._min_trust = float(self._config.get("min_trust_threshold", 0.3))
-
-    @property
-    def name(self) -> str:
-        return "holographic-plus"
-
-    def is_available(self) -> bool:
-        return True  # SQLite is always available, numpy is optional
-
-    def save_config(self, values, hermes_home):
-        """Write config to config.yaml under plugins.hermes-memory-store."""
-        from pathlib import Path
-        config_path = Path(hermes_home) / "config.yaml"
-        try:
-            import yaml
-            # Write-back round-trip: raw read is correct (merged defaults
-            # must not be persisted back into the user's file).
-            from hermes_cli.config import read_user_config_raw
-            existing = read_user_config_raw(config_path)
-            existing.setdefault("plugins", {})
-            existing["plugins"]["hermes-memory-store"] = values
-            with open(config_path, "w", encoding="utf-8") as f:
-                yaml.dump(existing, f, default_flow_style=False)
-        except Exception:
-            pass
-
-    def get_config_schema(self):
-        from hermes_constants import display_hermes_home
-        _default_db = f"{display_hermes_home()}/memory_store.db"
-        return [
-            {"key": "db_path", "description": "SQLite database path", "default": _default_db},
-            {"key": "auto_extract", "description": "Auto-extract facts at session end", "default": "false", "choices": ["true", "false"]},
-            {"key": "default_trust", "description": "Default trust score for new facts", "default": "0.5"},
-            {"key": "hrr_dim", "description": "HRR vector dimensions", "default": "1024"},
-        ]
-
-    def initialize(self, session_id: str, **kwargs) -> None:
-        from hermes_constants import get_hermes_home
-        _hermes_home = str(get_hermes_home())
-        _default_db = _hermes_home + "/memory_store.db"
-        db_path = self._config.get("db_path", _default_db)
-        # Expand $HERMES_HOME in user-supplied paths so config values like
-        # "$HERMES_HOME/memory_store.db" or "~/.hermes/memory_store.db" both
-        # resolve to the active profile's directory.
-        if isinstance(db_path, str):
-            db_path = db_path.replace("$HERMES_HOME", _hermes_home)
-            db_path = db_path.replace("${HERMES_HOME}", _hermes_home)
-        default_trust = float(self._config.get("default_trust", 0.5))
-        hrr_dim = int(self._config.get("hrr_dim", 1024))
-        hrr_weight = float(self._config.get("hrr_weight", 0.15))
-        fts_weight = float(self._config.get("fts_weight", 0.25))
-        jaccard_weight = float(self._config.get("jaccard_weight", 0.15))
-        semantic_weight = float(self._config.get("semantic_weight", 0.45))
-        temporal_decay = int(self._config.get("temporal_decay_half_life", 0))
-        entity_merge_threshold = float(self._config.get("entity_merge_threshold", 0.88))
-
-        # holographic-plus: embedding client (fail-open; disabled without key)
-        embedder = None
-        if is_truthy_value(self._config.get("embedding_enabled", True)):
-            from .embeddings import EmbeddingClient
-            embedder = EmbeddingClient(
-                base_url=str(self._config.get("embedding_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")),
-                model=str(self._config.get("embedding_model", "text-embedding-v4")),
-                dim=int(self._config.get("embedding_dim", 1024)),
-                timeout_s=float(self._config.get("embedding_timeout_s", 3.0)),
-                enabled=True,
-                api_key=self._config.get("embedding_api_key") or None,
-            )
-
-        self._store = MemoryStore(
-            db_path=db_path,
-            default_trust=default_trust,
-            hrr_dim=hrr_dim,
-            embedder=embedder,
-            entity_merge_threshold=entity_merge_threshold,
-        )
-        self._retriever = FactRetriever(
-            store=self._store,
-            temporal_decay_half_life=temporal_decay,
-            fts_weight=fts_weight,
-            jaccard_weight=jaccard_weight,
-            hrr_weight=hrr_weight,
-            semantic_weight=semantic_weight,
-            hrr_dim=hrr_dim,
-        )
-        _record_telemetry_ready()
-        self._session_id = session_id
-
-    def system_prompt_block(self) -> str:
-        if not self._store:
-            return ""
-        try:
-            total = self._store._conn.execute(
-                "SELECT COUNT(*) FROM facts"
-            ).fetchone()[0]
-        except Exception:
-            total = 0
-        if total == 0:
-            return (
-                "# Holographic Memory\n"
-                "Active. Empty fact store — proactively add facts the user would expect you to remember.\n"
-                "Use fact_store(action='add') to store durable structured facts about people, projects, preferences, decisions.\n"
-                "Use fact_feedback to rate facts after using them (trains trust scores)."
-            )
-        return (
-            f"# Holographic Memory\n"
-            f"Active. {total} facts stored with entity resolution and trust scoring.\n"
-            f"Use fact_store to search, probe entities, reason across entities, or add facts.\n"
-            f"Use fact_feedback to rate facts after using them (trains trust scores)."
-        )
-
-    def prefetch(self, query: str, *, session_id: str = "") -> str:
-        if not self._retriever or not query:
-            return ""
-        try:
-            results = self._retriever.search(query, min_trust=self._min_trust, limit=5)
-            if not results:
-                return ""
-            lines = []
-            for r in results:
-                trust = r.get("trust_score", r.get("trust", 0))
-                lines.append(f"- [{trust:.1f}] {r.get('content', '')}")
-            _record_recall_event(results, "prefetch", session_id or None)
-            return "## Holographic Memory\n" + "\n".join(lines)
-        except Exception as e:
-            logger.debug("Holographic prefetch failed: %s", e)
-            return ""
-
-    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
-        # Holographic memory stores explicit facts via tools, not auto-sync.
-        # The on_session_end hook handles auto-extraction if configured.
-        pass
-
-    def get_tool_schemas(self) -> List[Dict[str, Any]]:
-        return [FACT_STORE_SCHEMA, FACT_FEEDBACK_SCHEMA]
-
-    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
-        if tool_name == "fact_store":
-            return self._handle_fact_store(args)
-        elif tool_name == "fact_feedback":
-            return self._handle_fact_feedback(args)
-        return tool_error(f"Unknown tool: {tool_name}")
-
-    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
-        # is_truthy_value: the config schema declares auto_extract as a string
-        # enum ("false"/"true"), and a plain truthiness check treats the string
-        # "false" as enabled (#57682).
-        if not is_truthy_value(self._config.get("auto_extract", False)):
-            return
-        if not self._store or not messages:
-            return
-        self._auto_extract_facts(messages)
-
-    def on_memory_write(self, action: str, target: str, content: str) -> None:
-        """Mirror built-in memory writes as facts."""
-        if action == "add" and self._store and content:
-            try:
-                category = "user_pref" if target == "user" else "general"
-                self._store.add_fact(content, category=category)
-            except Exception as e:
-                logger.debug("Holographic memory_write mirror failed: %s", e)
-
-    def shutdown(self) -> None:
-        # Release the shared SQLite connection deterministically on the
-        # caller's thread. Dropping the reference alone leaves fd finalization
-        # to GC, which keeps the connection (and its write lock) alive on a
-        # long-running gateway and prolongs the "database is locked" contention
-        # this store's shared-connection refcounting is meant to eliminate.
-        # close() is idempotent and refcount-guarded, so siblings stay safe.
-        if self._store is not None:
-            try:
-                self._store.close()
-            except Exception as e:
-                logger.debug("Holographic shutdown close() failed: %s", e)
-        self._store = None
-        self._retriever = None
-
-    # -- Tool handlers -------------------------------------------------------
-
-    def _handle_fact_store(self, args: dict) -> str:
-        try:
-            action = args["action"]
-            store = self._store
-            retriever = self._retriever
-
-            if action == "add":
-                fact_id = store.add_fact(
-                    args["content"],
-                    category=args.get("category", "general"),
-                    tags=args.get("tags", ""),
-                    entities=args.get("entities"),
-                )
-                return json.dumps({"fact_id": fact_id, "status": "added"})
-
-            elif action == "search":
-                results = retriever.search(
-                    args["query"],
-                    category=args.get("category"),
-                    min_trust=float(args.get("min_trust", self._min_trust)),
-                    limit=int(args.get("limit", 10)),
-                )
-                _record_recall_event(results, "provider_tool_search")
-                return json.dumps({"results": results, "count": len(results)})
-
-            elif action == "probe":
-                results = retriever.probe(
-                    args["entity"],
-                    category=args.get("category"),
-                    limit=int(args.get("limit", 10)),
-                )
-                _record_recall_event(results, "provider_tool_probe")
-                return json.dumps({"results": results, "count": len(results)})
-
-            elif action == "related":
-                results = retriever.related(
-                    args["entity"],
-                    category=args.get("category"),
-                    limit=int(args.get("limit", 10)),
-                )
-                _record_recall_event(results, "provider_tool_related")
-                return json.dumps({"results": results, "count": len(results)})
-
-            elif action == "reason":
-                entities = args.get("entities", [])
-                if not entities:
-                    return tool_error("reason requires 'entities' list")
-                results = retriever.reason(
-                    entities,
-                    category=args.get("category"),
-                    limit=int(args.get("limit", 10)),
-                )
-                _record_recall_event(results, "provider_tool_reason")
-                return json.dumps({"results": results, "count": len(results)})
-
-            elif action == "contradict":
-                results = retriever.contradict(
-                    category=args.get("category"),
-                    limit=int(args.get("limit", 10)),
-                )
-                return json.dumps({"results": results, "count": len(results)})
-
-            elif action == "update":
-                updated = store.update_fact(
-                    int(args["fact_id"]),
-                    content=args.get("content"),
-                    trust_delta=float(args["trust_delta"]) if "trust_delta" in args else None,
-                    tags=args.get("tags"),
-                    category=args.get("category"),
-                )
-                return json.dumps({"updated": updated})
-
-            elif action == "remove":
-                removed = store.remove_fact(int(args["fact_id"]))
-                return json.dumps({"removed": removed})
-
-            elif action == "list":
-                facts = store.list_facts(
-                    category=args.get("category"),
-                    min_trust=float(args.get("min_trust", 0.0)),
-                    limit=int(args.get("limit", 10)),
-                )
-                return json.dumps({"facts": facts, "count": len(facts)})
-
-            else:
-                return tool_error(f"Unknown action: {action}")
-
-        except KeyError as exc:
-            return tool_error(f"Missing required argument: {exc}")
-        except Exception as exc:
-            return tool_error(str(exc))
-
-    def _handle_fact_feedback(self, args: dict) -> str:
-        try:
-            fact_id = int(args["fact_id"])
-            helpful = args["action"] == "helpful"
-            result = self._store.record_feedback(fact_id, helpful=helpful)
-            return json.dumps(result)
-        except KeyError as exc:
-            return tool_error(f"Missing required argument: {exc}")
-        except Exception as exc:
-            return tool_error(str(exc))
-
-    # -- Auto-extraction (on_session_end) ------------------------------------
-
-    def _auto_extract_facts(self, messages: list) -> None:
-        # Local import (pattern used in initialize()): the compressor module is
-        # heavier than this plugin and is only needed when auto_extract is on.
-        from agent.context_compressor import (
-            _MERGED_PRIOR_CONTEXT_HEADER,
-            _MERGED_SUMMARY_DELIMITER,
-            is_compaction_summary_message,
-        )
-
-        def _pre_delimiter_user_segment(msg: dict):
-            """Return the genuine user text preceding a merged-into-tail
-            compaction summary, or None when the whole message is a summary.
-
-            Merge-into-tail messages (agent/context_compressor.py ~3163-3190)
-            wrap real prior tail content BEFORE ``_MERGED_SUMMARY_DELIMITER``,
-            prefixed with ``_MERGED_PRIOR_CONTEXT_HEADER``, then append the
-            generated handoff summary AFTER the delimiter. Dropping the whole
-            row (as ``is_compaction_summary_message`` alone would suggest)
-            discards that genuine pre-delimiter content too (#57690 review).
-            Only the summary suffix must be excluded from harvesting.
-            """
-            content = msg.get("content", "")
-            if not isinstance(content, str) or _MERGED_SUMMARY_DELIMITER not in content:
-                return None
-            pre = content.split(_MERGED_SUMMARY_DELIMITER, 1)[0]
-            if pre.startswith(_MERGED_PRIOR_CONTEXT_HEADER):
-                pre = pre[len(_MERGED_PRIOR_CONTEXT_HEADER):]
-            pre = pre.strip()
-            return pre or None
-
-        _PREF_PATTERNS = [
-            re.compile(r'\bI\s+(?:prefer|like|love|use|want|need)\s+(.+)', re.IGNORECASE),
-            re.compile(r'\bmy\s+(?:favorite|preferred|default)\s+\w+\s+is\s+(.+)', re.IGNORECASE),
-            re.compile(r'\bI\s+(?:always|never|usually)\s+(.+)', re.IGNORECASE),
-        ]
-        _DECISION_PATTERNS = [
-            re.compile(r'\bwe\s+(?:decided|agreed|chose)\s+(?:to\s+)?(.+)', re.IGNORECASE),
-            re.compile(r'\bthe\s+project\s+(?:uses|needs|requires)\s+(.+)', re.IGNORECASE),
-        ]
-
-        extracted = 0
-        for msg in messages:
-            if msg.get("role") != "user":
-                continue
-            # Compaction handoff summaries can be inserted as role="user"
-            # messages; their prose reliably matches the decision patterns, so
-            # without this guard the compactor's own output is stored as a
-            # durable "fact" on every rollover (#57682). A merge-into-tail
-            # summary also carries genuine pre-delimiter user content in the
-            # SAME row; harvest that segment instead of dropping the whole
-            # message (#57690 review).
-            pre_delimiter_segment = _pre_delimiter_user_segment(msg)
-            if pre_delimiter_segment is not None:
-                content = pre_delimiter_segment
-            elif is_compaction_summary_message(msg):
-                continue
-            else:
-                content = msg.get("content", "")
-            if not isinstance(content, str) or len(content) < 10:
-                continue
-
-            for pattern in _PREF_PATTERNS:
-                if pattern.search(content):
-                    try:
-                        self._store.add_fact(content[:400], category="user_pref")
-                        extracted += 1
-                    except Exception:
-                        pass
-                    break
-
-            for pattern in _DECISION_PATTERNS:
-                if pattern.search(content):
-                    try:
-                        self._store.add_fact(content[:400], category="project")
-                        extracted += 1
-                    except Exception:
-                        pass
-                    break
-
-        if extracted:
-            logger.info("Auto-extracted %d facts from conversation", extracted)
-
-
-# ---------------------------------------------------------------------------
-# Plugin entry point
-# ---------------------------------------------------------------------------
-
-def register(ctx) -> None:
-    """Register the holographic-plus memory provider with the plugin system."""
-    config = _load_plugin_config()
-    provider = HolographicPlusMemoryProvider(config=config)
-    ctx.register_memory_provider(provider)
diff --git a/plugin/holographic-plus/embedding_index.py b/plugin/holographic-plus/embedding_index.py
deleted file mode 100644
index 1743d60..0000000
--- a/plugin/holographic-plus/embedding_index.py
+++ /dev/null
@@ -1,65 +0,0 @@
-"""Sidecar-only schema and read-only consistency inspection (no MemoryStore init)."""
-import hashlib
-import math
-
-SOURCES = (("facts", "fact_embeddings", "fact_id", "content"),
-           ("entities", "entity_embeddings", "entity_id", "name"))
-
-
-def text_hash(text):
-    return hashlib.sha256(text.encode("utf-8")).hexdigest()
-
-
-def inspect(conn, model="text-embedding-v4", dim=1024):
-    result = {}
-    for source, sidecar, key, column in SOURCES:
-        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({sidecar})")}
-        originals = dict(conn.execute(f"SELECT {key}, {column} FROM {source}"))
-        expression = "content_hash" if "content_hash" in cols else "NULL"
-        rows = {r[0]: r[1:] for r in conn.execute(
-            f"SELECT {key}, model, dim, vector, {expression} FROM {sidecar}")} if cols else {}
-        missing, stale, orphan = [], [], sorted(set(rows) - set(originals))
-        for ident, text in originals.items():
-            if ident not in rows:
-                missing.append(ident)
-                continue
-            m, d, vector, digest = rows[ident]
-            invalid = m != model or d != dim or digest != text_hash(text)
-            try:
-                import embeddings as emb
-                decoded = emb.bytes_to_vec(vector)
-                invalid |= len(decoded) != dim or not all(math.isfinite(v) for v in decoded)
-            except Exception:
-                invalid = True
-            if invalid:
-                stale.append(ident)
-        result[source] = {"source_count": len(originals), "embedding_count": len(rows),
-                          "hash_column": "content_hash" in cols,
-                          "missing": sorted(missing), "stale": sorted(stale), "orphan": orphan}
-    return result
-
-
-def migrate(conn):
-    # Only sidecar tables change. Do not initialize any base schema/FTS/banks.
-    for source, sidecar, key, _ in SOURCES:
-        conn.execute(f"CREATE TABLE IF NOT EXISTS {sidecar} ("
-                     f"{key} INTEGER PRIMARY KEY REFERENCES {source}({key}), "
-                     "model TEXT NOT NULL, dim INTEGER NOT NULL, vector BLOB NOT NULL, "
-                     "content_hash TEXT" +
-                     (", created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if source == "facts" else "") + ")")
-        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({sidecar})")}
-        if "content_hash" not in cols:
-            conn.execute(f"ALTER TABLE {sidecar} ADD COLUMN content_hash TEXT")
-
-
-def save_if_current(conn, spec, ident, text, vector, model):
-    import embeddings as emb
-    source, sidecar, key, column = spec
-    cur = conn.execute(
-        f"INSERT INTO {sidecar} ({key},model,dim,vector,content_hash) "
-        f"SELECT {key},?,?,?,? FROM {source} WHERE {key}=? AND {column}=? "
-        f"ON CONFLICT({key}) DO UPDATE SET model=excluded.model,dim=excluded.dim,"
-        "vector=excluded.vector,content_hash=excluded.content_hash" +
-        (",created_at=CURRENT_TIMESTAMP" if source == "facts" else ""),
-        (model, len(vector), emb.vec_to_bytes(vector), text_hash(text), ident, text))
-    return cur.rowcount == 1
diff --git a/plugin/holographic-plus/embeddings.py b/plugin/holographic-plus/embeddings.py
deleted file mode 100644
index 06b9ba7..0000000
--- a/plugin/holographic-plus/embeddings.py
+++ /dev/null
@@ -1,173 +0,0 @@
-"""Semantic embedding client for holographic-plus.
-
-DashScope OpenAI-compatible embeddings (text-embedding-v4, 1024-dim by
-default). Design rules:
-
-- Fail-open everywhere: any API/network failure returns None and is logged;
-  fact writes and retrieval must NEVER break because embeddings are down.
-- Query-side in-memory LRU cache (prefetch fires per user message).
-- Batch API for backfill (DashScope accepts up to 10 inputs per call).
-
-API key resolution order:
-  1. explicit config embedding_api_key
-  2. env DASHSCOPE_API_KEY
-  3. disabled (no credential-file fallback)
-"""
-
-from __future__ import annotations
-
-import json
-import logging
-import math
-import os
-import struct
-import threading
-import urllib.request
-from collections import OrderedDict
-
-logger = logging.getLogger(__name__)
-
-_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
-_DEFAULT_MODEL = "text-embedding-v4"
-_DEFAULT_DIM = 1024
-_BATCH_SIZE = 10
-_LRU_MAX = 256
-_F32_PREFIX = b"EMB1"
-
-
-def _load_api_key() -> str:
-    return os.environ.get("DASHSCOPE_API_KEY", "").strip()
-
-
-class EmbeddingClient:
-    """Thread-safe, fail-open embedding client with LRU query cache."""
-
-    def __init__(
-        self,
-        base_url: str = _DEFAULT_BASE_URL,
-        model: str = _DEFAULT_MODEL,
-        dim: int = _DEFAULT_DIM,
-        timeout_s: float = 3.0,
-        enabled: bool = True,
-        api_key: str | None = None,
-    ) -> None:
-        self.base_url = base_url.rstrip("/")
-        self.model = model
-        self.dim = dim
-        self.timeout_s = timeout_s
-        self._api_key = (api_key or "").strip() or _load_api_key()
-        self.enabled = bool(enabled and self._api_key)
-        self._cache: OrderedDict[str, list[float]] = OrderedDict()
-        self._lock = threading.Lock()
-        if enabled and not self._api_key:
-            logger.warning("holographic-plus: embedding enabled but no API key found; semantic features disabled")
-
-    # ------------------------------------------------------------------
-    # Public API
-    # ------------------------------------------------------------------
-
-    def embed(self, text: str) -> list[float] | None:
-        """Embed a single text (cached). Returns None on any failure."""
-        if not self.enabled:
-            return None
-        text = (text or "").strip()
-        if not text:
-            return None
-        with self._lock:
-            hit = self._cache.get(text)
-            if hit is not None:
-                self._cache.move_to_end(text)
-                return hit
-        vec = self._request([text])
-        if vec is None:
-            return None
-        v = vec[0]
-        with self._lock:
-            self._cache[text] = v
-            if len(self._cache) > _LRU_MAX:
-                self._cache.popitem(last=False)
-        return v
-
-    def embed_batch(self, texts: list[str]) -> list[list[float] | None]:
-        """Embed many texts in batches of 10. Per-item None on failure."""
-        results: list[list[float] | None] = [None] * len(texts)
-        if not self.enabled or not texts:
-            return results
-        for start in range(0, len(texts), _BATCH_SIZE):
-            chunk_idx = list(range(start, min(start + _BATCH_SIZE, len(texts))))
-            chunk = [(texts[i] or "").strip() for i in chunk_idx]
-            vecs = self._request(chunk)
-            if vecs is None:
-                continue
-            for i, v in zip(chunk_idx, vecs):
-                results[i] = v
-        return results
-
-    # ------------------------------------------------------------------
-    # HTTP
-    # ------------------------------------------------------------------
-
-    def _request(self, inputs: list[str]) -> list[list[float]] | None:
-        payload = {
-            "model": self.model,
-            "input": inputs,
-            "dimensions": self.dim,
-            "encoding_format": "float",
-        }
-        req = urllib.request.Request(
-            self.base_url + "/embeddings",
-            data=json.dumps(payload).encode("utf-8"),
-            headers={
-                "Content-Type": "application/json",
-                "Authorization": "Bearer " + self._api_key,
-            },
-            method="POST",
-        )
-        try:
-            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
-                body = json.loads(resp.read().decode("utf-8"))
-            data = body.get("data") or []
-            # OpenAI-compatible: each item has embedding + index; sort by index
-            data.sort(key=lambda d: d.get("index", 0))
-            vecs = [d["embedding"] for d in data]
-            if len(vecs) != len(inputs):
-                logger.warning("embedding count mismatch: got %d want %d", len(vecs), len(inputs))
-                return None
-            if [d.get("index") for d in data] != list(range(len(inputs))):
-                logger.warning("embedding index mismatch")
-                return None
-            if any(len(v) != self.dim or any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in v) for v in vecs):
-                logger.warning("embedding dimension/nonfinite mismatch")
-                return None
-            return vecs
-        except Exception as e:
-            logger.warning("embedding request failed (%d inputs): %s", len(inputs), e)
-            return None
-
-
-# ----------------------------------------------------------------------
-# Vector (de)serialization + similarity (pure stdlib)
-# ----------------------------------------------------------------------
-
-def vec_to_bytes(vec: list[float]) -> bytes:
-    return _F32_PREFIX + struct.pack("<%df" % len(vec), *vec)
-
-
-def bytes_to_vec(data: bytes) -> list[float]:
-    if data.startswith(_F32_PREFIX):
-        data = data[len(_F32_PREFIX):]
-    n = len(data) // 4
-    return list(struct.unpack("<%df" % n, data))
-
-
-def cosine(a: list[float], b: list[float]) -> float:
-    dot = 0.0
-    na = 0.0
-    nb = 0.0
-    for x, y in zip(a, b):
-        dot += x * y
-        na += x * x
-        nb += y * y
-    if na == 0.0 or nb == 0.0:
-        return 0.0
-    return dot / (math.sqrt(na) * math.sqrt(nb))
diff --git a/plugin/holographic-plus/holographic.py b/plugin/holographic-plus/holographic.py
deleted file mode 100644
index 5623218..0000000
--- a/plugin/holographic-plus/holographic.py
+++ /dev/null
@@ -1,304 +0,0 @@
-"""Holographic Reduced Representations (HRR) with phase encoding.
-
-HRRs are a vector symbolic architecture for encoding compositional structure
-into fixed-width distributed representations. This module uses *phase vectors*:
-each concept is a vector of angles in [0, 2π). The algebraic operations are:
-
-  bind   — circular convolution (phase addition)  — associates two concepts
-  unbind — circular correlation (phase subtraction) — retrieves a bound value
-  bundle — superposition (circular mean)           — merges multiple concepts
-
-Phase encoding is numerically stable, avoids the magnitude collapse of
-traditional complex-number HRRs, and maps cleanly to cosine similarity.
-
-Atoms are generated deterministically from SHA-256 so representations are
-identical across processes, machines, and language versions.
-
-References:
-  Plate (1995) — Holographic Reduced Representations
-  Gayler (2004) — Vector Symbolic Architectures answer Jackendoff's challenges
-"""
-
-import hashlib
-import logging
-import struct
-import math
-import sys
-from pathlib import Path
-
-# The Hermes process interpreter ships no NumPy of its own. Script-side entry
-# points inject <HERMES_HOME>/pylibs themselves, but nothing did that for the
-# long-lived gateway/agent processes, so every fact written via the in-process
-# fact_store path was silently stored without hrr_vector (kanban t_f16f154e).
-# pylibs314 holds the NumPy build matching the gateway interpreter (cp314);
-# the older pylibs tree targets cp313 and cannot load here. Appended (not
-# prepended) so nothing in the runtime gets shadowed. This plugin lives under
-# the data dir, so runtime upgrades do not revert the injection.
-_PYLIBS314 = Path(__file__).resolve().parents[2] / "pylibs314"
-if _PYLIBS314.is_dir() and str(_PYLIBS314) not in sys.path:
-    sys.path.append(str(_PYLIBS314))
-
-try:
-    import numpy as np
-    _HAS_NUMPY = True
-except ImportError:
-    _HAS_NUMPY = False
-
-logger = logging.getLogger(__name__)
-
-_TWO_PI = 2.0 * math.pi
-_FLOAT32_BLOB_PREFIX = b"HRR1"
-
-
-def _require_numpy() -> None:
-    if not _HAS_NUMPY:
-        raise RuntimeError("numpy is required for holographic operations")
-
-
-def _np():
-    """Return the numpy module after the runtime availability guard."""
-    _require_numpy()
-    return np  # type: ignore[name-defined]
-
-
-def encode_atom(word: str, dim: int = 1024) -> "np.ndarray":
-    """Deterministic phase vector via SHA-256 counter blocks.
-
-    Uses hashlib (not numpy RNG) for cross-platform reproducibility.
-
-    Algorithm:
-    - Generate enough SHA-256 blocks by hashing f"{word}:{i}" for i=0,1,2,...
-    - Concatenate digests, interpret as uint16 values via struct.unpack
-    - Scale to [0, 2π): phases = values * (2π / 65536)
-    - Truncate to dim elements
-    - Returns np.float64 array of shape (dim,)
-    """
-    _require_numpy()
-
-    # Each SHA-256 digest is 32 bytes = 16 uint16 values.
-    values_per_block = 16
-    blocks_needed = math.ceil(dim / values_per_block)
-
-    uint16_values: list[int] = []
-    for i in range(blocks_needed):
-        digest = hashlib.sha256(f"{word}:{i}".encode()).digest()
-        uint16_values.extend(struct.unpack("<16H", digest))
-
-    phases = np.array(uint16_values[:dim], dtype=np.float64) * (_TWO_PI / 65536.0)
-    return phases
-
-
-def bind(a: "np.ndarray", b: "np.ndarray") -> "np.ndarray":
-    """Circular convolution = element-wise phase addition.
-
-    Binding associates two concepts into a single composite vector.
-    The result is dissimilar to both inputs (quasi-orthogonal).
-    """
-    _require_numpy()
-    return (a + b) % _TWO_PI
-
-
-def unbind(memory: "np.ndarray", key: "np.ndarray") -> "np.ndarray":
-    """Circular correlation = element-wise phase subtraction.
-
-    Unbinding retrieves the value associated with a key from a memory vector.
-    unbind(bind(a, b), a) ≈ b  (up to superposition noise)
-    """
-    _require_numpy()
-    return (memory - key) % _TWO_PI
-
-
-def bundle(*vectors: "np.ndarray") -> "np.ndarray":
-    """Superposition via circular mean of complex exponentials.
-
-    Bundling merges multiple vectors into one that is similar to each input.
-    The result can hold O(sqrt(dim)) items before similarity degrades.
-    """
-    _require_numpy()
-    complex_sum = np.sum([np.exp(1j * v) for v in vectors], axis=0)
-    return np.angle(complex_sum) % _TWO_PI
-
-
-def similarity(a: "np.ndarray", b: "np.ndarray") -> float:
-    """Phase cosine similarity. Range [-1, 1].
-
-    Returns 1.0 for identical vectors, near 0.0 for random (unrelated) vectors,
-    and -1.0 for perfectly anti-correlated vectors.
-    """
-    _require_numpy()
-    return float(np.mean(np.cos(a - b)))
-
-
-def encode_text(text: str, dim: int = 1024) -> "np.ndarray":
-    """Bag-of-words: bundle of atom vectors for each token.
-
-    Tokenizes by lowercasing, splitting on whitespace, and stripping
-    leading/trailing punctuation from each token.
-
-    Returns bundle of all token atom vectors.
-    If text is empty or produces no tokens, returns encode_atom("__hrr_empty__", dim).
-    """
-    _require_numpy()
-
-    tokens = [
-        token.strip(".,!?;:\"'()[]{}")
-        for token in text.lower().split()
-    ]
-    tokens = [t for t in tokens if t]
-
-    if not tokens:
-        return encode_atom("__hrr_empty__", dim)
-
-    atom_vectors = [encode_atom(token, dim) for token in tokens]
-    return bundle(*atom_vectors)
-
-
-def encode_fact(content: str, entities: list[str], dim: int = 1024) -> "np.ndarray":
-    """Structured encoding: content bound to ROLE_CONTENT, each entity bound to ROLE_ENTITY, all bundled.
-
-    Role vectors are reserved atoms: "__hrr_role_content__", "__hrr_role_entity__"
-
-    Components:
-    1. bind(encode_text(content, dim), encode_atom("__hrr_role_content__", dim))
-    2. For each entity: bind(encode_atom(entity.lower(), dim), encode_atom("__hrr_role_entity__", dim))
-    3. bundle all components together
-
-    This enables algebraic extraction:
-        unbind(fact, bind(entity, ROLE_ENTITY)) ≈ content_vector
-    """
-    _require_numpy()
-
-    role_content = encode_atom("__hrr_role_content__", dim)
-    role_entity = encode_atom("__hrr_role_entity__", dim)
-
-    components: list[np.ndarray] = [
-        bind(encode_text(content, dim), role_content)
-    ]
-
-    for entity in entities:
-        components.append(bind(encode_atom(entity.lower(), dim), role_entity))
-
-    return bundle(*components)
-
-
-def phases_to_bytes(phases: "np.ndarray", dim: int | None = None) -> bytes:
-    """Serialize phase vectors as float32 blobs.
-
-    float32 halves SQLite BLOB storage versus the legacy float64 format
-    (4 KB + a 4-byte format prefix instead of 8 KB at dim=1024) while
-    preserving enough precision for phase-similarity retrieval.
-    ``bytes_to_phases`` keeps reading legacy float64 blobs for backward
-    compatibility.
-
-    When ``dim`` is 1 the prefixed float32 blob (8 bytes) collides in size
-    with a raw float64 blob (8 bytes), making the format ambiguous.  In
-    that case we fall back to writing raw float64 so that ``bytes_to_phases``
-    can never misinterpret the blob.
-    """
-    numpy = _np()
-    if dim is None:
-        dim = int(phases.shape[0])
-    float32_blob_bytes = len(_FLOAT32_BLOB_PREFIX) + dim * numpy.dtype(numpy.float32).itemsize
-    float64_bytes = dim * numpy.dtype(numpy.float64).itemsize
-    if float32_blob_bytes == float64_bytes:
-        # dim=1: sizes collide, write legacy float64 to stay unambiguous
-        return numpy.asarray(phases, dtype=numpy.float64).tobytes()
-    payload = numpy.asarray(phases, dtype=numpy.float32).tobytes()
-    return _FLOAT32_BLOB_PREFIX + payload
-
-
-def bytes_to_phases(data: bytes, dim: int | None = None) -> "np.ndarray":
-    """Deserialize a phase vector from new float32 or legacy float64 storage.
-
-    New float32 blobs carry a small prefix so callers can round-trip without
-    knowing ``dim``. Legacy float64 blobs are raw NumPy bytes and remain
-    readable for backward compatibility. The returned array is copied and
-    promoted to float64 so downstream HRR math keeps the existing numerical
-    behavior.
-
-    When ``dim`` is 1 the prefixed float32 blob and the raw float64 blob are
-    both 8 bytes, so size alone cannot disambiguate.  ``phases_to_bytes``
-    avoids writing prefixed blobs in that case; here we guard the remaining
-    collision window (a legacy float64 blob that happens to start with the
-    ``HRR1`` prefix) by preferring the legacy interpretation when sizes
-    match and the caller supplied ``dim``.
-    """
-    numpy = _np()
-
-    if dim is not None:
-        float32_payload_bytes = dim * numpy.dtype(numpy.float32).itemsize
-        float32_blob_bytes = len(_FLOAT32_BLOB_PREFIX) + float32_payload_bytes
-        float64_bytes = dim * numpy.dtype(numpy.float64).itemsize
-
-        # When sizes collide (dim=1), prefer legacy float64 for a blob that
-        # starts with the prefix, because phases_to_bytes never writes a
-        # prefixed float32 blob at dim=1 — any such blob must be legacy.
-        if float32_blob_bytes == float64_bytes:
-            if len(data) == float64_bytes:
-                return numpy.frombuffer(data, dtype=numpy.float64).copy()
-            if data.startswith(_FLOAT32_BLOB_PREFIX):
-                payload_len = len(data) - len(_FLOAT32_BLOB_PREFIX)
-                raise ValueError(
-                    f"HRR vector blob has {len(data)} bytes ({payload_len} payload bytes after "
-                    f"the float32 prefix); expected {float64_bytes} (legacy float64) for dim={dim}"
-                )
-            raise ValueError(
-                f"HRR legacy vector blob has {len(data)} bytes; expected "
-                f"{float64_bytes} (float64) for dim={dim}"
-            )
-
-        if data.startswith(_FLOAT32_BLOB_PREFIX) and len(data) == float32_blob_bytes:
-            payload = data[len(_FLOAT32_BLOB_PREFIX):]
-            return numpy.frombuffer(payload, dtype=numpy.float32).astype(numpy.float64)
-        if len(data) == float64_bytes:
-            return numpy.frombuffer(data, dtype=numpy.float64).copy()
-        if data.startswith(_FLOAT32_BLOB_PREFIX):
-            payload_len = len(data) - len(_FLOAT32_BLOB_PREFIX)
-            raise ValueError(
-                f"HRR vector blob has {len(data)} bytes ({payload_len} payload bytes after "
-                f"the float32 prefix); expected {float32_blob_bytes} (prefixed float32) "
-                f"or {float64_bytes} (legacy float64) for dim={dim}"
-            )
-        raise ValueError(
-            f"HRR legacy vector blob has {len(data)} bytes; expected "
-            f"{float64_bytes} (float64) for dim={dim}"
-        )
-
-    if data.startswith(_FLOAT32_BLOB_PREFIX):
-        payload = data[len(_FLOAT32_BLOB_PREFIX):]
-        if len(payload) % numpy.dtype(numpy.float32).itemsize != 0:
-            raise ValueError(
-                f"HRR float32 vector blob has invalid payload byte length: {len(payload)}"
-            )
-        return numpy.frombuffer(payload, dtype=numpy.float32).astype(numpy.float64)
-
-    if len(data) % numpy.dtype(numpy.float64).itemsize != 0:
-        raise ValueError(f"HRR legacy vector blob has invalid byte length: {len(data)}")
-    return numpy.frombuffer(data, dtype=numpy.float64).copy()
-
-
-def snr_estimate(dim: int, n_items: int) -> float:
-    """Signal-to-noise ratio estimate for holographic storage.
-
-    SNR = sqrt(dim / n_items) when n_items > 0, else inf.
-
-    The SNR falls below 2.0 when n_items > dim / 4, meaning retrieval
-    errors become likely. Logs a warning when this threshold is crossed.
-    """
-    _require_numpy()
-
-    if n_items <= 0:
-        return float("inf")
-
-    snr = math.sqrt(dim / n_items)
-
-    if snr < 2.0:
-        logger.warning(
-            "HRR storage near capacity: SNR=%.2f (dim=%d, n_items=%d). "
-            "Retrieval accuracy may degrade. Consider increasing dim or reducing stored items.",
-            snr,
-            dim,
-            n_items,
-        )
-
-    return snr
diff --git a/plugin/holographic-plus/plugin.yaml b/plugin/holographic-plus/plugin.yaml
deleted file mode 100644
index 20a89fe..0000000
--- a/plugin/holographic-plus/plugin.yaml
+++ /dev/null
@@ -1,3 +0,0 @@
-name: holographic-plus
-description: Holographic memory + semantic embeddings (DashScope text-embedding-v4) — semantic retrieval, semantic entity resolution, CJK entity extraction. Fork of bundled holographic, same SQLite DB.
-version: 1.0.0
diff --git a/plugin/holographic-plus/retrieval.py b/plugin/holographic-plus/retrieval.py
deleted file mode 100644
index 532c241..0000000
--- a/plugin/holographic-plus/retrieval.py
+++ /dev/null
@@ -1,777 +0,0 @@
-"""Hybrid keyword/BM25 retrieval for the memory store.
-
-Ported from KIK memory_agent.py — combines FTS5 full-text search with
-Jaccard similarity reranking and trust-weighted scoring.
-"""
-
-from __future__ import annotations
-
-import math
-import hashlib
-from datetime import datetime, timezone
-from typing import TYPE_CHECKING
-
-if TYPE_CHECKING:
-    from .store import MemoryStore
-
-try:
-    from . import holographic as hrr
-except ImportError:
-    import holographic as hrr  # type: ignore[no-redef]
-
-try:
-    from . import embeddings as emb
-except ImportError:
-    try:
-        import embeddings as emb  # type: ignore[no-redef]
-    except ImportError:
-        emb = None  # type: ignore[assignment]
-
-
-class FactRetriever:
-    """Multi-strategy fact retrieval with trust-weighted scoring."""
-
-    def __init__(
-        self,
-        store: MemoryStore,
-        temporal_decay_half_life: int = 0,  # days, 0 = disabled
-        fts_weight: float = 0.25,
-        jaccard_weight: float = 0.15,
-        hrr_weight: float = 0.15,
-        semantic_weight: float = 0.45,
-        hrr_dim: int = 1024,
-    ):
-        self.store = store
-        self.half_life = temporal_decay_half_life
-        self.hrr_dim = hrr_dim
-
-        # Auto-redistribute weights if numpy unavailable
-        if hrr_weight > 0 and not hrr._HAS_NUMPY:
-            fts_weight += hrr_weight / 2
-            jaccard_weight += hrr_weight / 2
-            hrr_weight = 0.0
-
-        # holographic-plus: semantic channel comes from the store's embedder;
-        # without it, redistribute the semantic weight to FTS/Jaccard so
-        # retrieval degrades to the bundled behaviour.
-        self._embedder = getattr(store, "_embedder", None)
-        if semantic_weight > 0 and (self._embedder is None or emb is None):
-            fts_weight += semantic_weight / 2
-            jaccard_weight += semantic_weight / 2
-            semantic_weight = 0.0
-
-        self.fts_weight = fts_weight
-        self.jaccard_weight = jaccard_weight
-        self.hrr_weight = hrr_weight
-        self.semantic_weight = semantic_weight
-
-    def _active_predicate(self, alias: str = "") -> str:
-        """Read-side compatibility for stores predating the deprecated_at column."""
-        if not getattr(self.store, "_has_deprecated_at", False):
-            return "1=1"
-        prefix = f"{alias}." if alias else ""
-        return f"{prefix}deprecated_at IS NULL"
-
-    def search(
-        self,
-        query: str,
-        category: str | None = None,
-        min_trust: float = 0.3,
-        limit: int = 10,
-    ) -> list[dict]:
-        """Hybrid search: FTS5 candidates → Jaccard rerank → trust weighting.
-
-        Pipeline:
-        1. FTS5 search: Get limit*3 candidates from SQLite full-text search
-        2. Jaccard boost: Token overlap between query and fact content
-        3. Trust weighting: final_score = relevance * trust_score
-        4. Temporal decay (optional): decay = 0.5^(age_days / half_life)
-
-        Returns list of dicts with fact data + 'score' field, sorted by score desc.
-        """
-        # Stage 1: Get FTS5 candidates (more than limit for reranking headroom)
-        candidates = self._fts_candidates(query, category, min_trust, limit * 3)
-
-        # holographic-plus: semantic candidate pool. FTS5 (especially with
-        # CJK text) misses paraphrases entirely; a brute-force cosine scan
-        # over fact_embeddings supplies candidates FTS never saw. At this
-        # store's scale (hundreds-to-thousands of 1024-dim float32 vectors)
-        # an exhaustive scan is sub-millisecond with numpy, low single-digit
-        # ms in pure Python.
-        sem_sims: dict[int, float] = {}
-        sem_candidates = self._semantic_candidates(query, category, min_trust, limit * 3)
-        if sem_candidates:
-            by_id = {f["fact_id"]: f for f in candidates}
-            for fact, sim in sem_candidates:
-                sem_sims[fact["fact_id"]] = sim
-                if fact["fact_id"] not in by_id:
-                    candidates.append(fact)
-
-        if not candidates:
-            return []
-
-        # Stage 2: Rerank with Jaccard + trust + optional decay
-        query_tokens = self._tokenize(query)
-        # The query vector is loop-invariant — encode it at most once, on
-        # the first candidate that actually carries an HRR vector. Lazy on
-        # purpose: migrated stores can have FTS candidates whose hrr_vector
-        # was never backfilled (MemoryStore._init_db adds the column
-        # without backfilling), and those must not pay for an encode
-        # nothing will use. encode_text is deterministic (SHA-256 counter
-        # blocks), so the hoisted vector is bit-identical to what the
-        # per-candidate calls produced.
-        query_vec = None
-        scored = []
-
-        for fact in candidates:
-            content_tokens = self._tokenize(fact["content"])
-            tag_tokens = self._tokenize(fact.get("tags", ""))
-            all_tokens = content_tokens | tag_tokens
-
-            jaccard = self._jaccard_similarity(query_tokens, all_tokens)
-            fts_score = fact.get("fts_rank", 0.0)
-
-            # HRR similarity
-            if self.hrr_weight > 0 and fact.get("hrr_vector"):
-                fact_vec = hrr.bytes_to_phases(fact["hrr_vector"], dim=self.hrr_dim)
-                if query_vec is None:
-                    query_vec = hrr.encode_text(query, self.hrr_dim)
-                hrr_sim = (hrr.similarity(query_vec, fact_vec) + 1.0) / 2.0  # shift to [0,1]
-            else:
-                hrr_sim = 0.5  # neutral
-
-            # holographic-plus: semantic similarity for this fact (0 when the
-            # fact never entered the semantic pool — e.g. not yet backfilled)
-            sem_sim = sem_sims.get(fact["fact_id"], 0.0)
-
-            # Combine FTS5 + Jaccard + HRR + semantic
-            relevance = (self.fts_weight * fts_score
-                        + self.jaccard_weight * jaccard
-                        + self.hrr_weight * hrr_sim
-                        + self.semantic_weight * sem_sim)
-
-            # Trust weighting
-            score = relevance * fact["trust_score"]
-
-            # Optional temporal decay
-            if self.half_life > 0:
-                score *= self._temporal_decay(fact.get("updated_at") or fact.get("created_at"))
-
-            fact["score"] = score
-            scored.append(fact)
-
-        # Sort by score descending, return top limit
-        scored.sort(key=lambda x: x["score"], reverse=True)
-        results = scored[:limit]
-        # Strip raw HRR bytes — callers expect JSON-serializable dicts
-        for fact in results:
-            fact.pop("hrr_vector", None)
-        return results
-
-    def probe(
-        self,
-        entity: str,
-        category: str | None = None,
-        limit: int = 10,
-    ) -> list[dict]:
-        """Compositional entity query using HRR algebra.
-
-        Unbinds entity from memory bank to extract associated content.
-        This is NOT keyword search — it uses algebraic structure to find facts
-        where the entity plays a structural role.
-
-        Falls back to FTS5 search if numpy unavailable.
-        """
-        if not hrr._HAS_NUMPY:
-            # Fallback to keyword search on entity name
-            return self.search(entity, category=category, limit=limit)
-
-        conn = self.store._conn
-
-        # Encode entity as role-bound vector
-        role_entity = hrr.encode_atom("__hrr_role_entity__", self.hrr_dim)
-        entity_vec = hrr.encode_atom(entity.lower(), self.hrr_dim)
-        probe_key = hrr.bind(entity_vec, role_entity)
-
-        # Try category-specific bank first, then all facts
-        if category:
-            bank_name = f"cat:{category}"
-            bank_row = conn.execute(
-                "SELECT vector FROM memory_banks WHERE bank_name = ?",
-                (bank_name,),
-            ).fetchone()
-            if bank_row:
-                bank_vec = hrr.bytes_to_phases(bank_row["vector"], dim=self.hrr_dim)
-                extracted = hrr.unbind(bank_vec, probe_key)
-                # Use extracted signal to score individual facts
-                return self._score_facts_by_vector(
-                    extracted, category=category, limit=limit
-                )
-
-        # Score against individual fact vectors directly
-        where = f"WHERE hrr_vector IS NOT NULL AND {self._active_predicate()}"
-        params: list = []
-        if category:
-            where += " AND category = ?"
-            params.append(category)
-
-        rows = conn.execute(
-            f"""
-            SELECT fact_id, content, category, tags, trust_score,
-                   retrieval_count, helpful_count, created_at, updated_at,
-                   hrr_vector
-            FROM facts
-            {where}
-            """,
-            params,
-        ).fetchall()
-
-        if not rows:
-            # Final fallback: keyword search
-            return self.search(entity, category=category, limit=limit)
-
-        # role_content is loop-invariant — encode it once (deterministic
-        # SHA-256-based atom) instead of once per fact row.
-        role_content = hrr.encode_atom("__hrr_role_content__", self.hrr_dim)
-        scored = []
-        for row in rows:
-            fact = dict(row)
-            fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"), dim=self.hrr_dim)
-            # Unbind probe key from fact to see if entity is structurally present
-            residual = hrr.unbind(fact_vec, probe_key)
-            # Compare residual against content signal
-            content_vec = hrr.bind(hrr.encode_text(fact["content"], self.hrr_dim), role_content)
-            sim = hrr.similarity(residual, content_vec)
-            fact["score"] = (sim + 1.0) / 2.0 * fact["trust_score"]
-            scored.append(fact)
-
-        scored.sort(key=lambda x: x["score"], reverse=True)
-        return scored[:limit]
-
-    def related(
-        self,
-        entity: str,
-        category: str | None = None,
-        limit: int = 10,
-    ) -> list[dict]:
-        """Discover facts that share structural connections with an entity.
-
-        Unlike probe (which finds facts *about* an entity), related finds
-        facts that are connected through shared context — e.g., other entities
-        mentioned alongside this one, or content that overlaps structurally.
-
-        Falls back to FTS5 search if numpy unavailable.
-        """
-        if not hrr._HAS_NUMPY:
-            return self.search(entity, category=category, limit=limit)
-
-        conn = self.store._conn
-
-        # Encode entity as a bare atom (not role-bound — we want ANY structural match)
-        entity_vec = hrr.encode_atom(entity.lower(), self.hrr_dim)
-
-        # Get all facts with vectors
-        where = f"WHERE hrr_vector IS NOT NULL AND {self._active_predicate()}"
-        params: list = []
-        if category:
-            where += " AND category = ?"
-            params.append(category)
-
-        rows = conn.execute(
-            f"""
-            SELECT fact_id, content, category, tags, trust_score,
-                   retrieval_count, helpful_count, created_at, updated_at,
-                   hrr_vector
-            FROM facts
-            {where}
-            """,
-            params,
-        ).fetchall()
-
-        if not rows:
-            return self.search(entity, category=category, limit=limit)
-
-        # Score each fact by how much the entity's atom appears in its vector
-        # This catches both role-bound entity matches AND content word matches
-        # Both role atoms are loop-invariant — encode them once here
-        # (deterministic SHA-256-based atoms) instead of twice per fact row.
-        role_entity = hrr.encode_atom("__hrr_role_entity__", self.hrr_dim)
-        role_content = hrr.encode_atom("__hrr_role_content__", self.hrr_dim)
-        scored = []
-        for row in rows:
-            fact = dict(row)
-            fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"), dim=self.hrr_dim)
-
-            # Check structural similarity: unbind entity from fact
-            residual = hrr.unbind(fact_vec, entity_vec)
-            # A high-similarity residual to ANY known role vector means this entity
-            # plays a structural role in the fact
-
-            entity_role_sim = hrr.similarity(residual, role_entity)
-            content_role_sim = hrr.similarity(residual, role_content)
-            # Take the max — entity could appear in either role
-            best_sim = max(entity_role_sim, content_role_sim)
-
-            fact["score"] = (best_sim + 1.0) / 2.0 * fact["trust_score"]
-            scored.append(fact)
-
-        scored.sort(key=lambda x: x["score"], reverse=True)
-        return scored[:limit]
-
-    def reason(
-        self,
-        entities: list[str],
-        category: str | None = None,
-        limit: int = 10,
-    ) -> list[dict]:
-        """Multi-entity compositional query — vector-space JOIN.
-
-        Given multiple entities, algebraically intersects their structural
-        connections to find facts related to ALL of them simultaneously.
-        This is compositional reasoning that no embedding DB can do.
-
-        Example: reason(["peppi", "backend"]) finds facts where peppi AND
-        backend both play structural roles — without keyword matching.
-
-        Falls back to FTS5 search if numpy unavailable.
-        """
-        if not hrr._HAS_NUMPY or not entities:
-            # Fallback: search with all entities as keywords
-            query = " ".join(entities)
-            return self.search(query, category=category, limit=limit)
-
-        conn = self.store._conn
-        role_entity = hrr.encode_atom("__hrr_role_entity__", self.hrr_dim)
-
-        # For each entity, compute what the bank "remembers" about it
-        # by unbinding entity+role from each fact vector
-        entity_residuals = []
-        for entity in entities:
-            entity_vec = hrr.encode_atom(entity.lower(), self.hrr_dim)
-            probe_key = hrr.bind(entity_vec, role_entity)
-            entity_residuals.append(probe_key)
-
-        # Get all facts with vectors
-        where = f"WHERE hrr_vector IS NOT NULL AND {self._active_predicate()}"
-        params: list = []
-        if category:
-            where += " AND category = ?"
-            params.append(category)
-
-        rows = conn.execute(
-            f"""
-            SELECT fact_id, content, category, tags, trust_score,
-                   retrieval_count, helpful_count, created_at, updated_at,
-                   hrr_vector
-            FROM facts
-            {where}
-            """,
-            params,
-        ).fetchall()
-
-        if not rows:
-            query = " ".join(entities)
-            return self.search(query, category=category, limit=limit)
-
-        # Score each fact by how much EACH entity is structurally present.
-        # A fact scores high only if ALL entities have structural presence
-        # (AND semantics via min, vs OR which would use mean/max).
-        role_content = hrr.encode_atom("__hrr_role_content__", self.hrr_dim)
-
-        scored = []
-        for row in rows:
-            fact = dict(row)
-            fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"), dim=self.hrr_dim)
-
-            entity_scores = []
-            for probe_key in entity_residuals:
-                residual = hrr.unbind(fact_vec, probe_key)
-                sim = hrr.similarity(residual, role_content)
-                entity_scores.append(sim)
-
-            min_sim = min(entity_scores)
-            fact["score"] = (min_sim + 1.0) / 2.0 * fact["trust_score"]
-            scored.append(fact)
-
-        scored.sort(key=lambda x: x["score"], reverse=True)
-        return scored[:limit]
-
-    def contradict(
-        self,
-        category: str | None = None,
-        threshold: float = 0.3,
-        limit: int = 10,
-    ) -> list[dict]:
-        """Find potentially contradictory facts via entity overlap + content divergence.
-
-        Two facts contradict when they share entities (same subject) but have
-        low content-vector similarity (different claims). This is automated
-        memory hygiene — no other memory system does this.
-
-        Returns pairs of facts with a contradiction score.
-        Falls back to empty list if numpy unavailable.
-        """
-        if not hrr._HAS_NUMPY:
-            return []
-
-        conn = self.store._conn
-
-        # Get all facts with vectors and their linked entities
-        where = f"WHERE f.hrr_vector IS NOT NULL AND {self._active_predicate('f')}"
-        params: list = []
-        if category:
-            where += " AND f.category = ?"
-            params.append(category)
-
-        rows = conn.execute(
-            f"""
-            SELECT f.fact_id, f.content, f.category, f.tags, f.trust_score,
-                   f.created_at, f.updated_at, f.hrr_vector
-            FROM facts f
-            {where}
-            """,
-            params,
-        ).fetchall()
-
-        if len(rows) < 2:
-            return []
-
-        # Guard against O(n²) explosion on large fact stores.
-        # At 500 facts, that's ~125K comparisons — acceptable.
-        # Above that, only check the most recently updated facts.
-        _MAX_CONTRADICT_FACTS = 500
-        if len(rows) > _MAX_CONTRADICT_FACTS:
-            rows = sorted(rows, key=lambda r: r["updated_at"] or r["created_at"], reverse=True)
-            rows = rows[:_MAX_CONTRADICT_FACTS]
-
-        # Build entity sets per fact
-        fact_entities: dict[int, set[str]] = {}
-        for row in rows:
-            fid = row["fact_id"]
-            entity_rows = conn.execute(
-                """
-                SELECT e.name FROM entities e
-                JOIN fact_entities fe ON fe.entity_id = e.entity_id
-                WHERE fe.fact_id = ?
-                """,
-                (fid,),
-            ).fetchall()
-            fact_entities[fid] = {r["name"].lower() for r in entity_rows}
-
-        # Compare all pairs: high entity overlap + low content similarity = contradiction
-        facts = [dict(r) for r in rows]
-        contradictions = []
-
-        for i in range(len(facts)):
-            for j in range(i + 1, len(facts)):
-                f1, f2 = facts[i], facts[j]
-                ents1 = fact_entities.get(f1["fact_id"], set())
-                ents2 = fact_entities.get(f2["fact_id"], set())
-
-                if not ents1 or not ents2:
-                    continue
-
-                # Entity overlap (Jaccard)
-                entity_overlap = len(ents1 & ents2) / len(ents1 | ents2) if (ents1 | ents2) else 0.0
-
-                if entity_overlap < 0.3:
-                    continue  # Not enough entity overlap to be contradictory
-
-                # Content similarity via HRR vectors
-                v1 = hrr.bytes_to_phases(f1["hrr_vector"], dim=self.hrr_dim)
-                v2 = hrr.bytes_to_phases(f2["hrr_vector"], dim=self.hrr_dim)
-                content_sim = hrr.similarity(v1, v2)
-
-                # High entity overlap + low content similarity = potential contradiction
-                # contradiction_score: higher = more contradictory
-                contradiction_score = entity_overlap * (1.0 - (content_sim + 1.0) / 2.0)
-
-                if contradiction_score >= threshold:
-                    # Strip hrr_vector from output (not JSON serializable)
-                    f1_clean = {k: v for k, v in f1.items() if k != "hrr_vector"}
-                    f2_clean = {k: v for k, v in f2.items() if k != "hrr_vector"}
-                    contradictions.append({
-                        "fact_a": f1_clean,
-                        "fact_b": f2_clean,
-                        "entity_overlap": round(entity_overlap, 3),
-                        "content_similarity": round(content_sim, 3),
-                        "contradiction_score": round(contradiction_score, 3),
-                        "shared_entities": sorted(ents1 & ents2),
-                    })
-
-        contradictions.sort(key=lambda x: x["contradiction_score"], reverse=True)
-        return contradictions[:limit]
-
-    def _score_facts_by_vector(
-        self,
-        target_vec: "np.ndarray",
-        category: str | None = None,
-        limit: int = 10,
-    ) -> list[dict]:
-        """Score facts by similarity to a target vector."""
-        conn = self.store._conn
-
-        where = f"WHERE hrr_vector IS NOT NULL AND {self._active_predicate()}"
-        params: list = []
-        if category:
-            where += " AND category = ?"
-            params.append(category)
-
-        rows = conn.execute(
-            f"""
-            SELECT fact_id, content, category, tags, trust_score,
-                   retrieval_count, helpful_count, created_at, updated_at,
-                   hrr_vector
-            FROM facts
-            {where}
-            """,
-            params,
-        ).fetchall()
-
-        scored = []
-        for row in rows:
-            fact = dict(row)
-            fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"), dim=self.hrr_dim)
-            sim = hrr.similarity(target_vec, fact_vec)
-            fact["score"] = (sim + 1.0) / 2.0 * fact["trust_score"]
-            scored.append(fact)
-
-        scored.sort(key=lambda x: x["score"], reverse=True)
-        return scored[:limit]
-
-    def _fts_candidates(
-        self,
-        query: str,
-        category: str | None,
-        min_trust: float,
-        limit: int,
-    ) -> list[dict]:
-        """Get raw FTS5 candidates from the store.
-
-        Uses the store's database connection directly for FTS5 MATCH
-        with rank scoring. Normalizes FTS5 rank to [0, 1] range.
-        """
-        conn = self.store._conn
-
-        # Build query - FTS5 rank is negative (lower = better match)
-        # We need to join facts_fts with facts to get all columns
-        params: list = []
-        where_clauses = ["facts_fts MATCH ?", self._active_predicate("f")]
-        # FTS5 defaults to AND-between-tokens, which kills recall on
-        # natural-language queries ("what happened with the deployment
-        # rollback"). Sanitize: drop stopwords, OR-join content tokens, so
-        # any significant term can match.
-        params.append(self._sanitize_fts_query(query))
-
-        if category:
-            where_clauses.append("f.category = ?")
-            params.append(category)
-
-        where_clauses.append("f.trust_score >= ?")
-        params.append(min_trust)
-
-        where_sql = " AND ".join(where_clauses)
-
-        sql = f"""
-            SELECT f.*, facts_fts.rank as fts_rank_raw
-            FROM facts_fts
-            JOIN facts f ON f.fact_id = facts_fts.rowid
-            WHERE {where_sql}
-            ORDER BY facts_fts.rank
-            LIMIT ?
-        """
-        params.append(limit)
-
-        try:
-            rows = conn.execute(sql, params).fetchall()
-        except Exception:
-            # FTS5 MATCH can fail on malformed queries — fall back to empty
-            return []
-
-        if not rows:
-            return []
-
-        # Normalize FTS5 rank: rank is negative, lower = better
-        # Convert to positive score in [0, 1] range
-        raw_ranks = [abs(row["fts_rank_raw"]) for row in rows]
-        max_rank = max(raw_ranks) if raw_ranks else 1.0
-        max_rank = max(max_rank, 1e-6)  # avoid div by zero
-
-        results = []
-        for row, raw_rank in zip(rows, raw_ranks):
-            fact = dict(row)
-            fact.pop("fts_rank_raw", None)
-            fact["fts_rank"] = raw_rank / max_rank  # normalize to [0, 1]
-            results.append(fact)
-
-        return results
-
-    def _semantic_candidates(
-        self,
-        query: str,
-        category: str | None,
-        min_trust: float,
-        limit: int,
-    ) -> list[tuple[dict, float]]:
-        """holographic-plus: exhaustive cosine scan over fact_embeddings.
-
-        Returns [(fact_dict, cosine_sim)] for the top ``limit`` facts, each
-        fact_dict carrying fts_rank=0.0 (they came from the semantic pool,
-        not FTS). Empty list when embeddings are unavailable or the sidecar
-        table is empty. cosine is shifted to [0, 1] for blending.
-        """
-        if self.semantic_weight <= 0 or self._embedder is None or emb is None:
-            return []
-        try:
-            query_vec = self._embedder.embed(query)
-        except Exception:
-            return []
-        if query_vec is None:
-            return []
-
-        conn = self.store._conn
-        params: list = [min_trust]
-        category_clause = ""
-        if category:
-            category_clause = "AND f.category = ?"
-            params.append(category)
-        try:
-            rows = conn.execute(
-                f"""
-                SELECT f.*, fe.vector AS sem_vector, fe.content_hash AS sem_hash, fe.model AS sem_model, fe.dim AS sem_dim
-                FROM fact_embeddings fe
-                JOIN facts f ON f.fact_id = fe.fact_id
-                WHERE f.trust_score >= ? AND {self._active_predicate('f')}
-                {category_clause}
-                """,
-                params,
-            ).fetchall()
-        except Exception:
-            return []
-        if not rows:
-            return []
-
-        scored: list[tuple[dict, float]] = []
-        for row in rows:
-            fact = dict(row)
-            blob = fact.pop("sem_vector")
-            content_hash = fact.pop("sem_hash")
-            model, dim = fact.pop("sem_model"), fact.pop("sem_dim")
-            if (content_hash != hashlib.sha256(fact["content"].encode("utf-8")).hexdigest()
-                    or model != self._embedder.model or dim != self._embedder.dim):
-                continue
-            sim = emb.cosine(query_vec, emb.bytes_to_vec(blob))
-            sim01 = (sim + 1.0) / 2.0  # shift [-1,1] -> [0,1]
-            fact["fts_rank"] = 0.0
-            scored.append((fact, sim01))
-
-        scored.sort(key=lambda x: x[1], reverse=True)
-        return scored[:limit]
-
-    @staticmethod
-    def _tokenize(text: str) -> set[str]:
-        """Simple whitespace tokenization with lowercasing.
-
-        Strips common punctuation. No stemming/lemmatization (Phase 1).
-        """
-        if not text:
-            return set()
-        # Split on whitespace, lowercase, strip punctuation
-        tokens = set()
-        for word in text.lower().split():
-            cleaned = word.strip(".,;:!?\"'()[]{}#@<>")
-            if cleaned:
-                tokens.add(cleaned)
-        return tokens
-
-    # Stopwords dropped before FTS5 OR-expansion. Short English function
-    # words that carry no retrieval signal and force false-negative AND
-    # matches when left in the query.
-    _FTS_STOPWORDS = frozenset({
-        "a", "about", "above", "after", "again", "all", "am", "an", "and",
-        "any", "are", "as", "at", "be", "because", "been", "before", "being",
-        "between", "both", "but", "by", "can", "could", "did", "do", "does",
-        "doing", "don", "down", "during", "each", "few", "for", "from",
-        "further", "had", "has", "have", "having", "he", "her", "here",
-        "hers", "herself", "him", "himself", "his", "how", "i", "if", "in",
-        "into", "is", "it", "its", "itself", "just", "me", "more", "most",
-        "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
-        "only", "or", "other", "our", "ours", "ourselves", "out", "over",
-        "own", "same", "she", "should", "so", "some", "such", "than", "that",
-        "the", "their", "theirs", "them", "themselves", "then", "there",
-        "these", "they", "this", "those", "through", "to", "too", "under",
-        "until", "up", "very", "was", "we", "were", "what", "when", "where",
-        "which", "while", "who", "whom", "why", "will", "with", "would",
-        "you", "your", "yours", "yourself", "yourselves",
-    })
-
-    @classmethod
-    def _sanitize_fts_query(cls, query: str) -> str:
-        """Convert a natural-language query to an FTS5-safe OR expression.
-
-        FTS5 treats a multi-word MATCH argument as AND-joined by default,
-        which tanks recall on prose queries. This helper:
-          - tokenizes the query
-          - drops stopwords and short (<2 char) tokens
-          - strips FTS5 special characters from each token
-          - OR-joins the survivors
-
-        If nothing remains (pathological query), falls back to the raw
-        query so the caller sees zero results instead of a SQL error.
-        """
-        if not query:
-            return ""
-        # Strip FTS5 operator characters from EACH token to avoid
-        # accidentally creating a malformed query.
-        _FTS_SPECIAL = '"()*^:-+'
-        tokens: list[str] = []
-        for raw in query.lower().split():
-            cleaned = raw.strip(".,;:!?\"'()[]{}#@<>") .translate(
-                str.maketrans("", "", _FTS_SPECIAL)
-            )
-            if len(cleaned) < 2:
-                continue
-            if cleaned in cls._FTS_STOPWORDS:
-                continue
-            # FTS5 phrase-literal each token to ensure no special chars
-            # sneak through as operators.
-            tokens.append(f'"{cleaned}"')
-        if not tokens:
-            # Fallback: raw query (likely returns 0, but never crashes)
-            return query
-        return " OR ".join(tokens)
-
-    @staticmethod
-    def _jaccard_similarity(set_a: set, set_b: set) -> float:
-        """Jaccard similarity coefficient: |A ∩ B| / |A ∪ B|."""
-        if not set_a or not set_b:
-            return 0.0
-        intersection = len(set_a & set_b)
-        union = len(set_a | set_b)
-        return intersection / union if union > 0 else 0.0
-
-    def _temporal_decay(self, timestamp_str: str | None) -> float:
-        """Exponential decay: 0.5^(age_days / half_life_days).
-
-        Returns 1.0 if decay is disabled or timestamp is missing.
-        """
-        if not self.half_life or not timestamp_str:
-            return 1.0
-
-        try:
-            if isinstance(timestamp_str, str):
-                # Parse ISO format timestamp from SQLite
-                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
-            else:
-                ts = timestamp_str
-
-            if ts.tzinfo is None:
-                ts = ts.replace(tzinfo=timezone.utc)
-
-            age_days = (datetime.now(timezone.utc) - ts).total_seconds() / 86400
-            if age_days < 0:
-                return 1.0
-
-            return math.pow(0.5, age_days / self.half_life)
-        except (ValueError, TypeError):
-            return 1.0
diff --git a/plugin/holographic-plus/store.py b/plugin/holographic-plus/store.py
deleted file mode 100644
index ef8eb1b..0000000
--- a/plugin/holographic-plus/store.py
+++ /dev/null
@@ -1,883 +0,0 @@
-"""
-SQLite-backed fact store with entity resolution and trust scoring.
-Single-user Hermes memory store plugin.
-"""
-
-import logging
-import hashlib
-import os
-import re
-import sqlite3
-import threading
-from pathlib import Path
-
-logger = logging.getLogger(__name__)
-
-try:
-    from . import holographic as hrr
-except ImportError:
-    import holographic as hrr  # type: ignore[no-redef]
-
-try:
-    from . import embeddings as emb
-except ImportError:
-    try:
-        import embeddings as emb  # type: ignore[no-redef]
-    except ImportError:
-        emb = None  # type: ignore[assignment]
-
-_SCHEMA = """
-CREATE TABLE IF NOT EXISTS facts (
-    fact_id         INTEGER PRIMARY KEY AUTOINCREMENT,
-    content         TEXT NOT NULL UNIQUE,
-    category        TEXT DEFAULT 'general',
-    tags            TEXT DEFAULT '',
-    trust_score     REAL DEFAULT 0.5,
-    retrieval_count INTEGER DEFAULT 0,
-    helpful_count   INTEGER DEFAULT 0,
-    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
-    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
-    hrr_vector      BLOB
-);
-
-CREATE TABLE IF NOT EXISTS entities (
-    entity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
-    name        TEXT NOT NULL,
-    entity_type TEXT DEFAULT 'unknown',
-    aliases     TEXT DEFAULT '',
-    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-);
-
-CREATE TABLE IF NOT EXISTS fact_entities (
-    fact_id   INTEGER REFERENCES facts(fact_id),
-    entity_id INTEGER REFERENCES entities(entity_id),
-    PRIMARY KEY (fact_id, entity_id)
-);
-
-CREATE INDEX IF NOT EXISTS idx_facts_trust    ON facts(trust_score DESC);
-CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);
-CREATE INDEX IF NOT EXISTS idx_entities_name  ON entities(name);
-
-CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts
-    USING fts5(content, tags, content=facts, content_rowid=fact_id);
-
-CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
-    INSERT INTO facts_fts(rowid, content, tags)
-        VALUES (new.fact_id, new.content, new.tags);
-END;
-
-CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
-    INSERT INTO facts_fts(facts_fts, rowid, content, tags)
-        VALUES ('delete', old.fact_id, old.content, old.tags);
-END;
-
-CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE ON facts BEGIN
-    INSERT INTO facts_fts(facts_fts, rowid, content, tags)
-        VALUES ('delete', old.fact_id, old.content, old.tags);
-    INSERT INTO facts_fts(rowid, content, tags)
-        VALUES (new.fact_id, new.content, new.tags);
-END;
-
-CREATE TABLE IF NOT EXISTS memory_banks (
-    bank_id    INTEGER PRIMARY KEY AUTOINCREMENT,
-    bank_name  TEXT NOT NULL UNIQUE,
-    vector     BLOB NOT NULL,
-    dim        INTEGER NOT NULL,
-    fact_count INTEGER DEFAULT 0,
-    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-);
-
--- holographic-plus: semantic embedding sidecar tables (additive; original
--- tables untouched so the bundled holographic provider keeps working on the
--- same database).
-CREATE TABLE IF NOT EXISTS fact_embeddings (
-    fact_id    INTEGER PRIMARY KEY REFERENCES facts(fact_id),
-    model      TEXT NOT NULL,
-    dim        INTEGER NOT NULL,
-    vector     BLOB NOT NULL,
-    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
-    content_hash TEXT
-);
-
-CREATE TABLE IF NOT EXISTS entity_embeddings (
-    entity_id  INTEGER PRIMARY KEY REFERENCES entities(entity_id),
-    model      TEXT NOT NULL,
-    dim        INTEGER NOT NULL,
-    vector     BLOB NOT NULL,
-    content_hash TEXT
-);
-"""
-
-# Trust adjustment constants
-_HELPFUL_DELTA   =  0.05
-_UNHELPFUL_DELTA = -0.10
-_TRUST_MIN       =  0.0
-_TRUST_MAX       =  1.0
-
-# Entity extraction patterns
-_RE_CAPITALIZED  = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
-_RE_DOUBLE_QUOTE = re.compile(r'"([^"]+)"')
-_RE_SINGLE_QUOTE = re.compile(r"'([^']+)'")
-_RE_AKA          = re.compile(
-    r'(\w+(?:\s+\w+)*)\s+(?:aka|also known as)\s+(\w+(?:\s+\w+)*)',
-    re.IGNORECASE,
-)
-# holographic-plus: CJK quoted-term patterns. Chinese text has no
-# capitalization and FTS-unfriendly tokenization, so quoted spans are the
-# reliable regex-detectable entity signal.
-_RE_CJK_CORNER   = re.compile(r'「([^」]{1,30})」')
-_RE_CJK_BOOK     = re.compile(r'《([^》]{1,30})》')
-_RE_CJK_DQUOTE   = re.compile(r'“([^”]{1,30})”')
-
-
-def _clamp_trust(value: float) -> float:
-    return max(_TRUST_MIN, min(_TRUST_MAX, value))
-
-
-class MemoryStore:
-    """SQLite-backed fact store with entity resolution and trust scoring."""
-
-    # --- Process-wide shared connection registry -------------------------
-    # SQLite permits only one writer at a time. Each MemoryStore instance used
-    # to open its own connection guarded by its own RLock, so the several
-    # providers that coexist in one process (the main agent plus every
-    # delegate_task subagent) raced as independent WAL writers. Combined with
-    # writes that were not rolled back on error, one connection could leave an
-    # open write transaction that pinned the write lock and made every other
-    # connection's write fail with "database is locked" for the full busy
-    # timeout. All instances for the same database now share ONE connection and
-    # ONE re-entrant lock, so access is fully serialized and cross-connection
-    # contention is impossible. The shared connection is refcounted, so closing
-    # one instance never tears the connection out from under a live sibling.
-    _shared: dict = {}
-    _shared_guard = threading.Lock()
-
-    def __init__(
-        self,
-        db_path: "str | Path | None" = None,
-        default_trust: float = 0.5,
-        hrr_dim: int = 1024,
-        embedder=None,
-        entity_merge_threshold: float = 0.88,
-    ) -> None:
-        if db_path is None:
-            from hermes_constants import get_hermes_home
-            db_path = str(get_hermes_home() / "memory_store.db")
-        self.db_path = Path(db_path).expanduser()
-        self.db_path.parent.mkdir(parents=True, exist_ok=True)
-        self.default_trust = _clamp_trust(default_trust)
-        self.hrr_dim = hrr_dim
-        self._hrr_available = hrr._HAS_NUMPY
-        # Facts stored while HRR is unavailable get no hrr_vector and become
-        # invisible to reason/related retrieval. Used to be a silent skip;
-        # count it and warn so the gap is observable (kanban t_f16f154e).
-        self._hrr_dropped = 0
-        # holographic-plus: optional EmbeddingClient (fail-open semantics live
-        # in the client; None here means semantic features fully off).
-        self._embedder = embedder if (embedder is not None and getattr(embedder, "enabled", False)) else None
-        self._entity_merge_threshold = float(entity_merge_threshold)
-
-        # Acquire (or open) the process-wide shared connection for this DB.
-        # resolve() (not just expanduser) so symlinked/relative paths to the
-        # same file share ONE connection instead of silently reintroducing
-        # the multi-writer contention this registry exists to prevent.
-        try:
-            self._key = str(self.db_path.resolve())
-        except OSError:
-            self._key = str(self.db_path)
-        with MemoryStore._shared_guard:
-            entry = MemoryStore._shared.get(self._key)
-            if entry is None:
-                conn = sqlite3.connect(
-                    self._key,
-                    check_same_thread=False,
-                    timeout=10.0,
-                    # Autocommit: every statement is its own transaction, so a
-                    # write that raises mid-method can never leave a dangling
-                    # transaction (and its write lock) open. The explicit
-                    # commit() calls below become harmless no-ops.
-                    isolation_level=None,
-                )
-                conn.row_factory = sqlite3.Row
-                entry = {"conn": conn, "lock": threading.RLock(), "refs": 0, "ready": False}
-                MemoryStore._shared[self._key] = entry
-            entry["refs"] += 1
-            self._entry = entry
-            self._conn = entry["conn"]
-            self._lock = entry["lock"]
-
-        # Initialise the schema once per shared connection.
-        with self._lock:
-            if not self._entry["ready"]:
-                self._init_db()
-                self._entry["ready"] = True
-            columns = {row[1] for row in self._conn.execute("PRAGMA table_info(facts)").fetchall()}
-            self._has_deprecated_at = "deprecated_at" in columns
-
-    # ------------------------------------------------------------------
-    # Initialisation
-    # ------------------------------------------------------------------
-
-    def _init_db(self) -> None:
-        """Create tables, indexes, and triggers if they do not exist. Enable WAL mode."""
-        # Use the shared WAL-fallback helper so memory_store.db degrades
-        # gracefully on NFS/SMB/FUSE-mounted HERMES_HOME (same issue as
-        # state.db / kanban.db — see hermes_state._WAL_INCOMPAT_MARKERS).
-        from hermes_state import apply_wal_with_fallback
-        apply_wal_with_fallback(self._conn, db_label="memory_store.db (holographic)")
-        self._conn.executescript(_SCHEMA)
-        # Additive sidecar-only migration; old writers leave NULL => detectable stale.
-        for table in ("fact_embeddings", "entity_embeddings"):
-            cols = {r[1] for r in self._conn.execute(f"PRAGMA table_info({table})")}
-            if "content_hash" not in cols:
-                self._conn.execute(f"ALTER TABLE {table} ADD COLUMN content_hash TEXT")
-        # Migrate: add hrr_vector column if missing (safe for existing databases)
-        columns = {row[1] for row in self._conn.execute("PRAGMA table_info(facts)").fetchall()}
-        if "hrr_vector" not in columns:
-            self._conn.execute("ALTER TABLE facts ADD COLUMN hrr_vector BLOB")
-        self._conn.commit()
-
-    # ------------------------------------------------------------------
-    # Public API
-    # ------------------------------------------------------------------
-
-    def add_fact(
-        self,
-        content: str,
-        category: str = "general",
-        tags: str = "",
-        entities: "list[str] | None" = None,
-    ) -> int:
-        """Insert a fact and return its fact_id.
-
-        Deduplicates by content (UNIQUE constraint). On duplicate, returns
-        the existing fact_id without modifying the row. Extracts entities from
-        the content and links them to the fact.
-
-        holographic-plus: ``entities`` lets callers (LLM extraction pipeline,
-        the fact_store tool) supply explicit entity names; they are unioned
-        with regex-extracted candidates. A semantic embedding of the content
-        is stored best-effort after insert.
-        """
-        with self._lock:
-            content = content.strip()
-            if not content:
-                raise ValueError("content must not be empty")
-
-            try:
-                cur = self._conn.execute(
-                    """
-                    INSERT INTO facts (content, category, tags, trust_score)
-                    VALUES (?, ?, ?, ?)
-                    """,
-                    (content, category, tags, self.default_trust),
-                )
-                self._conn.commit()
-                fact_id: int = cur.lastrowid  # type: ignore[assignment]
-            except sqlite3.IntegrityError:
-                # Duplicate content — return existing id
-                row = self._conn.execute(
-                    "SELECT fact_id FROM facts WHERE content = ?", (content,)
-                ).fetchone()
-                return int(row["fact_id"])
-
-            # Entity extraction and linking: explicit caller-supplied
-            # entities first (higher quality), then regex candidates.
-            names: list[str] = []
-            seen_names: set[str] = set()
-            for name in (entities or []) + self._extract_entities(content):
-                stripped = (name or "").strip()
-                if stripped and stripped.lower() not in seen_names:
-                    seen_names.add(stripped.lower())
-                    names.append(stripped)
-            for name in names:
-                entity_id = self._resolve_entity(name)
-                self._link_fact_entity(fact_id, entity_id)
-
-            # Compute HRR vector after entity linking
-            self._compute_hrr_vector(fact_id, content)
-            self._rebuild_bank(category)
-            # holographic-plus: semantic embedding, best-effort (never raises)
-            self._save_fact_embedding(fact_id, content)
-
-            return fact_id
-
-    def search_facts(
-        self,
-        query: str,
-        category: str | None = None,
-        min_trust: float = 0.3,
-        limit: int = 10,
-    ) -> list[dict]:
-        """Full-text search over facts using FTS5.
-
-        Returns a list of fact dicts ordered by FTS5 rank, then trust_score
-        descending. Also increments retrieval_count for matched facts.
-        """
-        with self._lock:
-            query = query.strip()
-            if not query:
-                return []
-
-            # FTS5 AND-joins tokens by default, which zeroes out recall on
-            # natural-language queries. Reuse the retriever's sanitizer
-            # (stopword drop + OR-join content tokens). Imported lazily to
-            # avoid a store->retrieval import cycle.
-            # holographic-plus: import the fork's retriever, not the bundled one
-            try:
-                from .retrieval import FactRetriever
-            except ImportError:
-                from retrieval import FactRetriever  # type: ignore[no-redef]
-
-            match_query = FactRetriever._sanitize_fts_query(query)
-            params: list = [match_query, min_trust]
-            category_clause = ""
-            if category is not None:
-                category_clause = "AND f.category = ?"
-                params.append(category)
-            params.append(limit)
-
-            sql = f"""
-                SELECT f.fact_id, f.content, f.category, f.tags,
-                       f.trust_score, f.retrieval_count, f.helpful_count,
-                       f.created_at, f.updated_at
-                FROM facts f
-                JOIN facts_fts fts ON fts.rowid = f.fact_id
-                WHERE facts_fts MATCH ?
-                  AND f.trust_score >= ?
-                  {"AND f.deprecated_at IS NULL" if self._has_deprecated_at else ""}
-                  {category_clause}
-                ORDER BY fts.rank, f.trust_score DESC
-                LIMIT ?
-            """
-
-            rows = self._conn.execute(sql, params).fetchall()
-            results = [self._row_to_dict(r) for r in rows]
-
-            if results:
-                ids = [r["fact_id"] for r in results]
-                placeholders = ",".join("?" * len(ids))
-                self._conn.execute(
-                    f"UPDATE facts SET retrieval_count = retrieval_count + 1 WHERE fact_id IN ({placeholders})",
-                    ids,
-                )
-                self._conn.commit()
-
-            return results
-
-    def update_fact(
-        self,
-        fact_id: int,
-        content: str | None = None,
-        trust_delta: float | None = None,
-        tags: str | None = None,
-        category: str | None = None,
-    ) -> bool:
-        """Partially update a fact. Trust is clamped to [0, 1].
-
-        Returns True if the row existed, False otherwise.
-        """
-        with self._lock:
-            row = self._conn.execute(
-                "SELECT fact_id, trust_score, content FROM facts WHERE fact_id = ?", (fact_id,)
-            ).fetchone()
-            if row is None:
-                return False
-
-            content_changed = content is not None and content.strip() != row["content"]
-            assignments: list[str] = ["updated_at = CURRENT_TIMESTAMP"]
-            params: list = []
-
-            if content is not None:
-                assignments.append("content = ?")
-                params.append(content.strip())
-            if tags is not None:
-                assignments.append("tags = ?")
-                params.append(tags)
-            if category is not None:
-                assignments.append("category = ?")
-                params.append(category)
-            if trust_delta is not None:
-                new_trust = _clamp_trust(row["trust_score"] + trust_delta)
-                assignments.append("trust_score = ?")
-                params.append(new_trust)
-
-            params.append(fact_id)
-            self._conn.execute(
-                f"UPDATE facts SET {', '.join(assignments)} WHERE fact_id = ?",
-                params,
-            )
-            self._conn.commit()
-
-            # Only actual text changes invalidate semantic/entity indexes.
-            if content_changed:
-                self._conn.execute(
-                    "DELETE FROM fact_entities WHERE fact_id = ?", (fact_id,)
-                )
-                for name in self._extract_entities(content):
-                    entity_id = self._resolve_entity(name)
-                    self._link_fact_entity(fact_id, entity_id)
-                self._conn.commit()
-
-            # Old semantic hash remains stale if API fails (fail-open).
-            if content_changed:
-                self._compute_hrr_vector(fact_id, content.strip())
-                self._save_fact_embedding(fact_id, content.strip())
-            # Rebuild bank for relevant category
-            cat = category or self._conn.execute(
-                "SELECT category FROM facts WHERE fact_id = ?", (fact_id,)
-            ).fetchone()["category"]
-            self._rebuild_bank(cat)
-
-            return True
-
-    def remove_fact(self, fact_id: int) -> bool:
-        """Delete a fact and its entity links. Returns True if the row existed."""
-        with self._lock:
-            row = self._conn.execute(
-                "SELECT fact_id, category FROM facts WHERE fact_id = ?", (fact_id,)
-            ).fetchone()
-            if row is None:
-                return False
-
-            self._conn.execute("SAVEPOINT hp_remove_fact")
-            try:
-                self._conn.execute("DELETE FROM fact_embeddings WHERE fact_id = ?", (fact_id,))
-                self._conn.execute("DELETE FROM fact_entities WHERE fact_id = ?", (fact_id,))
-                self._conn.execute("DELETE FROM facts WHERE fact_id = ?", (fact_id,))
-                self._conn.execute("RELEASE hp_remove_fact")
-            except Exception:
-                self._conn.execute("ROLLBACK TO hp_remove_fact")
-                self._conn.execute("RELEASE hp_remove_fact")
-                raise
-            self._rebuild_bank(row["category"])
-            return True
-
-    def list_facts(
-        self,
-        category: str | None = None,
-        min_trust: float = 0.0,
-        limit: int = 50,
-    ) -> list[dict]:
-        """Browse facts ordered by trust_score descending.
-
-        Optionally filter by category and minimum trust score.
-        """
-        with self._lock:
-            params: list = [min_trust]
-            category_clause = ""
-            if category is not None:
-                category_clause = "AND category = ?"
-                params.append(category)
-            params.append(limit)
-
-            sql = f"""
-                SELECT fact_id, content, category, tags, trust_score,
-                       retrieval_count, helpful_count, created_at, updated_at
-                FROM facts
-                WHERE trust_score >= ?
-                  {"AND deprecated_at IS NULL" if self._has_deprecated_at else ""}
-                  {category_clause}
-                ORDER BY trust_score DESC
-                LIMIT ?
-            """
-            rows = self._conn.execute(sql, params).fetchall()
-            return [self._row_to_dict(r) for r in rows]
-
-    def record_feedback(self, fact_id: int, helpful: bool) -> dict:
-        """Record user feedback and adjust trust asymmetrically.
-
-        helpful=True  -> trust += 0.05, helpful_count += 1
-        helpful=False -> trust -= 0.10
-
-        Returns a dict with fact_id, old_trust, new_trust, helpful_count.
-        Raises KeyError if fact_id does not exist.
-        """
-        with self._lock:
-            row = self._conn.execute(
-                "SELECT fact_id, trust_score, helpful_count FROM facts WHERE fact_id = ?",
-                (fact_id,),
-            ).fetchone()
-            if row is None:
-                raise KeyError(f"fact_id {fact_id} not found")
-
-            old_trust: float = row["trust_score"]
-            delta = _HELPFUL_DELTA if helpful else _UNHELPFUL_DELTA
-            new_trust = _clamp_trust(old_trust + delta)
-
-            helpful_increment = 1 if helpful else 0
-            self._conn.execute(
-                """
-                UPDATE facts
-                SET trust_score    = ?,
-                    helpful_count  = helpful_count + ?,
-                    updated_at     = CURRENT_TIMESTAMP
-                WHERE fact_id = ?
-                """,
-                (new_trust, helpful_increment, fact_id),
-            )
-            self._conn.commit()
-
-            return {
-                "fact_id":      fact_id,
-                "old_trust":    old_trust,
-                "new_trust":    new_trust,
-                "helpful_count": row["helpful_count"] + helpful_increment,
-            }
-
-    # ------------------------------------------------------------------
-    # Entity helpers
-    # ------------------------------------------------------------------
-
-    def _extract_entities(self, text: str) -> list[str]:
-        """Extract entity candidates from text using simple regex rules.
-
-        Rules applied (in order):
-        1. Capitalized multi-word phrases  e.g. "John Doe"
-        2. Double-quoted terms             e.g. "Python"
-        3. Single-quoted terms             e.g. 'pytest'
-        4. AKA patterns                    e.g. "Guido aka BDFL" -> two entities
-
-        Returns a deduplicated list preserving first-seen order.
-        """
-        seen: set[str] = set()
-        candidates: list[str] = []
-
-        def _add(name: str) -> None:
-            stripped = name.strip()
-            if stripped and stripped.lower() not in seen:
-                seen.add(stripped.lower())
-                candidates.append(stripped)
-
-        for m in _RE_CAPITALIZED.finditer(text):
-            _add(m.group(1))
-
-        for m in _RE_DOUBLE_QUOTE.finditer(text):
-            _add(m.group(1))
-
-        for m in _RE_SINGLE_QUOTE.finditer(text):
-            _add(m.group(1))
-
-        for m in _RE_AKA.finditer(text):
-            _add(m.group(1))
-            _add(m.group(2))
-
-        # holographic-plus: CJK quoted spans
-        for pattern in (_RE_CJK_CORNER, _RE_CJK_BOOK, _RE_CJK_DQUOTE):
-            for m in pattern.finditer(text):
-                _add(m.group(1))
-
-        return candidates
-
-    def _resolve_entity(self, name: str) -> int:
-        """Find an existing entity by name or alias (case-insensitive) or create one.
-
-        holographic-plus: after exact name/alias misses, falls back to
-        semantic resolution — embed the name and merge into the best-matching
-        existing entity (cosine >= entity_merge_threshold) by appending the
-        new name to its aliases. Merges are logged and reversible (aliases
-        are plain CSV, no data is deleted).
-
-        Returns the entity_id.
-        """
-        # Exact name match
-        row = self._conn.execute(
-            "SELECT entity_id FROM entities WHERE name LIKE ?", (name,)
-        ).fetchone()
-        if row is not None:
-            return int(row["entity_id"])
-
-        # Search aliases — aliases stored as comma-separated; use LIKE with % boundaries
-        alias_row = self._conn.execute(
-            """
-            SELECT entity_id FROM entities
-            WHERE ',' || aliases || ',' LIKE '%,' || ? || ',%'
-            """,
-            (name,),
-        ).fetchone()
-        if alias_row is not None:
-            return int(alias_row["entity_id"])
-
-        # holographic-plus: semantic merge against existing entities
-        merged = self._find_semantic_entity(name)
-        if merged is not None:
-            return merged
-
-        # Create new entity
-        cur = self._conn.execute(
-            "INSERT INTO entities (name) VALUES (?)", (name,)
-        )
-        self._conn.commit()
-        entity_id = int(cur.lastrowid)  # type: ignore[return-value]
-        # holographic-plus: embed the new canonical name (best-effort)
-        self._save_entity_embedding(entity_id, name)
-        return entity_id
-
-    # ------------------------------------------------------------------
-    # holographic-plus: embedding helpers (all best-effort, never raise)
-    # ------------------------------------------------------------------
-
-    def _save_fact_embedding(self, fact_id: int, content: str) -> None:
-        self._save_embedding("facts", "fact_embeddings", "fact_id", "content", fact_id, content)
-
-    def _save_entity_embedding(self, entity_id: int, name: str) -> None:
-        # Canonical name is the embedding input; aliases do not change it.
-        self._save_embedding("entities", "entity_embeddings", "entity_id", "name", entity_id, name)
-
-    def _save_embedding(self, source, sidecar, key, column, ident, text) -> None:
-        if self._embedder is None or emb is None:
-            return
-        try:
-            vec = self._embedder.embed(text)
-            if vec is None:
-                logger.warning("%s embedding unavailable for id=%s; missing/stale", source, ident)
-                return
-            # CAS in one SQL statement: do not resurrect a deleted fact or attach
-            # a vector to content another process changed while HTTP was in flight.
-            self._conn.execute(
-                f"INSERT INTO {sidecar} ({key}, model, dim, vector, content_hash) "
-                f"SELECT {key}, ?, ?, ?, ? FROM {source} WHERE {key}=? AND {column}=? "
-                f"ON CONFLICT({key}) DO UPDATE SET model=excluded.model, dim=excluded.dim, "
-                "vector=excluded.vector, content_hash=excluded.content_hash" +
-                (", created_at=CURRENT_TIMESTAMP" if sidecar == "fact_embeddings" else ""),
-                (self._embedder.model, len(vec), emb.vec_to_bytes(vec),
-                 hashlib.sha256(text.encode("utf-8")).hexdigest(), ident, text),
-            )
-        except Exception as e:
-            logger.warning("%s embedding save failed for id=%s (%s); missing/stale", source, ident, type(e).__name__)
-
-    def _find_semantic_entity(self, name: str) -> "int | None":
-        """Cosine-match *name* against embedded entities; merge on high sim.
-
-        On a match the new name is appended to the entity's aliases and the
-        existing entity_id is returned. Returns None when semantic resolution
-        is unavailable or nothing clears the threshold.
-        """
-        if self._embedder is None or emb is None:
-            return None
-        try:
-            vec = self._embedder.embed(name)
-            if vec is None:
-                return None
-            rows = self._conn.execute(
-                """
-                SELECT ee.entity_id, ee.vector, ee.content_hash, ee.model, ee.dim, e.name, e.aliases
-                FROM entity_embeddings ee
-                JOIN entities e ON e.entity_id = ee.entity_id
-                """
-            ).fetchall()
-            best_id = None
-            best_sim = -1.0
-            best_name = ""
-            best_aliases = ""
-            for row in rows:
-                if (row["content_hash"] != hashlib.sha256(row["name"].encode("utf-8")).hexdigest()
-                        or row["model"] != self._embedder.model or row["dim"] != self._embedder.dim):
-                    continue
-                sim = emb.cosine(vec, emb.bytes_to_vec(row["vector"]))
-                if sim > best_sim:
-                    best_sim = sim
-                    best_id = int(row["entity_id"])
-                    best_name = row["name"]
-                    best_aliases = row["aliases"] or ""
-            if best_id is not None and best_sim >= self._entity_merge_threshold:
-                new_aliases = (best_aliases + "," + name) if best_aliases else name
-                self._conn.execute(
-                    "UPDATE entities SET aliases = ? WHERE entity_id = ?",
-                    (new_aliases, best_id),
-                )
-                self._conn.commit()
-                logger.info(
-                    "holographic-plus: entity '%s' merged into '%s' (id=%d, cosine=%.3f, threshold=%.2f)",
-                    name, best_name, best_id, best_sim, self._entity_merge_threshold,
-                )
-                return best_id
-            return None
-        except Exception as e:
-            logger.debug("semantic entity resolution failed for '%s': %s", name, e)
-            return None
-
-    def _link_fact_entity(self, fact_id: int, entity_id: int) -> None:
-        """Insert into fact_entities, silently ignore if the link already exists."""
-        self._conn.execute(
-            """
-            INSERT OR IGNORE INTO fact_entities (fact_id, entity_id)
-            VALUES (?, ?)
-            """,
-            (fact_id, entity_id),
-        )
-        self._conn.commit()
-
-    def _compute_hrr_vector(self, fact_id: int, content: str) -> None:
-        """Compute and store HRR vector for a fact. Counted + warned if numpy unavailable."""
-        with self._lock:
-            if not self._hrr_available:
-                self._hrr_dropped += 1
-                if self._hrr_dropped == 1 or self._hrr_dropped % 100 == 0:
-                    logger.warning(
-                        "holographic-plus: HRR unavailable (numpy not importable in this process); "
-                        "fact %d stored WITHOUT hrr_vector (dropped this process: %d). "
-                        "It will be invisible to HRR retrieval (reason/related) until backfilled.",
-                        fact_id, self._hrr_dropped,
-                    )
-                return
-
-            # Get entities linked to this fact
-            rows = self._conn.execute(
-                """
-                SELECT e.name FROM entities e
-                JOIN fact_entities fe ON fe.entity_id = e.entity_id
-                WHERE fe.fact_id = ?
-                """,
-                (fact_id,),
-            ).fetchall()
-            entities = [row["name"] for row in rows]
-
-            vector = hrr.encode_fact(content, entities, self.hrr_dim)
-            self._conn.execute(
-                "UPDATE facts SET hrr_vector = ? WHERE fact_id = ?",
-                (hrr.phases_to_bytes(vector), fact_id),
-            )
-            self._conn.commit()
-
-    def _rebuild_bank(self, category: str) -> None:
-        """Full rebuild of a category's memory bank from all its fact vectors."""
-        with self._lock:
-            if not self._hrr_available:
-                return
-
-            bank_name = f"cat:{category}"
-            rows = self._conn.execute(
-                "SELECT hrr_vector FROM facts WHERE category = ? AND hrr_vector IS NOT NULL",
-                (category,),
-            ).fetchall()
-
-            if not rows:
-                self._conn.execute("DELETE FROM memory_banks WHERE bank_name = ?", (bank_name,))
-                self._conn.commit()
-                return
-
-            vectors = [hrr.bytes_to_phases(row["hrr_vector"], dim=self.hrr_dim) for row in rows]
-            bank_vector = hrr.bundle(*vectors)
-            fact_count = len(vectors)
-
-            # Check SNR
-            hrr.snr_estimate(self.hrr_dim, fact_count)
-
-            self._conn.execute(
-                """
-                INSERT INTO memory_banks (bank_name, vector, dim, fact_count, updated_at)
-                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
-                ON CONFLICT(bank_name) DO UPDATE SET
-                    vector = excluded.vector,
-                    dim = excluded.dim,
-                    fact_count = excluded.fact_count,
-                    updated_at = excluded.updated_at
-                """,
-                (bank_name, hrr.phases_to_bytes(bank_vector), self.hrr_dim, fact_count),
-            )
-            self._conn.commit()
-
-    def rebuild_all_vectors(self, dim: int | None = None) -> int:
-        """Recompute all HRR vectors + banks from text. For recovery/migration.
-
-        Returns the number of facts processed.
-        """
-        with self._lock:
-            if not self._hrr_available:
-                return 0
-
-            if dim is not None:
-                self.hrr_dim = dim
-
-            rows = self._conn.execute(
-                "SELECT fact_id, content, category FROM facts"
-            ).fetchall()
-
-            categories: set[str] = set()
-            for row in rows:
-                self._compute_hrr_vector(row["fact_id"], row["content"])
-                categories.add(row["category"])
-
-            for category in categories:
-                self._rebuild_bank(category)
-
-            return len(rows)
-
-    # ------------------------------------------------------------------
-    # Utilities
-    # ------------------------------------------------------------------
-
-    def _row_to_dict(self, row: sqlite3.Row) -> dict:
-        """Convert a sqlite3.Row to a plain dict."""
-        return dict(row)
-
-    @classmethod
-    def release_all_under(cls, directory: "str | Path") -> int:
-        """Force-close every shared connection whose database lives under ``directory``.
-
-        ``close()`` is refcount-driven, so a live holder (e.g. an agent's
-        memory provider) keeps a profile's SQLite handle open indefinitely.
-        That is exactly what a profile delete must break on Windows: the
-        desktop's main ``serve`` process opens ``memory_store.db`` for every
-        known profile, and ``rmtree`` of the profile directory fails with
-        ``WinError 32`` while any of those handles is open (#88347). This
-        closes the matching connections unconditionally — the directory is
-        going away, so later use by a stale holder is expected to fail — and
-        returns how many were closed. In a process that holds none (e.g. the
-        CLI deleting from outside serve) this is a harmless no-op returning 0.
-        """
-        root = os.path.normcase(str(Path(directory).expanduser().resolve())) + os.sep
-        with cls._shared_guard:
-            # Snapshot the keys first so the registry stays stable while
-            # connections are closed inside their per-database locks (closing
-            # can run no user code, but this keeps the invariant obvious).
-            doomed = [
-                key
-                for key in cls._shared
-                if os.path.normcase(key).startswith(root)
-            ]
-            for key in doomed:
-                entry = cls._shared.pop(key)
-                try:
-                    with entry["lock"]:
-                        entry["conn"].close()
-                except Exception:
-                    # A connection that is already closed or broken must not
-                    # abort releasing its siblings.
-                    pass
-        return len(doomed)
-
-    def close(self) -> None:
-        """Release this instance's reference to the shared connection.
-
-        The underlying connection is closed only when the last MemoryStore
-        referencing the same database is closed, so closing one instance can
-        never break sibling instances that still hold it. Idempotent.
-        """
-        if getattr(self, "_entry", None) is None:
-            return
-        with MemoryStore._shared_guard:
-            entry = self._entry
-            if entry is None:
-                return
-            entry["refs"] -= 1
-            if entry["refs"] <= 0:
-                try:
-                    entry["conn"].close()
-                finally:
-                    # Pop only OUR entry. After release_all_under() force-
-                    # closed this entry (profile delete, #88347) a same-path
-                    # store may have re-registered a FRESH entry under the
-                    # same key; a stale holder's late close() must not evict
-                    # it — that would silently reintroduce the multi-writer
-                    # contention this registry exists to prevent.
-                    if MemoryStore._shared.get(self._key) is entry:
-                        MemoryStore._shared.pop(self._key, None)
-            self._entry = None
-
-    def __enter__(self) -> "MemoryStore":
-        return self
-
-    def __exit__(self, *_: object) -> None:
-        self.close()
````

### 步骤 4e：dreaming submodule 提交

时间（UTC）：2026-10-13T10:57:23.390806+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git commit -m 'Move holographic-plus into its own repo as a git submodule'
[main 6821576] Move holographic-plus into its own repo as a git submodule
 10 files changed, 4 insertions(+), 2847 deletions(-)
 create mode 100644 .gitmodules
 create mode 160000 plugin/holographic-plus
 delete mode 100644 plugin/holographic-plus/NOTICE
 delete mode 100644 plugin/holographic-plus/__init__.py
 delete mode 100644 plugin/holographic-plus/embedding_index.py
 delete mode 100644 plugin/holographic-plus/embeddings.py
 delete mode 100644 plugin/holographic-plus/holographic.py
 delete mode 100644 plugin/holographic-plus/plugin.yaml
 delete mode 100644 plugin/holographic-plus/retrieval.py
 delete mode 100644 plugin/holographic-plus/store.py
````

### 步骤 4e：推送 dreaming 到 Gitea

时间（UTC）：2026-10-13T10:57:24.378336+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git push origin
remote: . Processing 1 references        
remote: Processed 1 references in total        
To http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git
   1119d53..6821576  main -> main
````

### dreaming HEAD

时间（UTC）：2026-10-13T10:57:24.380830+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git rev-parse HEAD
68215762663fe390f257b2003aeb6818d4faa634
````

### 收工生产 SHA256

时间（UTC）：2026-10-13T10:58:06.482051+00:00；退出码：0。

````text
$ SHA256 of every production *.py (recursive)
13985c6ee52d543f981f20d96d0af5a855f642b9c39ab018f71dbe3fe54eb56e  __init__.py
0d806068ca22c46512e5733a702f0c70553c0a7601cad94412facb2d84925272  embedding_index.py
3659df156e67721e5af0b76752a1872e2944e44ef05d9af007b860434643d658  embeddings.py
ffc27abd0f1ffe1ffa01c79c34dbbbb5b7a99ba72b7a75c8e9a0d1b7cbb94315  holographic.py
e4fd2162452937812136d107c7d2c7c4472a1220433d972a3199ceebc9d183e1  retrieval.py
98e1de5f2efdfb4ef617386aa45fabfd7c0f972763907f44623ad849a18030f2  store.py
75d33ea89b5bdd085307b3061efc53b156ca3fdf0bf23a48b4a79f1e60179c1b  test_entities_p0.py
d294d8d1925f0f6a8588c7799fccf8b9975a1a6afa228cdb5721b7ddc53b24f3  test_p0.py
4d7176fe6d4ba6b138d1d375c8cdc7bbe3ed365681681dab7b6f291ea3425366  test_rebuild_p0.py
510669e538551ec8d9244955f5cb9b25baf5b954e2b5b57284e9e84d066c066b  test_semantic_phase106.py
a28775b8b30e6c07cfa3b291592de0fe54d31574323e6b2b5e00db281452446b  test_sweep_p0.py
9822ea221e44ea5128690e0c5f63beac72a130c5d5a44c512341b449d2b5889c  test_timing_phase104.py
a77cd95ed27bab7552d83b4036a5d453a78e0491953d7bce5475ea485a8d2917  validate_entities_mutations.py
````

### 生产开工/收工核对

时间（UTC）：2026-10-13T10:58:06.482277+00:00；退出码：0。

````text
$ compare complete production *.py path/hash dictionaries
PASS: same 13 paths, same 13 SHA256 values; no added or removed Python files.
````

### 最终插件 HEAD

时间（UTC）：2026-10-13T10:58:06.484857+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git rev-parse HEAD
3521896162c86d6beced36820cae62753f0c3239
````

### 最终 dreaming HEAD

时间（UTC）：2026-10-13T10:58:06.487506+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git rev-parse HEAD
68215762663fe390f257b2003aeb6818d4faa634
````

### 插件 远程 main 核对

时间（UTC）：2026-10-13T10:58:07.086702+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git ls-remote origin refs/heads/main
3521896162c86d6beced36820cae62753f0c3239	refs/heads/main
````

### 插件 tracked 工作区检查

时间（UTC）：2026-10-13T10:58:07.090263+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git status --porcelain --untracked-files=no

````

### dreaming 远程 main 核对

时间（UTC）：2026-10-13T10:58:07.647858+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git ls-remote origin refs/heads/main
68215762663fe390f257b2003aeb6818d4faa634	refs/heads/main
````

### dreaming tracked 工作区检查

时间（UTC）：2026-10-13T10:58:07.657409+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git status --porcelain --untracked-files=no

````

### 插件仓提交数

时间（UTC）：2026-10-13T10:58:07.660478+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git rev-list --count HEAD
1
````

### dreaming 父提交核对

时间（UTC）：2026-10-13T10:58:07.663150+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git rev-parse 'HEAD^'
1119d53554570b93addaac140e0af3065816c00f
````

### 最终 git submodule status

时间（UTC）：2026-10-13T10:58:07.697459+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git submodule status
 3521896162c86d6beced36820cae62753f0c3239 plugin/holographic-plus (heads/main)
````

### 插件仓 git ls-files

时间（UTC）：2026-10-13T10:58:07.700133+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git ls-files
.gitignore
LICENSE
NOTICE
README.md
__init__.py
embedding_index.py
embeddings.py
holographic.py
plugin.yaml
retrieval.py
store.py
test_entities_p0.py
test_p0.py
test_rebuild_p0.py
test_semantic_phase106.py
test_sweep_p0.py
test_timing_phase104.py
validate_entities_mutations.py
````

### gitlink 模式核对

时间（UTC）：2026-10-13T10:58:07.703089+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git ls-tree HEAD plugin/holographic-plus
160000 commit 3521896162c86d6beced36820cae62753f0c3239	plugin/holographic-plus
````

### 最终 dreaming 远程

时间（UTC）：2026-10-13T10:58:07.705879+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git remote
origin
````

### 最终 dreaming 远程 URL

时间（UTC）：2026-10-13T10:58:07.708535+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git remote -v
origin	http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git (fetch)
origin	http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git (push)
````

### 最终 dreaming push URL

时间（UTC）：2026-10-13T10:58:07.710800+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git remote get-url --push --all origin
http://192.168.71.67:4100/zijianzhou/hermes-dreaming-plugin.git
````

### 原有提示文件保留核对

时间（UTC）：2026-10-13T10:58:07.711185+00:00；退出码：0。

````text
$ SHA256 phase-merge-prompt.md and phase-submodule-prompt.md
PASS: both pre-existing untracked prompt files unchanged.
````

### 已提交源码核对

时间（UTC）：2026-10-13T10:58:07.743001+00:00；退出码：0。

````text
$ SHA256 standalone working copy, submodule working copy and plugin HEAD blobs
PASS: all 13 Python files match production in all three locations, including committed Git blobs.
````

### LICENSE 字节一致核对

时间（UTC）：2026-10-13T10:58:07.743264+00:00；退出码：0。

````text
$ compare plugin LICENSE to dreaming root LICENSE
PASS: byte-identical MIT LICENSE.
````

### 步骤 5：写入报告

时间（UTC）：2026-10-13T10:59:20.950940+00:00；退出码：0。

````text
$ write dreaming/work_report_submodule_20261013.md
Created untracked report; includes both HEAD hashes, both raw push outputs, full SHA256 table, submodule status, git ls-files, choices and complete command outputs.
````

### 最终插件仓完整状态

时间（UTC）：2026-10-13T10:59:20.954370+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/holographic-plus && git status --short

````

### 最终 dreaming 完整状态

时间（UTC）：2026-10-13T10:59:20.962012+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git status --short
?? phase-merge-prompt.md
?? phase-submodule-prompt.md
?? work_report_submodule_20261013.md
````

### 确认报告未提交

时间（UTC）：2026-10-13T10:59:20.964454+00:00；退出码：0。

````text
$ cd /vol1/1000/hermes-new/data/projects/hermes-dreaming-plugin && git ls-files -- work_report_submodule_20261013.md

````

