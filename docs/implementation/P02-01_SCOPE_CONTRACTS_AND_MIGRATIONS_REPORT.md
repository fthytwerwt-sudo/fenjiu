# P02-01｜Scope 合同与 migration 基线报告

> **状态：remote_readback_verified_clean_worktree_required**
>
> **执行日期：2026-08-06**
>
> **基线提交：** `8dc4807b4a342941e746e4215141ab420c21cae4`
>
> **远端代码提交：** `b08722a703f37a0cfcce0c928fec8c01c4596357`
>
> **范围边界：** 仅实现本地 schema contract、synthetic fixture metadata 与数据库约束；不创建真实 tenant、SKU、价格、库存，不连接外部数据库，不改变业务状态。

## 1. 实现结论

- `core/contracts/` 已提供 stdlib dataclass/enum 合同：`TenantContract`、`ProjectContract`、`BusinessLineContract`、`ScopeRef`、`SourceRef`、`DataVersionRef`、`BaseMetadata`、`DataState` 与 `Sensitivity`。
- scope/source/version/state/sensitivity、timezone-aware timestamps、created_by 与 correlation ID 均显式校验；缺失或类型错误以稳定 error code fail closed。
- synthetic contract 只允许 `fixture/mock`，且 `external_execution_allowed` 永久为 false；synthetic → approved/real/external action 被拒绝。
- `assert_same_scope` 与 `assert_metadata_lineage` 拒绝跨 tenant/project/business line 及 source/version lineage 不一致。
- 未新增 Pydantic、ORM、PostgreSQL Python driver、package 或 lockfile。任务卡中的 Pydantic 建议按本轮 P0 约束采用 stdlib fallback；数据库约束未被绕过。

## 2. Migration graph

```text
0001_scope_contracts.sql
  -> schema_migrations
  -> data_state + sensitivity enums
  -> tenants
  -> projects --compound FK--> tenants
  -> business_lines --compound FK--> projects
  -> source_refs --compound FK--> business_lines
  -> data_versions --compound FK--> source_refs
  -> entity_metadata --compound FK--> source_refs + data_versions
```

`0001` 只含 schema metadata/DDL，不含 tenant、project、business line、SKU、价格、库存或任何真实业务行。重复执行使用 `IF NOT EXISTS`、duplicate-object guard 与 migration version upsert，已在 disposable database 连续重放两次。

## 3. 数据库约束证明

PostgreSQL 约束强制：

1. 所有 scoped metadata 的 tenant/project/business_line/source/version/state/sensitivity 均 `NOT NULL`。
2. compound foreign keys 把 project、business line、source、version 与 entity metadata 锁定在同一 scope 和 synthetic marker。
3. `fixture/mock` 与 `is_synthetic=true` 双向一致；synthetic row 不能写成 `approved`。
4. `external_execution_allowed=true` 在所有表层均由 CHECK constraint 拒绝。
5. source/version lineage 必须同时匹配 scope、source ID、version ID 与 synthetic marker。

在 disposable local PostgreSQL 中已验证以下 5 类负例全部失败：缺 mandatory metadata、跨 business line 引用 source、synthetic fixture 升级 approved、fixture 开启 external execution、source/version 不匹配。

## 4. Fixture 范围

仓库仅保留 `fixtures/synthetic_metadata.json`：

- `is_synthetic=true`
- `data_state=fixture`
- `external_execution_allowed=false`
- `business_external_ready=false`
- 仅使用固定 synthetic UUID 与内部 metadata，不包含真实业务线 slug、SKU、价格、库存、联系人、凭据或文件。

`make load-fixtures` 继续保持 P01 safe no-op；本任务没有增加可把 fixture 装载到真实或外部目标的入口。数据库负例只在临时测试库插入 synthetic metadata，脚本退出时删除该测试库。

## 5. 本地入口与验证

- `make migrate` 只枚举仓库内编号 SQL 文件，并通过固定 Compose `postgres` service 的容器内 loopback 执行 `psql -X -v ON_ERROR_STOP=1`。
- 入口不读取 `.env`、不接受 DSN/URL/host 参数、不连接生产或外部数据库、不插入业务资料。
- `make migration-test` 先强制验证 Docker command、Compose plugin 与 daemon；任一不可用即明确非零失败，不跳过数据库测试。通过后只启动当前 worktree 隔离 project 的 PostgreSQL，创建 disposable test database，执行两次 replay、schema/version assertions 与 5 类 negative constraints，退出时强制 drop test database，并清理本任务 Compose containers、network 与 volumes。
- `make regression` 强制调用 `make migration-test`，因此默认回归同时覆盖 PostgreSQL migration replay/negative constraints、原有 architecture/regression/local-runtime/control-plane 套件与 scope contract tests；数据库验证不再是独立的可选步骤。
- Docker health、P01 flags/readiness/log semantics 保持不变；`make load-fixtures` 仍报告 `writes_data=false` 与 `loads_fixtures=false`。

## 6. Rollback 与 deferred

- 本地 probe rollback：删除 disposable test database；migration regression trap 使用 `compose down -v --remove-orphans` 清理当前 worktree 隔离的本任务容器、网络和 disposable volumes。
- 已应用 migration 的结构变更遵循 forward-fix / expand-contract；未增加破坏性 down migration。
- PostgreSQL RLS、advanced encryption、retention length、legal region、真实 scope、database adapter/driver 与生产连接全部 `DEFER`。
- 本任务不解除 SKU、价格、库存、资质、账号、收款、履约或 TikTok 酒类业务闸门；external send/publish/quote/payment/order/refund 及 business external readiness 继续为 false。
