# P02-02｜真值实体、版本与状态机报告

> **状态：local_verification_passed_git_completion_reported_out_of_band**
>
> **执行日期：2026-08-06**
>
> **基线提交：** `43ec53fc4441f22fd2492324c2d0d3a3da460f6b`
>
> **范围边界：** 仅实现 value-free、local-only 的 synthetic contract probes、纯 SQL schema/trigger/view 与测试；不包含真实 SKU、价格、库存、资质、素材、禁语正文、ORM/driver、生产连接或外部动作。

## 1. 实现结论

- `TruthEntityKind` 固定九类合同：`product`、`sku`、`price`、`inventory`、`delivery_rule`、`compliance_document`、`content_asset`、`approved_fact`、`forbidden_expression`。
- `TruthPayloadRef` 只保存 `subject_ref`、字段名集合和 SHA-256 reference，不保存商品、SKU、金额、币种、数量、日期、证件或表达式正文。
- `TruthVersion` 复用 P02-01 的 compound scope、source、data version 与 metadata lineage，增加 `parent_version_id`、`changed_fields`、`diff_hash`、effective window 和 approval evidence。
- `ApprovalEvidence` 将 reviewer actor、decision、evidence、policy、approved time 明确绑定到同 scope 的 source 与 data version；缺任一 lineage 时 approved contract 构造失败。
- `InMemoryTruthRepository` 只提供 append、scoped history/read；没有 update/delete API，拒绝重复 version、重复 record、分叉历史、缺 parent、跨 scope 和非法状态迁移。

## 2. 状态机与 current-truth 规则

```text
fixture/mock ──X──> approved

staging -> approved | blocked | conflict | superseded
approved -> expired | blocked | conflict | superseded
expired/blocked/superseded -> staging
conflict -> staging | approved(with new approval evidence)
```

- `fixture`、`mock` 与 `staging`（candidate）永不直接作为 current truth。
- `expired`、`blocked`、`conflict` 与 `superseded` head 永不作为 current truth。
- 只有唯一 chain head 同时满足 `approved`、source/version/approval lineage 完整、effective window fresh、scope 精确匹配时，read model 才返回。
- conflict 不使用 timestamp、confidence 或 version number 做 latest-wins；冲突期间返回空，只有新的 approved successor 和新 approval evidence 才恢复 current read。
- effective window 未开始或已到期均返回空；无默认日期、币种、金额、库存或资质有效期。

## 3. PostgreSQL schema 防护

`0002_truth_entities_versions_and_states.sql` 增加：

- 九类 `truth_entity_kind` enum 和 `truth_versions` append-only table。
- compound scope/source/data-version/parent lineage foreign keys、scope+subject+version uniqueness、single-child chain 和 external execution 永久 false。
- approval fields 原子完整性、approved evidence/effective window/parent 必填、fixture/mock 与 synthetic marker 一致性。
- insert trigger 对 parent scope、连续 version number 与状态图做二次校验。
- update/delete trigger 阻止覆盖或删除历史；更正只能 append 新 version。
- `current_approved_truth` view 只返回 fresh、approved、evidence-complete、无 successor 的 chain head；synthetic fixture probe 验证结果为 0 行。

migration 只创建 schema、function、trigger 与 view，不插入真实 tenant/project/business line 或任何业务值。P02-01 的 fixture/mock 不可提升与 compound lineage 防护没有放宽。

## 4. 验证证据

- truth/scope contract suite：22 项通过，覆盖九类 entity、candidate→approved、approval lineage、effective window、fixture/candidate/expired/conflict/superseded current-read rejection、explicit conflict resolution、cross scope、immutable history、invalid input/state/diff。
- PostgreSQL migration：`0001` + `0002` 连续 replay 两次；11 类负向约束通过，包括 P02-01 五类基线以及 P02-02 缺 approval evidence、重复 version、跨业务线 parent、fixture 非法迁移、UPDATE 和 DELETE 拒绝。
- `make regression`、P00 default/all-files scan、mechanism validation、diff check 与 Docker cleanup 以本轮最终执行输出为准；本报告不把生成时状态预写成 Git/远端完成。

## 5. 自我审查与回退

- 自审发现并修正 Python parent chain 与 SQL parent FK 初版指向不同 ID 的问题；两层现统一以 `data_version_id` 作为 `parent_version_id`。
- 自审将状态迁移和 append-only 从 application-only guard 下沉到 PostgreSQL trigger，避免将数据库直写路径留为隐式绕过。
- 回退为删除 P02-02 的独立 `0002` schema contract、truth module 文件和对应 tests；已应用数据库不提供破坏性 down migration，遵循 forward-fix / expand-contract。

## 6. 状态边界与 P02-03 依赖

- **CONFIRMED（本地工程）**：value-free truth contracts、state/read guards、migration replay 与负向约束已验证。
- **UNKNOWN / BLOCKED（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界和外部授权没有新增证据，所有外部业务 flags 继续 false。
- **未实现**：RLS、encryption、retention/legal-region、production repository/driver、真实 source/approval actor authentication、approval RBAC、ingestion parser、UI、CRM/support/video adapter 与 external network。
- **P02-03 前置**：必须先由控制器审查并把 P02-02 集成到 `main`；P02-03 再以 adversarial tests 扩大 cross-tenant/project/business-line、unscoped query、fixture injection 和 non-current truth consumer isolation，不能把本轮单进程 repository probe 写成生产隔离完成。
