# 决策记录｜DECISIONS

本文件使用轻量 ADR 结构。业务决定与协作机制决定分开记录；Accepted 仅表示本条取舍已被用户或仓库审计支持，不表示商业、合规或履约已完成。

## 业务决定

### BD-0001：汾酒当前只做尼泊尔 TikTok

- **日期**：2026-08-05
- **状态**：Accepted / CONFIRMED
- **来源**：用户明确确认，2026-08-05
- **背景**：历史研究包含 B2B、多平台和 90 天方案，容易被误作当前指令。
- **决定**：汾酒当前正式线上执行主渠道为尼泊尔 TikTok。
- **影响**：旧 B2B、多平台、90 天试销等不自动进入当前执行；WhatsApp Business、Meta、Instagram、网站等仅可作为辅助基础设施，不自动成为独立主渠道。
- **后果**：恢复任何旧范围须有新的用户明确确认。

### BD-0002：用户负责线上销售执行，供应链负责本地产品与履约条件

- **日期**：2026-08-05
- **状态**：Accepted / CONFIRMED
- **来源**：用户明确确认，2026-08-05
- **背景**：线上运营和当地合法销售/履约需要明确边界，不能由模板替代责任确认。
- **决定**：用户负责账号运营、TikTok 内容、商品展示/上架、客户沟通、订单转化和销售数据反馈；供应链负责当地合法销售主体、资质、产品、SKU/价格/库存、账号认证支持、当地收款、仓储配送、售后和结算。
- **影响**：供应链责任范围不等于已交付；每项实际资料和负责人仍须书面确认。
- **后果**：用户不因本条自动获得当地销售、收款或履约权限。

### BD-0003：当前进入供应链启动资料收集与首批商品上线准备

- **日期**：2026-08-05
- **状态**：Accepted / CONFIRMED
- **来源**：用户明确确认，2026-08-05
- **背景**：当前缺口是可售商品和本地执行条件，不是继续扩写市场方案。
- **决定**：优先取得商品单、价格、库存、账号/权限、资质/授权、收款、配送、售后和负责人，并据此决定首批可上架 SKU。
- **影响**：内部资料整理可继续；公开销售、广告、收款和履约仍由相关书面前置条件阻断。
- **后果**：没有实际供应链回传时，不得把首批 SKU 或上线状态写为已确认。

### BD-0004：尼泊尔海鲜是独立业务线

- **日期**：2026-08-05
- **状态**：Accepted / CONFIRMED
- **来源**：用户明确确认，2026-08-05
- **背景**：仓库同时保存两条业务资料线。
- **决定**：海鲜可在其自身范围内做 B2B/B2C，但不属于汾酒当前 TikTok 主线。
- **影响**：两线只可复用有限协作机制；产品、客户、价格、资质、履约和结论不能互推。
- **后果**：无明确任务时，Agent 默认只处理汾酒主线。

## 协作机制决定

### ADR-0001：以业务状态、总览和协作状态构成固定入口

- **日期**：2026-08-05
- **状态**：Accepted
- **背景**：新会话需要同时理解当前业务和仓库协作，而不能只看到机制或旧研究。
- **决定**：按 AGENTS、PROJECT_ENTRY、BUSINESS_STATUS、CURRENT_STATUS、SOURCE_OF_TRUTH、SCOPE_AND_BOUNDARIES、COLLABORATION_STATUS 的顺序读取。
- **影响**：CURRENT_STATUS 保持一页路由；业务和协作详情分别维护。
- **替代方案**：单一长状态文件；未采用，因为容易混淆业务事实和技术收口。

### ADR-0002：同步包保持最小 allowlist 与可跨机器元数据

- **日期**：2026-08-05
- **状态**：Accepted
- **背景**：交接需要轻量、可核验上下文，且不得披露本地结构、秘密或大体积资料。
- **决定**：同步包只收录允许的入口、状态、模板和构建逻辑；manifest 仅记录可跨机器使用的来源信息和哈希。
- **影响**：业务原件、媒体、缓存、线索和本地配置不打包；同步包的 source_commit 只表示生成时的基线。
- **替代方案**：全仓打包；未采用，因为存在隐私、秘密、体积和过期派生产物风险。

### ADR-0003：汾酒与海鲜资料线分开建模

- **日期**：2026-08-05
- **状态**：Accepted
- **背景**：两条资料线共享部分尼泊尔协作主题，但业务事实不可互推。
- **决定**：默认入口只服务汾酒；海鲜仅在显式任务与独立原始资料下处理。
- **影响**：状态、事实源、任务交接和产物必须标明业务线。
- **替代方案**：合并为同一事实库；未采用，因为会提高业务混淆风险。

### ADR-0004：私有配置、线索与派生产物保持本地受控

- **日期**：2026-08-05
- **状态**：Accepted
- **背景**：凭据、联系方式和大体积材料不适合作为共享仓库或同步包内容。
- **决定**：本地私有配置、线索、缓存、媒体、QA 和渲染产物不进入 Git 或同步包，并接受构建前扫描。
- **影响**：共享内容以最小披露为原则；发现真实凭据时应评估轮换，且不得回显值。
- **替代方案**：依赖人工逐次挑选；未采用，因为遗漏风险高。

### ADR-0005：GPT Project 配合机制包与 AGENTS 镜像进入正式协作入口

- **日期**：2026-08-06
- **状态**：Accepted
- **背景**：上一轮已建立 GitHub 项目事实交接包，但 GPT Project 侧缺少可手动上传的长期配合机制包；新增 P0 要求同时审计 AGENTS 与参考仓库机制。
- **决定**：建立 `GPT项目资料同步包_gpt_project_mechanism_sync/`，并在根 `AGENTS.md`、`PROJECT_ENTRY.md`、`README.md` 中明确 GPT Project 机制包、GitHub 事实包和 Codex 执行层边界；包内 `project_entry/AGENTS.md` 作为根 AGENTS 的生成时只读镜像。
- **影响**：新聊天框可通过 GPT Project 包理解汾酒 TikTok 主线、P0/P1/P2、六层需求确认、Codex 下发和复审规则；业务事实仍以 GitHub `main` 当前文件为准。
- **替代方案**：只创建机制文件夹，不更新 AGENTS；未采用，因为新会话会同时存在仓库入口和 GPT Project 包，若二者不一致会造成事实源冲突。

### ADR-0006：AI Native Sales OS 采用 Phase 0–8 模块化单体实施图

- **日期**：2026-08-06
- **状态**：Accepted / PLANNED（工程规划，不是已实施状态）
- **来源**：用户本轮明确要求与当前仓库资产审计。
- **背景**：已有 GPT Project / GitHub / Codex 治理层，但尚无从工程底座到真实资料导入、fixture 替换和受控运行的逐任务纵向路径。
- **决定**：采用模块化单体、PostgreSQL 真值中心、adapter-first、fixture 与真实资料严格隔离、人工审批与默认审计的 Phase 0–8 计划；Phase 9 只保留外部上线证据闸门。
- **影响**：后续 Codex 一次只执行 `docs/implementation/codex_tasks/` 中前置已完成的单卡；真实资料到达后按导入、mapping、批准、回归和 run-ready runbook 操作，而非重设架构。
- **替代方案**：直接一次开发全部 CRM/客服/视频/采集系统；未采用，因为当前真实资料、账号、授权、合规和履约前置缺失，会扩大耦合和事实污染风险。
- **状态边界**：本决定不确认任何商品、价格、库存、资质、账号、收款、履约、平台允许、外部上线、订单或销售。

### ADR-0007：P01-02 local runtime 默认 fail-closed 且按 worktree 隔离

- **日期**：2026-08-06
- **状态**：Accepted / CONFIRMED（工程机制）
- **来源**：P01-02 任务卡、控制器审查与独立 code review。
- **背景**：多 Codex 聊天框/临时 worktree 可能并行验证本地 Compose；固定 project name 会让容器、网络和 volumes 相互冲突。healthcheck 若接受任意 URL，也会超出 local-only 网络边界。
- **决定**：P01-02 的运行入口只允许固定 loopback healthcheck、no-op migration/fixture 和 fail-closed external flags；Make 从当前 worktree 绝对路径派生 `COMPOSE_PROJECT_NAME`，所有 Compose lifecycle 入口统一使用该隔离名称。
- **影响**：本地生命周期可以在独立 worktree 内验证；不代表应用数据库已连接、远端 CI 已启用或任何外部业务条件满足。
- **替代方案**：固定全局 Compose project name 或运行时允许任意 health URL；未采用，因为会产生跨 worktree 干扰或外部网络能力。

### ADR-0008：P01-03 settings、flags、readiness 与日志默认拒绝

- **日期**：2026-08-06
- **状态**：Accepted / CONFIRMED（工程机制）
- **来源**：P01-03 任务卡、控制器审查与独立 code review。
- **背景**：Phase 1 尚无 broker/provider/真实配置；若以环境、fixture、prompt 或日志自由文本作为隐式输入，会产生未授权能力或泄露风险。
- **决定**：settings 只提供静态 disabled 状态；FeatureFlagPort 对 unknown/invalid/fixture/prompt 输入均返回 false；liveness 与 readiness 分离，未具备依赖时固定 not-ready；日志仅放行安全结构化 metadata，其他文本/URL/DSN/path/secret 默认脱敏。
- **影响**：后续 Phase 2 可复用控制面合同，但必须显式新增经审计的真实配置和 provider readiness，不能仅改默认值。
- **替代方案**：允许环境变量/fixture 覆盖或以 liveness 表示服务可业务运行；未采用，因为当前没有对应授权、依赖与业务闸门证据。

### ADR-0009：P02-01 以 compound scope/lineage 约束和强制 migration regression 锁定 synthetic 边界

- **日期**：2026-08-06
- **状态**：Accepted / CONFIRMED（工程机制）
- **来源**：P02-01 任务卡、控制器验收与独立 code review。
- **背景**：Phase 2 将引入可持久化的 scope、source 与 version metadata；若仅依赖应用层验证或可选 migration test，跨业务线引用、fixture 升级或遗漏数据库回归都可能绕过预期边界。
- **决定**：以 stdlib typed contracts 和 PostgreSQL compound foreign keys/check constraints 共同要求 tenant/project/business-line/source/version/synthetic lineage；任何 `external_execution_allowed=true` 在 schema 层拒绝。`make regression` 必须先在 worktree 派生的隔离 PostgreSQL project 中执行 migration replay 与负向约束，Docker/Compose/daemon 不可用则明确失败并清理该项目资源。
- **影响**：P02-02 可在受限 schema 上增加 synthetic truth model，但不得引入真实 scope/业务资料、生产连接或把 migration test 降为可选步骤。
- **替代方案**：只用 Python contract tests 或把数据库回归留作手动 target；未采用，因为不能证明 DDL/FK/constraint 在 PostgreSQL 中实际生效。
- **状态边界**：本决定不确认任何真实 tenant、SKU、价格、库存、主体、资质、账号、收款、履约、平台许可、外部上线、订单或销售。

### ADR-0010：P02-02 以 append-only version chain 和 evidence-gated current read 建立真值合同

- **日期**：2026-08-06
- **状态**：Accepted / CONFIRMED（工程机制；`main` 已远端回读）
- **来源**：P02-02 任务卡、P02-01 contracts 与本轮 self-review/migration regression。
- **背景**：仅有 scope/source/version metadata 不能防止 candidate、fixture、过期或冲突事实被 consumer 当作当前真值，也不能证明历史未被覆盖或审批 evidence 与 version 同源。
- **决定**：九类 truth entity 共用 value-free payload reference 和 immutable data version；所有 successor 显式携带 parent、field diff/hash、effective window 与 scope/source/version lineage。current read 只返回唯一 approved/fresh/no-successor 且 approval evidence 完整的版本；Python repository 与 PostgreSQL trigger 同时拒绝非法状态迁移、分叉、UPDATE 和 DELETE。
- **影响**：P02-03 可针对同一 read/lineage contract 做 adversarial isolation；Phase 3 future ingestion 只能创建 candidate，不能直接写 current truth。
- **替代方案**：按时间戳或 version number取最新记录；未采用，因为 conflict/expired/superseded 可能被静默读出。只在 application 层检查；未采用，因为直接 SQL 会绕过状态与 append-only 防护。
- **状态边界**：本决定不表示真实 approval actor/RBAC、production repository/RLS、业务资料、供应链、合规或外部执行成立。

### ADR-0011：P02-03 以 sealed policy grant 和 append-only denial audit 锁定 consumer read

- **日期**：2026-08-06
- **状态**：Accepted / CONFIRMED（工程机制；`main` 已远端回读至 `451843601a1a610e50bfbd9794f437b5781f1401`）
- **来源**：P02-03 任务卡、adversarial regression、自审、控制器 REQUEST CHANGES 与最终独立 code review。
- **背景**：仅靠 scope 参数和 UI/prompt filter 不能阻止 downstream 直接读 repository；caller-controlled sensitivity、可伪造 grant/verifier、runtime probe helper、未强制 audit 的 direct current、read-time actor replacement 或可清空 denial log 均会破坏隔离或审计归因。
- **决定**：current truth consumer 必须走 command → fixed local policy → sealed nominal policy registry grant → exact repository current read → immutable audit result。external flags 必须完整且全 false；runtime repository 不暴露 history/by-id/current probe helpers；guarded current 在返回 truth 前必须通过 sealed audit recorder 强制写入 success audit；`actor_ref` 必须在 policy issuance 时进入 grant signature/validation，repository 不接受独立 actor 参数，只记录 validated grant actor。
- **影响**：P03-01 及以后只能在完整 scope 与 approved/fresh/no-conflict truth 合同内工作；synthetic staging 可写入候选，但不能成为 current truth 或任何 external fallback。
- **替代方案**：caller-supplied sensitivity allowlist；未采用，因为调用者可自我提权。自洽 dataclass grant 或 structural verifier protocol；未采用，因为 direct issuer/fake verifier 可绕过。用 Python underscore 隐藏 runtime probe；未采用，因为命名约定不是安全边界。只在 consumer 成功后写 audit；未采用，因为 direct grant read 可绕过。仅在 `current` 校验 actor 字符串；未采用，因为合法 grant holder 仍可替换归因。mutable list audit；未采用，因为 denial evidence 可被普通 clear。
- **状态边界**：本决定只证明 local in-process contract integrity；不表示 production auth/RBAC/RLS、真实 data classification、业务资料、合规或外部执行成立。

### ADR-0012：P03-01 将 synthetic staging 与 approved truth 分离，并以 locator lineage fail closed

- **日期**：2026-08-06
- **状态**：Accepted / CONFIRMED（工程代码已由 `main` 远端回读）
- **来源**：P03-01 task card、P02-03 contract、test-first、自审、控制器 atomicity REQUEST CHANGES 与独立专项 code review。
- **背景**：Phase 3 需要验证来源登记、hash、定位和失败留存，但真实供应链文件尚未授权入场，P02 fixture 也禁止被提升为 approved/real。若 fake extraction 直接保存值、允许无 locator 字段或逐字段部分写入，会破坏 evidence lineage 和人工审批边界。
- **决定**：P03-01 只接受 ephemeral synthetic bytes 和 value-free field descriptors；记录只保存 private relative/reference locator、hash、IDs、versions、field name 与 location。`workflow_state=staged` 不改变 `data_state=fixture`；runtime 不暴露单条 result/candidate mutator，只允许经一对一、无重复、lineage 一致的全批次原子写入。任何 unsafe/unknown/failed input 或不完整 batch 只进入 quarantine、blocked/manual 或稳定错误码 fail closed。
- **影响**：P03-02 可消费 source/job/result/candidate/locator/hash/version contract 做 synthetic mapping/quality，但不能回读 raw value、自动补值、批准或进入 P02 current truth。真实 parser/OCR、storage/database、auth/RBAC/RLS 必须另开任务和证据闸门。
- **替代方案**：在 P03-01 引入真实 OpenXML/PDF/OCR 解析器；未采用，因为需要真实文件/新依赖且超出授权。把 staged candidate 写成 non-synthetic `DataState.STAGING`；未采用，因为会伪装 fixture 来源并打开未来 promotion 风险。仅移除公共单条 mutator；未采用，因为 batch 入口本身仍可写入半批次。逐字段写入后再报告失败；未采用，因为会留下部分候选。
- **状态边界**：本决定不确认任何真实商品、价格、库存、资质、账号、收款、履约、platform rule、approved truth 或外部执行。

### ADR-0013：P03-02 只生成 value-free fingerprint，并将 replay 绑定完整 profile provenance

- **日期**：2026-08-06
- **状态**：Accepted / CONFIRMED（工程代码已由 `main` 远端回读）
- **来源**：P03-02 task card、控制器 forged-profile 复现、独立 reviewer lifecycle review、最终专项复审。
- **背景**：在没有真实资料、可解析原值、人工 mapping review 或 production storage 的阶段，normalization 不能冒充真实文本/单位/币种/日期处理。初始 profile registry 只比较 ID/version 与 replay run fingerprint，允许同 ID/version 的不同 profile 借用 canonical replay proof；mapping entrypoint 也未拒绝 P03-01 quarantine/non-staged lifecycle。
- **决定**：P03-02 normalizer 只从既有 content hash、transform IDs 和 known/unknown control status 产生 value-free fingerprint。Mapping report 必须带 engine-constructed full profile fingerprint；profile change 注册必须同时匹配已登记旧 profile、previous/current report、传入新 profile、scope 与 replay diff。mapping 前只接受 `SourceDisposition.REGISTERED`、job/candidate `IngestionWorkflowState.STAGED` 的完整 P03-01 lineage；其余只产生 blocked/manual 与稳定错误码。
- **影响**：P03-03 只能消费 synthetic candidate/report/replay evidence 建立人工 approval/publish/refresh contract，不能把 fingerprint 当作真实标准化结果、自动批准或 P02 current truth。
- **替代方案**：接入真实文本解析或以 profile ID/version 代表完整配置；未采用，前者需要未授权真实资料和新能力，后者已被 forged provenance 复现可绕过。
- **状态边界**：本决定不确认真实 mapping、SKU、价格、库存、资质、人工批准、production storage/auth/RBAC/RLS、合规或任何外部执行。

### ADR-0014：P03-03 将合成审批发布与 P02 当前真值隔离，并以业务范围刷新当前读取

- **日期**：2026-08-08
- **状态**：Accepted / CONFIRMED（工程代码已由 `main` 远端回读）
- **来源**：P03-03 task card、P02 fixture/current-truth contracts、test-first、控制器审查与两轮最终只读复核。
- **背景**：Phase 3 需要证明 source/quality lineage 经人工决定后可以形成不可变的内部发布版本并使下游草稿/缓存失效；但 P03 输入仍是 synthetic fixture，不能绕过 P02 `DataState.APPROVED` 或 P02 current truth。初版还发现 command correlation 可与审批链分离、过期无持久状态，以及 current read 把一次性 correlation 当作业务 series key。
- **决定**：P03-03 只创建 isolated approved synthetic version，固定 `DataState.FIXTURE` 与所有外部 flags false。approve/reject/revise/supersede/revoke、expiry、idempotency、scope/source/evidence 与 append-only audit 均在本地合同中 fail closed；request/decision/revoke 的 correlation 必须与所属记录一致。current read 仅以 tenant/project/business-line、fact type 和 subject 建立业务范围键，保留 record/refresh/audit 原 correlation 作为追踪信息；刷新只产生内部失效通知合同。
- **影响**：Phase 4 可以依赖 P03-03 的内部审批/失效合同，但仍必须另行建立真实身份/RBAC、生产存储与 action policy。P05/P06/P07 不得将此合成版本写成真实 approved fact，也不得把刷新合同解释为 CRM、客服或内容模块已实施。
- **替代方案**：复用 P02 `TruthVersion` 直接发布；未采用，因为会混淆 fixture 与 current truth。以完整 `ScopeRef`（含 correlation）作为 current key；未采用，因为新读取 correlation 会错误漏读同一业务范围当前版本。实现 consumer 模块或外部同步；未采用，因为本卡仅授权内部刷新合同。
- **状态边界**：本决定不确认真实审批身份、SKU、价格、库存、资质、供应链、合规、账号、收款、履约、外部发布或业务外部就绪。

### ADR-0015：P04-01 以受限本地工作流运行器保存恢复元数据，不让存储面成为审批旁路

- **日期**：2026-08-09
- **状态**：Accepted / CONFIRMED（工程代码已由 `main` 远端回读）
- **来源**：P04-01 task card、工作流/审批设计、test-first、控制器审查与两轮最终只读复核。
- **背景**：Phase 4 需要可靠地协调命令恢复，但 workflow 不能拥有 P03 approval truth、业务事实或 audit truth。初版审查发现终态 run 可经 approve 回流，随后发现公开 in-memory store 写入面能绕开 `approval_recorded` 事件或伪造终态重开。
- **决定**：以 local simple runner（本地简易运行器）作为主路线和回退路线；checkpoint 仅保存安全元数据/引用/哈希。只有 runner 的受控内部写面可记录命令、检查点、run、审批、队列和 fake effect（模拟内部效果）；公开 store 写 mutator 固定拒绝。approval 仅允许 `waiting_for_approval`，终态/人工队列不可重开；外部效果固定策略拒绝，未知效果进入人工队列。LangGraph 只保留无依赖安装的可用性探测，不成为恢复状态唯一来源。
- **影响**：P04-02 可在此运行元数据合同之上建立真实角色/RBAC 与 action policy（动作策略）合同，但不能把 runner/store 当作身份认证、审批真值、生产队列或 provider adapter（服务提供方适配器）。
- **替代方案**：让公开 store 提供通用写入 API；未采用，因为会绕过 runner 状态机和审批事件。直接接入 LangGraph；未采用，因为当前未安装、未获依赖准入且需先证明同一合同与退出能力。
- **状态边界**：本决定不确认真实 actor、RBAC、生产队列、真实 provider、业务真值、SKU、价格、库存、资质、供应链、合规、账号、收款、履约或任何外部动作。

### ADR-0016：P04-02 将审批绑定到精确事实版本与完整策略语义

- **日期**：2026-08-09
- **状态**：Accepted / CONFIRMED（工程代码已由 `main` 远端回读）
- **来源**：P04-02 task card、test-first、控制器审查与两轮最终只读复核。
- **背景**：P04-01 只安全协调 workflow 状态，不能认证角色或承担高风险动作的授权判断。初版 P04-02 虽能审核请求，但执行前未绑定批准时的事实版本，且同一幂等键可在证据、时效、开关、DNC/同意或环境变化后复用旧结果。
- **决定**：P04-02 以 local synthetic 的角色/动作矩阵、追加式审批决定和执行前复核承接 P04-01。获批请求仅可对完全相同的 `scope/action/target/correlation/subject_version` 复核；任何事实版本漂移返回稳定拒绝且不尝试外部执行。幂等指纹覆盖角色、范围、事实状态/时效、证据、开关、DNC/同意、环境、策略和审批语义；相同键但语义不同固定冲突拒绝。外部动作始终被策略拒绝。
- **影响**：P04-03 可在可追溯的本地策略/审批事件之上建立审计、指标、重试和死信合同；P05/P06/P07 只能消费这些 internal contract，仍不得把它解释为真实用户授权、真实业务事实或外部执行许可。
- **替代方案**：只绑定 scope/target 或只将 action/target 写入幂等键；未采用，因为前者允许旧审批覆盖新事实版本，后者允许策略语义漂移静默复用。直接接入真实身份/权限平台；未采用，因为当前没有生产身份来源、授权或业务资料。
- **状态边界**：本决定不确认真实身份、真实 RBAC、真实审批、生产审计/队列、SKU、价格、库存、资质、供应链、合规、账号、收款、履约或任何外部动作。

### ADR-0017：P04-03 以追加式失败补偿保护暂存效果，不把执行异常写成成功

- **日期**：2026-08-09
- **状态**：Accepted / CONFIRMED（工程代码已由 `main` 远端回读）
- **来源**：P04-03 task card、test-first、控制器审查与三轮最终只读复核。
- **背景**：P04 需要使后续模块能追踪本地命令、重试与人工处理，但当前没有可用生产数据库事务或 broker。初版先后暴露 success audit 失败后 effect 已可见，以及成功审计后 commit 失败仍保留成功意图的矛盾；直接修改历史审计又会违反 append-only。
- **决定**：命令 mutation 只能返回显式 staged effect（暂存效果），先记录开始、准备 effect、记录成功审计后才提交；成功审计失败时执行 rollback。若 commit 失败，则保留已有审计历史、best-effort rollback，并追加 `command_commit_failed` 作为最终失败/人工处理证据；rollback 失败同样追加安全事件并标记 `manual_required=true`。外部或未知副作用绝不自动重试，进入人工处理；所有审计、指标与日志均拒绝或脱敏敏感内容。
- **影响**：P05/P06/P07 可共享本地审计、失败分类和安全指标合同，但必须通过 P04-02 policy 及各自业务边界；不得将该内存合同解释为生产事务、真实监控、真实审批或外部执行许可。
- **替代方案**：先提交 effect 后写成功审计；未采用，因为审计失败会留下无证据变更。删除或修改已写成功事件；未采用，因为破坏 append-only。接入生产数据库/broker/monitor；未采用，因为缺少授权、连接与真实身份/资料。
- **状态边界**：本决定不确认生产审计/队列/监控、真实身份/RBAC、真实资料、SKU、价格、库存、资质、供应链、合规、账号、收款、履约或任何外部动作。
