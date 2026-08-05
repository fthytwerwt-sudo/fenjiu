# 测试、验收与回滚策略

> **状态：RECOMMENDED / 未实施。** 本文定义后续每个 Phase 要证明的行为；它不声称当前仓库已经具备该测试套件。路线与 gate 见 [分阶段路线](PHASED_ROADMAP_AND_ACCEPTANCE.md)。

## 1. 测试金字塔与最低通过线

| 层级 | 目标 | 最低证据 | 失败即停止 |
|---|---|---|---|
| Unit | policy、状态机、normalizer、dedupe、ID/scope 规则 | 每个核心规则正反例 | 业务规则可被绕过 |
| Contract | modules/adapters/legacy manifests 的版本化输入输出 | valid + invalid fixture；provider fake | 更换 adapter 会改变领域含义 |
| Integration | PostgreSQL、队列、migration、repository、RBAC/audit | 临时 DB/Redis compose；transaction/retry | 记录丢失、跨线可读、迁移不安全 |
| Workflow E2E | 五条纵向流程的 synthetic 闭环 | 固定 fixtures、correlation/audit 断言 | 有一步越过审批或 fixture guard |
| Regression | 现有视频/DOCX/XLSX/同步包链不回归 | CLI `--help`/dry-run、manifest/hash、现有验证脚本 | 新底座需改写旧脚本才能工作 |
| Security/operational | secret/PII/AppleDouble、日志、权限、恢复 | 扫描、negative tests、失败演练 | 秘密/真人资料可进入 Git/日志/外发 |

## 2. 必须覆盖的测试清单

### 2.1 数据合同与版本

- 所有 scoped entity 缺 `tenant_id/project_id/business_line_id`、`source_ref_id`、`version_id` 或 `data_state` 时 schema 失败。
- `approved_fact` 缺人工 approval、来源定位、有效期或有效 scope 时失败；`expired/conflict/blocked/superseded` 不能被 read model 提供给客户/内容。
- 同实体新版本创建 `data_version`、保留 parent/diff；禁止覆盖旧值。
- 冲突字段建立 conflict，不能按“最新时间”静默挑选；人为裁决后产生新版本。
- mapping rule 对固定 fixture 可重复输出；规则升级对历史 fixture 回归并出差异报告。

### 2.2 Fixture 与真实数据隔离

- 每个 fixture 有 `is_synthetic=true`, `data_state=fixture`, `source_kind=fixture`, `external_execution_allowed=false`。
- fixture 被传给 `external_sync`, `send`, `publish`, `payment`, `order`, `inventory_write` command 时，policy 明确拒绝并写 `audit_event`。
- 没有任何测试数据使用当前项目真实 SKU、价格、库存、联系方式、图片、PDF、视频、Token 或可识别供应链资料。
- Phase 5 的 real-data integration suite 在私有环境运行；Git 可提交的测试只含匿名/合成样本与 schema。

### 2.3 权限与人工闸门

- RBAC/tenant scope 对跨项目/跨业务线读、写、审批、导出全数拒绝。
- `approval_request` 只能由指定角色决策；过期、拒绝、撤销后不能 resume。
- 价格、库存、配送、合规、外联、发送、发布、退款、订单/支付每类都有 `requires_approval=true` 的 negative test。
- 客服 high-risk intent、DNC、事实不足、模型置信度低、合规禁语命中时均转人工；不生成可发送动作。
- 内容/视频 fact checker 对未经批准 SKU、价格、库存、功能/许可、素材权利不明、酒类限制表述的脚本失败关闭。

### 2.4 幂等、重试与恢复

- `ingestion_job`：相同 file hash + parser/mapping version 重跑不创建重复候选/事实。
- webhooks：相同 external message ID 不重复建 message、草稿或审计。
- lead snapshot：相同 URL/content hash/策略不重复创建 source evidence。
- 队列 worker：retry 在安全边界内，attempt count 和 dead-letter 可见；异常不会丢 audit event。
- workflow interrupt/resume：审批前副作用使用 idempotency key；恢复不会重发/重投/重建事实。
- legacy video：成功、失败、timeout、resume、质量重试上限、一次性 no-retry mode 都有 contract fake；不对真实 API 发请求。

### 2.5 审计与可观察性

- 任何 create/update/approve/reject/send-attempt/publish-attempt/adapter retry 都有 `audit_event`，且 correlation、actor、scope、policy result 可查。
- 测试模拟数据库写入失败，验证业务状态与 audit 不出现“成功但无审计”或“已发送但无证据”。
- 日志扫描确认不出现 secret、token、cookie、完整私人消息、绝对本机路径或二进制附件。
- metrics 至少覆盖队列积压、failed/dead-letter、approval pending/expired、data state、adapter errors；告警配置可后置，但指标名称/语义先有 contract。

### 2.6 Adapter 可替换性

- 每个 adapter 必有 port interface、fake adapter、contract fixture、capability registry 和 migration/export note。
- LangGraph/工作流层调用 application port；替换为简单状态机 runner 的测试不得影响 approval/审计结果。
- Crawl adapter 使用 synthetic HTML/响应 fixtures；替换工具不改变 source snapshot/lead contract。
- CRM/客服 adapter 启用前后都可用 CSV/JSON 导出当前 scope；不将 provider ID 当主键。
- 视频 adapter 将 legacy manifest 映射为 `video_task`，不修改 legacy script 输出格式；provider 替换只影响 adapter tests。

### 2.7 现有视频链回归

对 `generate_happyhorse_shots.py`、`generate_happyhorse_video_edit_once.py`、`prepare_video_assets.py`、`assemble_final_video.py`、`build_video_execution_report.py`：

1. 保留当前文件 hash/CLI usage 与已知 manifest fixture 的基线；
2. 无 `.env` 时只跑安全的 import/CLI help/manifest validation，不调用模型；
3. 断言新 adapter 只是 wrapper，不修改原脚本、原 outputs 或已有任务 state；
4. 对带“无官方 SKU/素材”情况的 fixture，fact policy 必须阻止将具体商品写进内容；
5. 视频技术成功与公开发布/业务验收分开报告。

## 3. Synthetic E2E 验收剧本

每次大版本至少跑一次，生成可归档但不含真实数据的测试报告。

1. 建立两个 synthetic business lines：`fenjiu_nepal_fixture` 与 `seafood_nepal_fixture`。
2. 导入 synthetic supplier spreadsheet：一个可批准商品描述、一个过期价格、一个冲突库存；验证状态与来源版本。
3. 以 public HTML fixture 建立 lead candidate；审核成组织，验证同名去重与跨线拒绝。
4. 生成外联草稿；DNC variant 必须失败；批准 variant 也只能显示“等待手动发送”。
5. 处理 synthetic inbound question：普通 FAQ 生成 draft；价格/退款/酒类/食品安全 variant 创建 handoff；无 approved fact variant 不给答案。
6. 用 approved synthetic facts 生成内容草稿和视频 manifest；缺事实 variant 阻断；fake video task 完成后 QC 未过的版本不可批准。
7. 使一个事实过期，验证所有引用草稿失效；运行重试/恢复 variant，确认没有重复实体、发送或 provider submission。
8. 导出 audit trail，检查每条记录 scope 正确、没有外部副作用、没有 fixture leakage、没有 secret/PII。

## 4. 阶段进入/停止的量化标准

| Gate | 可进入下一阶段 | 必须停止 |
|---|---|---|
| Contract gate | 100% core entities 有 valid/invalid schema fixtures；scope/version/source/approval negative tests 通过 | 任一 required field 可省略或 `approved` 无证据 |
| Fixture gate | E2E 证明 0 次 fixture external action | fixture 能进入 send/publish/payment/order 路径 |
| Approval gate | 所有高风险 action 有 pending/approve/reject/expire test | 任一高风险动作可在无审批下执行 |
| Audit gate | 100% mutating commands 产生 audit event；审计不含秘密 | 修改/决定缺审计或审计泄露私密内容 |
| Reliability gate | 幂等/retry/resume test 通过；dead-letter 可查询 | 重跑会重复发送、重复提交或丢失数据 |
| Legacy gate | 现有脚本未被修改，baseline 通过 | 新系统侵入式改变现有视频/DOCX/XLSX 链 |
| Production gate | 所有 Phase 6 书面证据和回滚演练通过 | 任何业务/合规/授权/owner/kill switch 缺失 |

## 5. 回滚分层

| 层 | 首选回滚 | 不能做 |
|---|---|---|
| Code/config | feature flag off → 还原单个明确 commit → 重跑 tests | `git reset --hard`、覆盖不相关工作 |
| Database schema | expand/contract migration；先禁用新路径，再按已演练 migration 处理 | 在含真实数据的生产库盲目 down migration |
| Data/facts | 创建 `superseded/revoked` 新版本；使草稿/缓存失效 | 删除原始来源或历史 audit |
| Workflow/job | 停止消费、保留 queue/dead-letter/trace、手工决定恢复 | 直接重试未知副作用任务 |
| External adapter | revoke feature flag/credential reference、停止 webhooks、隔离 payload | 以“重发/删记录”掩盖外部副作用 |
| Content/video | 标记 artifact withdrawn/expired，停止后续路径 | 覆盖或删除原视频/原任务证据 |

## 6. 实施回报模板

每个 Codex 任务收尾必须报告：

```text
Result: completed | partial_completed | blocked
Scope: tenant/project/business_line and fixture/real-data status
Changed files: explicit list only
Tests: command + result + key negative paths
Adapter impact: port/contract/fake/export/exit plan
Audit/approval proof: correlation IDs or anonymized fixture references
Regression: legacy/video/docs/sync impact
Git: branch, diff, staged paths, commit, push, remote readback
Remaining risks: confirmed / partial / needs verification / blocked
```

任何“测试通过”报告都必须另行标注：这是技术证据，不等于供应链确认、平台许可、公开发布、销售、履约或真实业务结果。
