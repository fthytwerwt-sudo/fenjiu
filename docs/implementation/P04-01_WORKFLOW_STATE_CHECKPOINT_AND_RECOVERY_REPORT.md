# P04-01｜Workflow state、checkpoint 与 recovery 报告

> **状态：task_branch_local_validated；最终 commit / push / remote readback 以执行回报为准。**
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** `origin/main` `e00806a580e1fe4f3e5c45e4ee396d81821d84f5`
>
> **任务分支：** `codex/p04-01-workflow-state`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic/value-free 的 workflow run state、checkpoint、idempotency、pause/resume/retry/DLQ 与 optional LangGraph probe 合同。不接入真实 provider、生产账号、外部发送、公开发布、报价、支付、订单、库存写回或真实业务资料。

## 1. 结论

- 新增 `workflows/runner.py`，实现 `SimpleWorkflowRunner`、`InMemoryWorkflowStore`、`WorkflowCommand`、`WorkflowCheckpoint`、`WorkflowRun` 与 non-blocking `probe_optional_langgraph_adapter()`。
- `simple runner` 是 `primary_route` 与 `fallback_route`；`capability_status=probe`。
- LangGraph 仅做本地 import availability probe；当前环境 probe 结果为 `deferred`，原因是 `langgraph_not_installed_no_dependency_added`。本任务未安装、升级或联网获取任何依赖。
- workflow 只保存运行元数据、checkpoint reference/hash、idempotency state、manual queue / DLQ metadata 和 run event sequence；不保存业务事实、不拥有 P03 approval truth、不写 P02 current truth。
- `core/application/interfaces.py` 仅新增 primitive `WorkflowQueuePort` 协议，队列端口只接收 `workflow_run_id` 与 `checkpoint_ref`，不接收 payload 或业务数据。

## 2. Run state 与 checkpoint 合同

每个 `WorkflowRun` 保留：

```text
workflow_run_id
scope
correlation_id
command_type
input_hash
policy_version
idempotency_key
attempt
checkpoint_ref
actor
created_at / updated_at
terminal_result
```

`WorkflowCheckpoint` 仅允许 safe resume metadata：identifier、hash、boolean、integer、reference-like value 和嵌套安全结构。以下内容 fail closed：secret / token / cookie / password key，raw/free text，private data key，本机绝对路径，敏感 metadata。

## 3. Recovery proofs

| 场景 | 已验证行为 |
|---|---|
| crash / replay | fake internal effect 已提交后模拟 crash；新 runner 用同一 store resume，终态 `succeeded`，effect commit count 仍为 1 |
| pause / resume | `fake_internal` command 先进入 `waiting_for_approval`，记录 approval ref 后 resume |
| retry / timeout / DLQ | timeout command 在 attempt 1 进入 `retry_scheduled`，attempt 2 进入 `dead_lettered`，无 effect commit |
| duplicate idempotency key | 相同 key / 相同 fingerprint 返回同一 run；相同 key / 不同 input hash 返回 `idempotency_conflict` |
| external forbidden effect | `external_forbidden` 直接 `policy_denied`，不调用 provider，不写 effect |
| unknown effect | `unknown` 进入 `manual_queue`，不调用 provider，不写 effect |
| audit consistency | workflow run events append-only sequence 从 1 连续增长；这些仅是 run metadata，不替代业务 audit truth |

## 4. Test-first evidence

- **RED**：首次运行 `python3 -m unittest tests.workflows.test_workflow_state_checkpoint_recovery` 因 `ModuleNotFoundError: No module named 'workflows.runner'` 失败。
- **GREEN**：新增最小 runner / store / checkpoint / probe 后，`python3 -m unittest discover -s tests/workflows` 8 项通过。

## 5. Validation evidence

- `python3 -m unittest discover -s tests/workflows`：8 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `python3 -m compileall -q -x '(^|/)\._' core modules adapters workflows tests`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `git diff --check`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha e00806a580e1fe4f3e5c45e4ee396d81821d84f5`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha e00806a580e1fe4f3e5c45e4ee396d81821d84f5 --all-files`：通过。
- `make regression`：通过；migration replay 两次、16 类 SQL negative constraints、8 architecture、14 regression、8 local-runtime、16 control-plane、46 contracts、35 ingestion tests 通过。

## 6. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P04-01 local simple runner 合同、checkpoint safety、idempotency、pause/resume、crash/replay、retry/DLQ、manual queue 与 optional LangGraph probe 已由本地测试覆盖。
- **CONFIRMED（工程边界）**：没有新增依赖、外部 provider、生产账号、真实连接、真实资料读取或业务外部动作。
- **DEFERRED（adapter）**：LangGraph adapter 未启用；仅记录当前环境未安装，后续如要接入必须复跑同一 contract suite，并证明 framework memory 不是唯一恢复来源。
- **BLOCKED / UNKNOWN（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实 approval actor/RBAC/RLS、production database 和任何外部业务动作仍未建立或未获书面证据。

## 7. P04-02 输入

- P04-02 可以复用 `WorkflowRun` 的 `actor`、`scope`、`correlation_id`、`policy_version`、`idempotency_key` 与 `checkpoint_ref`，在 action policy / RBAC 层决定是否允许 command 继续。
- 不应把 `SimpleWorkflowRunner` 扩大为 approval owner、audit truth owner 或 provider adapter。
