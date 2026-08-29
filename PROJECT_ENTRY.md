# 项目统一入口｜PROJECT_ENTRY

本文件是新 ChatGPT、Codex、Work 或人工协作者的业务优先导航；它不替代原始资料，也不把模板当作合作方已确认。

## 30 秒定位

- **当前正式范围**：汾酒采用 Sales-First：`business_gates → sellable offer → controlled channel touchpoint → unified inquiry → human-led sales → order handoff → feedback`。TikTok 是候选内容触点，不是自动获准的唯一销售渠道。
- **当前阶段**：`SR-1 Sellable Offer Ready`，即供应链资料、合规、账号、收款与履约证据准备；不是已经公开销售或履约。
- **汾酒用户职责**：渠道/账号运营、内容、商品展示、客户沟通、订单转化、销售数据和市场反馈，以及最终外部执行授权。
- **海鲜用户职责（P0 2026-08-29）**：Online Acquisition & Traffic，包括线上企业发现、搜索/内容/网站/目录获客、Lead Qualification、Supplier Handoff 和基于供应链结果的渠道优化；不承担尼泊尔当地报价、样品、谈判、收款、配送或售后。
- **供应链职责**：当地合法销售与产品/食品/进口资料、SKU/规格/价格/库存、冷链、当地报价/样品/谈判、收款、订单、仓储配送、售后和财务结算；这些均为确认的责任边界，不表示资料已 READY。
- **当前最重要任务**：取得一个最小 Offer 的商品单、价格/有效期、库存/补货、主体/许可/授权、账号与认证支持、收款、配送售后及明确负责人；资料齐备后才决定渠道试点和询盘入口。
- **不自动恢复的旧范围**：没有销售证据与单独授权的 B2B 接触、全平台同时运营、Facebook/Instagram 广告、YouTube/Viber、90 天试销、自动找客或自动外联。
- **海鲜当前阶段**：供应链为 `SF-S1 IN_PROGRESS_REPORTED / NOT_READY`；用户为 `SF-U1 Online Offer Pack Ready`。旧 SF-2 混合采购闭环已被双 Workstream 取代；真实发现、联系、发布和广告仍需 Route-specific 授权。

## 必读顺序

1. 用户本轮明确输入，也就是 `P0（用户本轮明确输入）`。
2. [AGENTS.md](AGENTS.md)
3. [GPT Project 配合机制包](GPT项目资料同步包_gpt_project_mechanism_sync/00_GPT_Project上传说明_readme.md)
4. 本文件
5. [业务状态](docs/project/BUSINESS_STATUS.md)
6. [总览状态](docs/project/CURRENT_STATUS.md)
7. [事实源地图](docs/project/SOURCE_OF_TRUTH.md)
8. [范围与边界](docs/project/SCOPE_AND_BOUNDARIES.md)
9. [协作机制状态](docs/collaboration/COLLABORATION_STATUS.md)
10. 与当前任务直接相关的原始资料；不要用派生产物替代原始资料。

## 先分清可继续与不可进入的动作

- **可继续准备**：内部资料整理、供应链启动表、商品字段/上架资料设计、事实核验、合规与平台问题清单、受控草稿。
- **业务闸门阻断外部执行**：未取得当前书面证据前，不得公开发布、投放、收款、下单、承诺交期或开展真实履约。关键 `business_gates（业务闸门）` 包括 SKU、价格、库存、主体和资质、账号权限、收款、配送售后，以及指定渠道的酒类内容/广告/商品展示/消息边界；缺失时状态为 `BLOCKED`。

## 状态和交接

- 业务事实以 [BUSINESS_STATUS.md](docs/project/BUSINESS_STATUS.md) 为准。
- 协作与仓库收口事实以 [COLLABORATION_STATUS.md](docs/collaboration/COLLABORATION_STATUS.md) 为准。
- 当前摘要以 [CURRENT_STATUS.md](docs/project/CURRENT_STATUS.md) 为准；它只路由，不替代两份详细状态。
- 重要任务完成后更新状态、决策、风险、下一步和 [执行历史](docs/collaboration/EXECUTION_HISTORY.md)。

生成交接包：

    python3 scripts/build_project_sync_pack.py

把 project_sync/latest 或本地 ZIP 与 [同步包说明](docs/sync/README.md) 一并交给新会话。新会话必须先复述当前范围、阶段、职责、事实分级、阻断和完成标准，再执行。

GPT Project 配合机制包位于 `GPT项目资料同步包_gpt_project_mechanism_sync/`，用于用户手动上传到 ChatGPT GPT Project。它和 `project_sync/latest/` 不同：前者保存长期配合机制，后者保存 GitHub 项目事实交接快照。包已生成不等于用户已上传 GPT Project UI。
