# P07-02｜HappyHorse / FFmpeg legacy adapter 与 manifest

| 元数据 | 值 |
|---|---|
| task_id / phase | `P07-02` / `phase_07` |
| depends_on / can_run_in_parallel_with | `P07-01` / `P05-02`, `P06-02` |
| writes_to | `adapters/video/`、content/video application/tests/docs |
| forbidden_paths | changes to existing video scripts, `.env*`, real DashScope request, outputs/media, publish adapter |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking |

## Goal

把现有 HappyHorse/DashScope 与 FFmpeg 链以 `VideoPort`/manifest wrapper 接入 fake provider，保持 legacy CLI、hash、retry/no-retry 语义不变。

## Context

legacy 已能提交、轮询、下载、合成；它不是 service，且测试不能读 API key/实际生成。

## Constraints

wrapper subprocess input/output only; no copied provider code; video-edit `no_auto_retry`; no real API/outputs overwrite.

## 六层需求确认

- 目标层：safe serviceization adapter, not media generation.
- 机制层：provider IDs/adapters not truth; idempotency & cost approval required.
- 实现设计层：`primary_route=LegacyVideoPort+fake manifest`；`fallback_route=manual export manifest`；`capability_status=synthetic`；`probe_required=CLI/hash contract`。
- 流程层：approved task→manifest→fake submit/poll→artifact ref→QC.
- 判断标准层：legacy unchanged, retries safe, edit no-retry preserved.
- 反馈层：provider uncertainty/manual review, no resubmit.

## Impact check

verify legacy baseline, output isolation, secret redaction, content fact lock and Phase 4 cost/approval policy.

## Must read

content plan, P07-01, Phase 0 legacy baseline, architecture legacy table, test matrix.

## Execution contract

- Capability status：fake video provider and legacy wrapper only。
- Probe required：yes — legacy hash/CLI/manifest probe。

- Primary route：VideoPort, manifest translator, fake provider, subprocess dry contract.
- Fallback route：record manually prepared manifest/status without execution.
- Allowed Codex autonomy：new adapter/fakes/tests/docs.
- Forbidden Codex guessing：API endpoints/models/credentials/quality result/retry eligibility.
- Required inputs：synthetic approved content task, legacy baseline manifest.
- Required outputs：versioned task manifest, fake status/artifact/QC refs.
- Execution entrypoints：video adapter contracts, legacy `--help`/hash only.

## Execution steps

1. Define provider-neutral manifest/state/idempotency.
2. Map to legacy inputs without modifying script.
3. Implement fake submission/poll/download and no-retry edit guard.
4. Assert legacy hash/CLI unchanged and no `.env` use.

## Validation commands

adapter fake tests; legacy baseline checks; no network/key/output mutation scan; `make regression`.

## Done when

synthetic task can traverse manifest/fake provider with legacy behavior preserved and no real generation.

## Blocked if

adapter requires editing legacy, real API key, or cannot preserve no-retry contract.

## Output 回报格式

legacy evidence/manifest/fake tests, Git/risks, P07-03 handoff.

## Git completion

stage wrapper/tests/docs only; never stage video assets or provider output.
