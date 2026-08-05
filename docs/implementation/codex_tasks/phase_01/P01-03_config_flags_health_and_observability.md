# P01-03｜配置、默认关闭 flags、健康检查与基础日志

| 元数据 | 值 |
|---|---|
| task_id / phase | `P01-03` / `phase_01` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | `P01-02` / 无 |
| writes_to | `core/security/`、`observability/`、`apps/`、tests/docs |
| forbidden_paths | `.env*`、真实 webhook/provider 配置、业务模块、legacy/资料 |
| estimated_risk / recommended_executor | medium / Codex 5.6 Thinking |

## Goal

建立 typed settings、feature flags、health/readiness、correlation-aware JSON log 与 secret redaction 的最小合同。

## Context

所有外部发送、发布、报价、退款、订单、支付、库存写回、real crawl/video 均必须默认 false。

## Constraints

不得记录 message/file 内容、API keys、Cookie、绝对路径；health 不泄露 config；flags 不能被 fixture 或 prompt 覆盖。

## 六层需求确认

- 目标层：控制安全默认，不启用能力。
- 机制层：missing/invalid config fail closed。
- 实现设计层：`primary_route=typed settings+flag service`；`fallback_route=local static disabled config`；`capability_status=local`；`probe_required=negative tests`。
- 流程层：应用/worker 读取→policy 决定→audit/log。
- 判断标准层：所有 sensitive flags false 且拒绝路径可测。
- 反馈层：未知配置/secret 命中停止并最小化报告。

## Impact check

不会与 legacy `.env` 或同步包机制耦合；日志格式未来须供 audit/metrics，但不替代 audit。

## Must read

`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`、`TEST_ACCEPTANCE_ROLLBACK_MATRIX.md`、`P01-02` config/Compose。

## Execution contract

- Capability status：local control plane; all sensitive actions disabled。
- Probe required：yes — flag, health and redaction probe。

- Primary route：settings schema、FeatureFlagPort、health/readiness、redacted logger 和 tests。
- Fallback route：没有 broker/provider 仍返回 disabled capability，不伪装 ready。
- Allowed Codex autonomy：新增指定基础设施代码/tests/docs。
- Forbidden Codex guessing：真实 URL/key、运营权限、合规允许。
- Required inputs：P01 runtime、flag list、log contract。
- Required outputs：config/flag/health tests and safe docs。
- Execution entrypoints：`make dev-up`、health test、`make regression`。

## Execution steps

1. 定义 settings 和 default flags。
2. 加 health/readiness 区分、correlation and redaction。
3. 测试 missing config、flag denial、secret/path redaction。
4. 文档化不等于 business ready。

## Validation commands

test runner config/flag suites；health probes；日志敏感扫描；`make regression`。

## Done when

所有高风险 flag 默认为 false、错误安全、日志无敏感内容、下游 Phase 2 可复用。

## Blocked if

需要真实 secret/provider 才能验证、health 被要求暴露内部详情、日志政策未确定。

## Output 回报格式

flags table、拒绝测试、health/log 结果、Git/风险、Phase 2 开始条件。

## Git completion

仅 stage 基础设施配置/测试/docs；push/readback 后报告，不提交环境文件。
