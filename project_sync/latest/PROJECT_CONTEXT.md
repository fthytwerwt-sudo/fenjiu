# 项目上下文｜PROJECT_CONTEXT

本文件由同步包脚本生成，汇总最小必要上下文；完整规则仍以同包原文件为准。

## 项目入口

# 项目统一入口｜PROJECT_ENTRY

本文件是新 ChatGPT、Codex、Work 或人工协作者的业务优先导航；它不替代原始资料，也不把模板当作合作方已确认。

## 30 秒定位

- **当前正式范围**：汾酒仅做尼泊尔 TikTok 线上销售准备。TikTok 是当前主销售与内容渠道。
- **当前阶段**：供应链启动资料收集与首批 TikTok 商品上线准备，不是已经公开销售或履约。
- **用户负责**：线上账号运营、TikTok 内容制作与发布、商品展示和上架、客户沟通、订单转化，以及销售数据和市场反馈。
- **供应链负责**：当地合法销售与品牌/产品资质、SKU/规格/价格/库存、账号主体认证支持、当地收款、仓储配送、退换货、质量、售后和财务结算；这些均为确认的责任边界，不表示资料已交付。
- **当前最重要任务**：取得商品单、真实价格与规则、库存/补货、账号和认证支持、资质授权、收款、配送售后及明确负责人；资料齐备后再决定首批可上架 SKU。
- **不自动恢复的旧范围**：B2B 经销商开发、多平台独立运营、Facebook/Instagram 独立营销、YouTube/Viber、90 天试销、自动找客或自动外联。
- **海鲜资料线**：独立业务线；可共享有限协作机制，不能直接用于汾酒事实或决策。

## 必读顺序

1. [AGENTS.md](AGENTS.md)
2. 本文件
3. [业务状态](docs/project/BUSINESS_STATUS.md)
4. [总览状态](docs/project/CURRENT_STATUS.md)
5. [事实源地图](docs/project/SOURCE_OF_TRUTH.md)
6. [范围与边界](docs/project/SCOPE_AND_BOUNDARIES.md)
7. [协作机制状态](docs/collaboration/COLLABORATION_STATUS.md)
8. 与当前任务直接相关的原始资料；不要用派生产物替代原始资料。

## 先分清可继续与不可进入的动作

- **可继续准备**：内部资料整理、供应链启动表、商品字段/上架资料设计、事实核验、合规与平台问题清单、受控草稿。
- **P0 阻断外部执行**：未取得当前书面证据前，不得公开发布、投放、收款、下单、承诺交期或开展真实履约。关键缺口包括 SKU、价格、库存、主体和资质、账号权限、收款、配送售后，以及 TikTok 酒类内容/广告边界。

## 状态和交接

- 业务事实以 [BUSINESS_STATUS.md](docs/project/BUSINESS_STATUS.md) 为准。
- 协作与仓库收口事实以 [COLLABORATION_STATUS.md](docs/collaboration/COLLABORATION_STATUS.md) 为准。
- 当前摘要以 [CURRENT_STATUS.md](docs/project/CURRENT_STATUS.md) 为准；它只路由，不替代两份详细状态。
- 重要任务完成后更新状态、决策、风险、下一步和 [执行历史](docs/collaboration/EXECUTION_HISTORY.md)。

生成交接包：

    python3 scripts/build_project_sync_pack.py

把 project_sync/latest 或本地 ZIP 与 [同步包说明](docs/sync/README.md) 一并交给新会话。新会话必须先复述当前范围、阶段、职责、事实分级、阻断和完成标准，再执行。

## 业务状态

# 业务项目状态｜BUSINESS_STATUS

- **最近更新**：2026-08-05
- **业务线**：汾酒尼泊尔主线
- **状态来源**：用户明确确认，2026-08-05；以及当前仓库原始资料存在性审计。

## 当前业务阶段

**CONFIRMED**：供应链启动资料收集与首批 TikTok 商品上线准备。

这表示可继续做内部资料、字段、清单和证据准备；不表示供应链已经交付资料，也不表示已可对外销售。

## 当前正式业务范围

- **CONFIRMED**：汾酒当前只做尼泊尔 TikTok 线上销售；TikTok 是主销售和内容渠道。
- **CONFIRMED**：WhatsApp Business、TikTok Business Center/广告账户、Facebook Page、Meta Business Manager、Instagram、官方网站、企业邮箱和当地收款账户可作为认证、广告、客服、询盘、收款或基础设施使用。
- **CONFIRMED**：上述辅助资产不自动成为独立营销主渠道。
- **SUPERSEDED**：旧研究中的 B2B 经销商开发、多平台独立运营、Facebook/Instagram 独立营销、YouTube、Viber、完整 90 天试销、自动找客和自动外联，仅在当前执行范围层面被替代；原始研究仍保留为历史背景，重新启用须由用户明确确认。

## 双方职责边界

| 角色 | CONFIRMED 的责任边界 | 不能据此推断 |
|---|---|---|
| 用户 | 线上账号运营、TikTok 内容制作与发布、商品线上展示和上架、客户沟通、订单转化、销售数据和市场反馈 | 已获平台权限、已完成发布或已成交 |
| 供应链 | 当地合法销售主体、进口/销售/品牌资质、产品合法可售、SKU/规格/价格/最低价/库存/补货、品牌素材、账号主体认证支持、当地收款、仓储发货配送、退换货、质量、售后和财务结算 | 任一资料已经提供、确认或可执行 |

## 当前已完成的内部准备

- **CONFIRMED**：汾酒市场、执行与文化/合规研究源文件存在。
- **CONFIRMED**：供应链启动文件/模板存在，商品、价格、库存、账号、资质和履约字段已被设计。
- **CONFIRMED**：当前范围、职责和资料收集优先级已被用户明确确认并写入项目状态。

## 正在进行

- **CONFIRMED**：整理和维护可交给供应链填写的启动资料入口。
- **UNKNOWN**：供应链是否已填写、回传或确认任何商品、价格、库存、账号、资质、收款或履约资料。
- **BLOCKED**：没有上述实际书面资料时，不能决定首批可上架 SKU，也不能进入真实外部销售。

## P0 待补输入

1. 真实 SKU、规格、商品图片/品牌素材、价格、价格有效期、最低销售价、库存和补货周期。
2. 当地销售/进口主体、产品合法可售、品牌授权与相关资质。
3. 账号主体、管理员权限和认证支持。
4. 当地收款主体、仓储、发货、配送、退换货、质量、售后和财务结算责任人。
5. TikTok 当前酒类内容、广告、账号和转化边界的书面核验。
6. 以上资料基础上确定的首批可上架 SKU。

## 可继续与必须停止的动作

- **可继续**：内部资料整理、供应链启动清单、商品信息收集、合规/平台问题核验、草稿和人工审核。
- **BLOCKED**：公开发布、广告投放、真实报价、收款、下单、发货、承诺交期、真实售后，直至对应 P0 输入和授权以当前书面证据解除。

## 海鲜资料线

**CONFIRMED**：尼泊尔海鲜为独立业务线，可有 B2B 与 B2C 范围。两条业务线可复用有限协作机制，但产品、客户、价格、资质、履约和业务结论不得互推；没有明确任务时，Agent 默认只处理汾酒主线。

## 更新规则

任何实际资料回传、责任确认或范围变化，都须附来源、日期、确认人和事实分级，并同步更新 OPEN_QUESTIONS、RISKS_AND_BLOCKERS、NEXT_ACTIONS 与必要的决策记录。

## 当前总览

# 当前项目总览｜CURRENT_STATUS

- **最近更新**：2026-08-05
- **用途**：本页只提供业务与协作的短摘要和路由；详细事实以链接文件为准。

## 业务状态摘要

- **CONFIRMED**：汾酒当前正式范围为尼泊尔 TikTok 线上销售准备，阶段为供应链启动资料收集与首批商品上线准备。
- **UNKNOWN**：供应链尚未在当前资料中实际提供 SKU、价格、库存、补货、主体/资质、品牌授权、账号权限、收款、仓储配送、售后及负责人确认。
- **当前最重要任务**：先补齐商品单、价格规则和库存，再确认首批可上架 SKU，并补齐账号、资质、收款和履约资料。
- **P0 阻断**：在上述资料及 TikTok 当前酒类内容/广告边界获得书面确认前，不能进入公开发布、广告、真实销售、收款、订单或履约。

详情：[BUSINESS_STATUS.md](BUSINESS_STATUS.md)｜[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)｜[RISKS_AND_BLOCKERS.md](RISKS_AND_BLOCKERS.md)｜[NEXT_ACTIONS.md](NEXT_ACTIONS.md)

## 协作机制状态摘要

- **CONFIRMED**：固定入口、事实分级、任务交接、执行记录和同步包机制已建立。
- **部分成立**：V2 正在将公开历史脱敏、干净 main、远端默认分支、visibility 和新同步包验证收口；这些事项必须以最终远端回读为准。
- **最近远端验证**：待 V2 最终阶段回读，不能用本文件编辑或本地 commit 替代。

详情：[COLLABORATION_STATUS.md](../collaboration/COLLABORATION_STATUS.md)｜[SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md)

## 范围提醒

旧 B2B、多平台与 90 天研究已作为历史输入保留，且仅在当前执行范围层面被替代；海鲜资料线独立，不自动进入汾酒任务。

## 事实源地图

# 事实源地图｜SOURCE_OF_TRUTH

发生冲突时按下表读取。派生产物、截图、口头转述、聊天摘要和旧同步包不能覆盖排名更高且较新的原始来源。

| 信息类型 | 当前事实源 | 状态与说明 |
|---|---|---|
| 当前正式业务范围、阶段、职责、未知与业务阻断 | docs/project/BUSINESS_STATUS.md | **CONFIRMED** 的范围和职责来自用户明确确认（2026-08-05）；供应链实际交付仍须原始书面证据 |
| 项目总览与路由 | docs/project/CURRENT_STATUS.md | 短摘要；不替代业务或协作详细状态 |
| 协作、Git、同步包与远端回读 | docs/collaboration/COLLABORATION_STATUS.md | 远端 branch、commit、默认分支和 visibility 仅以最终回读为准 |
| 协作规则与阅读顺序 | AGENTS.md、PROJECT_ENTRY.md | **CONFIRMED** 的仓库规则和导航 |
| 当前执行范围 | docs/project/PROJECT_GOAL.md、SCOPE_AND_BOUNDARIES.md | **CONFIRMED**；旧研究不覆盖当前范围 |
| 已采用的业务与机制取舍 | docs/project/DECISIONS.md | **CONFIRMED**；每条决定须保留来源、日期、影响和状态 |
| 待补业务输入、阻断与顺序 | OPEN_QUESTIONS.md、RISKS_AND_BLOCKERS.md、NEXT_ACTIONS.md | **UNKNOWN/BLOCKED**；收到书面证据后再更新 |
| 汾酒市场、渠道和合规研究 | research_root.json、research_execution.json、research_culture_compliance.json | 资料存在为 **CONFIRMED**；涉及 B2B、多平台、90 天方案的内容为 **SUPERSEDED**（仅当前执行范围层面被替代），保留为历史市场背景，须由用户重新确认才可恢复 |
| 汾酒供应链启动模板 | 任务相关的汾酒供应链原始文件 | 模板和字段存在为 **CONFIRMED**；未签署、未回执或未回传的字段不得写为已确认 |
| 尼泊尔海鲜业务资料 | 海鲜原始资料线与对应供应链文件 | 独立资料线；不得自动用于汾酒结论 |
| 生成逻辑 | 根目录生成脚本与 scripts | 脚本存在/运行结果不等于业务事实 |
| 派生产物 | outputs、交付物、qa、渲染和媒体 | 仅作结果或质量线索；必须回读源数据与脚本 |
| 本地私有配置和线索 | 本地受控资料 | 不进入 Git 或同步包；不能当作对外联系授权或共享事实源 |

## 更新规则

1. 新事实须有来源、日期、责任人和事实分级。
2. 原始资料与状态冲突时，记录冲突并暂停升级，不静默挑选。
3. 新决定替代旧决定时，在 DECISIONS 中标记 SUPERSEDED，并保留原始资料。
4. 法律、平台、价格、库存、主体、账号和联系方式均应在执行前重新核验，不可仅依赖历史研究。

## 范围与边界

# 范围与边界｜SCOPE_AND_BOUNDARIES

## 当前在范围内

- 汾酒尼泊尔 TikTok 线上销售准备；
- 供应链启动资料收集、商品字段核验、首批 SKU 决策输入与上线前准备；
- 用户的账号运营、内容、商品展示、客户沟通、订单转化和数据反馈准备；
- 供应链的主体/资质、产品、账号认证支持、收款与履约资料收集和书面确认；
- 事实分级、状态、决策、风险、交接和同步包机制维护；
- 海鲜资料线的独立保存与明确任务下的独立处理。

## 当前不在范围内

- 自动恢复旧研究中的汾酒 B2B 经销商开发、多平台独立运营、Facebook/Instagram 独立营销、YouTube、Viber、完整 90 天试销、自动找客或自动外联；
- 将 WhatsApp Business、Meta、Instagram、网站等辅助资产自动扩大为独立主营销渠道；
- 未经明确授权和书面前置条件的外发、发布、投放、真实报价、下单、收款、发货或售后；
- 将海鲜产品、客户、价格、资质、履约或结论用于汾酒，或反向推导；
- 将研究、模板、文档、提交或测试通过描述为当地许可、供应链确认、上线、销售或履约。

## 不可擅自修改

- 原始研究 JSON、原始 DOCX/XLSX/PDF、视频、素材与供应链原始资料；如需更正，应建立可追溯的新版本，不覆盖原件。
- 本地私有配置、凭据、线索、私人联系方式、缓存、媒体、渲染和 QA 材料的安全边界。
- 已确认的业务范围、职责和事实源；变更须有新的用户确认或书面证据。

## 许可与执行闸门

内部资料准备可继续。任何公开酒类内容、广告、商品展示、导流、订单、付款、配送或个人数据处理，必须同时满足：当地合法性、当前平台规则、主体/品牌/产品授权、年龄与地域限制、账号与数据归属、收款履约责任、用户授权和可审计证据。任一缺失即 **BLOCKED**。

## 协作机制状态

# 协作机制状态｜COLLABORATION_STATUS

- **最近更新**：2026-08-05
- **用途**：记录仓库协作、脱敏、Git 与同步包状态；不替代 BUSINESS_STATUS 中的业务事实。

## 入口与协作规则

| 项目 | 状态 | 说明 |
|---|---|---|
| AGENTS 规则 | **CONFIRMED** | 已要求先读业务状态，再读总览、事实源、范围和协作状态；禁止把机制完成写成业务完成 |
| PROJECT_ENTRY | **CONFIRMED** | 已以 TikTok、供应链启动阶段、双方职责、P0 输入、历史研究降级和海鲜隔离作为首屏信息 |
| 业务/协作状态分离 | **CONFIRMED** | BUSINESS_STATUS 记录业务，CURRENT_STATUS 仅作路由，本文记录协作与远端状态 |
| 交接模板与执行历史 | **CONFIRMED** | 已要求新会话先复述范围、事实分级、阻断和完成标准 |

## 安全与历史迁移审计

- **CONFIRMED**：旧临时分支历史共有 6 个提交；历史 manifest 与多份历史生成脚本曾暴露本机绝对路径和不必要的本地结构信息。
- **CONFIRMED**：使用高置信凭据规则检查 Git 历史，命中数为 0；这不等于无需继续保护或轮换可能只存在于本地的真实凭据。
- **CONFIRMED**：.env 与 .env.example 处于忽略状态，未作为受控 Git 内容。
- **CONFIRMED**：历史修复前的本地 Git bundle 已验证可读，并保留在仓库外；它不进入 Git 或同步包。
- **待验证**：完成干净 main、删除旧远端分支、设置默认分支和最终远端回读前，不得把历史清理或仓库安全收口写为完成。

## 同步包状态

- **CONFIRMED**：allowlist、敏感扫描、SHA-256、ZIP 完整性、AppleDouble/.DS_Store 清理、latest 原子替换和 verify 路径是保留机制。
- **同步包版本**：**CONFIRMED**；V2 Manifest schema 为 2，来源分支为 main，包含 BUSINESS_STATUS 和本文。
- **同步包脚本版本**：**CONFIRMED**；以构建时 Manifest 的 `source_git.source_commit` 为准；该字段只表示生成基线，不预写随后提交的自身 commit。
- **最近本地 bundle 验证日期**：2026-08-05；V2 build、`--verify`、ZIP 解压、SHA-256、路径/秘密扫描均通过。
- **CONFIRMED**：V2 脱敏脚本已完成重新生成与验证；最终包仍须在本文件本次回填提交后再次生成，确保新会话读到同一状态。
- **规则**：manifest 的 source_commit 是生成时的 Git 基线，不是随后提交 project_sync/latest 的 commit；不得构造自我引用版本。
- **规则**：包和 manifest 只可记录跨机器可用的信息；不得包含本机绝对路径、真实排除文件清单、秘密、私人联系资料或本地 ZIP 绝对路径。

## GitHub 收口状态

| 字段 | 当前状态 |
|---|---|
| Repository | fthytwerwt-sudo/fenjiu |
| Visibility | **BLOCKED / 未确认**：GitHub CLI 认证读取超时，尚无法读取或改为 Private |
| Default branch | **CONFIRMED（远端读取）**：仍为旧临时分支；目标为干净 main |
| 最近验证远端 branch | **CONFIRMED（远端读取）**：main 已创建 |
| 最近验证远端 commit | **CONFIRMED（远端读取）**：010b24ab76cd7ee1425e2c2ee56e14caae6d06e9 |
| Pull requests | **UNKNOWN**：需要 GitHub API/CLI 认证后回读 |
| 旧临时分支 | **待清理**；必须在 main 成功成为默认分支后再删除 |

## 剩余机制收口

1. **P0**：完成 GitHub CLI 登录，读取并将仓库 visibility 改为 Private。
2. 将 GitHub 默认分支切换为 main，随后删除旧临时远端分支，并回读全部远端状态。
3. 在包含本次状态回填的 main 上重新生成同步包，并完成解压、哈希和新会话接手验证。

## 更新规则

只能以实际命令、GitHub/API 回读、脚本验证和可读取的产物更新本文。本文记录最近一次可写入的远端验证；包的 source_commit 表示生成基线，不尝试构造“文件同时记录自身提交”的不可能结构。每次新提交后，最终远端 HEAD 仍须由执行回报再次回读。
