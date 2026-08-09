# 事实源地图｜SOURCE_OF_TRUTH

发生冲突时按下表读取。派生产物、截图、口头转述、聊天摘要和旧同步包不能覆盖排名更高且较新的原始来源。

| 信息类型 | 当前事实源 | 状态与说明 |
|---|---|---|
| 当前正式业务范围、阶段、职责、未知与业务阻断 | docs/project/BUSINESS_STATUS.md | **CONFIRMED** 的范围和职责来自用户明确确认（2026-08-05）；供应链实际交付仍须原始书面证据 |
| 项目总览与路由 | docs/project/CURRENT_STATUS.md | 短摘要；不替代业务或协作详细状态 |
| 协作、Git、同步包与远端回读 | docs/collaboration/COLLABORATION_STATUS.md | 远端 branch、commit、默认分支和 visibility 仅以最终回读为准 |
| 协作规则与阅读顺序 | AGENTS.md、PROJECT_ENTRY.md | **CONFIRMED** 的仓库规则和导航 |
| 当前执行范围 | docs/project/PROJECT_GOAL.md、SCOPE_AND_BOUNDARIES.md | **CONFIRMED**；旧研究不覆盖当前范围 |
| 已采用的业务与机制取舍 | docs/project/DECISIONS.md | **CONFIRMED**；每条决定须保留来源、日期、影响和状态 |
| 待补业务输入、阻断与顺序 | OPEN_QUESTIONS.md、RISKS_AND_BLOCKERS.md、NEXT_ACTIONS.md | **UNKNOWN/BLOCKED**；收到书面证据后再更新 |
| 汾酒市场、渠道和合规研究 | research_root.json、research_execution.json、research_culture_compliance.json | 资料存在为 **CONFIRMED**；涉及 B2B、多平台、90 天方案的内容为 **SUPERSEDED**（仅当前执行范围层面被替代），保留为历史市场背景，须由用户重新确认才可恢复 |
| 汾酒供应链启动模板 | 任务相关的汾酒供应链原始文件 | 模板和字段存在为 **CONFIRMED**；未签署、未回执或未回传的字段不得写为已确认 |
| 尼泊尔海鲜业务资料 | 海鲜原始资料线与对应供应链文件 | 独立资料线；不得自动用于汾酒结论 |
| 生成逻辑 | 根目录生成脚本与 scripts | 脚本存在/运行结果不等于业务事实 |
| P01 local-only runtime 与 control plane 验证 | `docker-compose.yml`、`Makefile`、`apps/*/local_runtime.py`、`core/security/`、`observability/`、`tests/local_runtime/`、`tests/control_plane/`、`docs/implementation/P01-02_LOCAL_RUNTIME_AND_MAKE_ENTRYPOINTS_REPORT.md`、`docs/implementation/P01-03_CONFIG_FLAGS_HEALTH_AND_OBSERVABILITY_REPORT.md` | **CONFIRMED（工程）**：`main` 代码已远端回读；仅证明 local-only runtime、disabled flags、not-ready control plane 和日志脱敏边界，不代表数据库接入、远端 CI、供应链、合规或业务执行成立 |
| P02-01 scope contracts 与 migration 防护 | `core/contracts/`、`migrations/0001_scope_contracts.sql`、`fixtures/synthetic_metadata.json`、`tests/contracts/`、`tests/migrations/`、`docs/implementation/P02-01_SCOPE_CONTRACTS_AND_MIGRATIONS_REPORT.md` | **CONFIRMED（工程）**：`main` P02-01 代码已远端回读至 `b08722a703f37a0cfcce0c928fec8c01c4596357`；仅证明 synthetic local metadata、scope/lineage database constraints 和隔离 migration regression，不代表 production database、真实 scope、真实业务数据、审批、供应链、合规或外部业务执行成立 |
| P02-02 truth contracts、version/state 与 current read 防护 | `modules/truth_center/`、`migrations/0002_truth_entities_versions_and_states.sql`、`tests/contracts/test_truth_contracts.py`、`tests/migrations/`、`docs/implementation/P02-02_TRUTH_ENTITIES_VERSIONS_STATES_REPORT.md` | **CONFIRMED（工程）**：`main` P02-02 代码已远端回读至 `0ba7f0575fdfe2906455c5b6301ac71c8872e727`；仅证明 value-free local contracts、append-only migration/trigger/view 与 fail-closed current read。它不代表真实业务资料、人工身份/RBAC、production isolation、合规或外部执行成立 |
| P02-03 isolation policy、fixture/consumer denial 与 audit contract | `core/contracts/access.py`、`core/security/isolation.py`、`core/application/truth_consumer.py`、`modules/truth_center/repository.py`、`tests/contracts/test_isolation_policy.py`、`tests/contracts/truth_repository_harness.py`、`docs/implementation/P02-03_ISOLATION_POLICY_AND_CONTRACT_TESTS_REPORT.md` | **CONFIRMED（工程）**：控制器已安全集成并从远端 `main` `451843601a1a610e50bfbd9794f437b5781f1401` 回读；guarded current read 在返回 truth 前强制 audit，actor attribution 由 signed grant 固定。只证明 local capability attribution integrity，不认证 actor 真伪，也不代表 production auth/RBAC/RLS、真实资料或外部执行成立 |
| P03-01 source registration、private locator、quarantine 与 fake extraction | `modules/ingestion/`、`adapters/storage/`、`fixtures/ingestion/synthetic_source_profiles.json`、`tests/ingestion/`、`docs/implementation/P03-01_SOURCE_REGISTRATION_AND_EXTRACTION_PORTS_REPORT.md` | **CONFIRMED（工程）**：控制器已将任务分支修复安全集成，并从远端 `main` `f92612bf03b5ac740e52d1d56e99f9959369b9fb` 回读。只证明 value-free synthetic fake ports、hash/idempotency、safe locator、failure retention 与 fixture workflow staging；不代表真实 parser/OCR/storage/database、approved truth、生产权限或外部执行成立 |
| P03-02 mapping、normalization fingerprint、quality 与 replay proof | `modules/ingestion/mapping.py`、`fixtures/ingestion/synthetic_mapping_profiles.json`、`tests/ingestion/test_mapping_normalization_and_quality.py`、`docs/implementation/P03-02_MAPPING_NORMALIZATION_AND_QUALITY_REPORT.md` | **CONFIRMED（工程）**：控制器已将 profile/replay provenance 和 lifecycle repair 安全集成，并从远端 `main` `355483121580c0205a43e59078eba8c29d719d93` 回读；最终独立 review `APPROVE`。只证明 synthetic value-free mapping/quality contract，不代表真实 mapping、approved truth、供应链、合规或外部执行成立 |
| P03-03 审批、隔离的合成真值发布与内部刷新 | `modules/ingestion/approval.py`、`tests/ingestion/test_approval_publish_and_refresh.py`、`docs/implementation/P03-03_APPROVAL_PUBLISH_AND_REFRESH_REPORT.md` | **CONFIRMED（工程）**：控制器已将三笔任务提交集成，并从远端 `main` `5d2c429bd253344ce3c2a3a30a31315f4a81f177` 回读。只证明合成 candidate 的人工决定、不可变隔离版本、supersede/revoke、过期审计与内部失效通知合同；记录保持 `DataState.FIXTURE`，不写入 P02 current truth，不代表真实审批、真实 approved fact、供应链、合规或任何外部执行成立 |
| P04-01 工作流状态、检查点与恢复 | `workflows/runner.py`、`core/application/interfaces.py`、`tests/workflows/test_workflow_state_checkpoint_recovery.py`、`docs/implementation/P04-01_WORKFLOW_STATE_CHECKPOINT_AND_RECOVERY_REPORT.md` | **CONFIRMED（工程）**：控制器已将三笔任务提交集成，并从远端 `main` `d2805b293cbb71f7c5898ad0c611d863fb87e4b7` 回读。只证明 local simple runner（本地简易运行器）的安全检查点、幂等恢复、重试/死信与人工队列合同；公开存储写入、终态回流和未记录审批事件均被回归拒绝。它不代表真实身份、RBAC（基于角色的权限控制）、生产队列/工作流框架、真实 provider（服务提供方）、业务真值或外部执行成立 |
| P04-02 角色、审批与动作策略 | `core/security/action_policy.py`、`tests/contracts/test_action_policy_rbac_approvals.py`、`docs/implementation/P04-02_RBAC_APPROVALS_AND_ACTION_POLICY_REPORT.md` | **CONFIRMED（工程）**：控制器已将任务提交集成，并从远端 `main` `fd727fd0a74068edfa5511a18f878c312c062b6c` 回读。只证明 local synthetic 的最小角色/动作矩阵、追加式审批决定和执行前复核；审批精确绑定版本，幂等键覆盖证据、数据状态、时效、开关、DNC/同意和环境等审批语义。它不代表真实身份认证、真实授权、生产审批/审计/队列、业务资料或任何外部执行成立 |
| 派生产物 | outputs、交付物、qa、渲染和媒体 | 仅作结果或质量线索；必须回读源数据与脚本 |
| 本地私有配置和线索 | 本地受控资料 | 不进入 Git 或同步包；不能当作对外联系授权或共享事实源 |

## 更新规则

1. 新事实须有来源、日期、责任人和事实分级。
2. 原始资料与状态冲突时，记录冲突并暂停升级，不静默挑选。
3. 新决定替代旧决定时，在 DECISIONS 中标记 SUPERSEDED，并保留原始资料。
4. 法律、平台、价格、库存、主体、账号和联系方式均应在执行前重新核验，不可仅依赖历史研究。
