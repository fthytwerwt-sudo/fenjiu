# P08-01｜真实资料包接收、归档与受控导入

| 元数据 | 值 |
|---|---|
| task_id / phase | `P08-01` / `phase_08` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | `P03-03,P04-03,P05-03,P06-03,P07-03` + 真实资料到达 | 无 |
| writes_to | 私有 storage/reference、ingestion job、审计、脱敏报告；少量 runbook 状态 docs |
| forbidden_paths | Git、`fixtures/`、`.env*`、媒体/资料包本体、production external actions |
| estimated_risk / recommended_executor | high / Work + Codex 5.6 Thinking + GPT review |

## Goal

按 Phase 8 runbook 接收真实供应链资料，私有归档、hash、quarantine、提取、mapping 和 missing/conflict/expiry 报告；不批准/外发。

## Context

资料包必须实际到达且有来源/日期/责任人；当前业务闸门此前仍是 UNKNOWN/BLOCKED，接收不等于确认。

## Constraints

原文件永不提交/复制到 fixture/sync package；不接收密码/token；不改来源文件；无 P0 资料只能报告缺口。

## 六层需求确认

- 目标层：资料证据进入候选链。
- 机制层：hash/scope/sensitivity/quarantine before extraction; no auto approval.
- 实现设计层：`primary_route=runbook ingest`；`fallback_route=private manual register`；`capability_status=requires real input`；`probe_required=package integrity`。
- 流程层：supplier→receiver→ingestion→review queue→supplier gap loop.
- 判断标准层：每字段 has locator, missing/conflict explicit.
- 反馈层：bad/unknown source quarantine; ask supplier, do not guess.

## Impact check

check data origin vs fixture, business line, PII/sensitive handling, no external modules activated; preserve audit/log redaction.

## Must read

`REAL_SUPPLIER_DATA_ONBOARDING_RUNBOOK.md`、ingestion pipeline、core contracts、current BUSINESS_STATUS/OPEN_QUESTIONS/RISKS_AND_BLOCKERS, Phase 3/4 reports.

## Execution contract

- Capability status：requires real private input; staging only。
- Probe required：yes — integrity/quarantine/idempotency probe。

- Primary route：`make ingest FILE=<private-path> BUSINESS_LINE=fenjiu` then inspect job.
- Fallback route：manual receiving record + private file reference; no mapping guess.
- Allowed Codex autonomy：hash/profile/extract/map/quality report; no approval.
- Forbidden Codex guessing：missing values, supplier authority, price/inventory/credential/permit validity.
- Required inputs：actual package, delivery source/date/owner, private storage access.
- Required outputs：receiving record, job IDs, mapping/missing/conflict/expiry report.
- Execution entrypoints：`make ingest`, `make inspect-ingestion JOB_ID=<id>`.

## Execution steps

1. Verify phase prerequisites/flags and create package receiving record.
2. Hash/classify/quarantine each file; record scope and evidence.
3. Extract/map/normalize into staging candidates with locators.
4. Produce supplier gap/conflict report and wait for new evidence as new version.

## Validation commands

hash/idempotency/quarantine reports; `make inspect-ingestion`; sensitive/path scan; no external action counters.

## Done when

real files are private, traceable staging candidates; no approved truth or enabled external capability is claimed.

## Blocked if

files absent, source/owner missing, critical files corrupt/unsafe, required fields conflict/missing, or private storage unavailable.

## Output 回报格式

received/missing/quarantined counts, job IDs/versions, data classification, no approval/external status, Git state (normally no raw-file commit).

## Git completion

Commit only sanitized runbook/report templates or code if changed; never stage raw package, paths, data extracts or credentials. Push/readback only those text changes.
