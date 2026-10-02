<!-- 使用说明：参数化模板。部署前替换所有 <...> 项，填入本实例确认过的 HERMES_HOME、Python 命令、时区、模型和现行策略哈希。先隔离 dry-run；禁止把个人记忆、绝对路径或真实会话标识写入模板。 -->

执行一轮夜间记忆整理。遵循 `$HERMES_HOME/skills/<category>/memory-consolidation/SKILL.md` 及其 references。使用 `<HERMES_PYTHON>`，本轮真实 session_id/run_id 为运行时提供值，记录策略文件哈希。

## 顺序与规则

1. 建立本轮 start 回执，锁定本轮实际策略版本。
2. 运行 `<HERMES_PYTHON> -B $HERMES_HOME/scripts/fact_extract_sweep.py`，完成纠错捕获与普通事实抽取。若失败，将失败记入本轮回执，继续后续独立工作。
3. 准备只读纠错窗口，读取所有未处理纠错。仅在同主体、主题、范围及可排序的用户明确偏好/工作惯例均可独立核验时按消息时间对账；身份、红线、引用不清、证据不足、保护冲突或状态漂移均记内部 deferred，保留来源。对纠错影响主题重新读取当前版本后再做瘦身。
4. 在纠错之后、水位测量之前运行 `<HERMES_PYTHON> -B $HERMES_HOME/scripts/memory_pending_review.py --list`。逐条依据 pending-review SOP 判断：重复锚点只审最新提案；忠实且保护仍有效的合并可批准；过时、已取代、未绑定、身份类或保护块提案按规定原因丢弃。锚点失效且改动未落盘时，先通过 memory 工具按当前条目重写，再丢弃旧提案。不得请求用户输入。应用决定时带本轮 run_id；每条留一条 PENDING_REVIEW 回执。
5. 继续本实例已批准的 dreaming、按需辅助任务与 skill 审计，只在其现行有效边界内执行。处理 queued、可重试失败及已解决但 apply 未完成的工作；按 action_intent 优先于 type 路由。每项必须达到 verified、内部 deferred 或设置有界技术重试（指数退避、最多三次）。不等待用户输入。不执行退役路径。
6. 每晚分别测量 MEMORY 和 USER，即使队列为空。达到各自 `ceil(limit*0.85)` 门槛时，按顺序执行措辞压缩、无损同主题合并、验证承接后下沉；无安全候选且仍触线时按实例公式自决提额。纠错不受水位门限制。保护块 bytes 与顺序必须冻结。
7. 若 recall telemetry 缺失、损坏、不完整或本进程未加载，衰减参数置零并保留源事实，其余独立工作继续。不得据此推断 recall，也不得物理删除事实。
8. 每项操作写入本轮 DREAM_ACTION_V2 回执；完成后校验保护集并写 finish 状态。只有全部覆盖且验收通过才标 verified，否则标 partial 或 failed。成功且无需用户动作时 stdout 与推送均为零。仅 failed 或执行异常发送一条告警，内容只写可验证计数与真实恢复状态，不含标识、路径、请求、记忆原文或行动项。

绝不修改保护 EXPECTED 来消除差异；不得要求用户审批单项记忆，不得将 pending 请求转发给用户。
