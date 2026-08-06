# 开源组件核验、选择与退出策略

> **核验日期：2026-08-06；结论表示计划建议，非已安装清单，P00-02 不冻结任何未在当前任务中重验的依赖版本。** 目标版本接入前必须重验 LICENSE、官方安全公告、部署文档、SBOM 与目标账号/API 条款。

## 1. 结论矩阵

| 组件 | 状态 | 当前依据与适配 | 自托管/锁定/退出策略 |
|---|---|---|---|
| PostgreSQL | `RECOMMENDED` | 事务、约束、JSON、version、audit 与导出都在成熟 Python/FastAPI 路径中；采用 [PostgreSQL License](https://www.postgresql.org/about/licence/)。 | 真值唯一存此处；使用可迁移 schema、SQL/CSV/JSON export，避免 vendor-only extension。 |
| Valkey + Python queue port | `RECOMMENDED` | Redis-compatible、BSD-3-Clause；只放短期队列/缓存，PostgreSQL 仍是事实与 job 意图库。 | 实施时可选择 RQ（JSON serializer）或等价 worker；用 `QueuePort`、fake 和 outbox，broker 可替换。 |
| Redis 官方发行版 | `DEFER` | 官方当前许可选择需要按部署/分发路径独立审核；不能把“Redis”写成无条件低风险默认。 | 只有法律/商业确认后连接 Redis adapter；在此之前 Valkey 或无 broker fake。 |
| LangGraph | `RECOMMENDED` | [MIT](https://github.com/langchain-ai/langgraph/blob/main/LICENSE)；官方文档支持 checkpoint、interrupt/resume 与持久化。只在 Phase 3 的审批/真值合同已通过后才做 adapter probe。 | 只在 `workflows/` 调 application ports；用内置简易 runner 跑同一 contract，防止 DSL 锁定。 |
| Crawl4AI | `NEEDS_VERIFY` | Python/async、Docker/self-host；既有规划材料提到 0.9 安全改动，但 P00-02 未联网重验具体版本，因此不得锁定版本。其 [LICENSE](https://github.com/unclecode/crawl4ai/blob/main/LICENSE) 以 Apache-2.0 为基础但另列署名要求，目标使用方式须做许可证/展示义务复核。 | 每域先批 source policy、robots/条款/频率；每源 adapter；保留 HTML/snapshot contract 和 CSV 人工导入 fallback。 |
| Twenty | `DEFER` | 具自托管 Docker Compose、REST/GraphQL/webhook 能力和活跃版本；但其 [LICENSE](https://github.com/twentyhq/twenty/blob/main/LICENSE) 以 AGPLv3 为主，包含 Application Exception、MIT 子包及明确商业文件，且 TypeScript/NestJS/React + PostgreSQL/Redis 会引入第二套运行平台与双真值风险。 | 第一版自建 CRM domain/admin；若后期需要 UI，只做 scoped `crm_adapter`、one-way import/export，先由法律/商业审查确认目标版本、例外和 enterprise 文件。 |
| Chatwoot | `DEFER` | [MIT](https://github.com/chatwoot/chatwoot/blob/develop/LICENSE)，官方提供自托管、多渠道 inbox、API/webhook；适合未来人工工作台。 | 先自建 conversation/policy/audit；日后以 one-way inbox adapter 接入，必须验证 webhook replay、PII/DNC、导出与关闭。 |
| RQ（可选 QueuePort 实现） | `RECOMMENDED` | [BSD-2-Clause 风格许可](https://github.com/rq/rq/blob/master/LICENSE)，支持 Redis/Valkey；官方安全说明指出默认 `pickle` 不安全，因此必须显式使用 JSON serializer 并只连接受信 broker。 | QueuePort、outbox、fake 与 PostgreSQL job/audit 仍为主；RQ 只调度，不保存真值，换 worker 时复跑同一 contract suite。 |

## 2. 当前官方证据与限制

- LangGraph 官方仓库为 MIT，近期仍有 release；其 durable execution 适合**已存在的**审批状态恢复，但它不得持有事实或代替 action policy。`interrupt` 恢复会重跑节点，所以副作用必须在批准后执行或具备幂等键。[仓库](https://github.com/langchain-ai/langgraph)｜[持久化/队列说明](https://docs.langchain.com/oss/python/langgraph/)｜[interrupt 约束](https://docs.langchain.com/oss/python/langgraph/interrupts)
- Crawl4AI 的具体版本、self-host 安全默认、token/网络配置和附加署名条款必须在接入任务中重新回读官方文档；P00-02 只保留 `NEEDS_VERIFY` 和 crawl port，不把旧材料中的版本写成已选型。[self-hosting](https://docs.crawl4ai.com/core/self-hosting/)｜[许可证](https://github.com/unclecode/crawl4ai/blob/main/LICENSE)
- Twenty 官方 repo 说明它可用 Docker Compose 自托管，且其 stack 已含 PostgreSQL/Redis/BullMQ；其主许可证/例外/商业文件组合需要逐版本审查。这正是早期引入会造成双运行时、双权限模型和非轻量许可评估的原因。[repo](https://github.com/twentyhq/twenty)｜[许可证](https://github.com/twentyhq/twenty/blob/main/LICENSE)
- Chatwoot 是 MIT 的自托管 omni-channel support 平台；功能成熟不自动解决汾酒的消息权限、酒类风险分类或 approved-fact 约束。[repo](https://github.com/chatwoot/chatwoot)｜[API](https://developers.chatwoot.com/api-reference/overview)
- Valkey 为 BSD-3-Clause，适合作为可替换 broker/cache；Redis 8 起为 RSALv2 / SSPLv1 / AGPLv3 三选一，故本计划不把 Redis 官方发行版写为无条件默认。RQ 支持 Redis/Valkey，但默认 `pickle` 必须在实施时关闭。[Valkey LICENSE](https://github.com/valkey-io/valkey/blob/unstable/COPYING)｜[Redis 许可证](https://redis.io/legal/licenses/)｜[RQ 安全说明](https://github.com/rq/rq)

维护活跃度仅通过本次官方 release/repository 可见信号评估，属于 `部分成立`，不是安全、合规或长期可用性承诺。

## 3. adapter-first 退出合同

每个外部组件进入仓库前必须同时具备：

1. port interface、capability registry、feature flag、fake adapter 和 contract fixtures；
2. 外部 ID 仅为映射字段，不能成为本系统主键或唯一事实来源；
3. scoped JSON/CSV export、导入、webhook replay、idempotency、断网失败与关闭 adapter 测试；
4. 服务关闭后仍可读取 PostgreSQL 中的 truth、audit、CRM 或 conversation 元数据；
5. version/tag、LICENSE hash、SBOM、官方 advisory 检查和退出 runbook 记录在实施任务回报中。

| Adapter | Port | 禁止由第三方保存的核心内容 | 退出验证 |
|---|---|---|---|
| workflow | `Run/Pause/ResumeWorkflow` | approval、audit、idempotency、业务状态 | 简易 runner 与 LangGraph 得出同一 state/audit。 |
| crawl | `FetchSnapshot/ExtractPublicFields` | source policy、snapshot hash、lead 审核结论 | fixture HTML 或 CSV fallback 产生同一 lead contract。 |
| CRM | `Export/ImportInteraction/MapExternalID` | organization/contact/opportunity/DNC/stage 真值 | scoped export 后禁用 adapter 仍可读。 |
| support | `Receive/Draft/SendApproved/Handoff` | conversation policy、事实版本、handoff 与审计 | replay fake webhook；关 adapter 自动回到 manual-only。 |
| video | `Submit/Poll/Fetch/RunQC` | content/video task、fact lock、QC、approval | fake provider 与 legacy wrapper 的 manifest contract 一致。 |

## 4. 引入门槛

具体组件仅在对应 Phase 的任务里 probe；没有通过以下事项则标记 `NEEDS_VERIFY`：官方安装最小运行证明、网络/认证边界、版本/许可证复核、数据 export、可关闭 flag、fake contract、无真实业务数据/外发的测试。Crawl、CRM、客服和视频的任何真实账号接入另需用户授权及相应平台/合规证据。
