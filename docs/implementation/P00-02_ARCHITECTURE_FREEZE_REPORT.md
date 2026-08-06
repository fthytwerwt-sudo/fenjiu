# P00-02｜架构冻结与 ADR 一致性报告

> **状态：completed_on_task_branch**
> **执行日期：2026-08-06**
> **任务卡：** `docs/implementation/codex_tasks/phase_00/P00-02_freeze_architecture_and_adr.md`
> **基线提交：** `fe76eb422b171b1f25170783e10d4a895e6c3e8f`
> **范围边界：** 本报告只冻结规划、ADR、port 和 Phase 1 文件级入口；不创建运行时代码、migration、fixtures、tests、依赖锁或外部连接。

## 1. 结论

| 项目 | 状态 | 证据与边界 |
|---|---|---|
| Phase 1 目录 ownership | 已冻结 | `apps/`、`core/`、`modules/`、`adapters/`、`workflows/`、`fixtures/`、`migrations/`、`tests/` 仅为未来 skeleton 入口；本任务未创建目录。 |
| 依赖方向 | 已冻结 | `apps/workflows -> core/application -> core/domain/modules/contracts`；`adapters -> ports/contracts`；domain/modules 禁止导入 provider SDK。 |
| optional ports | 已冻结为 fake-first | workflow、crawl、CRM、support、video 只保留 port/fake 和 exit 规则；未选定未核验 provider 或版本。 |
| legacy 视频/研究脚本 | `DEFER/BLOCKED` | P00-01 未在当前受控 Git 清单中定位 HappyHorse / DashScope / FFmpeg legacy 实体；规划引用不得写成现成可用。 |
| 外部业务动作 | `BLOCKED` | `external_execution_allowed=false`、`public_publish=false`、`real_quote=false`、`payment=false`、`order_create=false`、`business_external_ready=false` 继续默认拒绝。 |
| 业务范围 | 未改变 | 汾酒尼泊尔仍处 TikTok 销售准备和供应链资料收集阶段；本任务不更新 `docs/project/`。 |

## 2. Frozen architecture map

```text
apps/api, apps/admin, apps/worker
  -> core/application
    -> core/domain + modules/*
    -> core/contracts
adapters/*
  -> core/application ports + core/contracts
workflows
  -> core/application ports
fixtures
  -> exported contracts only; synthetic-only
```

禁止反向依赖：

- `core/domain` 与 `modules` 不导入 `adapters`、`apps`、`workflows`、外部 SDK 或环境变量读取。
- provider adapter 不写 `approved_fact`、价格、库存、订单、发送、发布、退款或履约状态。
- fixture、mock、draft 和 AI output 不升级为真实业务事实或 external action。

## 3. Phase 1 文件级入口

| 路径 | Phase 1 只允许 | Phase 1 不允许 |
|---|---|---|
| `apps/api/` | app factory、health、scope/correlation 占位 | 真实 auth/webhook/external write。 |
| `apps/worker/` | fake queue consumer、idempotency shell | 真实 broker、模型、采集、发布、支付。 |
| `apps/admin/` | approval/audit shell | 真实账号管理或 fixture approval。 |
| `core/domain/` | policy、state、domain event | provider SDK、DB session、HTTP client。 |
| `core/application/` | use case、command/query、port interface | 绕过 approval 或直接读 adapter 私有状态。 |
| `core/contracts/` | scope/error/event/schema version | SKU、价格、库存、客户或账号数据。 |
| `modules/*/` | README/docstring、空 service/repository contract | 跨模块私表访问或真实资料导入。 |
| `adapters/*/` | fake/in-memory adapter、capability registry | 未核验 SDK、token、真实 API 调用。 |
| `workflows/` | thin runner interface | workflow DSL 持有事实或审批。 |
| `fixtures/` | `is_synthetic=true` metadata | 真实资料复制或缺 synthetic 标记。 |
| `migrations/` | 空 migration 入口和命名规则 | 真实数据、生产连接串。 |
| `tests/` | architecture/import/flag negative tests | 网络、密钥或真实业务数据依赖。 |

## 4. Ports and exit rules

| Port | Default | Exit rule |
|---|---|---|
| `WorkflowPort` | fake/in-process | LangGraph 或等价组件必须重验版本、license、checkpoint/retry 语义，并可关闭回到简易 runner。 |
| `CrawlPort` | fake/manual import | 未完成 source policy、robots/terms/rate limit 审查时保持 blocked。 |
| `CrmPort` | internal domain + fake export | 第三方 CRM 关闭后 PostgreSQL scoped truth 仍可读；DNC/scope mismatch 时 manual-only。 |
| `SupportPort` | manual-only fake | 无 approved fact、高风险或账号授权不明时 handoff，不发送。 |
| `VideoPort` | fake provider | legacy/provider 未定位或未验证 hash/CLI/dry-safe 时不得调用真实 HappyHorse / DashScope / FFmpeg。 |

## 5. ADR changes

- ADR 状态从 `Proposed / RECOMMENDED` 冻结为 `Accepted for Phase 1 architecture freeze / runtime not implemented`。
- Decision 6 从“现有 HappyHorse/FFmpeg 脚本只包装”修正为“规划引用的 legacy 仅在实体定位和 hash/CLI/dry-safe 通过后包装；未定位前 `DEFER/BLOCKED`”。
- 新增 Phase 1 frozen follow-up decisions，明确目录 ownership、依赖方向、optional provider、legacy 和 external action 默认拒绝。

## 6. 未决项与后续影响

| Item | 状态 | 后续任务 |
|---|---|---|
| HappyHorse / DashScope / FFmpeg 实体定位 | `BLOCKED` | P00-03 或 P07-02 在授权位置回读 SHA-256、CLI、输入输出、dry-safe 行为。 |
| 具体开源组件版本 | `NEEDS_VERIFY` | 各 Phase 接入任务独立重验官方文档、license、SBOM、security advisory。 |
| 真实供应链资料 | `BLOCKED` | Phase 8 仅在资料到达、私有路径受控、hash/MIME/审批齐备后进入。 |
| 外部上线 | `BLOCKED` | Phase 9 书面证据、平台/合规、账号、收款履约和用户授权同时满足前保持关闭。 |

## 7. 验证计划

本任务可用以下文档级验证证明完成：

```text
rg -n 'HappyHorse|DashScope|FFmpeg|legacy' docs/implementation
rg -n 'apps/|core/|modules/|adapters/' docs/implementation
git diff --check
```

这些验证只证明文档和 ADR 一致性；不证明 runtime、数据库、依赖、业务资料、合规、上线、销售或履约成立。
