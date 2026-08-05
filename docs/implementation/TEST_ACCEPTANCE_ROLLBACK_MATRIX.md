# 测试、验收与回滚矩阵

> **状态：PLANNED。** 所有测试数据必须 synthetic 或经独立授权/脱敏的私有测试数据；仓库不得出现真实 SKU、价格、库存、客户或凭据。

## 1. 分层测试

| 层 | 覆盖 | 通过证据 |
|---|---|---|
| unit | normalizer、policy、state transition、scope guard | valid/invalid 向量和稳定 error code。 |
| contract | ports/adapters、Pydantic/JSON schema、mapping | fake 与 real-candidate adapter 同一合同。 |
| integration | PostgreSQL migration、queue/workflow、RBAC/audit | disposable local DB，up/down/upgrade path，append-only audit。 |
| E2E | Phase 3–7 synthetic workflows | 0 external send/publish/payment/order、跨线拒绝、手工 approval。 |
| regression | legacy video/DOCX/XLSX/sync behavior | legacy file hash/CLI/manifest baseline；不读 `.env`/不调模型。 |
| security/ops | secrets/path/PII, retry/DLQ, observability | no sensitive output、idempotency、metrics/correlation 可查。 |

## 2. 最小 acceptance matrix

| Gate | 必须为 true | 一票否决 |
|---|---|---|
| contract | 100% core entities 有 scope/source/version/state valid+invalid fixtures | approved 缺 evidence/reviewer，或跨线可读。 |
| fixture isolation | external action attempts = 0 | fixture 能进入 real/send/publish/payment/order path。 |
| approval/policy | 高风险 action pending/approve/reject/expire tests 完整 | AI 或同一生成者能批准自己的风险动作。 |
| audit | 每个 mutating command 有 correlation/scope/policy/result | 可普通更新/删除 audit，或 log 泄露正文/secret/path。 |
| reliability | idempotency/retry/resume/DLQ 全通过 | 重跑重复事实、消息、provider submit 或外发。 |
| legacy | old scripts unchanged and dry-safe baseline passes | wrapper 改变原 CLI/manifest/output semantics。 |
| Phase 8 real data | approved quality/mapping/review/report all green | missing/conflict/expired critical fact 仍被业务模块使用。 |

## 3. rollback 的优先级

1. **立即停动作：** 关闭对应 feature flag/worker/adapter，阻止新的外部副作用。
2. **保留证据：** freeze job/run、DLQ、audit、source reference、manifest 和错误码；不得删除掩盖问题。
3. **撤回数据可用性：** 创建 `revoked/superseded/expired` version，失效缓存和未执行草稿/task。
4. **恢复代码/结构：** 对确定的单一 commit 使用 forward fix 或已演练的 expand/contract migration；不使用 destructive reset/无证据 down migration。
5. **重新验收：** 从 affected contract/E2E scenario 及 full regression 重新运行，再由 reviewer 解除 flag。

## 4. 发布/业务判定边界

测试全绿只可证明 `technical_ready`（并在资料 approved 后可能证明 `data_ready`）。`business_external_ready` 与策略字段 `external_execution_allowed` 仍需 Phase 9 的用户授权、当地许可、品牌授权、平台酒类边界、账号权限、价格/库存、收款和履约/售后证据；测试不得替代它们。
