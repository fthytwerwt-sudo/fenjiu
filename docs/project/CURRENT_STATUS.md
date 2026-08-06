# 当前项目总览｜CURRENT_STATUS

- **最近更新**：2026-08-06
- **用途**：本页只提供业务与协作的短摘要和路由；详细事实以链接文件为准。

## 业务状态摘要

- **CONFIRMED**：汾酒当前正式范围为尼泊尔 TikTok 线上销售准备，阶段为供应链启动资料收集与首批商品上线准备。
- **UNKNOWN**：供应链尚未在当前资料中实际提供 SKU、价格、库存、补货、主体/资质、品牌授权、账号权限、收款、仓储配送、售后及负责人确认。
- **当前最重要任务**：先补齐商品单、价格规则和库存，再确认首批可上架 SKU，并补齐账号、资质、收款和履约资料。
- **P0 阻断**：在上述资料及 TikTok 当前酒类内容/广告边界获得书面确认前，不能进入公开发布、广告、真实销售、收款、订单或履约。

详情：[BUSINESS_STATUS.md](BUSINESS_STATUS.md)｜[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)｜[RISKS_AND_BLOCKERS.md](RISKS_AND_BLOCKERS.md)｜[NEXT_ACTIONS.md](NEXT_ACTIONS.md)

## 协作机制状态摘要

- **CONFIRMED**：固定入口、事实分级、任务交接、执行记录和同步包机制已建立。
- **CONFIRMED**：GPT Project 配合机制包已在仓库内生成并通过本地验证；包内 AGENTS 镜像与根 AGENTS SHA-256 一致。
- **部分成立**：V2 正在将公开历史脱敏、干净 main、远端默认分支、visibility 和新同步包验证收口；这些事项必须以最终远端回读为准。
- **最近远端验证**：待 V2 最终阶段回读，不能用本文件编辑或本地 commit 替代。

## 工程规划状态摘要

- **CONFIRMED（规划层）**：`docs/implementation/` 已形成 AI Native Sales OS 的 Phase 0–8 分阶段蓝图、机器可读依赖图和每阶段 3 张 Codex 任务卡；该规划承接 GPT Project / GitHub / Codex 治理机制，不替代它。
- **部分成立**：本摘要不表示已创建可连接数据库的业务服务、队列、CRM、客服、视频服务或真实资料导入；技术实施仍须按 `docs/implementation/CODEX_EXECUTION_INDEX.md` 一次一张任务卡推进。
- **CONFIRMED（工程 Phase 0）**：P00-01、P00-02 与 P00-03 已完成远端回读；P00-03 在干净独立 task worktree 通过 12 项回归和两种扫描模式。外置盘根目录存在既有 ignored 禁入路径，故不得在该根目录运行 P00 default/`--all-files` 扫描；`make regression` 的 compile step 已显式跳过 AppleDouble metadata，但后续任务仍须在新建、干净的独立 task worktree 中启动。
- **CONFIRMED（工程 Phase 1）**：P01-01 至 P01-03 已在 `main` 远端回读：模块化单体 skeleton、synthetic-only fixture metadata、local-only Docker Compose / Make、静态 typed settings / FeatureFlagPort、liveness/readiness 与 JSON 脱敏日志合同均已建立。所有敏感 flags 默认 false，broker/provider/real configuration 不存在时 `/ready` 返回 HTTP 503；日志只保留结构化安全码并 fail-closed 脱敏自由文本、URL、DSN、Cookie、secret 和绝对路径。当前通过 8 项 architecture、14 项 regression、8 项 local-runtime 与 16 项 control-plane 测试；未接入应用数据库连接、外部网络、模型、SDK 或真实业务资料。GitHub Actions workflow 因当前凭据缺少 `workflow` scope 未写入远端；Phase 2 仍须在新建干净 task worktree 中逐卡推进。
- **CONFIRMED（工程 Phase 2 / P02-01）**：`main` 的 P02-01 代码已远端回读至 `b08722a703f37a0cfcce0c928fec8c01c4596357`：stdlib scope/source/version metadata contracts、local PostgreSQL schema migration 与 compound scope/lineage constraints 已建立。默认 `make regression` fail-closed 地执行隔离 PostgreSQL migration replay（两次）与五类负向约束，再运行既有测试；本轮总计 54 项 Python 测试通过，临时容器与 volumes 已清理。
- **CONFIRMED（工程 Phase 2 / P02-02）**：`main` 的 P02-02 代码已远端回读至 `0ba7f0575fdfe2906455c5b6301ac71c8872e727`：九类 value-free truth contracts、append-only parent/version chain、approval/effective-window current read、PostgreSQL trigger/view 已建立。review 发现 terminal root 可绕过 staging ancestry 后，已在 Python 与 SQL 双层限制 root 只能为 synthetic fixture/mock 或 non-synthetic staging；完整回归通过 73 项 Python 测试、两次 migration replay 与 16 类 SQL 负例。它只证明 local contract/state/read 防护，未接入 production database、真实 tenant/SKU/价格/库存、认证审批/RBAC、RLS 或任何外部动作；P02-03 isolation/audit 证据见下一项。
- **CONFIRMED（工程 Phase 2 / P02-03）**：控制器已将审查后的 P02-03 六笔提交安全集成，并将 `main` 推送、回读至 `451843601a1a610e50bfbd9794f437b5781f1401`。runtime probes 只存在于 tests-only harness；guarded current truth 必须通过 sealed policy grant、强制 audit，且 audit actor 只能来自包含 actor signature binding 的 validated grant。控制器与独立 reviewer 发现的 direct helper、unaudited direct read 和 actor attribution replacement HIGH 均已修复，最终专项独立复审 `APPROVE`；集成后 `main` 回归通过 92 项 Python tests、两次 migration replay 与 16 类 SQL 负例。该 runtime contract 不是 actor authentication/RBAC；P03-01 可在新的干净 task worktree 单卡启动，但 production database、真实 tenant/SKU/价格/库存、认证审批/RBAC、RLS 或任何外部动作仍未建立。
- **部分成立（工程 Phase 3 / P03-01 task branch）**：P03-01 已在精确 `main` 基线 `bce35a01fa7c13cce797069198ce71dcf29ea2dc` 的干净 worktree 完成 stdlib/local-only/synthetic source registration、private relative/reference locator、hash/job/result/candidate idempotency、quarantine、七类 fake extraction ports 与 fixture staging。控制器发现的 runtime 单条 staging atomicity bypass HIGH 已修复：单条 mutator 已移除，批量入口强制 result/candidate 一对一且在任何可见写入前 fail closed。最终回归通过 106 项 Python tests、两次 migration replay和 16 类 SQL 负例；P00 两种扫描、mechanism validation、Docker cleanup 与独立专项复审 0 findings / `APPROVE`。任务分支代码提交 `e17196e06380827224a1463f01b53a9975382f22` 已 push/core-file readback，但尚未 merge/push `main`；真实 parser/OCR/storage/database/auth/RBAC/RLS/approved publish 与 external actions 均未建立。
- **BLOCKED（外部业务）**：该规划不解除 SKU、价格、库存、主体/资质、账号、收款、履约或 TikTok 酒类边界的业务闸门；公开发布、报价、收款、下单和履约仍保持停止。

详情：[COLLABORATION_STATUS.md](../collaboration/COLLABORATION_STATUS.md)｜[SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md)

## 范围提醒

旧 B2B、多平台与 90 天研究已作为历史输入保留，且仅在当前执行范围层面被替代；海鲜资料线独立，不自动进入汾酒任务。
