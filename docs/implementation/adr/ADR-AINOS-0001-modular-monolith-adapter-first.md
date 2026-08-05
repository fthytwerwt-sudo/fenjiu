# ADR-AINOS-0001：模块化单体、adapter-first、fixture-first 与人工闸门

- **日期：** 2026-08-06
- **状态：** Proposed / RECOMMENDED
- **确认边界：** 用户已确认“先建可插拔基础代码、用严格标记 fixture/mock 跑模拟闭环、真实资料到达后以映射与回归为主”的方向；本 ADR 的具体技术落地仍待后续实施审查，不是已部署决定。

## Context

当前仓库已有项目治理、DOCX/XLSX 生成、视频脚本、研究数据与人工转录的公开名单工具，但缺少运行时数据库、版本化真值、导入审查、CRM/客服链路、工作队列和审批后台。供应链真实资料与生产授权尚未到位；将所有模块或第三方系统直接粘合会放大未来替换成本和事实污染风险。

## Decision

第一版建议采用：

1. 一个模块化 Python 单体（API + worker + 极简 admin），一个 PostgreSQL 核心事实库；
2. `tenant/project/business_line` 强制隔离，汾酒与海鲜只共享代码/contract，不共享事实；
3. 原始资料到 `raw/extraction` 层，只有有来源、版本、有效期与人工批准的 `approved_fact` 可被业务模块读取；
4. 外部模型、工作流、采集器、CRM、客服、视频和未来支付/库存全部经 adapter port 接入；
5. 默认 synthetic `fixture` 运行；任何外部副作用、正式报价、发送、发布、退款、支付、订单、库存写回均由 policy + human approval 失败关闭；
6. 现有 HappyHorse/FFmpeg 脚本只包装、回归、服务化，不重写。

## Drivers

- 真实供应链资料尚未到位，但基础结构可先完成。
- 业务事实、合规、价格/库存、账号与外发必须可审计且可停止。
- 现有视频工具链已有价值，不能因新平台而丢失或被大改。
- 未来可能更换开源组件和供应链数据格式，需要把锁定成本限制在 adapter。
- 当前团队需要可小步下发、可回滚、可独立验收的 Codex 工作单。

## Alternatives considered

| 方案 | 结论 | 原因 |
|---|---|---|
| 直接采用多个 SaaS/开源平台作为系统核心 | Rejected | 业务真值、审批和隔离将分散；早期集成/维护成本高，退出困难。 |
| 一次建设微服务/事件平台 | Rejected for v1 | 当前没有吞吐/团队/独立部署证据，复杂度会掩盖业务与合规闸门。 |
| 先等所有真实资料齐全再建设 | Rejected | 能做的结构、contract、fixture、审批和回归会被无意义延后；但生产接入仍 BLOCKED。 |
| 为每条业务线建立完全独立系统 | Rejected for v1 | 代码、测试和机制重复；安全隔离应由强 scope 和权限实现。 |
| 让 LLM/RAG 直接查询上传文件和外部工具 | Rejected | 无版本/来源/审批，易将过期或未确认事实变为承诺。 |

## Consequences

### Positive

- 可以在没有真实供应链数据时开发安全的模拟闭环。
- 真实资料到达后的工作收敛为导入、映射、人工批准和回归。
- 外部组件可以替换；业务领域和审计 contract 保持稳定。
- 关键外部动作可显式暂停、拒绝、审计与回滚。

### Costs / risks

- 初期要先做看似“不产生页面”的数据、审批、审计和测试基础。
- adapter/contract 的纪律必须通过自动测试执行，否则会再次形成耦合。
- 多业务线隔离、PII、日志留存和访问控制需要专项审查。
- Phase 6 仍高度依赖供应链、合规、平台和用户授权，技术底座不能消除这些阻断。

## Follow-ups

1. 按 [Phase 0–8 执行图](../PHASE_0_TO_8_EXECUTION_MAP.md) 先执行 Phase 0，冻结目录与依赖方向。
2. 实施 Phase 1 前对 [核心数据合同](../CORE_DATA_CONTRACTS.md) 进行 schema/权限审查。
3. 每个外部组件在接入前通过 [开源组件选择与退出策略](../OPEN_SOURCE_SELECTION_AND_EXIT_STRATEGY.md) 的替换与 license 核验。
4. 真实资料进入前，在 synthetic E2E 中证明 fixture、审批、审计、幂等与隔离。
5. 任何生产 adapter 单独建立 ADR/风险评审与用户授权记录。
