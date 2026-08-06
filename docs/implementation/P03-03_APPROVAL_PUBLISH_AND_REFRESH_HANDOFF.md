# P03-03｜审批、版本化发布与下游刷新执行交接

## Repair note｜2026-08-06

- 初始任务分支提交 `8f2914844894a0a6bd721d640b99678a89c82e4d` 经控制器/独立复审标记 `CHANGES_REQUIRED`，不得作为可接受完成态引用。
- 本 repair 只在 `codex/p03-03-approval-publish-refresh` 上修复：canonical P03-01/P03-02 lineage gate、synthetic reviewer capability registry、publisher canonical decision/audit dependency、publish expiry recheck、ledger/outbox/idempotency atomic transaction、append-only revoke、P02 boundary assertion。
- 修复仍是 synthetic/value-free/internal proof only；P03 internal publication record 不是 P02 `TruthVersion`，不能被 P02 current-truth consumer 当成真值，也不代表真实 reviewer、真实业务资料、真实人工审批、生产 RBAC 或外部执行授权。

## Third repair note｜2026-08-06

- 第二轮 repair 提交 `074807b21fc215e4d28d21e524200c5029d70643` 经 5.6 独立复审继续标记 `CHANGES_REQUIRED`，不得作为可接受完成态引用。
- 第三轮 repair 只在同一任务分支修复：defensive deep snapshot、canonical fingerprint revalidation、grant/request/audit drift protection、ledger/outbox/transaction log atomic rollback、移除 public restore/snapshot mutation surface、full invalidation event fingerprint/outbox return validation、revoked successor append-only publish。
- 第三轮仍是 local synthetic contract，不是真实 auth/RBAC、process/DB crash proof、真实人工批准、真实 P02 truth 或外部业务 ready。

## Goal｜目标

- 只执行 `P03-03`：建立 synthetic/value-free 的 `mapped candidate -> approval request -> human decision -> immutable internal publication proof -> supersede/refresh` 闭环合同。
- 输入只接受 P03-02 quality-passed `MappedCandidate`，并保留 source/job/result/staging locator、rule、profile、normalization fingerprint 与 observed_at lineage。
- 本轮不读取真实供应链资料，不创建真实 approved truth，不打开任何 external action flag，不做外部同步。

## Context｜上下文

- 精确基线：`origin/main` 已由控制器回读到 `8637f827d62e5e5e48af96f4c1d1725fc0ff097d`。
- 当前任务分支：`codex/p03-03-approval-publish-refresh`。
- P03-01 已提供 synthetic source/extraction/staging lineage；P03-02 已提供 synthetic mapping/quality/replay proof；P02 truth guards 仍是 approved/current read 的唯一边界。
- business_gates、真实人工批准、真实 reviewer identity、SKU/价格/库存/资质/履约和所有 external action flags 均不变，继续 `UNKNOWN/BLOCKED/false`。

## Constraints｜边界

- 允许修改：`modules/ingestion/` 的最小 approval application service/contracts、P03-03 synthetic tests、报告/交接文档、必要的 package export。
- 禁止修改：真实业务资料、原始 DOCX/XLSX/PDF/image、`.env*`、外置盘根目录、CRM/support/video/legacy、生产连接、外部 API。
- 禁止行为：自动批准、自我审批、overwrite/delete history、reject/expire/conflict publish、真实数据 promotion、外部 send/publish/sync。
- 所有 fixture/mock 输出必须保持 `is_synthetic=true`、`external_execution_allowed=false`、`business_external_ready=false`。

## Impact check｜影响面

- 业务状态：不升级；工程能力通过不代表供应链确认、人工批准、上线、销售或履约。
- 工程状态：只在 test、regression、扫描、commit、push、remote readback 全部通过后可写 `task_branch_remote_readback_verified_not_main`。
- 真值边界：P02 `TruthVersion(data_state=approved)` 与 synthetic/fixture 绝对隔离；本卡不得创建 P02 approved truth，不得用 `is_synthetic=false` 伪装 synthetic candidate。P03-03 只创建独立 immutable simulated/internal publication record，并显式标记不可被 P02 current-truth consumer 当成真值。
- 下游刷新：只生成 internal invalidation/outbox fake event；不得存在外部同步 adapter。

## 六层需求确认

- 目标层：实现 synthetic approval/publish/refresh contract，不做真实审批、真实资料导入或外部执行。
- 机制层：request、decision、expiry、revise、publish、supersede 均需 evidence、policy、scope、actor、version 与 audit；reject/expire/conflict 不得 publish。
- 实现设计层：`primary_route=ApprovalRequestStore + SyntheticInternalPublicationLedger + internal invalidation outbox`；`fallback_route=staging/review only with stable denial code`；`capability_status=synthetic value-free local-only proof, not P02 current truth`；`probe_required=approval/invalidation E2E plus negative suite`；`allowed_codex_autonomy=contracts/services/tests/docs`；`forbidden_codex_guessing=reviewer identity, policy exception, real fact, external adapter, P02 approved truth promotion`；`required_inputs=quality-passed MappedCandidate + actor/policy/evidence envelope`；`required_outputs=internal approved publication proof, append-only audit, internal invalidation event, stable denial codes`；`execution_entrypoints=P03-03 unittest suite + make regression`；`validation_commands=focused tests, ingestion tests, contracts tests, regression, P00 scans, mechanism validation, compile, shell, diff`；`blocked_if_missing=quality-passed lineage, non-self reviewer, evidence, policy, scope match, atomic append/event`。
- 流程层：Codex 本轮实现本地合同和验证；ChatGPT/控制器复审并决定是否集成；用户/供应链仍负责真实业务授权和资料。
- 判断标准层：技术通过 = synthetic E2E 和负例通过；内容通过 = docs 明确不升级业务状态；业务通过 = 本轮不成立；Git 通过 = branch commit/push/readback。
- 反馈层：失败回到 scope/lineage、approval state、truth append、invalidation outbox、no-external-action guard 或 Git 验证；不得放宽 P02/P03 guards。

## Validation｜验证

- `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh`
- `python3 -m unittest discover -s tests/ingestion`
- `python3 -m unittest discover -s tests/contracts`
- `make regression`
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d`
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d --all-files`
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`
- `python3 -m compileall -q core modules adapters tests`
- shell syntax、`git diff --check`、forbidden value/external action scan。

## Blocked if｜阻断条件

- approval 与 truth append / invalidation event 不能保持原子性或幂等。
- 需要真实 reviewer 身份、真实资料、真实 policy exception、production database/auth/RBAC/RLS 或外部 API。
- P02 current truth guard、scope、audit、actor attribution、append-only contract 被绕过，或 P03 internal publication 被误声明为 P02 approved truth。
