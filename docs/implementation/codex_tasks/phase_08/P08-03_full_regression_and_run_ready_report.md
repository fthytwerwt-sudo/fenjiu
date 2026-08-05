# P08-03｜全链回归、受控演示、rollback 与 run-ready 报告

| 元数据 | 值 |
|---|---|
| task_id / phase | `P08-03` / `phase_08` |
| depends_on / can_run_in_parallel_with | `P08-02` | 无 |
| writes_to | test reports/private evidence/run-ready report、sanitized execution history/docs |
| forbidden_paths | real external sending/publishing/quotes/orders/payment/refunds, raw data/PII, fixture-to-real copy |
| estimated_risk / recommended_executor | high / Work + Codex 5.6 Thinking + GPT review |

## Goal

在真实 approved truth 上完成全链技术回归、指定受控内部会话/内容/video/CRM 演示、权限/日志/rollback 演练，并生成三层状态分离的 run-ready 报告。

## Context

Phase 8 目标是技术受控运行；Phase 9 外部上线闸门仍独立 blocked，所有 external feature flags 保持 false。

## Constraints

只用 designated internal/demo channel；不能发送客户、发布 TikTok、报价/收款/下单；报告不可含 raw supplier/customer details/absolute paths/secrets。

## 六层需求确认

- 目标层：prove system_technical_ready/data_usable, not external execution.
- 机制层：all tests/audit/rollback/flags must pass; failure disables affected modules.
- 实现设计层：`primary_route=make regression+demo+report`；`fallback_route=partial report with BLOCKED`；`capability_status=controlled internal`；`probe_required=full E2E`。
- 流程层：approved truth→modules→negative tests→rollback→report→human review.
- 判断标准层：zero external actions and evidence complete.
- 反馈层：any failure→flag off/revoke as needed/re-run affected suite.

## Impact check

verify source/version/scope, fixture separation, DNC/high-risk handoff, legacy behavior, audit/redaction, queue/DLQ and future Phase 9 boundary.

## Must read

runbook, test matrix, run-ready template, all Phase 5–7 reports, current BUSINESS_STATUS/RISKS/OPEN_QUESTIONS.

## Execution contract

- Capability status：controlled internal run-ready only; external action disabled。
- Probe required：yes — full E2E/rollback/zero-external-action probe。

- Primary route：`make regression`, `make demo-run BUSINESS_LINE=fenjiu`, `make run-ready-report BUSINESS_LINE=fenjiu`.
- Fallback route：failed/partial report with blocked modules and no state promotion.
- Allowed Codex autonomy：run controlled tests/rollback/report; no external action.
- Forbidden Codex guessing：business approval, platform license, customer intent, acceptable legal/commercial risk.
- Required inputs：approved fact set, all prerequisite test environments/reviewer, feature flags false externally.
- Required outputs：test evidence, rollback proof, run-ready report, Phase 9 gap list.
- Execution entrypoints：listed make commands and audit/flag queries.

## Execution steps

1. Confirm source/version approvals and flags/external count=0.
2. Run unit/contract/integration/E2E/legacy negative suites.
3. Run controlled internal CS/CRM/content-video demos and handoff/DNC/expired fact cases.
4. Disable an internal module, rollback/supersede scenario, and prove recovery/audit.
5. Generate report marking three status fields separately and list Phase 9 blockers.

## Validation commands

`make regression`; `make demo-run BUSINESS_LINE=fenjiu`; `make run-ready-report BUSINESS_LINE=fenjiu`; secret/path/PII scan; audit/DLQ/feature-flag checks.

## Done when

report evidence supports named `system_technical_ready`/`data_usable` values; fixture isolation, full regression and rollback pass; `external_execution_allowed=false` is explicit.

## Blocked if

any regression/mapping/approval/audit/rollback fails, missing critical data, nonzero external action, or Phase 9 evidence absent (the latter always blocks external use).

## Output 回报格式

three-state conclusion, module matrix, tests/negative cases/rollback, Git remote readback, unresolved Phase 9 gates and owner.

## Git completion

Stage only sanitized reports/docs/scripts; no raw data/PII. Commit/push/remote readback is technical evidence, not business approval.
