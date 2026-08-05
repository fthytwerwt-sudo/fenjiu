# 开源组件核验与选型矩阵

> **核验日期：2026-08-06。** 状态词表示本计划建议，不表示已经安装、批准或已在本仓库使用。任何实际引入前必须再核验目标版本的 LICENSE、SBOM、安全公告、部署要求和平台/API 条款。

## 1. 结论先行

| 层 | 建议 | 状态 | 原因 |
|---|---|---|---|
| 核心真值/事务 | PostgreSQL | **RECOMMENDED** | 开放许可、成熟、可承载版本/审计/约束；仅它保存业务真值。 |
| 后台队列 | RQ + Valkey-compatible broker（使用 JSON serializer） | **RECOMMENDED** | Python 集成简单、任务/重试/worker 足够第一版；broker 被 port 隔离。 |
| AI 编排 | LangGraph（仅 workflow adapter） | **RECOMMENDED AFTER P1** | 可提供 durable execution、checkpoint、human interrupt/resume；不得拥有事实或审批权。 |
| 公开网页采集 | Crawl4AI（仅 crawl adapter） | **ALTERNATIVE / NEEDS_VERIFY** | Python、异步/结构化提取、可自托管；真实使用前逐域核验 robots/条款/频率、版本安全与合规。 |
| CRM 工作台 | 自建极简 CRM domain/admin；Twenty 仅保留后期 adapter/UI 候选 | **TWENTY: NOT NOW** | Twenty 是大型 TypeScript/NestJS/React 平台，主要 AGPLv3 且有 enterprise/commercial 部分；现在会造成双真值和运维耦合。 |
| 客服工作台 | 自建会话/审批 domain；Chatwoot 仅保留后期 inbox adapter/UI 候选 | **CHATWOOT: NOT NOW** | MIT 且功能成熟，但引入完整 Rails/Ruby 运维栈与外部会话模型过早；待真实咨询和渠道授权出现后再评估。 |
| Redis 官方发行版 | 不作为新的默认绑定 | **NOT NOW** | Redis 8+ 是 RSALv2/SSPLv1/AGPLv3 三选一，需针对部署/分发方式单独法律核验；不应把“Redis”写成默认无条件许可。 |

## 2. 核验方法与边界

本矩阵按官方文档/官方仓库检查：许可证、可见维护活跃度、自托管、API/webhook/导出、Python/FastAPI/PostgreSQL适配、数据迁移和替换成本。可见的 issues/PR/commits/release 只能说明社区活动信号，**不构成安全、合规或长期维护保证**。所有 “API/Webhook” 能力即使存在，也不构成接入生产账号的授权。

公共规则：

- 第三方只能位于 `adapters/` 或 `workflows/`；主键、事实版本、审批与审计始终在本项目 PostgreSQL domain。
- 每个 adapter 需有 port、capability register、fake、contract tests、导出路径、feature flag 和退出 runbook。
- 不复制或提交第三方源码/镜像；锁定版本、生成 SBOM，运行时镜像/依赖的 license 再由实施任务复核。

### 2026-08-06 维护信号快照

这些只是本次审计时官方仓库的可见信号，不能替代在实际接入日再次核验：LangGraph 官方仓库显示约 7,000 commits、426 issues、235 PR；Crawl4AI 显示约 1,589 commits、107 PR，并在 README 标注 v0.9.2 维护补丁；Twenty 显示约 14,184 commits、56 PR；Chatwoot、RQ 与 Valkey 均有官方 repo、release/安全或贡献入口。RQ 官方 release 页显示 v2.9 发布于 2026-05-19。该快照支持“候选仍在维护”，不支持“任何版本都安全/稳定”的结论。

## 3. 逐项矩阵

| 组件 | 功能适配 / 维护与许可证（核验） | 自托管 / Python 与数据接口 | 锁定与替换成本 | 结论与进入条件 |
|---|---|---|---|---|
| [PostgreSQL](https://www.postgresql.org/) | 适合作为事务、约束、JSON、审计与版本库；官方 PostgreSQL License 为宽松许可，且官方声明无计划变更。 | 标准容器/托管均可；Python/FastAPI 成熟；SQL/CSV/JSON 导出可由本项目控制。 | **低至中**：数据库 schema 是核心资产，但可迁移；避免 vendor-only SQL extension 作为第一版前提。 | **RECOMMENDED。** Phase 0 只建 local compose，Phase 1 才建 migration。 |
| [RQ](https://github.com/rq/rq) | Python background queue；官方仓库展示 Redis/Valkey 支持、重试/调度/unique job；BSD-2-Clause 许可。官方安全说明提示默认 `pickle` 不安全。 | 轻量 worker；可与 FastAPI 分进程部署；使用 JSON serializer、受信 broker、job payload schema。 | **低**：以 `QueuePort` 封装；job domain state仍在 Postgres，不以 RQ job 为事实。 | **RECOMMENDED。** Phase 0/1 采用 fake queue + local RQ；禁止 pickle、禁止以队列消息存 PII/秘密。 |
| [Valkey](https://valkey.io/) | Redis-compatible key-value server；官方 repo 为 BSD-3-Clause、LF Projects 社区；避免 Redis 许可证变动带来的默认判断。 | local compose 易部署；RQ 文档明确支持 Valkey >=7.2；不承担永久业务记录。 | **低**：由 broker/cache port 隔离；可换 managed Redis/RabbitMQ 等。 | **RECOMMENDED。** 只作 queue/cache；PostgreSQL 仍为 source of truth。 |
| [Redis](https://github.com/redis/redis) | 官方 repo 当前说明 8.0+ 三选一 RSALv2/SSPLv1/AGPLv3；活跃不等于许可简单。 | 技术兼容广；但企业使用/托管/分发路径须单独确认对应许可证。 | **中**：协议兼容但运行/法律选择影响大。 | **NOT NOW。** 若已有受控 Redis，由法律/业务选择许可证后才建 adapter。 |
| [LangGraph](https://github.com/langchain-ai/langgraph) | MIT；官方文档提供 durable execution、checkpoint、human-in-the-loop interrupt/resume；官方 repo 可见持续开发活动。 | Python 可单独使用，不强制 LangChain；checkpoint 可接持久存储。 | **中**：编排 DSL/状态模型可能渗透。 | **RECOMMENDED AFTER P1。** 先实现 application command + approval/audit；图只调用 port。需测试 interrupt 重放的幂等副作用。 |
| [Crawl4AI](https://github.com/unclecode/crawl4ai) | Apache-2.0；官方 repo 提供 Python、async crawling、Markdown/结构化提取、Docker 与安全更新，当前可见维护活动。 | Python/async 适配好；可本地/Docker 运行；可存 snapshot/hash 后做结构化提取。 | **中**：浏览器/依赖重、站点策略和安全面复杂。 | **ALTERNATIVE / NEEDS_VERIFY。** Phase 2 先 fake snapshot；逐域人工批准 robots/条款/频率后，才选择性接入。不能越过登录、限制或将模型结果当事实。 |
| [Twenty](https://github.com/twentyhq/twenty) | 自托管 CRM，官方文档说明 Docker Compose；repo 采用以 AGPLv3 为主、部分 commercial enterprise/部分 MIT package 的混合许可，且提供 REST/GraphQL/webhooks 的 Application Interface exception。 | 技术栈为 TypeScript/Nx/NestJS/React/PostgreSQL/Redis，和 Python 模块化单体是另一运行平台。 | **高**：对象/工作流/权限/数据模型会与本系统 CRM 重叠；迁移需持续同步/导出核验。 | **NOT NOW。** 后期若需要成熟销售界面，作为 `crm_adapter` 或 read-only/one-way UX 候选；先法律审查 AGPL/enterprise 边界、API/webhook、导出、tenant mapping。 |
| [Chatwoot](https://github.com/chatwoot/chatwoot) | MIT；官方 repo 提供 omni-channel inbox、报告和部署文档，当前可见维护活动。 | 自托管但引入 Rails/Ruby/Redis/PostgreSQL 与消息渠道配置；其 API/webhook/导出能力需按目标版本/渠道再测试。 | **高**：会话、客户、inbox 与自动化会和本项目客服 domain 重叠；PII/保留策略需双向治理。 | **NOT NOW。** 真实咨询量、渠道授权与人工工作台需求出现后，作为 `support_inbox_adapter` 评估；先做 one-way import、webhook replay、DNC/PII/导出与关闭演练。 |

## 4. 推荐栈（第一版）

```text
Python / FastAPI API + Python worker
PostgreSQL (truth, versions, approvals, audits, CRM state)
RQ + Valkey (background execution only; JSON jobs)
Pydantic / JSON Schema (contracts)
Docker Compose (local development only)
LangGraph optional workflow adapter after Phase 1
Crawl4AI optional crawl adapter after source-policy review
```

此栈不要求把 RQ/Valkey/LangGraph/Crawl4AI 同时装入 Phase 0；先定义 ports/fakes，再在与功能直接相关的 Phase 单独引入。FastAPI、ORM/migration、测试库的具体版本在 Phase 0 任务中根据当时官方文档锁定，不在规划阶段伪造已选依赖。

## 5. 适配器合同与退出方案

| Adapter | 必要 port | 必须保存于本项目的内容 | 替换/退出验证 |
|---|---|---|---|
| `workflow` | `RunWorkflow`, `PauseForApproval`, `ResumeWorkflow` | approval request、状态、audit、idempotency key | 用一个内置简易 runner 跑同一 fixture，得到同样批准/审计结果。 |
| `crawl` | `FetchSnapshot`, `ExtractPublicFields` | source policy、snapshot hash、URL、证据定位、lead candidate | 用 fixture HTML + 第二 crawler fake 重跑，lead contract 不变。 |
| `queue` | `Enqueue`, `Cancel`, `Retry`, `GetStatus` | job intent、attempt、idempotency、business state、audit | fake queue + 切换 broker；未完成 job 安全重建，避免读 vendor job state。 |
| `crm` | `ExportCRM`, `ImportInteraction`, `MapExternalID` | organization/contact/opportunity/interaction/DNC/stage | 导出 scoped JSON/CSV，停用 external CRM 后核心 CRM 仍可读。 |
| `support` | `ReceiveMessage`, `DraftReply`, `SendApproved`, `Handoff` | conversation/message refs、policy、fact versions、handoff/audit | fake adapter/webhook replay，关闭 adapter 时系统保持 manual-only。 |
| `video` | `Submit`, `Poll`, `FetchArtifact`, `RunQC` | content/video task、manifest ref、QC、approval/audit | fake provider + existing legacy port 对相同 fixture 的 output contract。 |

## 6. 接入前核验清单

每一个真实组件引入任务必须在合并前输出：

1. 官方版本、commit/tag、LICENSE 文件 hash、依赖 SBOM 和 security advisory 结果；
2. 自托管 compose/Helm 或官方安装路径的最小运行证明；
3. API/webhook auth、重放、速率、导出/删除、backfill/rollback 和 tenant scope 的 integration test；
4. 用 fake adapter 跑同一 contract suite 的结果；
5. data export 结果、退出步骤、关闭 feature flag 后的行为；
6. Crawl/客服/CRM 涉及真实资料时的 source policy、合法性/平台条款和用户授权记录；
7. Twenty/Redis 等许可有条件或版本变化的项目，取得适用商业/法律确认，否则保持 `NEEDS_VERIFY` 或 `NOT NOW`。

## 7. 官方核验入口

- LangGraph：[repo / MIT license](https://github.com/langchain-ai/langgraph)；[human-in-the-loop interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)；[persistence](https://docs.langchain.com/oss/python/langgraph/persistence)。
- Crawl4AI：[repo / Apache-2.0](https://github.com/unclecode/crawl4ai)；[官方文档](https://docs.crawl4ai.com/)；[hosted 服务与开源库边界](https://docs.crawl4ai.com/terms/)。
- Twenty：[repo](https://github.com/twentyhq/twenty)；[LICENSE](https://raw.githubusercontent.com/twentyhq/twenty/main/LICENSE)；[self-hosting docs](https://docs.twenty.com/installation/self-hosting/docker-compose)。
- Chatwoot：[repo / MIT](https://github.com/chatwoot/chatwoot)；[self-hosting documentation](https://www.chatwoot.com/docs/self-hosted)；[API documentation](https://developers.chatwoot.com/api-reference/overview)。
- PostgreSQL：[license](https://www.postgresql.org/about/licence/)；[official documentation](https://www.postgresql.org/docs/)。
- RQ：[repo](https://github.com/rq/rq)；[license](https://raw.githubusercontent.com/rq/rq/master/LICENSE)；[security and serializers note](https://python-rq.org/docs/)。
- Valkey：[repo / BSD-3-Clause](https://github.com/valkey-io/valkey)；[documentation](https://valkey.io/)。
- Redis：[current LICENSE](https://github.com/redis/redis/blob/unstable/LICENSE.txt)；版本/许可选择必须另核验。
