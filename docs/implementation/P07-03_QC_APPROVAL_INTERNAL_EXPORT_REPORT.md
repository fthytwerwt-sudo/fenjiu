# P07-03｜视频 QC、人工审批与内部导出报告

> **状态：task_branch_validated；最终 commit / push / remote readback 以执行回报为准。**
>
> **状态回填边界：** `docs/project/*`、`docs/collaboration/*` 与 `docs/implementation/implementation_plan.yaml` 由 controller 在审查/集成后统一更新；本任务分支不修改这些全局状态文件。
>
> **执行日期：** 2026-08-10
>
> **精确工程基线：** `origin/main` `37b19ed4bffff3b9d7a0341c6e756f71ce6ff6e4`
>
> **任务分支：** `codex/p07-03-qc-approval-internal-export`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic 的 video QC、human approval/reject/revise 与 internal-export-only reference 合同。不调用真实 provider、网络、TikTok/social adapter、FFmpeg、媒体生成或 legacy 脚本；不写 raw output archive、媒体文件、真实素材或业务状态。

## 1. 结论

- 新增 `modules/content_video/qc.py`，定义 `VideoManifestEvidence`、`VideoArtifactEvidence`、`ProviderQcEvidence`、`VideoTechnicalCheck`、`VideoQcReport`、`HumanVideoDecision` 与 `InternalVideoExportRef`。
- P07-03 只消费 P07-02 `safe_summary()` 级别的 manifest/artifact/QC refs；不导入 provider adapter，不读取 media/path，不保存 raw payload。
- `VideoQcApprovalWorkflow.run_qc()` 覆盖 technical QC、fact lock、asset/source lock、policy lock 和 external flag 复核；任何失败都 fail closed 到 `revision_required` 或 `manual_hold`。
- `asset_origin=unknown`、缺失/损坏 artifact、artifact/manifest mismatch、fact expired/conflict/invalidated、policy expired/unknown、external publish flag 均不会通过 QC。
- `record_human_decision()` 支持 `approve_internal_export`、`reject`、`revise`；失败 QC 不允许 approve，revise 必须带 `revision_ref`。
- `create_internal_export_ref()` 只在 QC passed + human approved 后生成 internal-only reference；`external_publish_attempts=0`、`publish_port_present=false`、`public_publish_allowed=false` 固定为硬边界。
- 更新 `modules/content_video/__init__.py` 导出 P07-03 合同；未修改 P07-02 legacy 脚本、P05 CRM 主体或 P06 客服主体。

## 2. 行为合同

| 场景 | 稳定结果 |
|---|---|
| manifest/artifact/QC refs + technical pass + current approved synthetic fact/asset/policy | `VideoQcReport.state=passed` |
| decode/format/subtitle/audio/origin label failure | `revision_required` 或 `manual_hold`，不允许 human approve |
| missing/corrupted/mismatched artifact | `manual_hold`，`external_publish_attempts=0` |
| `asset_origin=unknown` / rights unknown | `manual_hold: asset_origin_unknown` / `asset_rights_unknown` |
| fact expired/conflict/not current/invalidated | `manual_hold`，不生成 export |
| policy expired/unknown/version drift | `manual_hold`，不生成 export |
| human reject/revise | 形成终态 decision，不生成 internal export |
| publish port 或 external publish flag | `external_publish_forbidden`，外部发布尝试计数仍为 0 |

## 3. RED → GREEN 证据

- **RED**：新增 `tests/contracts/test_video_qc_approval_internal_export.py` 后，首次运行 `python3 -m unittest tests.contracts.test_video_qc_approval_internal_export` 失败于缺少 `HumanVideoDecisionAction` 导出。
- **GREEN**：新增 P07-03 QC/approval/export contracts 与导出后，P07-03 专项 5 项通过。
- **Repair**：首轮 GREEN 前发现错误类型未对齐 `ContentVideoBoundaryError`，且安全 reason code `external_publish_forbidden` 被引用过滤器误伤；已修复并保持专项通过。

## 4. Validation evidence

- `python3 -m unittest tests.contracts.test_video_qc_approval_internal_export`：5 项通过。
- `python3 -m unittest tests.contracts.test_content_video_contracts tests.contracts.test_legacy_video_adapter_manifest tests.contracts.test_video_qc_approval_internal_export`：18 项通过。
- `python3 -m unittest tests.contracts.test_action_policy_rbac_approvals tests.contracts.test_audit_metrics_retry_dead_letter`：16 项通过。
- `python3 -m unittest tests.contracts.test_outreach_draft_zero_send tests.contracts.test_customer_service_fact_retrieval_risk_policy_and_drafts`：13 项通过。
- `python3 -m unittest discover -s tests/contracts`：114 项通过。
- `python3 -m unittest discover -s tests/ingestion`：35 项通过。
- `python3 -m unittest discover -s tests/workflows`：11 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `bash tests/migrations/run_scope_migration_regression.sh`：两轮 migration replay 与 P02/P05/P06 negative constraints 通过并清理。
- `make regression`：通过；migration replay、compileall、architecture、regression、local-runtime、control-plane、contracts 与 ingestion 全部通过。
- `python3 scripts/validate_regression_baseline.py --base-sha origin/main`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha origin/main --all-files`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `git diff --check`：通过。

## 5. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：P00 default 与 `--all-files` 均通过；新增文件不含 secret、token、cookie、本地绝对路径、媒体或 raw archive。
- `configuration_validation（配置验证）`：未新增配置、环境变量、provider endpoint、真实账号、feature flag 默认值或依赖。
- `data_safety_check（数据安全检查）`：实现和测试仅使用 synthetic refs、UUID、hash、policy/action identifiers；不读取 `.env`、真实供应链资料、真实客户资料、海鲜资料、价格、库存、资质、账号、收款、订单或履约资料。
- `audit/redaction（审计与脱敏）`：P07-03 records 暴露 `audit_metadata()` 的 safe refs/counters only；专项测试用 P04 `InMemoryAuditLog` 记录 QC、decision、internal export 事件并验证 chain，safe summary 不含路径、media、provider raw id 或 prompt text。
- `legacy_regression（legacy 回归）`：P07-02 `test_legacy_video_adapter_manifest` 与 P07-03 联跑通过；未修改 legacy scripts 或 `adapters/video/fake.py`。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖文件。

## 6. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P07-03 synthetic QC、human approve/reject/revise、audit metadata 与 internal-only export reference 已由专项、相邻合同、完整回归、P00 扫描、机制验证和 compile/diff 检查验证。
- **CONFIRMED（工程边界）**：`external_publish_attempts=0`、`publish_port_present=false`、`public_publish_allowed=false` 在 report/decision/export 层固定；没有接入 TikTok/social adapter、真实 provider、网络、媒体生成、raw archive 或 legacy script execution。
- **BLOCKED（业务）**：真实 SKU、素材授权、平台酒类边界、价格、库存、主体/资质、账号、收款、履约、真实 content approval、真实视频生成和公开发布仍未建立或未获当前书面证据。
- **不成立**：本任务不代表视频真实生成、真实画质通过、平台允许发布、供应链确认、线上销售、收款、订单或履约就绪。

## 7. Phase 8 / controller handoff

- P08 只能把本任务的 internal export reference 当作 synthetic engineering artifact，不得当作真实素材、真实 provider 输出或可发布内容。
- 若后续任务需要真实视频、素材、provider 或公开发布，必须重新经过业务闸门、平台酒类边界、人工授权、provider adapter contract、审计和 no-publish-to-publish 的单独批准。
