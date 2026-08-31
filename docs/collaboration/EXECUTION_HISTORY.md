# 执行历史｜EXECUTION_HISTORY

## 2026-08-31｜Aidge 本地运行环境就绪（等待用户填两个 Key）

- **Goal / P0**：用户只填 `ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET`；Codex 自动建立其余 Aidge/OSS 本地配置、依赖、权限与 doctor 入口。本轮明确禁止收费 `VideoGeneration`。
- **本地私有配置**：ignored `.env` 已保留原有 DashScope Key，新增两个 `FILL_ME`、`cn-beijing`、SDK 自动 Aidge Endpoint、北京 OSS 公网 Endpoint、用户确认 Bucket 和 `video-orchestrator` prefix。`.env` 未跟踪且未进入本提交。
- **代码修复**：补上 placeholder credential 解析的 fail-closed 逻辑，并让 OSS doctor 区分 `BLOCKED_OSS_CREDENTIALS_ABSENT`、缺配置、endpoint 非法与 SDK 缺失，避免把 `FILL_ME` 误报为真实凭据。
- **当前状态**：Aidge/OSS SDK 均可 import，region/endpoint/bucket/prefix 已配置。OSS Bucket 存在且地域为北京，极小 synthetic object 的 put、30 分钟 signed GET、内容回读与 delete 全部通过。Aidge 只读 `QueryAsyncTaskResult` 以随机不存在 task ID 到达服务端并返回 `InvalidParameter`，证明 credentials/endpoint 被接受；不证明 `aidge:VideoGeneration` 权限或付费生成成功。
- **验证**：placeholder 解析与 OSS doctor 状态均按 TDD 先复现失败再修复；171 contracts、8 architecture 与完整 `make regression` 通过，SDK import/版本、Aidge SDK 自动 endpoint、OSS SDK 构造、`.env` ignore/未跟踪和 doctor 脱敏输出通过。外置盘 exFAT/noowners 将 `chmod 600` 表现为 `0700`，但 group/other 均无权限。当前 `pip check` 仍报 `grpcio 1.78.1 is not supported on this platform`，不影响本轮两个 SDK import，也未擅自升级其他依赖。
- **边界**：本轮没有调用 Aidge `VideoGeneration`、没有上传业务素材、没有修改 RAM/开通产品/充值，不改变业务状态。当前最终工程状态为 `OSS_AVAILABLE / AIDGE_PROBE_REQUIRED`。

## 2026-08-31｜Video Orchestrator 统一能力层与 Aidge 受控接入

- **Goal / P0**：把 Aidge、Wan3、HappyHorse、MiniMax、Qwen-MT、Paraformer、VideoRetalk 和 FFmpeg 收敛成 capability-first 总控；上层不暴露 Model ID。本轮要求 Aidge 正确实现、最小物理 probe 或精确外部阻断，不改变 Sales-First 业务状态。
- **实现设计**：保留 `modules/content_video` 与 P07 fake-only `VideoPort`；在 `core/application/video_orchestrator` 新增 registry/router/error/preset/runtime port，在 `adapters/video` 新增真实 provider composition，在 `apps/videoctl.py` 和 `videoctl` 提供统一命令。真实调用默认关闭，须显式费用、素材上传与 fallback/provider/max-cost 授权。
- **Provider 状态**：MiniMax Nepali TTS=`PROBE_PASSED`；VideoRetalk/Paraformer/HappyHorse=`PREVIOUSLY_TESTED`；FFmpeg=`CURRENTLY_AVAILABLE`；Wan3/Prime、Qwen-MT、MiniMax Turbo=`PROBE_REQUIRED`。Aidge `VideoGeneration` 使用官方 SDK `alibabacloud_aidge20260428==5.3.1`，SDK import/request model、1–6 图、5–15 秒、9:16、720p/1080p、`aidge:VideoGeneration` 与 5 秒 720p 约人民币 7 元均已核验。
- **Aidge 阻断**：目标仓库当前没有 `ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET` 和 private OSS endpoint/bucket；`videoctl probe-aidge --execute --approve-cost --max-cost-cny 7` 在发请求前返回 `AUTH_REQUIRED`，故付费调用数为 0、无输出媒体。不得借用其他项目密钥或自动开通/充值。
- **意外 MiniMax 调用**：代码复审为验证成本闸门，误执行 1 次 `MiniMax/speech-2.8-hd` TTS（7 个输入字符，未使用克隆声音）。公开刊例估算为人民币 `0.00245` 元，实际账单待验证；本地 `outputs/video_orchestrator/voice.mp3` 为 21,300 bytes、1.184219 秒、mono MP3，ffprobe/ffmpeg 技术验证可解码。该媒体受 Git ignore 保护，不进入提交；技术通过不等于内容试听或业务验收。
- **安全修复**：独立复审发现的本地任意文件上传、endpoint override、任意输出覆盖、付费 fallback 与 SSRF 风险已通过输入/输出根目录、媒体签名/大小、阿里 endpoint/下载主机、DNS 私网拦截、显式 upload/fallback/provider/max-cost 授权和 pipeline 累计预算修复；VideoRetalk 本地链与 Paraformer transcript wait 已补齐。最终安全复审无 Blocking/High/Medium。
- **验证**：Video Orchestrator 专项 49 项、完整 contracts 169 项、architecture 8 项通过；`make regression` 进一步通过双次 migration replay、16 regression、8 local-runtime、16 control-plane、169 contracts 与 35 ingestion。Python 编译、`git diff --check` 通过。`pip check` 仅报现有 `grpcio 1.78.1 is not supported on this platform`，依赖 CVE 数据库审计待验证。最终 path-limited stage、Lore commit、push main、remote HEAD 与核心文件 readback 由本轮执行回报收口。
- **状态边界**：这是工程能力与本地执行入口，不证明商品、素材权、Aidge 开通、视频已生成、发布、平台允许、销售或履约成立；所有媒体仍须技术 QC 和人工复审。

## 2026-08-29｜海鲜 Online Acquisition 双 Workstream 重构

- **Goal / P0**：只修改海鲜线，把用户职责从混合的当地采购/样品/成交改为 Online Acquisition、Qualified Lead、Supplier Handoff 和结果归因；供应链独立负责尼泊尔当地商品、销售、成交与履约。汾酒路线不重写。
- **事实与外部证据**：回读 `origin/main=cfb0cf6`、海鲜 execution/content、Targeting Spec 和 Source Catalog；当前 OSM/ODbL/Nominatim 仍只支持受限低频 discovery，Google Maps 名单抽取仍拒绝，Gmail/TikTok 技术能力不等于联系人处理或项目授权。
- **设计决定**：旧 SF-2 标 `SUPERSEDED`；新增 SF-S1 + SF-U0–U8、Kathmandu Valley Chinese/Hotpot First ICP、Search/Web Primary、Digital Referral fallback、Organic B2B Content later，以及 Lead Handoff/Supplier Feedback/attribution contract。
- **状态边界**：供应链“正在推进”仅为 P0 progress report，不升级任一 business gate；本轮不抓客户、不处理联系人、不发送、不发布、不投广告、不报价、不下单。
- **验证**：角色冲突、SF-U0–U8 字段、First ICP/Route 唯一性、Handoff/Feedback、Content Route、旧 SF-2 supersession、链接和本轮 diff 路径扫描均通过；汾酒 strategy 文件及共享矩阵 Fenjiu section 与基线一致。GPT Project mechanism validation、48 文件 sync-pack build/verify 通过。`make regression` 通过两次 migration replay、31 类 SQL negative constraints、8 architecture、16 regression、8 local-runtime、16 control-plane、120 contract 与 35 ingestion tests；Docker 资源已清理。
- **独立复审与修复**：初审无 Blocking/High，发现 2 项 Medium：顶层职责仍泛化“用户订单转化”，以及 SF-U3 未授权/已授权出口不闭合。已把顶层职责拆成汾酒/海鲜并限定 Scope；SF-U3 改为未授权 `internal_discovery_baseline_only / waiting_authorization` 不解锁、已授权且至少 1 Qualified Lead 才进入 SF-U4。复审结论 `APPROVE`，无剩余 Blocking/High/Medium。
- **待收口**：最终 sync-pack、path-limited stage、Lore commit、push、remote HEAD/core-file readback。

## 2026-08-28｜双业务线 Sales-First 执行化与 AI 手机质感内容设计

- **Goal / Scope**：将既有 Sales-First 总规划落为汾酒与海鲜独立的执行/内容手册、阶段闸门和 KPI；不进行发布、外联、报价、收款、订单、履约或真实 AI 视频生成。
- **事实核验**：从 `origin/main` 读取当前项目边界；视觉核验用户提供的 5 页海鲜货品单，记录 20 行产品候选、表内数量 554、重量 2,895 kg、总立方 11.2323145。此资料仅作产品候选/包装摘记，不升级为库存或冷链/食品事实。公开研究确认青花 20/30 存在多度数/容量/包装变体，故不把名称当固定尼泊尔 SKU。
- **实际产物**：新增 FJ/SF execution playbook、content playbook、双线 stage-gate/KPI matrix；补入客户问题、人工跟进、失单原因、归因、AI iPhone Natural Look、48 张内容卡与渠道/AI/自动化 gate。
- **状态边界**：所有内容卡保持 `publish_blocked_pending_business_gates`；没有生成或发布媒体，未处理客户资料，也没有外部动作。
- **验证**：`git diff --check` 通过；六份新策略文件均非空；两条线各 24 个唯一 content ID，汾酒 30 条 Hook、海鲜 B2B/B2C 各 30 条 Hook；双线关键词污染与本机绝对路径检查无命中。GPT Project mechanism validation、同步包 build/verify 均通过（46 文件）。`make regression` 通过：两次 migration replay、31 类 SQL negative constraints、8 architecture、16 regression、8 local-runtime、16 control-plane、120 contract 与 35 ingestion tests；Docker 资源已清理。
- **独立复审与修复**：复审发现同步包新增镜像未纳入最终版本、root mirror/PROJECT_CONTEXT 的相对链接失效，以及一个青花 30 来源 URL 已失效。已将 6 个镜像文件 path-limited 纳入、在同步脚本中为平铺/聚合 Markdown 按源路径重写内部链接，并将失效来源替换为当前可访问的海外商业产品页且降级其证据角色。重建后 `--verify` 通过，root mirror 与 PROJECT_CONTEXT 不再含 `../strategy`、`../project` 或 `../collaboration` 失效链接。
- **待最终收口**：path-limited stage、Lore commit、push、remote HEAD 和核心文件 readback。

## 2026-08-28｜Sales-First 项目级审计、目标架构重构与机制同步

- **目标与边界**：先以 `origin/main` 完整审计项目事实、Phase 0–8 文档和实际代码，再将北极星从“完成 AI Native Sales OS / TikTok-only”重设为“业务闸门满足后验证最小、可核验的销售闭环”。本轮只改规划/事实/机制文件；不重构业务代码，不连接真实系统，不发布、外联、报价、付款、订单或履约。
- **Git 基线**：确认工作区、仓库根目录、分支均为预期；`origin=https://github.com/fthytwerwt-sudo/fenjiu.git`，`git fetch origin` 后 `HEAD` 与 `origin/main` 同为 `f89a86f3317fdf32b9c6c498455bb76ec8d4249b`，divergence 为 `0/0`。本次最终 Git 收口证据以后续 commit/push/readback 为准。
- **审计结论**：现有 Truth Center、ingestion、workflow、审批、审计、leads/CRM/DNC、客服、内容/视频均为 synthetic/local-only 合同或 fake；`external_execution_allowed=false`，真实 provider/账号/客户/订单/履约未实现。正确资产是隔离、来源、DNC、审批、审计、人工接管与 QC；最关键缺口是可售 Offer、渠道承接、人工销售、订单交接和销售反馈。
- **外部资料核验**：官方资料显示 TikTok/Meta/Instagram/WhatsApp/Gmail 的部分技术能力存在，但不等于项目可用；TikTok 酒类广告条件严格、Meta commerce channels 不得销售酒类、WhatsApp 不得交易酒类；尼泊尔 Madira Act 是许可框架。本项目账号、许可、地域、数据处理和用户授权保持 `UNKNOWN / BLOCKED`。
- **实际改动**：新增 `docs/strategy/` 的总规划、差距/架构/阶段/渠道/指标/复用/政策矩阵；更新项目事实、决定、入口、工程索引、sync allowlist 和 GPT Project 长期机制。旧决定以 `SUPERSEDED` 保留，不删除历史。
- **状态边界**：本轮规划、文档、测试、commit 或推送不确认 SKU、价格、库存、许可、账户资格、收款、客户、订单、履约或销售成立。下一张任务为 `SR-1 / Sellable Offer Evidence Contract`。
- **验证**：`git diff --check`、两份同步脚本的 `py_compile`、战略文件非空/引用/敏感路径检查、`python3 scripts/validate_gpt_project_mechanism_sync.py --write-manifest`、`python3 scripts/build_project_sync_pack.py`、`python3 scripts/build_project_sync_pack.py --verify` 全部通过；`make regression` 通过 Compose 配置、两次 migration replay、负向 SQL 约束、8 architecture、16 regression、8 local-runtime、16 control-plane、120 contract 和 35 ingestion 测试。其余 Git commit/push/remote readback 以本轮最终执行回报为准。

此处只记录真实仓库执行，不补写没有证据的业务动作。每个实质变更、生成、验证、commit/push 或新阻断点应新增条目。

## 2026-08-23｜双业务线真实获客来源目录与 100 分评分合同修复

- **目标与边界**：只研究未来从哪里发现企业客户，形成可审计 Source Catalog（来源目录）和单业务线机器配置；不建立真实客户名单、不处理联系人、不写 CRM、不运行 crawler、不发送 Gmail。汾酒与海鲜继续隔离，汾酒产品事实、海鲜食品/冷链事实均不补猜。
- **实际研究**：逐项打开并审阅 OpenStreetMap/ODbL/Nominatim、Hotel Association Nepal、FNCCI、CNI、Liquor Association of Kathmandu、REBAN、Nepal Tourism Board、TEPC、DirectoryOfNepal、Nepal Business Directory、DFTQC/NNSW 与付费贸易情报来源的入口或条款。目录把企业发现、企业字段存储、联系人处理三项分开；Google Maps/Places、付费联系人数据、登录绕过和私人资料均列为拒绝路线。Nepali 查询词完成实际结果检验，全部降级为人工实验词，不进入自动查询词库。
- **实际改动**：新增两份人工阅读目录和三份 `source_catalogs/` 配置/说明；修正 Customer Score 为 60 + 40 的精确 100 分制，新增 Commercial Accessibility 10 分和八个合成评分验证案例；更新项目状态、决策、风险、待办与事实源，并让同步包 allowlist 收录这些可交接规范资产。
- **状态边界**：`source_catalog_ready` 只表示来源研究和配置已完成。最低限度的公司级企业发现尚未开始；联系人、真实 CRM、Gmail、酒类/食品合规、供应链事实、冷链、价格、报价、订单与履约仍未获授权或确认。

## 2026-08-23｜双业务线客户定位规范与 Codex 输入合同

- **目标与边界**：在不接触真实客户名单、联系人、CRM、邮件、价格、库存或供应链私有资料的前提下，建立未来客户发现、人工评分和 CRM 准入可引用的业务标准。汾酒和海鲜严格隔离；汾酒仍保持 TikTok 上线准备范围，真实获客与外联不因此恢复。
- **实际读取与来源**：读取仓库入口、业务/当前/事实源/范围/协作状态、海鲜隔离机制、Phase 8-RAB 规划与用户上传的 5 页《尼泊尔市场冻品2026年第一批次进货清单》。PDF 经文本提取和逐页视觉核验，识别 20 个产品行与表内 2,895 kg 合计；这些均只作产品族输入，不是库存或可售事实。外部只核验国家统计、旅游统计、DFTQC 食品进口/登记资料入口及 Google Maps 条款。
- **实际改动**：新增 `docs/implementation/NEPAL_CUSTOMER_TARGETING_SPECIFICATION.md`；更新 CURRENT_STATUS、SOURCE_OF_TRUTH、DECISIONS、NEXT_ACTIONS、OPEN_QUESTIONS 与 RISKS_AND_BLOCKERS，使其链接该内部规范与新增真实获客治理阻断。
- **验证与卫生检查**：文档结构、字段、引用、绝对路径/敏感词、业务线隔离与 `git diff --check` 由本轮最终验证命令确认。未新增依赖、代码、真实业务数据、联系人、密钥或外部动作；PDF 渲染仅留在受 Git 忽略保护的临时目录。
- **状态边界**：本条只确认内部规范与治理记录已写入仓库。真实来源采集、联系人处理、真实 CRM 写入、Gmail、酒类/食品合规、供应链产品事实、冷链、报价、订单与履约仍为 `BLOCKED`，必须由后续独立授权和证据解除。

## 2026-08-10｜Phase 5–7 合成工程合同完成与 Phase 8 资料闸门（controller integration）

- **目标与边界**：清理已实现但未集成的 P07-02、P05-03，并按依赖推进 P06-03、P07-03；全程只处理 synthetic（合成）数据与本地合同。未读取真实供应链资料、未创建真实联系人或客户、未连接生产服务，`external_execution_allowed = false（外部执行允许 = 否）`。
- **集成结果**：P07-02 经规格与质量复审后集成至 `73b1a01`；P05-03 经规格检查与独立质量复审后集成至 `37b19ed`；P06-03 经规格与质量复审后集成至 `bbc742d`；P07-03 在包含 P06-03 的最新 `main` 上完成控制器规格/质量检查后集成至 `ae84e18`。P05-03 保持 zero-send（零发送）草稿；P06-03 保持 receive-only fake inbox（只接收模拟收件箱）和审计式人工接管；P07-03 保持 QC（质量检查）/人审/internal export reference（内部导出引用），`external_publish_attempts=0`。
- **验证与卫生检查**：各任务均在干净 task worktree（任务工作目录）完成 repository hygiene check（仓库卫生检查）、configuration validation（配置验证）、data safety check（数据安全检查）、机制验证与任务回归；无依赖变化。最终 `main` 的 `make regression` 通过两次 migration replay（迁移重放）、P02/P05/P06 负向约束、8 项 architecture（架构）、16 项 regression（回归）、8 项 local-runtime（本地运行）、16 项 control-plane（控制面）、120 项 contracts（合同）和 35 项 ingestion（导入）测试。同步包重新生成后，`--verify` 通过解压、SHA-256、路径和敏感内容检查。
- **Git 证据**：`origin/main` 已逐次回读 `73b1a01cad82e01077b452a8486dc8211b567229`、`37b19ed4bffff3b9d7a0341c6e756f71ce6ff6e4`、`bbc742d22bc0f19f6b2cbe8b7be7abc058b7f197` 和 `ae84e183be38da62d17c8567569f75206ddb35f1`；本条状态回填将作为其后的独立提交推送并再次回读。未使用 force push（强制推送），未使用 `git add .`。
- **状态边界**：Phase 5、Phase 6、Phase 7 的工程任务已完成，但不表示 business_external_ready（外部业务就绪）。P08-01 虽已满足工程依赖，仍因未提供当前、获授权的真实 SKU、价格、库存、授权、资质和履约资料而为 `BLOCKED / real_supplier_data_missing（阻断 / 缺少真实供应链资料）`。GitHub visibility（可见性）尚未认证回读且默认分支仍非 `main`，为独立仓库治理待办。

## 2026-08-09｜P05-02 合成线索、CRM、DNC 与迁移序列协调（controller integration）

- **目标与边界**：只建立 local-only/synthetic 的已审查线索→CRM、DNC、同意/来源、去重/人工合并与受控导出合同；不得建立真实联系人、外联、发送、生产 CRM 或任何外部动作。
- **控制器审查与修复**：并行 P06-01 已占用 `0003`，故任务分支非破坏性合并当前 main 后将自身迁移顺延为 `0004`，保留 P06 的隐私迁移。规格审查发现回归脚本未实际断言 `0004` 已登记，执行线程先以 RED（失败测试）复现，再改为精确有序断言 `0001/0002/0003/0004` 且各一次；复审通过。DNC、来源/同意、跨范围、外部开关和导出标识均保持 fail closed（默认拒绝）。
- **验证**：控制器复验 29 项 P05/P06/P07 相邻合同、16 项策略/审计、11 项工作流、8 项架构、双次迁移重放与 P02/P05/P06 负向约束、完整 `make regression`（91 项合同、35 项导入）、机制验证、编译和 diff 均通过。
- **Git 证据**：任务基线合并提交 `4ddee7b` 与修复提交 `35d6e1f` 已 push；控制器快进集成并将 `main` push/readback 至 `35d6e1f12ad6ed2e4bfa86a2c9f70463f9dcacb9`。远端 P05 合同、`0004` 迁移、专项测试与报告 blob（文件对象）已回读。
- **状态边界**：仅为 Phase 5/P05-02 工程完成，不代表 Phase 5 整体完成；不改变 BUSINESS_STATUS、真实联系人、外联、发送、真实 CRM、SKU/价格/库存/资质/账号/收款/履约或任何 external flag（外部动作开关）。

## 2026-08-09｜P06-01 会话隐私、未知范围隔离与人工转交（controller integration）

- **目标与边界**：只建立 local-only/synthetic 的客服会话、消息、意图、草稿、人工转交与未知范围隔离合同；不得接渠道、模型、发送器、真实客户或外部动作。
- **控制器审查与修复**：规格审查先发现 unknown scope（未知范围）可能被写入需要范围字段的转交记录，故改为独立 quarantine（隔离）记录；质量审查随后发现已知范围输入的原始外部标识可能进入摘要、审计和迁移，故改为 deterministic opaque reference（确定性不透明引用）。复审证明未知范围不创建范围会话/消息/转交，已知范围的回放仍幂等，原始外部标识不会暴露。
- **验证**：6 项客服专项、8 项内容视频、8 项来源、9 项审计、7 项策略、11 项工作流、8 项架构、`make migration-test` 的双次迁移重放与负向约束、完整 `make regression`（84 项合同、35 项导入）、机制验证、编译与 diff 均通过。
- **Git 证据**：任务提交 `bb3334b`、`28902e9` 与 `4d3f57e` 已 push；控制器快进集成并将 `main` push/readback 至 `4d3f57e75bcae4bbe5c9df3ecd27e6139a8c0928`。远端客服合同、迁移、专项测试和 P06-01 报告 blob（文件对象）已回读。
- **状态边界**：仅为 Phase 6/P06-01 工程完成，不代表 Phase 6 整体完成；不改变 BUSINESS_STATUS、真实客户资料、身份、渠道、模型、发送、SKU/价格/库存/资质/账号/收款/履约或任何 external flag（外部动作开关）。

## 2026-08-09｜P07-01 内容、素材与政策事实锁（controller integration）

- **目标与边界**：只建立 local-only/synthetic 的 content brief（内容简报）、asset（素材）和 policy lock（政策锁）合同；不得调用供应商、生成视频、写入媒体、导出或发布。
- **控制器审查与集成**：规格与质量复审均确认内容事实、素材引用与策略引用必须同范围、同版本并保持有效，任一缺失、过期、撤销、冲突或 external flag（外部动作开关）均拒绝。任务分支与已接受的 P06-01 并行，控制器采用不改写任务分支历史的合并提交，确认 P06 隐私合同与 P05 来源政策均未回退。
- **验证**：8 项内容视频、6 项客服、8 项来源、9 项审计、7 项策略、11 项工作流、8 项架构、双次迁移重放与负向约束、完整 `make regression`（84 项合同、35 项导入）、机制验证、编译与 diff 均通过。
- **Git 证据**：任务提交 `c713e6d` 与基线保留提交 `0954b7e` 已 push；控制器合并提交 `f02360d7e386f61b6b39cf2d8f3051e59fe21bc4` 已推送并回读。远端内容合同、合成策略 fixture（测试数据）、专项测试和 P07-01 报告 blob 已回读。
- **状态边界**：仅为 Phase 7/P07-01 工程完成，不代表 Phase 7 整体完成；不改变 BUSINESS_STATUS、真实素材、供应商、生成服务、导出、发布、SKU/价格/库存/资质/账号/收款/履约或任何 external flag。

## 2026-08-09｜P05-01 来源政策与零网络模拟抓取（controller integration）

- **目标与边界**：只建立 local-only/synthetic 的 source policy（来源政策）、snapshot/evidence/hash（快照/证据/哈希）和 fake CrawlPort（模拟抓取端口）；不得访问真实网站、读取研究联系人、建立 lead/contact/CRM 或外联。
- **实际改动**：新增来源政策、合成快照、证据引用、公开字段候选和内存 fake port，以及 8 项 P05-01 专项测试与合成来源 fixture。任何 real network（真实网络）均不存在，`external_fetch_count=0`；审计只记录安全哈希与稳定代码。
- **控制器审查与修复**：规格审查发现 `allowed_fields` 可允许 `contact_email` 等联系字段进入候选，虽然值已哈希仍会突破“公开页面不是可联系授权”的边界。执行线程先以 RED/GREEN（先失败/后通过）修复：政策构造拒绝联系词根，fetch 再验证，evidence/candidate 也拒绝，fake port 对 forged policy（伪造政策）二次拒绝并输出脱敏审计。最终规格与质量复审均为 `APPROVE`。
- **验证**：干净 task worktree 的 P00 default/`--all-files`、8 项来源、9 项审计、7 项策略、11 项 workflow、8 项 architecture、完整 `make regression`（两次 migration replay、16 类 SQL negative constraints）、机制验证、compile 与 diff 均通过。控制器在外置盘 root 复验来源/审计/策略/工作流/架构、完整 `make regression`、机制验证、diff 和排除 AppleDouble `._*` 的编译；root 不运行 P00 default/`--all-files`，因为既有用户文件会使该模式失真。
- **Git 证据**：任务提交 `f9189db` 与修复提交 `f034857` 均已 push；控制器 fast-forward 集成并将 `main` push/readback 至 `f034857d5ec5715c2677e06d8add6338f65f50e1`。远端来源政策、fake port、专项测试和 P05-01 报告 blob 已从 `origin/main` 回读。
- **状态边界**：仅为 Phase 5/P05-01 工程完成，不代表 Phase 5 整体完成；不改变 BUSINESS_STATUS、真实网站访问、线索/联系人/CRM/外联授权、SKU/价格/库存/资质/账号/收款/履约或任何 external flag（外部动作开关）。

## 2026-08-09｜P04-03 审计、指标、重试与死信队列（controller integration）

- **目标与边界**：只建立 local-only/synthetic/value-free 的追加式 audit（审计）、retry/DLQ/manual（重试/死信/人工）分类和脱敏 metrics/log（指标/日志）合同；不得接数据库、broker、监控 SaaS、真实资料或任何外部动作。
- **实际改动**：新增 audit chain（审计链）、staged effect（暂存效果）协议、retry classification（重试分类）、DLQ 记录和 safe metrics（安全指标）模块，以及 9 项 P04-03 专项测试与工程报告。审计 metadata 只允许安全标识符/代码/布尔值，命令与效果只以 correlation、scope、版本和安全引用追踪。
- **控制器审查与修复**：规格审查先发现 success audit 写入失败可让 mutation 已发生而无成功审计；修复为 staged effect 在成功审计后才提交，失败即回滚。质量审查继而发现 `commit()` 失败会在不可篡改的 `command_succeeded` 后留下假成功；修复为 best-effort rollback 并追加 `command_commit_failed`，即使 rollback 再失败也保留 `manual_required=true` 的安全失败事件。最终规格与质量复审均为 `APPROVE`。
- **验证**：干净 task worktree 的 P00 default/`--all-files`、9 项审计、7 项策略、11 项 workflow、8 项 architecture、完整 `make regression`（两次 migration replay、16 类 SQL negative constraints）、机制验证、compile 与 diff 均通过。控制器在外置盘 root 复验审计/策略/工作流/架构、完整 `make regression`、机制验证、diff 和排除 AppleDouble `._*` 的编译；root 不运行 P00 default/`--all-files`，因为既有用户文件会使该模式失真。
- **Git 证据**：任务提交 `8554beb`、`fc86a43` 与 `6cf2033` 均已 push；控制器 fast-forward 集成并将 `main` push/readback 至 `6cf2033b0376add9fabb6487d818d00f8a4805d1`。远端审计、重试、指标、专项测试和 P04-03 报告 blob 已从 `origin/main` 回读。
- **状态边界**：Phase 4 仅为工程完成；不改变 BUSINESS_STATUS、真实身份/权限、SKU/价格/库存/资质/账号/收款/履约、生产审计/队列/监控/数据库或任何 external flag（外部动作开关）。

## 2026-08-09｜P04-02 角色、审批与动作策略（controller integration）

- **目标与边界**：只建立 stdlib/local-only/synthetic 的最小角色/动作矩阵、追加式审批与执行前复核合同；不得认证真实身份、读取真实业务资料、授权外部执行或将审批合同写成真实业务权限。
- **实际改动**：新增 `core/security/action_policy.py`、安全模块出口、7 项 P04-02 contract tests 与工程报告。策略同时复核角色/范围、数据状态、事实时效、证据、功能开关、DNC/同意、环境、审批状态与 correlation；外部发送、发布、报价、支付、订单、退款和库存写入一律策略拒绝。
- **控制器审查与修复**：规格审查发现执行前复核未将获批请求绑定到 exact `subject_version`，以及同一幂等键未涵盖证据、时效、开关、DNC/同意和环境等审批语义。执行线程先以 RED/GREEN（先失败/后通过）回归修复；复审证明版本不一致返回 `approval_subject_version_mismatch` 且 `external_execution_attempted=false`，任一语义变更返回 `idempotency_conflict`。质量审查未发现公共接口绕过、敏感输出或追加式决定回归。
- **验证**：干净 task worktree 的 P00 default/`--all-files`、7 项策略专项、11 项 workflow、8 项 architecture、完整 `make regression`（两次 migration replay、16 类 SQL negative constraints）、机制验证、compile 与 diff 均通过。控制器在外置盘 root 复验策略/工作流/架构、完整 `make regression`、机制验证、diff 和排除 AppleDouble `._*` 的编译；root 不运行 P00 default/`--all-files`，因为既有用户文件会使该模式失真。
- **Git 证据**：任务提交 `fe492f1` 与修复提交 `fd727fd` 均已 push；控制器 fast-forward 集成并将 `main` push/readback 至 `fd727fd0a74068edfa5511a18f878c312c062b6c`。远端安全模块、策略专项测试与 P04-02 报告 blob 已从 `origin/main` 回读。
- **状态边界**：仅为 Phase 4/P04-02 工程完成，不代表 Phase 4 整体完成；不改变 BUSINESS_STATUS、真实身份/权限、SKU/价格/库存/资质/账号/收款/履约、生产审计/队列/数据库或任何 external flag（外部动作开关）。

## 2026-08-09｜P04-01 工作流状态、检查点与恢复（controller integration）

- **目标与边界**：只建立 stdlib/local-only/synthetic/value-free 的 workflow run（工作流运行）、checkpoint（检查点）、idempotency（幂等）、pause/resume（暂停/恢复）、retry/DLQ（重试/死信队列）与 manual queue（人工队列）合同；不得让 workflow 拥有业务真值、真实审批、外部 adapter（适配器）或外部动作。
- **实际改动**：新增 local simple runner（本地简易运行器）、仅接收运行/检查点引用的 `WorkflowQueuePort`（工作流队列端口）、工作流专项测试与 P04-01 工程报告。checkpoint 只允许标识符、哈希、布尔/整数和安全引用；外部效果直接 policy denied（策略拒绝），未知效果进入人工队列，LangGraph 仅做未安装即 deferred（暂缓）的本地探测。
- **控制器审查与修复**：规格审查发现终态或人工队列 run 可被 `approve()` 回流并再次恢复，已限定仅 `waiting_for_approval` 可批准。质量审查随后发现公开 store 写面可绕过审批事件或伪造终态重开；已关闭公开写 mutator（写入方法），runner 使用受控内部写面，且内部保存拒绝终态回流。两轮修复均先以 RED/ GREEN（先失败/后通过）专项回归复现，最终规格和质量复审均为 `APPROVE`。
- **验证**：任务干净 worktree 的 P00 default/`--all-files`、11 项 workflow、8 项 architecture、完整 `make regression`（两次 migration replay、16 类 SQL negative constraints）、mechanism validation、compile 与 diff 均通过。控制器在外置盘 root 复验 11 项 workflow、8 项 architecture、完整 `make regression`、机制验证、diff 和排除 AppleDouble `._*` 的编译；root 不运行 P00 default/`--all-files`，因为既有用户文件会使该模式失真。
- **Git 证据**：任务分支三笔提交 `d2fbd91`、`618303d`、`d2805b2` 均已 push；控制器 fast-forward 集成并将 `main` push/readback 至 `d2805b293cbb71f7c5898ad0c611d863fb87e4b7`。远端 `runner.py`、工作流专项测试、P04-01 报告和 application port 的 SHA-256 与本地一致。
- **状态边界**：仅为 Phase 4/P04-01 工程完成，不代表 Phase 4 整体完成；不改变 BUSINESS_STATUS、真实 SKU/价格/库存/资质/账号/收款/履约、真实 actor/RBAC、生产队列/工作流框架、业务真值或任何 external flag（外部动作开关）。

## 2026-08-08｜P03-03 审批、隔离的合成发布与内部刷新（controller integration）

- **目标与边界**：只完成 stdlib/local-only/synthetic/value-free 的 candidate→review→human decision→isolated approved synthetic version→supersede/revoke→internal invalidation 合同；不得把 P03 synthetic fixture 提升为 P02 `DataState.APPROVED` current truth，不读取真实资料或实现外部动作。
- **实际改动**：新增 `modules/ingestion/approval.py`、P03-03 专项测试和工程报告；审批请求、人工决定、版本、刷新和审计均保留 source/job/result/staging、profile/report、actor、时间、evidence、policy、version 与 correlation。只允许 current approved synthetic version 被内部读取；candidate、rejected/revised/expired/conflict/superseded/revoked 均不可读。刷新仅为未来 customer_service/content_video/crm 的内部失效通知合同。
- **控制器审查与修复**：初版先后补齐 correlation mismatch 拒绝与 `EXPIRED` append-only 审计状态；独立规格审查再发现 current read 把一次性 correlation 作为业务 series key，控制器要求改为 tenant/project/business-line 的私有逻辑业务范围键，并补同业务范围新 correlation 可读、跨租户/项目/业务线不可读、revoke 后不可读回归。两轮最终只读审查结论为 `APPROVE` 与无阻断评论。
- **验证**：任务干净 worktree 的 P00 default/`--all-files`、专项 9 项、ingestion 35 项、完整 `make regression`（两次 migration replay、16 类 SQL negative constraints）、mechanism validation 与编译/diff 均通过。控制器在外置盘 root 复验专项、ingestion、完整 `make regression`、机制验证、diff 和排除 AppleDouble `._*` 的编译；root 不运行 P00 default/`--all-files`，因为既有用户文件会使该模式失真。
- **Git 证据**：任务分支三笔提交 `1911808`、`9682483`、`5d2c429` 均已 push；控制器 fast-forward 集成并将 `main` push/readback 至 `5d2c429bd253344ce3c2a3a30a31315f4a81f177`。远端 `approval.py`、专项测试和 P03-03 报告 SHA-256 与本地一致。
- **状态边界**：仅为 Phase 3/P03-03 工程完成，不代表 Phase 3 整体完成；不改变 BUSINESS_STATUS、真实 SKU/价格/库存/资质/账号/收款/履约、真实 approval actor/RBAC/RLS、P02 current truth、CRM/客服/内容视频实现或任何 external flag。

## 2026-08-06｜P03-02 profile replay provenance HIGH 与 lifecycle MEDIUM repair（task branch）

- **控制器发现**：初始 P03-02 `MappingProfileRegistry.register_profile_change` 只检查 profile ID/version、run fingerprints 与 diff，未证明 current report 由传入完整 profile 生成；合法 forged v2 可改变 transforms 且仍借用 canonical report/proof 被接受，故 task branch 暂不接受或集成。
- **独立 reviewer 发现**：`MappingEvidence.validate()` 仅校验 scope/IDs/locator；调用方以公开 P03-01 runtime API 组装 lineage 一致、但 `source_file.disposition=QUARANTINED` 或 job/candidate 非 `STAGED` 的对象时，engine 仍返回 mapped candidate，故同一 task branch 继续不接受或集成。
- **实际修复**：`MappingReport` 新增 engine-constructed `profile_fingerprint`；registry 写入前验证 registered prior profile/previous report 与传入 current profile/current report 各自的完整 fingerprint 和 scope，再验证 replay diff。差异 profile 的 transforms、target contract、rules、source signature 或 scope 均返回 `profile_report_provenance_mismatch`，写入前停止；canonical replay/diff 仍可登记。
- **实际修复**：`MappingEvidence.validate()` 在 mapping 前使用实际 `SourceDisposition.REGISTERED` 与 `IngestionWorkflowState.STAGED` enum；source quarantine、non-staged job 或 adversarial non-staged candidate 都统一抛出 `lineage_invalid`，engine 因而只返回 `blocked_manual` / 零 candidate。
- **验证**：先新增 forged-profile 与三条 lifecycle regression，修复前均复现失败；修复后 focused mapping 12 项、ingestion 26 项、`make regression`（两次 migration replay、16 类 SQL negative、118 项 Python suites）、P00 default/all-files、mechanism validation、compile/shell/diff 均通过，isolated Docker resources 无残留。
- **Git 证据**：repair 代码提交 `969a2114c83350a606c917f4c9b8e11c72ca56f0` 已 push/readback；控制器在最终独立复审 `APPROVE` 后按提交顺序集成，并将 `main` push/readback 至 `355483121580c0205a43e59078eba8c29d719d93`。远端 `mapping.py` SHA-256 为 `5e581650a1312228b253eb0cc06dd923b408334cc9e61b54db015bf198cabff0`，mapping test SHA-256 为 `c55c4d722b76ade087eb034a3ebf4ca7610bb989c0d22550571b73c1751b0f8e`。
- **状态边界**：P03-02 已为远端 `main` 工程完成；未改变业务状态、approved truth、真实资料或任何 external flag。P03-03 仅可在含本次状态回填的最新远端 `main` 新建干净 worktree。

## 2026-08-06｜P03-02 字段 mapping、清洗与数据质量（task branch）

- **目标**：只建立 stdlib/local-only/synthetic/value-free 的 versioned mapping profile、deterministic normalization fingerprint、missing/conflict/expiry/duplicate quality report 和 profile change replay/diff proof；不读取真实文件、不写 approved truth 或外部动作。
- **实际改动**：新增 `modules/ingestion/mapping.py` 与 10 项 mapping contract probes；只消费 P03-01 source/job/result/staging chain，candidate 保留 scope、source/job/result/staging IDs、locator、content hash、rule/profile lineage。strict profile schema 拒绝 implicit/generic mapping，unknown unit/currency/date/language、missing、conflict、duplicate、freshness、scope/lineage/signature 以 stable code fail closed。新增一个 synthetic mapping fixture，并以 `.gitignore` 精确 allowlist，其他 ingestion fixtures 继续被忽略。
- **审查与验证**：test-first 从缺少 `modules.ingestion.mapping` 的 ImportError 开始；fixture allowlist test 首次正确发现新 fixture 被忽略。自审发现 P00 all-files scan 将测试中的字面绝对路径检测样例视作违规，改为运行时构造后保持同一断言且两种扫描通过。focused mapping 10 项、ingestion 24 项、`make regression`（两次 migration replay、16 类 SQL negative、116 项 Python suites）、P00 default/all-files、mechanism validation、compile/shell/diff 均通过。
- **Git 证据**：基线为 `origin/main` `f92612bf03b5ac740e52d1d56e99f9959369b9fb`，状态回填基线 `535857f376765b16c056049e3c9ae86a348fee64`；任务代码提交 `a219463108ca3cf098920d57d17a6b7d8657b01f` 已 push，并从远端同名分支 readback。`main` 仍为 `535857f376765b16c056049e3c9ae86a348fee64`，尚待控制器集成。
- **状态边界**：仅为 task-branch local engineering `PARTIAL`；业务状态、business gates、真实资料、approved truth、生产 storage/database/auth/RBAC/RLS 与所有 external flags 均不变化。

## 2026-08-06｜P03-01 原始登记、隔离存储与 extraction ports

- **目标**：只建立 stdlib/local-only/synthetic 的 source registration、private relative/reference locator、hash/idempotency、quarantine、type-specific fake extraction 和 fixture staging；不读取真实供应链资料、不接 production、不写真值或外部动作。
- **实际改动**：新增 source/job/result/candidate/failure 合同、七类 fake ports、全批次原子 staging store、synthetic source profile 和 14 项 ingestion tests；workflow staging 仍保持 `data_state=fixture`。runtime 不暴露单条 result/candidate mutator，批量入口强制一对一完整性；unknown MIME、oversize/empty、storage/folder traversal、unlocated field、parse/OCR、cross-scope、replay mismatch、secret-like metadata、real/external flags 全部 stable-code fail closed。
- **审查与验证**：test-first 从缺失 adapter ImportError 开始；自审修复 partial write、failure rerun、lineage 与 fixture allowlist。独立 reviewer 第一轮发现 secret metadata retention HIGH 和 locator alias idempotency MEDIUM，修复后 `APPROVE`。控制器再发现 runtime 单条 staging atomicity bypass HIGH；本次移除单条 mutator、拒绝 partial/duplicate/mismatched batch，原 reviewer 专项只读复核为 0 findings / `APPROVE`。外置盘 AppleDouble sidecar 使 P03 静态 AST 审计误读非 UTF-8 元数据；控制器将源码枚举限为非 `._*`，未删除用户文件。最终 `make regression` 通过 106 项 Python tests、两次 migration replay与 16 类 SQL 负例；mechanism、compile/shell/diff、Docker cleanup 均通过。
- **Git 证据**：精确任务基线为远端 `main` `bce35a01fa7c13cce797069198ce71dcf29ea2dc`；任务分支修复提交 `e17196e06380827224a1463f01b53a9975382f22` 已 push。控制器按提交顺序集成并将 P03-01 工程代码 push/readback 至远端 `main` `f92612bf03b5ac740e52d1d56e99f9959369b9fb`；本地 `HEAD`、`origin/main` 与 `ls-remote` 一致，core-file SHA-256 已再次回读。本任务未生成 sync archive。
- **状态边界**：P03-01 已为远端 `main` 工程完成；P03-02 仅可从包含本次状态回填的最新远端 `main` 新建干净 worktree。业务状态、business gates、approved truth、production auth/RBAC/RLS、真实资料和所有 external flags 不变化。

## 2026-08-06｜P02-03 业务线隔离、fixture 防护与合同测试

- **目标**：只把 tenant/project/business-line、fixture production separation、sensitivity/flags、approved/fresh/no-conflict truth consumer 与 denial audit 锁进 local repository/command contracts；不实现真实资料、production connection 或外部 adapter。
- **实际改动**：新增 sealed policy-issued repository grant、fixed local sensitivity、scoped `TruthConsumerCommand`、exact current read 与 payload-free immutable audit；runtime probes 已移至 tests-only harness，guarded current 在返回 truth 前强制 success audit。最新修复把 `actor_ref` 纳入 policy issuance、grant field/signature/validation；repository 删除独立 actor 参数且只记录 validated grant actor。adversarial tests 覆盖 scope/fixture/state/sensitivity/flags、grant tamper/reuse/forgery、fake verifier/audit recorder、direct read/audit enforcement 与 actor attribution replacement。
- **审查与验证**：控制器和独立 reviewer 先后复现 runtime helper direct truth read、real-policy direct current audit bypass 与合法 grant 的 actor attribution replacement（均为 HIGH）。依次移除 helper、下沉 mandatory audit、绑定 actor 到 signed grant 后，最终 actor-binding 专项独立复审 0 findings / `APPROVE`。最终 `make regression` 通过 92 项 Python tests、两次 migration replay 和 16 类 SQL 负例；P00 default/all-files、mechanism validation、compile/shell/diff 与 Docker cleanup 通过。
- **Git 证据**：从远端 main `6d247b0613b517ff4474095abece2f64331a40a8` 新建干净 worktree；任务分支代码提交 `3341042c51a83d0eeac9abd91b1b01a3e07e2551` 已 push 并回读。控制器在 review 通过后逐笔集成六笔任务提交，并将 `main` push/readback 至 `451843601a1a610e50bfbd9794f437b5781f1401`；四份核心代码/测试文件从远端读取 SHA-256 一致。default branch 仍为旧协作分支，visibility 因 GitHub API 连接失败保持 `UNKNOWN/BLOCKED`。
- **状态边界**：Phase 2 engineering contracts 已在 `main`；P03-01 可在新干净 worktree 单卡开始。业务状态、业务闸门和所有 external flags 不变化；production auth/RBAC/RLS、真实资料与外部执行仍阻断。

## 2026-08-06｜P02-02 真值实体、版本与状态机

- **目标**：只以 value-free contract probes 建立 product/SKU/price/inventory/delivery/compliance/asset/approved_fact/forbidden expression 的 candidate/version/expiry/conflict/supersede 与 current-read 防护；不实现真实资料、parser、UI、adapter 或外部连接。
- **实际改动**：新增九类 truth entity enum、payload/source/version/parent/diff/effective-window/approval evidence 合同、append-only in-memory repository、明确状态图、`0002` PostgreSQL table/trigger/current view、27 项 truth contract tests 和扩展后的 migration negative suite。fixture/mock 不可提升，candidate/expired/blocked/conflict/superseded 不可作为 current truth；approved 必须同 scope 且 source/version/approval evidence 完整。
- **自审与验证**：自审统一 Python/SQL 的 `parent_version_id=data_version_id` 语义，并将 transition 和 update/delete 拒绝下沉到 PostgreSQL trigger。独立 code review 进一步发现 terminal root 可经 `conflict → approved` 绕过 staging ancestry，已在 Python repository、SQL CHECK/trigger 使用同一 root allowlist 修复，并新增四类非法 root 与 conflict-root child 负例。控制器和原 reviewer 二次复核后，完整 `make regression` 通过 73 项 Python tests、两次 migration replay 与 16 类 SQL 负例；P00 两种扫描、mechanism validation、diff/shell check 和 scoped Docker cleanup 均通过。P02-02 两笔工程提交已推送并从远端 `main` 回读为 `0ba7f0575fdfe2906455c5b6301ac71c8872e727`。
- **状态边界**：本条只完成 value-free local truth contract/state/read 防护；业务事实和所有外部 flags 不变化。RLS、authenticated approval/RBAC、production repository/connection、真实资料和远端 CI 仍未完成；P02-03 只能在新的干净 task worktree 中继续。

## 2026-08-06｜P02-01 scope contracts、migration 与 synthetic isolation 基线

- **目标**：只建立 local PostgreSQL schema、stdlib metadata contracts 与 synthetic fixture 防护，为后续 truth model 提供 scope/source/version/lineage 基础；不导入真实资料或开放外部能力。
- **实际改动**：新增 scope/source/version/state/sensitivity typed contracts、`0001_scope_contracts.sql`、synthetic-only metadata fixture、PostgreSQL compound FK/check constraints、migration replay/negative test 与 P02-01 报告。所有 scoped metadata 显式记录 tenant/project/business-line/source/version/state/sensitivity；schema 层拒绝跨业务线 lineage、synthetic→approved、fixture external execution 和任意 `external_execution_allowed=true`。
- **审查与验证**：P02-01 初审发现 database replay/negative constraints 未进入默认回归；已将 `make migration-test` 变为 Docker/Compose/daemon 缺失即非零失败的自包含隔离 PostgreSQL runner，并由 `make regression` 强制调用。控制器和独立复核均确认两次 migration replay、五类 SQL 负例、8 architecture、14 regression、8 local-runtime、16 control-plane、8 contracts（共 54 项 Python 测试）、P00 default/all-files scan 与 `git diff --check` 通过；临时 Compose containers/volumes 为零残留。P02-01 代码已推送并从远端 `main` 回读为 `b08722a703f37a0cfcce0c928fec8c01c4596357`。
- **状态边界**：仅完成 synthetic local schema/contract 防护；RLS、加密、retention、法域、真实 scope、ORM/driver、production connection、真实业务资料、审批和远端 CI 均未完成。SKU、价格、库存、资质、账号、收款、履约、合规、公开发布和销售没有新增确认，所有外部 flags 继续为 false。

## 2026-08-06｜P01-03 fail-closed config、readiness 与脱敏日志控制面

- **目标**：建立不读取环境/文件/secret reference 的 typed settings、不可提权 flags、liveness/readiness 以及不泄露文本/路径/secret 的基础 JSON log 合同。
- **实际改动**：新增 static `ControlPlaneSettings`、`FeatureFlagPort`、11 个敏感 action flag、`/live` / `/ready`、correlation-aware JSON logger 与 control-plane 测试。liveness 只报告 local control plane；因没有 broker/provider/real configuration，readiness 固定 `not_ready` / HTTP 503。日志只允许严格 identifier/code、数字和布尔值；其他自由文本及 URL/DSN/Cookie/secret/path 均 `[REDACTED]`。
- **审查与验证**：控制器和独立 code review 发现中性 metadata key 可泄露短文本，已以 allowlist 式字符串策略修复并补 2 项负向测试。最终在干净 task worktree 通过 8 项 architecture、14 项 regression、8 项 local-runtime、16 项 control-plane、P00 默认/全量扫描和 `git diff --check`；完整 local Docker lifecycle 保持 no-op / readiness reject，且容器清理完成。P01-03 四个任务提交已合入 `main`，代码远端回读为 `915d6116f114e3cea0d6bc8032fac2bdee4f3e15`。
- **状态边界**：本条只完成 local control plane，既不启用 broker/provider/远端 CI，也不确认 SKU、价格、库存、账号、资质、收款、履约、合规、公开发布或销售。所有业务外部 flags 继续为 false。

## 2026-08-06｜P01-02 local-only runtime、Make 入口与多 worktree Compose 隔离

- **目标**：只建立可复现的本地工程运行底座，不连接应用数据库、不读取 `.env`、不导入真实资料、不调用外部 HTTP 或任何业务外部动作。
- **实际改动**：新增固定镜像的 Docker Compose、stdlib-only API/admin loopback health endpoint、worker idle/health/no-op entrypoint、`.env.example` placeholder、Make 入口与 local-runtime 测试。Compose 无 host `ports`，代码挂载只读；`COMPOSE_PROJECT_NAME` 从 worktree 绝对路径派生，避免不同 Codex worktree 共享容器、网络或 volumes。
- **审查与验证**：控制器与独立审查先后收紧任意 healthcheck URL、嵌套 `.env.example` allowlist、Compose 静态 render 覆盖及固定 Compose project name。最终在干净 task worktree 通过 `make regression`（8 architecture、14 regression、8 local-runtime）、P00 默认/全量扫描、`git diff --check` 和完整 `make dev-up → health → migrate → load-fixtures → dev-down`；本地生命周期结束后无该 project 的残留容器。P01-02 三个任务提交已合入 `main`，代码远端回读为 `c2e9b1ce2f8109ec255e184d70331840a4da1651`。
- **已知阻断**：尝试提交仅做静态验证的 GitHub Actions workflow 时，被远端以当前凭据缺少 `workflow` scope 拒绝；因此远端 CI 未启用，本地静态验证不等于 GitHub CI。
- **状态边界**：所有业务外部 flags 继续为 false；Docker 拉取仅用于固定 local-runtime 镜像验证，不表示对外业务执行。P01-03 仍待新建干净 worktree 执行；SKU、价格、库存、资质、账号、收款、履约、平台合规和真实销售仍无新增确认。

## 2026-08-06｜P01-01 模块化单体 skeleton 与导入边界

- **目标**：只建立可 import、可测试的 Python skeleton，不实现产品、CRM、客服、数据库、网络或任何外部 adapter。
- **实际改动**：新增 apps/core/modules/adapters/workflows 的空包、模块 ownership README、typed scope/error/port 占位、synthetic-only fixture metadata、迁移占位与 architecture tests；`.gitignore` 仅放行 P01 必需源码及两份 fixture 文件。
- **审查与验证**：控制器发现并修复了 committed diff 尾部空白、相对导入可绕过 application/security 边界、fixtures allowlist 过宽及 AppleDouble 元数据导致边界测试解码失败四项问题。最终在干净 task worktree 通过 `compileall`、8 项 architecture tests、12 项 P00 回归以及两种 P00 扫描；控制器在外置盘根目录复验 8 项 architecture tests 与 12 项 P00 回归均通过，`main` 远端已回读。
- **状态边界**：外部动作默认全为 false；无新增依赖、ORM、数据库连接、模型、SDK、真实资料或业务状态。P01-02 后续已另行验证 local-only runtime；P01-03 仍待执行，不能把 skeleton 写成可运行销售系统。

## 2026-08-06｜P00-03 dry-safe 回归扫描与主工作区基线阻断

- **目标**：建立不联网、不读取 `.env*` 内容、不调用模型或真实渲染的敏感/路径/legacy 回归入口，并验证其 fail-closed 行为。
- **实际改动**：新增 `scripts/validate_regression_baseline.py`、12 项 stdlib 回归测试和 P00-03 报告；覆盖 `.env*` 路径级检测、ignored 非 ASCII 路径、AppleDouble、符号链接跳过、绝对路径、secret-like assignment、fixture 泄漏、Git 失败和过长路径的受控失败。
- **控制器验证**：任务分支测试、静态检查、默认/全量扫描与远端文件回读均完成；控制器在授权主工作区复验时，扫描器无 traceback，但正确发现 202 项默认带基线和 1,262 项全量既有 ignored 禁入路径。
- **状态边界**：扫描器实现本身为 **CONFIRMED**；外置盘根目录的工程基线为 **BLOCKED（局部）**，且任务规则禁止删除 AppleDouble、读取 `.env*` 或放宽扫描以伪造通过。控制器随后在干净 P00-03 task worktree 复验 12 项测试和两种扫描均通过，因此 Phase 0 可作为隔离工程路径完成；Phase 1 必须一任务一新 worktree。业务状态及外部行为没有变化。

## 2026-08-06｜P00-01 工程资产与禁区基线审计

- **目标**：只执行 `P00-01`，以当前仓库证据建立工程资产、legacy hash/CLI、禁区和 Phase 1 输入基线；不创建运行时代码，不调用模型/API，不读取密钥值，不改变业务事实。
- **实际读取**：AGENTS、PROJECT_ENTRY、业务/当前/事实源/范围/协作状态、GPT Project 机制包核心文件、AI Native Sales OS 总蓝图、架构与模块边界、P00-01 task card、受控 Git 文件清单和根目录脚本入口。
- **实际改动**：新增 `docs/implementation/P00-01_ENGINEERING_ASSET_BASELINE_REPORT.md`，追加本执行历史记录。
- **审计结果**：当前受控仓库主要为治理/状态/实施规划文档、GPT Project 机制包、同步包快照和两个根 Python 脚本；未发现 runtime 目录、migration、Docker/Make 入口或可运行服务。两个根脚本已记录 SHA-256 和安全 `--help` 入口；规划中 HappyHorse/DashScope/FFmpeg legacy 实体未在当前受控 Git 清单中定位，保持 `BLOCKED`，后续不得假设可运行。
- **禁区结果**：本轮未修改原始研究、DOCX/XLSX/PDF、媒体、`outputs/`、`.env*`、`research_channels.json` 或 `project_sync/latest/`；AppleDouble 和超过 10MB 文件检查无命中。
- **状态边界**：本条只表示 P00-01 在任务分支形成工程审计证据；不表示 Phase 0 已合入 main，不表示运行时系统、供应链资料、平台合规、账号权限、外部发布、报价、收款、订单、履约或销售成立。

## 2026-08-06｜AI Native Sales OS Phase 0–8 工程实施蓝图落库

- **目标**：把已有 GPT Project / GitHub / Codex 治理机制与运行时工程规划分层，形成从工程基线到真实供应链资料导入、fixture 替换、全链回归和受控运行的可下发路径；本轮不开发业务代码。
- **实际读取**：项目入口、业务/协作状态、事实源、范围、决策、风险、下一步、GPT Project 机制包/Manifest、未合并早期实施规划、HappyHorse/DashScope/FFmpeg 和研究/文档工具脚本，以及当前官方开源组件资料。
- **实际改动**：重组 `docs/implementation/` 为 Phase 0–8 总蓝图、分阶段执行图、数据/导入/工作流/CRM/客服/视频/真实资料 runbook、测试回滚矩阵、run-ready 模板、机器可读依赖图和 27 张独立 Codex 任务卡；旧粗粒度规划入口标为 SUPERSEDED，避免混用编号。
- **验证边界**：文档非空、任务卡字段、链接/路径、敏感/本地路径、业务线污染和 Git diff 检查须以本轮最终命令结果为准；Git commit/push/remote readback 在执行报告中单独回报。
- **状态边界**：规划落库只表示工程实施设计完成；不表示运行时系统、供应链资料、平台合规、账号权限、外部发布、报价、收款、订单、履约或销售已完成。

## 2026-08-06｜GPT Project 机制包语义一致性与来源追溯修正

- **目标**：消除 P0/P1/P2 两套定义，修正业务闸门误称为 P0 的表达，统一 blocked/Git 状态词，并让 `project_entry/AGENTS.md` 可由 Manifest 记录的 source commit 复现。
- **实际读取**：根 `AGENTS.md`、`PROJECT_ENTRY.md`、GPT Project 机制包核心文件、Manifest、验证脚本、验证报告和 AGENTS 机制对照审计。
- **第一阶段 source commit**：`28e6f92eb91548fc3f9ef3b79865cb4a591eb4d0`，用于生成 AGENTS 镜像。
- **实际改动**：统一来源优先级定义；将商品、价格、库存、资质、账号、收款、履约和酒类合规前置统一称为 `business_gates（业务闸门）`；新增语义一致性审计；升级 Manifest、验证脚本和验证报告以验证 AGENTS provenance。
- **状态边界**：`package_ready_for_manual_upload = true`；`user_uploaded_to_gpt_project_ui = false`。本条不表示用户已上传 GPT Project UI，也不表示供应链、平台、合规、上线、销售或履约成立。

## 2026-08-06｜GPT Project 配合机制同步包与 AGENTS 交叉审计

- **目标**：补齐汾酒 GPT Project 手动上传用配合机制包，并按 P0 补充要求交叉审计 `AGENTS.md`、`PROJECT_ENTRY.md` 与参考仓库机制。
- **实际读取**：当前汾酒 AGENTS、PROJECT_ENTRY、业务与协作状态、任务执行单；主参考仓库 `fthytwerwt-sudo/-` 根 AGENTS、完整 GPT Project 上传包和关键提交 `4b535ef`、`8a1350b`、`7402250`；补充参考 `fthytwerwt-sudo/lanxinse--` 根 AGENTS 与同名 GPT Project 机制包。
- **实际改动**：新增 `GPT项目资料同步包_gpt_project_mechanism_sync/` 23 文件；新增参考机制学习报告、AGENTS 机制对照审计、验证脚本和验证报告；更新 AGENTS、PROJECT_ENTRY、README、协作流程、任务模板、决策和协作状态。
- **验证结果**：`python3 -m py_compile scripts/validate_gpt_project_mechanism_sync.py` 通过；`python3 scripts/validate_gpt_project_mechanism_sync.py --write-manifest` 通过，文件数 23、系统提示词 3081 字符、Manifest 一致、AGENTS 镜像 SHA 一致、敏感信息/绝对路径/参考项目污染/媒体扫描通过。
- **状态边界**：`package_ready_for_manual_upload = true`；`user_uploaded_to_gpt_project_ui = false`。本条不表示供应链资料已回传、TikTok 酒类边界已确认、业务上线、销售或履约成立。

## 2026-08-05｜协作机制 V2：业务状态与协作状态分离

- **目标**：在不删除原始资料或虚构供应链交付的前提下，修正入口、当前范围、历史研究定位和协作收口状态。
- **实际读取**：用户确认的 TikTok 范围、双方职责、当前阶段与海鲜边界；现有入口、状态、事实源、决策、风险、下一步、模板、Git 历史摘要和 V2 任务要求。
- **审计事实**：旧临时分支有 6 个提交；历史 manifest 与多份历史生成脚本曾包含本机绝对路径/结构信息；高置信凭据规则在 Git 历史命中 0；本地 bundle 已验证可读且不进入仓库。
- **实际改动**：新增 BUSINESS_STATUS 和 COLLABORATION_STATUS；CURRENT_STATUS 改为总览路由；入口、决策、事实源、范围、待确认、风险、下一步和交接模板按当前 TikTok 与供应链启动范围更新。
- **未写为完成**：供应链尚未实际提供 SKU、价格、库存、主体/资质、账号、收款、仓储配送、售后或负责人确认；本条不宣称业务上线、合规许可或履约已完成。
- **待最终收口**：同步包脚本脱敏、干净 main、visibility、默认分支、旧远端分支清理、新同步包验证和远端回读，均以 COLLABORATION_STATUS 的最终证据为准。

## 2026-08-05｜建立跨会话协作与同步包机制

- **目标**：从参考仓库提炼可迁移协作机制，并为汾酒项目建立入口、事实分级、状态/决策体系和同步包自动化。
- **实际改动**：本轮建立的协作文件和同步包脚本见提交 diff；未移动或删除任何现有业务资料。
- **业务状态**：未新增当地许可、平台权限、SKU、库存、合作方确认、订单或销售结论。
- **说明**：该初始机制的部分同步包元数据和历史状态已在 V2 中被替代，具体以当前协作状态和最终远端回读为准。
