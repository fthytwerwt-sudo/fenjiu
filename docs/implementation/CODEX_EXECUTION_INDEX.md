# Codex 分阶段执行索引

> **SUPERSEDED AS CURRENT BUSINESS QUEUE｜2026-08-28**：此索引保留为已完成 synthetic/local-only 工程任务的历史与技术依赖图。它不是当前业务优先队列；尤其 P08 不能因代码依赖完成而自动开始。先读 [`docs/strategy/SALES_EXECUTION_PHASES.md`](../strategy/SALES_EXECUTION_PHASES.md) 和 `docs/project/NEXT_ACTIONS.md`，并为每个新实现任务补齐 Sales-First 的实现设计层和业务闸门证据。

> **使用规则：** 一次只下发一个 task card；任务执行前重读当前事实源，执行后按该卡 Git completion 收口。不要把 Phase、目录或 task 卡当作业务已完成。

| Phase | 任务 | 依赖 | 可并行 | 目的 |
|---|---|---|---|---|
| 00 | [P00-01](codex_tasks/phase_00/P00-01_engineering_asset_baseline.md) | 无 | 无 | 审计资产和禁区。 |
| 00 | [P00-02](codex_tasks/phase_00/P00-02_freeze_architecture_and_adr.md) | P00-01 | P00-03 | 冻结技术路线/ADR。 |
| 00 | [P00-03](codex_tasks/phase_00/P00-03_validation_and_sensitive_scan_baseline.md) | P00-01 | P00-02 | 建 legacy/敏感扫描基线。 |
| 01 | [P01-01](codex_tasks/phase_01/P01-01_modular_monolith_skeleton.md) | Phase 00 | 无 | 创建空工程骨架。 |
| 01 | [P01-02](codex_tasks/phase_01/P01-02_local_runtime_and_make_entrypoints.md) | P01-01 | 无 | Compose/Make/CI。 |
| 01 | [P01-03](codex_tasks/phase_01/P01-03_config_flags_health_and_observability.md) | P01-02 | 无 | 配置、flags、health/log。 |
| 02 | [P02-01](codex_tasks/phase_02/P02-01_scope_contracts_and_migrations.md) | Phase 01 | 无 | scope 和 migration 基线。 |
| 02 | [P02-02](codex_tasks/phase_02/P02-02_truth_entities_versions_and_states.md) | P02-01 | 无 | 真值实体/状态/version。 |
| 02 | [P02-03](codex_tasks/phase_02/P02-03_isolation_policy_and_contract_tests.md) | P02-02 | 无 | 隔离与 negative contracts。 |
| 03 | [P03-01](codex_tasks/phase_03/P03-01_source_registration_and_extraction_ports.md) | Phase 02 | 无 | 原始登记和 extraction ports。 |
| 03 | [P03-02](codex_tasks/phase_03/P03-02_mapping_normalization_and_quality.md) | P03-01 | 无 | mapping/清洗/质量。 |
| 03 | [P03-03](codex_tasks/phase_03/P03-03_approval_publish_and_refresh.md) | P03-02 | 无 | 人审、publish、失效。 |
| 04 | [P04-01](codex_tasks/phase_04/P04-01_workflow_state_checkpoint_and_recovery.md) | Phase 03 | 无 | workflow/checkpoint/recovery。 |
| 04 | [P04-02](codex_tasks/phase_04/P04-02_rbac_approvals_and_action_policy.md) | P04-01 | 无 | RBAC/approval/policy。 |
| 04 | [P04-03](codex_tasks/phase_04/P04-03_audit_metrics_retry_and_dead_letter.md) | P04-02 | 无 | audit/metrics/DLQ。 |
| 05 | [P05-01](codex_tasks/phase_05/P05-01_source_policy_and_crawl_port.md) | Phase 04 | P06-01, P07-01 | public source/fake crawl。 |
| 05 | [P05-02](codex_tasks/phase_05/P05-02_leads_and_crm_domain.md) | P05-01 | P06-02, P07-02 | leads/CRM/DNC。 |
| 05 | [P05-03](codex_tasks/phase_05/P05-03_outreach_draft_and_export.md) | P05-02 | P06-03, P07-03 | draft-only/outbound 0。 |
| 06 | [P06-01](codex_tasks/phase_06/P06-01_conversation_contracts_and_privacy.md) | Phase 04 | P05-01, P07-01 | conversation/message contracts。 |
| 06 | [P06-02](codex_tasks/phase_06/P06-02_fact_retrieval_risk_policy_and_drafts.md) | P06-01 | P05-02, P07-02 | truth read/draft/handoff。 |
| 06 | [P06-03](codex_tasks/phase_06/P06-03_support_adapter_and_human_takeover.md) | P06-02 | P05-03, P07-03 | fake inbox/handoff。 |
| 07 | [P07-01](codex_tasks/phase_07/P07-01_content_video_contracts_and_fact_lock.md) | Phase 04 | P05-01, P06-01 | content/video contracts。 |
| 07 | [P07-02](codex_tasks/phase_07/P07-02_legacy_video_adapter_and_manifest.md) | P07-01 | P05-02, P06-02 | legacy wrapper/fake. |
| 07 | [P07-03](codex_tasks/phase_07/P07-03_qc_approval_and_internal_export.md) | P07-02 | P05-03, P06-03 | QC/internal output only。 |
| 08 | [P08-01](codex_tasks/phase_08/P08-01_real_package_receipt_and_controlled_ingest.md) | 03–07 + real data | 无 | 真实包登记/导入。 |
| 08 | [P08-02](codex_tasks/phase_08/P08-02_real_truth_approval_and_fixture_switch.md) | P08-01 | 无 | approved truth/fixture isolation。 |
| 08 | [P08-03](codex_tasks/phase_08/P08-03_full_regression_and_run_ready_report.md) | P08-02 | 无 | 全链回归/run-ready。 |

Phase 9 没有 Codex 实现卡：它是合规、平台、账号、履约、收款和用户授权的业务闸门，不应被自动化任务替代。
