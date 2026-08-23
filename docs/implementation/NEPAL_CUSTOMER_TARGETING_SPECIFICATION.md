# 尼泊尔精准客户获取标准与 Codex 输入规范

> **文档状态：** `INTERNAL_SPECIFICATION / 策略与数据合同`
> **版本：** `v1.0`
> **日期：** 2026-08-23
> **适用业务线：** `fenjiu_nepal`（汾酒尼泊尔）与 `seafood_nepal`（尼泊尔海鲜）
> **本轮不做：** 不搜索真实客户、不抓取网页、不保存联系人、不导入 CRM、不发送邮件、不报价、不下单。

## 0. 先读结论

本文件定义未来由 Codex 执行客户发现、人工筛选与 CRM 录入时必须遵循的**业务标准和结构化输入**。它不是营销方案，也不是当前对外获客授权。

两条业务线必须使用独立的 `business_line`、产品范围、评分理由、客户记录与证据链。不得将海鲜客户、产品、价格、资质、冷链能力或履约结论用于汾酒，也不得反向推导。

| 事项 | 当前判断 | 说明 |
|---|---|---|
| 汾酒正式业务范围 | **已确认** | 仍是尼泊尔 TikTok（短视频平台）线上销售准备；自动找客和自动外联此前为 `SUPERSEDED`，本文件不恢复它们。 |
| 汾酒产品范围 | **本轮 P0（用户输入）** | 未来定位只允许 `fenjiu_20_year` 与 `fenjiu_30_year` 两个产品标识；没有书面 SKU、度数、容量、价格、库存、授权和可售证明。 |
| 海鲜产品范围 | **部分成立** | 上传的《尼泊尔市场冻品2026年第一批次进货清单》列出 20 个产品行，可用于产品族和客户匹配设计；不能证明可售库存、价格、进口资格、标签、冷链或履约。 |
| 真实客户发现 / 联系人采集 | **BLOCKED** | 现有代码的 leads、CRM 与 outreach 合同仍是 `synthetic/local-only`；真实来源、联系人处理依据、DNC（拒绝联系）、保留/删除、审批与外部动作授权尚未齐备。 |
| Google Maps 作为名单来源 | **禁止路线** | Google Maps 条款禁止为服务外用途导出、提取或抓取 Maps 内容，包括企业名称、地址和评论；不得把它用于批量名单或 CRM 数据源。见 [Google Maps Platform Terms](https://cloud.google.com/maps-platform/terms)。 |

## 1. 文档目的、边界与术语

### 1.1 目标

未来获客执行必须能从本规范直接回答以下问题：

1. 本次只找哪条业务线、哪些产品相关的企业客户；
2. 先搜索哪些城市、客户类型与公开允许的来源类别；
3. 每家公司至少收集哪些**非敏感**字段，哪些字段必须留在受控联系人存储；
4. 如何把“看起来像客户”与“可进入 CRM 审核”分开；
5. 如何基于可解释评分排序，而不把评分当成联系或发送许可；
6. 哪些信息不足、风险信号或业务闸门缺失时必须停止。

### 1.2 不在本规范授权范围内

- 不授权真实网页抓取、目录下载、Google Maps/Places 数据落库、邮箱猜测、邮箱验证、批量触达或 Gmail 发送；
- 不声明任何目标客户具备采购能力、付款能力、酒类/食品进口资格、冷链能力或当地销售资格；
- 不声明汾酒 20 年或 30 年的价格层级、容量、酒精度、库存、利润、最低价、授权或可售状态；
- 不把海鲜清单上的数量或重量写成已可销售库存、采购订单或到货事实；
- 不建立 B2C（面向个人消费者）个人名单；本期只定义 B2B（面向企业）客户发现标准；
- 不替代当地持牌专业人士、当地供应链、平台或主管机关的合规判断。

### 1.3 关键术语

| 术语 | 中文含义 | 本文件中的严格含义 |
|---|---|---|
| `candidate` | 候选企业 | 来自允许来源、尚未通过人工审核的企业线索；不是客户、也不是可联系对象。 |
| `CRM admission` | CRM 准入 | 经过来源、范围、重复、DNC、处理依据和人工审核后，才允许写入未来真实 CRM 读模型的动作。 |
| `DNC` | 拒绝联系 | 企业或联系人要求不再联系，或当前政策要求抑制时的最高优先级阻断记录。 |
| `processing_basis` | 联系人处理依据 | 允许持有或处理某条公开业务联系信息的书面政策/法律依据；当前为 `UNKNOWN`。 |
| `source evidence` | 来源证据 | 来源所有者、URL/目录标识、采集日期、适用条款、允许字段、版本或哈希等可复核信息。 |
| `score` | 客户评分 | 用于人工排序的可解释建议，不代表真实性、信用、合规或发送许可。 |
| `business_gate` | 业务闸门 | SKU、价格、库存、主体/资质、账号、收款、履约、数据与外部动作授权等必须以当前书面证据解除的条件。 |

## 2. 事实、策略建议与待验证项

### 2.1 已确认 / 部分成立的输入

| 输入 | 状态 | 使用方式 |
|---|---|---|
| 汾酒当前以 TikTok 为主的线上销售准备；供应链资料仍缺 | **已确认** | 汾酒的本规范只能用于内部定义与受控草稿准备，不能声称 B2B 已恢复为正式销售渠道。 |
| 汾酒与海鲜业务线隔离 | **已确认** | 强制使用独立 `business_line`、分数和产品匹配字典。 |
| 汾酒产品仅限“20 年”“30 年”两项 | **本轮 P0** | 仅作为候选产品标识；不得补猜商品规格、价格或定位。 |
| 海鲜 PDF 的 20 个产品行与合计 2,895 kg | **部分成立** | 用于产品族分类；清单中个别行的重量字段为 0 或缺失，不能将其转成库存结论。 |
| 尼泊尔国家统计局发布 2021 人口普查结果 | **已确认的外部来源存在** | 用作城市选择需要后续复核的人口/城市资料入口，而不是具体客户需求证明。见 [National Population and Housing Census 2021](https://censusresults.nsonepal.gov.np/)。 |
| 尼泊尔旅游局持续发布旅游统计资料 | **已确认的外部来源存在** | 用于后续审查酒店/旅游集群的研究证据；不证明某家酒店有采购需求。见 [Nepal Tourism Board statistics hub](https://trade.ntb.gov.np/downloads-cat/nepal-tourism-statistics/)。 |
| 尼泊尔 DFTQC（食品技术与质量控制部）存在食品进口许可、产品登记及 NNSW（国家单一窗口）相关资料 | **已确认的外部来源存在** | 海鲜线需把食品进口/登记资料列为准入核验项；具体适用性和当前要求必须由当地合规责任人重新确认。见 [DFTQC 年度公告](https://www.dftqc.gov.np/downloadfiles/DFTQC-Annual-Bulletin-Eng-2082-Book-for-WEB-%281%29-1779272721.pdf) 与 [产品登记表](https://www.dftqc.gov.np/noticefiles/46-1742812951.pdf)。 |

### 2.2 本规范的策略建议

以下内容均为 `RECOMMENDATION`，目的是让后续发现工作可比较、可停止、可人工复核：

- 优先从 **Kathmandu Valley（加德满都谷地）** 的企业客户开始，再以数据质量和履约闸门决定是否扩大至 Pokhara、Chitwan 及区域分销城市；
- 先收集企业与来源证据，后在通过处理依据、DNC 和人工审核后才处理公开业务联系人；
- 汾酒和海鲜均先做 B2B；海鲜 B2C 只定义渠道客户（如合规零售商），不采集消费者资料；
- 先按产品-客户用途匹配与可验证的经营信号评分，再决定是否送人工审核；
- “没有网站”不是自动淘汰条件，但会降低可验证性；没有允许来源、公司身份或业务联系方式时，不能进入可联系队列。

### 2.3 必须保持 UNKNOWN / BLOCKED 的变量

| 变量 | 当前状态 | 影响 |
|---|---|---|
| 汾酒两款的 SKU、规格、度数、包装、价格、库存、授权、可售地区与交付条件 | `UNKNOWN / BLOCKED` | 不能做真实报价、产品承诺、库存承诺或针对具体用途的营销表达。 |
| 汾酒客户的酒类牌照、年龄限制、酒店/餐厅供酒权限及渠道主体 | `UNKNOWN / BLOCKED` | 分数不得替代资格核验；接触和合作前须由当地合规/供应链书面确认。 |
| 海鲜的原产地、标签、批次、保质期、储运温度、过敏原、检验/进口/食品登记、到货和冷链责任 | `UNKNOWN / BLOCKED` | 不得把 PDF 产品图或数量用于销售、报价或履约判断。 |
| 客户实际采购预算、付款信用、付款周期、最小订购量和决策人 | `UNKNOWN` | 仅可记录可验证的公开经营信号；不得臆测信用能力。 |
| 真实来源、联系人处理依据、DNC/删除/保留政策、真实身份/RBAC、OAuth/密钥管理与外联授权 | `BLOCKED` | 未来真实获客桥接层（`P08-RAB`）不能进入生产联系或发送。 |

## 3. 产品结构与产品-客户匹配模型

### 3.1 汾酒产品范围：先共享客户方向，后做产品分层

当前只有两项产品名称。没有经核验的产品资料时，不能声称“20 年更适合某类客户”或“30 年价格更高”。因此，未来发现先使用共同的 `fenjiu_baijiu_premium_candidate` 客户用途方向；待供应链提供产品卡后，才能启用产品差异化评分。

| 产品 ID | 当前可用事实 | 优先候选客户类型 | 购买可能的策略假设 | 不能推断 |
|---|---|---|---|---|
| `fenjiu_20_year` | 本轮用户指定的产品名称 | 高端中餐/泛亚洲餐饮、优质酒类渠道、酒店餐饮、合规礼赠渠道 | 这些业态可能具备餐饮搭配、商务宴请、礼赠或酒类分销的使用场景。 | 定价、容量、酒精度、供货、利润、最小订购量、当地合法销售。 |
| `fenjiu_30_year` | 本轮用户指定的产品名称 | 高端酒店、宴会/商务餐饮、优质酒类进口/分销、受控企业礼赠渠道 | 这些业态可能更重视品牌叙事、礼赠和高客单场景。此处是待验证的客户假设。 | 该产品的“高端程度”、价格、稀缺性、库存或任何优先级优势。 |

#### 汾酒客户类型优先级

| 优先级 | 客户类型 | 纳入原因（策略建议） | 最少验证信号 | 暂不适合 / 排除条件 |
|---|---|---|---|---|
| P1 | 高端餐饮 | 可能存在中餐搭配、商务宴请、成人餐饮和品牌体验场景。 | 明确餐饮定位、成年人餐饮场景、稳定营业信息、公开企业身份。 | 面向未成年人的场所；只提供低价快餐且无成人饮品场景；没有可验证企业身份。 |
| P1 | 酒类渠道 | 进口商、分销商、优质酒铺等可能承担当地合规、铺货和零售网络角色。 | 公开显示合法企业身份、酒类/饮料/进口或分销经营信号；本地许可由人工核验。 | 无法确认经营主体；要求绕过主体/授权；来源或条款不允许。 |
| P2 | 酒店 | 可能有餐饮、宴会、商务接待或礼宾场景，但单店采购权和许可不能假定。 | 明确酒店及餐饮/宴会设施、采购或 F&B（餐饮）部门入口、所在城市。 | 没有餐饮/成人饮品服务证据；只有个人住宿房源；无可验证主体。 |
| P2 | 礼品 / 商务场景 | 企业礼赠服务商、会议/会展服务商或企业采购可能存在成人礼赠场景。 | 企业客户服务、成人礼赠定位、主体信息与合规渠道责任。 | 暗示向未成年人送酒；要求无品牌授权或无年龄控制的公开促销。 |
| P3 | 其他潜在客户 | 合规的高端零售、会员制餐饮、宴会服务或文化体验场所。 | 与酒类、成人餐饮或合规礼赠有明确可验证交集。 | 仅凭泛“生活方式”标签；没有产品用途或合规路径。 |

#### 汾酒高端酒客户信任建立变量（只用于人工审查）

| 变量 | 可记录的证据 | 不可猜测的内容 |
|---|---|---|
| 合法主体与渠道资格 | 官网、公开注册/许可引用、供应链或持牌方书面确认。 | 不能因店面规模、地图评分或社交帐号就认定已持牌。 |
| 品牌与产品事实完整性 | 供应链批准的产品卡、授权、标签/素材、价格和库存版本。 | 不得用历史研究、图片或产品名称补齐。 |
| 场景匹配 | 可验证的中餐、餐饮、宴会、成人礼赠、精品零售或商务服务信号。 | 不得把“有游客”推断为会购买白酒。 |
| 采购与决策路径 | 公开的采购/F&B/品类负责人渠道，或经允许的企业总机/邮箱。 | 不得抓取私人社交帐号、猜测邮箱或将个人号码当企业联系人。 |
| 首次接触适配性 | 公司身份、来源条款、DNC、联系人处理依据、产品事实和人工审核完整。 | 高评分不等于可以发信、发 WhatsApp 或报价。 |

### 3.2 海鲜 PDF 产品结构

**来源：** 用户上传《尼泊尔市场冻品2026年第一批次进货清单》（5 页，Excel 导出 PDF，已逐页视觉核验）。文件列出 20 个产品行、表内合计数量 554、合计重量 2,895 kg、合计外箱体积 11.2323145；这些只可作为清单自身的记录，不能解释为可销售库存或已到货商品。

| 产品族 ID | PDF 中产品（原文/可识别译名） | 客户用途方向（策略建议） | 关键准入核验 |
|---|---|---|---|
| `shrimp` | 2125 真空虾仁、41/50 单冻虾仁、小河虾、50-60 王牌盐冻虾、12 头黑虎虾、单冻干冰青虾、1620 白灼虾 | 酒店餐饮、海鲜餐厅、中餐/火锅、冻品批发、合规零售。 | 冷冻储运、规格/净重、标签、过敏原、货源与批次、采购频率。 |
| `fish` | 500/700 带鱼、50-100 干冰耗儿鱼、700/800 多宝鱼、14 条黄花鱼、800/900 大白叼 | 中餐、海鲜餐厅、酒店餐饮、冻品分销。 | 鱼种/形态、规格、冷链、菜单适配、保存与解冻要求。 |
| `shellfish_mollusc` | 青口贝、花甲、72 生蚝、蛏子肉、大板鱿鱼须 | 海鲜餐厅、中餐、酒店、专业冻品分销。 | 食品安全/标签、过敏原、储存温度、门店后厨冷冻能力和损耗管理。 |
| `premium_specialty` | 8 头辽参、大 A 鲍鱼 | 高端中餐、酒店宴会、特色海鲜餐厅、礼宴食材渠道。 | 规格、等级、来源、保质期、冷链与目标菜单/厨师需求。 |
| `crayfish` | 小龙虾 | 中餐、休闲餐饮、海鲜餐厅、冻品批发。 | 季节性需求、烹饪方式、冷链、最小订货和促销限制。 |

#### 海鲜客户类型优先级

| 优先级 | 客户类型 | 产品-客户匹配原因（策略建议） | 必须验证的运营信号 | 不适合 / 停止条件 |
|---|---|---|---|---|
| P1 | 酒店采购 | 多 SKU 餐饮、宴会和后厨可能需要稳定规格的冻品供给。 | 餐饮规模、采购入口、冷库/冷柜能力、验收与配送窗口。 | 无餐饮设施；不接受冷冻品；无法核验冷链交接。 |
| P1 | 海鲜餐厅 | 与虾、鱼、贝、鱿鱼和特色食材的菜单用途最直接。 | 海鲜菜单/业态、后厨冷冻能力、采购周期、食品安全要求。 | 仅生鲜且不接受冻品；无冷冻储存；无企业身份。 |
| P1 | 中餐厅 | 多数 SKU 可能与中餐、火锅、宴会或特色菜匹配。 | 菜系、目标菜单、后厨冷冻能力、采购与收货能力。 | 不使用相关食材且无冷链；无法确认餐饮主体。 |
| P2 | 冻品批发商 | 可能具备仓储、分销网络与多客户覆盖，适合更大批量的商品族。 | 冷库、配送网络、覆盖地区、食品/进口经营资格、付款与对账流程。 | 无冷链/仓配证据；来源不允许采集；要求规避食品合规。 |
| P2 | 食品进口商 | 在当地食品进口、登记与合规资料链中可能承担关键角色。 | 当前品类、进口资格、食品登记流程、主体/责任人。 | 仅凭名称为“importer”；没有当前品类或许可核验。 |
| P3 | 超市 / 零售渠道 | 可作为合规 B2C 渠道客户，承接包装、陈列与消费者销售。 | 冷冻柜、食品品类、门店/配送能力、上架/标签流程。 | 直接采集消费者；无冷冻陈列或零售合规链。 |
| P3 | 其他潜在客户 | 中央厨房、餐饮供应商、会展餐饮或专业餐配服务。 | 企业餐饮规模、冷链、合同与食品安全流程。 | 无实际采购用途或对方是个人消费者。 |

#### 海鲜独有的冷链与食品安全变量

| 变量 | 记录方法 | 规则 |
|---|---|---|
| 冷冻储存能力 | `freezer_present / unknown`、证据 URL/照片引用（仅在授权私有存储）、核验日期。 | 不得因经营海鲜就假定有冷库。 |
| 温度要求 | 只记录供应链批准的标签、COA（检验证书）或规格书要求。 | PDF 没有给出可执行温度时填 `UNKNOWN`；不可自行写 `-18°C`。 |
| 冷链配送与收货 | 配送区域、时段、验收标准、温控责任、异常处理责任。 | 缺任一项时，不得认定可以履约。 |
| 食品/进口/产品登记 | 责任主体、许可/登记引用、核验日期、核验人。 | DFTQC/NNSW 资料说明存在相关流程，但具体产品适用性必须由当地责任人确认。 |
| 过敏原和标签 | 产品标签、配料、过敏原、语言、批次和保质期引用。 | 未核验前不得生成面向客户的食品说明。 |
| 客户采购能力 | 菜单规模、采购频率、冷链、门店/仓库、合同/对账能力等可验证企业信号。 | 不收集/推断个人信用；付款能力仅在合法且经人工批准的企业尽调阶段处理。 |

### 3.3 产品-客户-未来处理路径矩阵

下表的“未来处理路径”不是外联话术或联系授权。它只规定：如果来源、数据治理、供应链事实和人工审核在未来全部通过，哪类业务入口最值得**先由人工核验**。任何路径均不得绕过 `DNC`、处理依据、客户意愿、当地合规或产品事实锁。

| 业务线 / 产品范围 | 首选客户类型 | 首要验证目的 | 未来优先业务入口（需授权） | 不应直接做的事 |
|---|---|---|---|---|
| 汾酒 20 年 | 高端中餐/亚洲餐饮、酒店 F&B、优质酒类渠道 | 是否存在成人餐饮、宴会、酒类渠道或中国餐饮搭配的可验证场景。 | 公司官网的采购/F&B/品类入口，或经允许目录中的企业公共入口。 | 猜测决策人、承诺价格/库存、以高分直接发信。 |
| 汾酒 30 年 | 高端酒店、商务/宴会餐饮、优质进口/分销、礼赠渠道 | 是否具备商务宴请、礼赠或高端渠道的真实业务用途。 | 企业采购、F&B、进口/分销或礼赠业务入口；先由人工验证主体和授权。 | 把“30 年”自动解释为定价/等级；向个人或未成年人相关对象推广。 |
| 海鲜：虾 / 鱼 / 贝类 / 鱿鱼 | 酒店采购、海鲜餐厅、中餐厅、冻品批发 | 菜单、冷冻储存、收货、损耗和采购周期是否适配。 | 企业采购、厨房/F&B、冻品品类或仓配入口；先核冷链与食品责任。 | 将菜单匹配当作可配送、可进口或可售事实。 |
| 海鲜：辽参 / 鲍鱼 | 高端中餐、酒店宴会、特色海鲜餐厅 | 规格、等级、菜单需求、储存和食材验收是否可验证。 | 厨师/采购/宴会业务入口，但只在企业公开或经授权的渠道中处理。 | 以图片或名称承诺品质等级、原产地、价格或供货。 |
| 海鲜：小龙虾 | 中餐、休闲餐饮、海鲜餐厅、冻品批发 | 烹饪/菜单场景、季节性、冷链和批量采购需求。 | 采购/品类/供应链企业入口。 | 直接建立消费者名单或用低价促销假设替代验证。 |

### 3.4 首次接触前的“处理目标”字段

未来在任何真实联系获授权前，应只把以下内容作为人工审核的 `first_contact_objective`（首次接触目标）候选，而不是自动生成或发送的文案：

| 客户类型 | 允许的目标表述 | 必须已有的事实 | 必须避免 |
|---|---|---|---|
| 汾酒餐饮 / 酒店 | 确认是否存在合规的采购/F&B 业务入口和产品场景评估意愿。 | 合法主体、批准的产品卡、当地渠道责任和联系处理依据。 | 价格、库存、交期、健康功效、年龄不明对象或任何酒类合规承诺。 |
| 汾酒进口/分销 | 确认品类/渠道评估流程及本地合规责任边界。 | 品牌授权、产品/库存事实、当地资格和处理依据。 | 以“进口商”名称推断许可，或承诺独家/利润/市场权。 |
| 海鲜餐饮 / 酒店 | 确认采购/后厨是否需要评估特定冻品产品族，以及冷链/收货条件。 | 已批准产品规格、标签/食品资料、温控/配送责任和处理依据。 | 承诺食品安全、温度、批次、到货、价格或配送能力。 |
| 海鲜批发 / 进口 | 确认其品类、冷库、分销和合规资料的审核流程。 | 供应链主体、进口/食品责任、产品事实、冷链资料和处理依据。 | 把冷库或进口资质当作已确认，或以任何个人联系方式启动批量触达。 |

## 4. 地域策略与搜索顺序

### 4.1 原则

城市排序是**搜索与人工验证的优先顺序**，不是已确认销售区域、配送区域、酒类许可区域或海鲜冷链覆盖范围。每扩大一个城市，都必须重新验证来源、主体/许可、配送/冷链、价格与库存条件。

优先从城市集群而非全尼泊尔扫描开始：这样可以先在较小范围内验证来源质量、产品匹配、联系人处理和履约条件。尼泊尔国家统计局和旅游局都提供可进一步验证人口及旅游/酒店相关信号的官方资料入口；它们不能替代企业级证据或需求证明。[National Statistics Office](https://censusresults.nsonepal.gov.np/) · [Nepal Tourism Board](https://trade.ntb.gov.np/downloads-cat/nepal-tourism-statistics/)

### 4.2 汾酒城市顺序

| 顺序 | 搜索集群 | 首选客户类型 | 为什么先搜（策略建议） | 进入下一集群的停止线 |
|---|---|---|---|---|
| 1 | Kathmandu Valley：Kathmandu、Lalitpur、Bhaktapur | 高端餐饮、酒类渠道、酒店、商务礼赠 | 企业、酒店、餐饮与商务服务更易在同一集群内做来源质量和人工审核对比。 | 未取得可用来源、产品事实或当地酒类责任主体前，不扩大。 |
| 2 | Pokhara | 酒店、旅游餐饮、精品餐饮、合规零售/渠道 | 作为独立的酒店与餐饮验证集群；先验证实际采购和合规路径。 | 无供应链配送/主体/许可书面证据时，不进入真实联系。 |
| 3 | Chitwan 集群：Bharatpur / Sauraha | 酒店、度假餐饮、商务餐饮 | 只作为第二阶段候选；需要先证明产品用途与配送可行。 | 首个集群的来源/DNC/人工审查流程未通过时停止。 |
| 4 | 其他城市 | 仅经当地合规、供应链和渠道事实支持后决定 | 不做预设全国扩张。 | 任何外部执行闸门缺失即停止。 |

### 4.3 海鲜城市顺序

| 顺序 | 搜索集群 | 首选客户类型 | 必须先确认的本地条件 | 说明 |
|---|---|---|---|---|
| 1 | Kathmandu Valley：Kathmandu、Lalitpur、Bhaktapur | 酒店采购、海鲜餐厅、中餐厅、冻品批发商、食品进口商 | 供应链主体、食品/进口责任、冷库/配送、产品标签和到货事实。 | 首轮先验证“客户需要”与“能否稳定冷链履约”是否同时成立。 |
| 2 | Pokhara | 酒店、餐饮、合规零售渠道 | 实际配送时效、冻链能力、收货窗口和退换/异常责任。 | 不能把 Kathmandu 的能力外推到 Pokhara。 |
| 3 | Chitwan 集群：Bharatpur / Sauraha | 酒店、旅游餐饮、中餐/海鲜餐厅 | 路线、冷链、产品状态和客户验收条件。 | 仅在首轮结果和履约资料支持后纳入。 |
| 4 | 区域分销城市 | 冻品批发商、食品进口商、零售渠道 | 具体仓储、覆盖区域、进口主体和合同付款流程。 | 不预设城市；由已确认的物流/进口路线决定。 |

## 5. 客户搜索关键词库

### 5.1 使用规则

1. 关键词仅用于查询，不构成来源授权；结果必须按第 6 节来源等级和第 7 节字段规则审查。
2. 英文与 Nepali（尼泊尔语）查询词应并行试验；尼泊尔语词是**查询扩展候选**，需由母语者或首轮人工检索验证拼写和本地使用习惯。
3. 一次查询只改变一个主要变量：`城市 + 客户类型 + 产品/用途`，以便比较结果质量。
4. 禁止把 Google Maps 结果、截图或 Places 数据导出为名单。也不得以搜索引擎片段作为公司或联系人的唯一证据。
5. 查询只用于寻找公司自有网站、允许目录或已授权的协会/机构名录；不得绕过登录、CAPTCHA、robots、条款或 rate limit（访问频率限制）。

### 5.2 汾酒关键词

| 客户类型 | 英文基础词 | Nepali 查询扩展词（待人工校验） | 推荐组合 |
|---|---|---|---|
| 高端中餐/亚洲餐饮 | `Chinese restaurant`, `fine dining`, `Asian restaurant`, `banquet restaurant` | `चिनियाँ रेस्टुरेन्ट`, `उच्चस्तरीय रेस्टुरेन्ट`, `भोज रेस्टुरेन्ट` | `"Chinese restaurant" "Kathmandu"`, `"fine dining" "Lalitpur"`, `काठमाडौं चिनियाँ रेस्टुरेन्ट` |
| 酒类进口/分销 | `liquor importer`, `alcohol distributor`, `beverage distributor`, `wine and spirits` | `मदिरा आयातकर्ता`, `मदिरा वितरक`, `पेय पदार्थ वितरक` | `"liquor importer" Nepal`, `"alcohol distributor" Kathmandu`, `नेपाल मदिरा आयातकर्ता` |
| 酒店 | `five star hotel`, `boutique hotel`, `hotel F&B`, `hotel banquet` | `पाँच तारे होटल`, `बुटिक होटल`, `होटल खाद्य तथा पेय` | `"hotel F&B" Kathmandu`, `"hotel banquet" Nepal`, `काठमाडौं पाँच तारे होटल` |
| 礼赠 / 商务场景 | `corporate gifting`, `business gifts`, `event gifting`, `conference organizer` | `कर्पोरेट उपहार`, `व्यावसायिक उपहार`, `कार्यक्रम उपहार` | `"corporate gifting" Nepal`, `"business gifts" Kathmandu`, `नेपाल कर्पोरेट उपहार` |
| 精品零售 / 其他 | `premium liquor store`, `wine shop`, `specialty beverage retailer` | `मदिरा पसल`, `वाइन पसल`, `विशेष पेय पसल` | `"premium liquor store" Kathmandu`, `काठमाडौं मदिरा पसल` |

### 5.3 海鲜关键词

| 客户类型 | 英文基础词 | Nepali 查询扩展词（待人工校验） | 推荐组合 |
|---|---|---|---|
| 酒店采购 | `hotel procurement`, `hotel F&B`, `hotel kitchen`, `banquet catering` | `होटल खरिद विभाग`, `होटल खाद्य तथा पेय`, `होटल भान्सा` | `"hotel procurement" Kathmandu`, `"hotel F&B" Pokhara`, `काठमाडौं होटल खरिद विभाग` |
| 海鲜餐厅 | `seafood restaurant`, `seafood menu`, `fish restaurant` | `समुद्री खाना रेस्टुरेन्ट`, `माछा रेस्टुरेन्ट` | `"seafood restaurant" Kathmandu`, `पोखरा समुद्री खाना रेस्टुरेन्ट` |
| 中餐 / 火锅 | `Chinese restaurant`, `Chinese seafood`, `hotpot restaurant` | `चिनियाँ रेस्टुरेन्ट`, `हटपोट रेस्टुरेन्ट` | `"Chinese seafood" Kathmandu`, `"hotpot restaurant" Nepal`, `काठमाडौं चिनियाँ रेस्टुरेन्ट` |
| 冻品批发 | `frozen food distributor`, `frozen seafood wholesaler`, `cold storage`, `foodservice distributor` | `फ्रोजन फूड वितरक`, `थोक वितरक`, `कोल्ड स्टोरेज`, `शीत भण्डार` | `"frozen food distributor" Nepal`, `"cold storage" Kathmandu`, `नेपाल फ्रोजन फूड वितरक` |
| 食品进口商 | `food importer`, `seafood importer`, `frozen food importer` | `खाद्य आयातकर्ता`, `समुद्री खाना आयातकर्ता`, `फ्रोजन खाद्य आयातकर्ता` | `"food importer" Nepal`, `"seafood importer" Nepal`, `नेपाल खाद्य आयातकर्ता` |
| 超市 / 零售渠道 | `supermarket frozen food`, `grocery chain`, `frozen food retail` | `सुपरमार्केट`, `फ्रोजन फूड खुद्रा`, `किराना चेन` | `"supermarket" Kathmandu "frozen food"`, `काठमाडौं सुपरमार्केट` |

### 5.4 组合搜索模板

```text
<city> + <customer type> + <product/use case>
<city> + <customer type> + <business function>
<city> + <customer type> + <official website or association>
<city> + <Nepali client-type term>
```

示例仅用于**查询设计**：

```text
Kathmandu + Chinese restaurant + banquet
Pokhara + hotel F&B + procurement
Nepal + frozen food distributor + cold storage
काठमाडौं + चिनियाँ रेस्टुरेन्ट
नेपाल + फ्रोजन फूड वितरक
```

## 6. 允许来源、来源等级与排除规则

### 6.1 来源等级

| 等级 | 来源类别 | 可用于什么 | 必要证据 | 不能做什么 |
|---|---|---|---|---|
| `A` | 公司自有官网、官方酒店/餐厅网站、官方协会/政府机构公开目录、经书面授权的供应链名单 | 企业身份、公开业务信息、公司自有公开业务渠道。 | URL、页面/目录版本、采集日期、来源 owner、条款或授权。 | 不自动把任何公开信息变成联系许可。 |
| `B` | 明确允许的商业目录、展会名录、行业协会目录、合作伙伴目录 | 初始候选发现和交叉验证。 | 来源条款、允许字段、更新时间、来源可信度、人工复核。 | 不使用登录墙、付费名单、受限导出或未授权批量数据。 |
| `C` | 公司官方社交主页、媒体报道、活动页 | 只作辅助验证/发现。 | 与公司自有资料或 A/B 来源的交叉证据。 | 不从个人帐号抓取联系方式；不得把它作为唯一公司/联系人证据。 |
| `D` | 搜索结果片段、未验证转载、论坛、匿名名单 | 仅可作为人工检索线索。 | 必须回到 A/B/C 级来源重新验证。 | 不得入 CRM、不得评分为 A/B、不得用于联系。 |
| `X` | Google Maps/Places 的抓取或落库、泄露名单、私人社交资料、登录/验证码绕过、无条款来源 | 不允许。 | 不适用。 | 不得采集、导出、保存、验证或联系。 |

### 6.2 每个来源必须登记的字段

```yaml
source_id: "SRC-..."
business_line: "fenjiu_nepal | seafood_nepal"
source_tier: "A | B | C | D | X"
source_owner: ""
source_category: "company_website | association_directory | partner_list | ..."
source_url_or_private_locator: ""
terms_or_authorization_reference: ""
terms_reviewed_at: "YYYY-MM-DD"
allowed_fields: []
collection_method: "manual_review | approved_import | future_adapter"
evidence_version_or_hash: ""
collected_at: "ISO-8601"
data_freshness_date: "YYYY-MM-DD | unknown"
source_risk_notes: []
approved_for_candidate_discovery: false
approved_for_business_contact_processing: false
```

`approved_for_candidate_discovery=true` 不等于 `approved_for_business_contact_processing=true`。后者在当前项目中必须保持 `false`，直到数据治理、DNC 和联系人处理依据被书面批准。

### 6.3 通用排除与人工升级规则

立即排除或隔离，不进入 CRM：

- 企业记录同时出现两个 `business_line`，或不清楚属于汾酒还是海鲜；
- 来源条款、来源 owner、允许字段或采集日期缺失；
- 数据来自 Google Maps/Places 的抓取、导出或缓存；
- 个人联系人、私人电话、私人邮箱或儿童/未成年人相关信息；
- 被标记为 `DNC`、`delete_requested`、`do_not_process` 或存在冲突的删除请求；
- 无法辨认公司主体、重复记录无法安全合并、来源与企业不匹配；
- 海鲜客户缺少冷链/食品安全的最低可核验信息；
- 汾酒候选涉及面向未成年人、鼓励过量饮酒、未经许可的酒类宣传或试饮承诺。

转人工审核而不自动排除：

- 没有官网但有可交叉验证的正式企业主体；
- 企业规模、采购能力、进口经验或冷链能力尚不清楚；
- 公开业务电话/邮箱存在，但处理依据或 DNC 状态尚未确定；
- 一个企业同时符合多个**同一业务线内**客户类型；
- 产品匹配依赖尚未得到供应链确认的规格/价格/库存。

## 7. Customer Discovery Schema（客户发现数据结构）

### 7.1 设计原则

1. `company_candidate`（公司候选）和 `business_contact`（业务联系人）必须分表/分对象保存；联系人字段的敏感性更高。
2. 真实数据不得写入 Git、fixture、测试、日志、审计正文或公开文档。Git 只保存 schema、枚举、reason code 和脱敏示例。
3. `business_line` 为不可空且不可在记录生命周期中修改的字段；跨线记录必须新建而非复制。
4. 每条评分必须保存版本和理由；缺证据的字段不得以默认满分代替。
5. 任何 CRM 准入、草稿或将来发送前都要重新检查来源、DNC、事实版本、范围和保留状态。

### 7.2 公司候选对象（可在经批准的未来私有存储中使用）

| 字段 | 必填阶段 | 说明 / 验证规则 |
|---|---|---|
| `candidate_id` | 发现 | 系统生成 ID；不得复用电话号码或邮箱作为 ID。 |
| `business_line` | 发现 | `fenjiu_nepal` 或 `seafood_nepal`，二选一。 |
| `scope_version` | 发现 | 本规范或未来批准范围的版本号。 |
| `legal_or_trading_name` | 发现 | 公司公开名称；记录原文与规范化名，保留来源引用。 |
| `company_type` | 发现 | 使用第 3 节客户类型枚举，如 `hotel`, `frozen_food_wholesaler`。 |
| `segment_tags` | 发现 | 仅同一业务线的标签，如 `premium_dining`、`cold_chain_candidate`。 |
| `country`, `province`, `city`, `area` | 发现 | `country=NP`；地点以公司自有或允许来源的公开地址为准。 |
| `address_as_published` | 审核后 | 不做地址猜测；Google Maps/Places 内容不得填入。 |
| `website_url` | 发现 | 优先公司自有域名；需记录可访问时间。 |
| `official_business_social_urls` | 可选 | 仅公司官方页面；不是个人 profile。 |
| `source_refs` | 发现 | 至少一个符合第 6 节的来源证据 ID。 |
| `source_tier_best` | 发现 | A/B/C/D；`D` 不得获得 CRM 准入。 |
| `source_freshness_date` | 发现 | 不明则 `unknown`，并限制评分上限。 |
| `identity_confidence` | 发现 | `high/medium/low`，由交叉证据决定，不得自评。 |
| `product_match_ids` | 发现 | 仅本业务线字典中的产品或产品族 ID。 |
| `product_match_reason_codes` | 发现 | 如 `MENU_FIT`, `BANQUET_CAPABILITY`, `COLD_CHAIN_CANDIDATE`。 |
| `operational_signals` | 发现 | 结构化的可核验经营信号，见第 8 节。 |
| `risk_flags` | 发现 | `DNC`, `SOURCE_TERMS_UNKNOWN`, `NO_COLD_CHAIN_EVIDENCE` 等。 |
| `candidate_status` | 发现 | 使用第 9 节状态机。 |
| `score_version`, `score_total`, `score_breakdown` | 评分后 | 必须可解释、可重放；不作为联系许可。 |
| `review_owner`, `reviewed_at`, `review_decision` | 人审 | 人工负责人与理由；禁止系统静默准入。 |
| `outcome_metrics_ref` | 仅 future live-pilot 后 | 指向脱敏的触达/回复/资格/转人工结果；当前必须为空，不能用它创建外联权限。 |

### 7.3 联系人对象（仅在未来数据治理解除后）

| 字段 | 何时允许处理 | 规则 |
|---|---|---|
| `contact_ref` | 受控存储建立后 | 不在 CRM 摘要、日志、审计或 Git 中写入明文联系人。 |
| `organization_candidate_id` | 处理时 | 必须关联唯一同线公司候选。 |
| `business_role` | 处理时 | 只记录公开或经授权的业务角色，如 `procurement`, `F&B`, `owner`, `import_manager`。 |
| `public_business_email`, `public_business_phone`, `business_messaging_channel` | 处理时 | 需要来源、处理依据、DNC/删除/保留规则和人工审核；不得猜测/验证邮箱。 |
| `contact_source_ref` | 处理时 | 指向已批准的来源证据和允许字段。 |
| `processing_basis_ref` | 处理时 | 缺失时必须拒绝处理。 |
| `dnc_status`, `dnc_checked_at` | 每次使用前 | DNC 优先级最高；任何命中都不允许草稿/联系。 |
| `retention_until`, `deletion_request_ref` | 处理时 | 无保留/删除规则则停止。 |
| `contact_review_status` | 处理时 | `not_allowed`, `pending_review`, `allowed_for_internal_review`, `suppressed`；当前默认 `not_allowed`。 |

### 7.4 业务线特有扩展字段

| 字段组 | 汾酒 `fenjiu_nepal` | 海鲜 `seafood_nepal` |
|---|---|---|
| 产品用途 | `dining_pairing_signal`, `banquet_signal`, `gift_channel_signal`, `alcohol_channel_signal` | `menu_fit_signal`, `frozen_seafood_signal`, `specialty_seafood_signal`, `retail_freezer_signal` |
| 运营能力 | `adult_beverage_service_signal`, `fnb_or_procurement_signal`, `channel_distribution_signal` | `freezer_signal`, `cold_storage_signal`, `temperature_requirement_ref`, `delivery_window_signal`, `food_import_or_registration_signal` |
| 商业能力 | `premium_positioning_signal`, `business_event_signal`, `china_product_experience_signal` | `foodservice_scale_signal`, `cold_chain_distribution_signal`, `seafood_or_frozen_category_experience_signal` |
| 必须不猜测 | 酒类许可、年龄控制、品牌授权、价格/库存、付款能力。 | 进口许可、食品登记、温控、批次、过敏原、库存、付款能力。 |

## 8. Customer Score（客户评分模型）

### 8.1 总分与硬性限制

`Customer Score = Opportunity Fit（机会匹配 0-60） + Admission Readiness（准入就绪 0-40） - Risk Penalty（风险扣分）`

| 维度 | 分值 | 评分依据 |
|---|---:|---|
| 产品-客户用途匹配 | 0-20 | 可验证的菜单、酒类/食品品类、宴会、冷冻品或分销用途；不以主观“看起来高端”打分。 |
| 客户类型优先级与经营规模信号 | 0-15 | 第 3 节中客户类型、门店/酒店/仓储/分销等公开经营信号；规模不明可为 0。 |
| 地域与可执行性 | 0-10 | 是否属于当前批准搜索集群，以及是否存在运输/服务的待验证路径。 |
| 进口 / 品类 / 中国商品相关经验 | 0-10 | 公司公开资料或经批准来源明确显示；不存在不扣分，不能臆测。 |
| 当前采购或菜单/渠道信号 | 0-5 | 有可核验的采购、F&B、品类、冻品、宴会或礼赠服务信号。 |
| 来源质量与公司身份可信度 | 0-10 | A/B 级来源、公司官网、交叉验证、更新日期。 |
| 可审查的企业沟通入口 | 0-10 | 仅在来源和处理依据允许时记录；目前可作为“待处理信号”，不是发送许可。 |
| 合规 / 履约就绪信号 | 0-10 | 汾酒：主体/渠道/产品事实引用；海鲜：冷链/食品/进口责任引用。缺失不加分。 |
| **风险扣分** | `0` 至 `-35` | 来源条款不明、数据过期、身份冲突、跨线、冷链缺证据、DNC/删除请求等。DNC、私人数据或禁止来源直接 `BLOCKED`，不只扣分。 |

### 8.2 等级、上限和解释规则

| 等级 | 分数 | 必须同时满足 | 处理动作 |
|---|---:|---|---|
| `A` | 80-100 | `source_tier_best` 为 A 或可交叉验证 B；无风险旗标；客户类型/产品用途明确；关键业务线准入信号有证据。 | 送人工复核；仍不可自动联系或发送。 |
| `B` | 65-79 | 公司身份与用途较明确，但至少一项采购、合规、冷链或联系治理变量待补。 | 进入人工补证队列。 |
| `C` | 45-64 | 有初步产品/城市匹配，但证据不足、来源较弱或运营能力不明。 | 仅保留为候选；不处理联系人。 |
| `D` | 0-44 | 目标客户不匹配、重复、陈旧、来源不可靠或缺少最小身份信息。 | 不入 CRM；可标记 `rejected` 或 `quarantined`。 |
| `BLOCKED` | 不适用 | DNC、删除请求、禁止来源、跨线、私人数据、无处理依据、强制合规/履约闸门缺失。 | 停止处理，记录安全原因码，不保留不必要的原始数据。 |

额外限制：

- 任何 `source_tier_best=D` 的记录最高只能为 `C`；
- 没有 `product_match_reason_codes` 的记录最高只能为 `C`；
- 海鲜缺少 `freezer_signal` 与 `cold_storage_signal` 时，酒店/批发/零售候选最高只能为 `C`；
- 汾酒缺少批准的产品/渠道/合规事实时，任何记录不得进入“可报价、可推广、可联系”状态；
- 分数必须写入 `score_reason_codes` 和 `score_version`，便于日后根据真实反馈调整，不允许黑箱改分。

### 8.3 建议的 reason code（评分理由代码）

```text
FIT_PREMIUM_DINING
FIT_CHINESE_CUISINE
FIT_HOTEL_FNB
FIT_BANQUET_OR_EVENT
FIT_ALCOHOL_CHANNEL_CANDIDATE
FIT_FROZEN_SEAFOOD_MENU
FIT_FROZEN_WHOLESALE
FIT_FOOD_IMPORT_CANDIDATE
FIT_RETAIL_FREEZER
SIGNAL_COLD_STORAGE
SIGNAL_COLD_CHAIN_DISTRIBUTION
SIGNAL_IMPORT_EXPERIENCE
SIGNAL_BUSINESS_GIFTING
SIGNAL_PUBLIC_PROCUREMENT_CHANNEL
SOURCE_A_PRIMARY
SOURCE_B_DIRECTORY_VERIFIED
RISK_SOURCE_TERMS_UNKNOWN
RISK_DATA_STALE
RISK_IDENTITY_CONFLICT
RISK_NO_COLD_CHAIN_EVIDENCE
RISK_MISSING_PROCESSING_BASIS
RISK_DNC
RISK_CROSS_BUSINESS_LINE
```

## 9. 客户生命周期与 CRM 准入状态机

```text
source_registered
  -> company_discovered
  -> source_review_pending
  -> candidate_reviewed
  -> scored
  -> crm_eligible_for_internal_review
  -> [未来单独审批后] contact_processing_review
  -> [未来单独审批后] outreach_draft_internal
  -> [未来单独审批后] send_approval
  -> [未来单独 live-pilot] sent / reply_received / human_handoff

任意阶段 -> duplicate_review | quarantined | rejected | suppressed_dnc | delete_requested | hold_missing_business_gate
```

### 9.1 当前允许达到的最高状态

本轮文档工作只允许达到 `source_registered` 的**规范定义层**，不创建任何真实记录。根据当前项目事实，即使未来有真实候选，也只能在新的来源/隐私合同、批准的私有存储和人工审核完成后考虑 `crm_eligible_for_internal_review`；当前 synthetic CRM 不能直接承载真实数据。

### 9.2 CRM 准入前置条件

必须全部为真：

```yaml
business_line_is_exact: true
approved_source_evidence_present: true
source_terms_or_authorization_present: true
company_identity_reviewed: true
dedupe_completed: true
dnc_checked_and_clear: true
retention_and_deletion_policy_present: true
processing_basis_present_if_contact_data_exists: true
score_version_and_reasons_present: true
human_review_decision: "approved_for_internal_review"
approved_product_facts_present_if_draft_or_offer_is_created: true
```

若任何值为 `false` 或 `unknown`，记录必须进入 `hold_missing_business_gate`、`source_review_pending` 或 `quarantined`，而不是 CRM 或外联队列。

## 10. Codex 输入规范

### 10.1 每次运行前的必填运行包

后续 Codex 只能接收一个业务线的运行包。禁止同一次运行同时写入汾酒和海鲜，禁止仅凭自然语言补猜字段。

```yaml
spec_version: "1.0"
run_id: "CT-YYYYMMDD-001"
purpose: "internal_candidate_discovery_only"
business_line: "fenjiu_nepal" # 或 seafood_nepal，二选一

product_scope:
  include_ids: ["fenjiu_20_year", "fenjiu_30_year"]
  # 海鲜线示例： ["shrimp", "fish", "shellfish_mollusc"]
  exclude_ids: []

geography:
  country: "NP"
  city_cluster: "Kathmandu Valley"
  cities: ["Kathmandu", "Lalitpur", "Bhaktapur"]

target_customer_types:
  include: ["premium_dining", "hotel", "alcohol_channel_candidate"]
  exclude: ["consumer", "minor_facing_venue"]

allowed_source_policy:
  allowed_tiers: ["A", "B"]
  prohibited_sources: ["google_maps_or_places_export", "private_social", "login_required_source"]
  approved_source_ids: []

collection_mode:
  permitted_actions: ["search_query_design", "manual_company_candidate_review"]
  prohibited_actions: ["scrape", "download_bulk_data", "contact_enrichment", "email_verification", "send_message"]
  contact_processing_enabled: false
  crm_write_enabled: false

required_candidate_fields:
  - legal_or_trading_name
  - company_type
  - city
  - source_refs
  - source_tier_best
  - product_match_ids
  - product_match_reason_codes
  - candidate_status

score:
  model_version: "customer-targeting-v1"
  grade_gate: "manual_review_required"

stop_conditions:
  - "source terms or authorization missing"
  - "business_line ambiguity"
  - "DNC or deletion request"
  - "raw personal contact data"
  - "missing required business gate"

output_contract:
  format: "private structured candidate review"
  no_raw_contact_data_in_git_or_logs: true
  include: ["summary_counts", "reason_codes", "blocked_counts", "source_quality_summary"]
```

### 10.2 Codex 的确定性处理流程

1. 验证运行包只有一个 `business_line`，并检查产品 ID 是否属于该业务线。
2. 验证城市、客户类型、允许来源和禁止来源都存在；否则返回 `blocked_need_targeting_run_config`。
3. 只在已批准来源类别内寻找企业候选；不抓取、不绕过限制、不收集个人资料。
4. 对每个候选记录来源证据、业务线、产品匹配理由和缺失变量；不因名称/城市自动补全联系方式。
5. 运行去重、跨线污染、来源风险、DNC/删除和数据最小化检查。
6. 按第 8 节评分，输出 `score_total`、`grade`、`reason_codes`、`risk_flags` 和 `next_review_action`。
7. 仅把通过人工审核的候选交给未来、经批准的 CRM 准入接口；当前代码的 synthetic CRM 仍不可写入真实记录。
8. 输出脱敏汇总：来源等级数、各等级数量、各城市/客户类型数量、阻断原因和待补证据；不输出私人联系信息。

### 10.3 必须返回的结果类型

| 返回码 | 含义 | Codex 下一步 |
|---|---|---|
| `candidate_ready_for_manual_review` | 企业候选的来源和最小字段齐全，评分只是建议。 | 送人工审核。 |
| `hold_missing_evidence` | 缺少来源条款、公司身份、产品匹配或业务线证据。 | 补证据，不处理联系人。 |
| `hold_missing_business_gate` | 产品、合规、冷链、供应链、保留/DNC 或处理依据缺失。 | 维持内部 hold。 |
| `quarantined` | 存在来源、重复、跨线、个人资料或数据质量风险。 | 安全隔离并最小化保存。 |
| `suppressed_dnc` | DNC 或删除请求命中。 | 停止后续处理。 |
| `blocked_scope_or_authorization` | 本轮范围、来源授权或外部动作授权不满足。 | 不继续采集/CRM/联系。 |

## 11. 关键变量检查清单

### 11.1 所有 B2B 客户

- [ ] 公司主体与经营地址可由允许来源交叉验证；
- [ ] 客户类型、产品用途、城市和业务线清晰；
- [ ] 采购规模只记录公开或经允许的经营信号，不推断信用；
- [ ] 付款能力、账期、信用额度只能在未来合法的企业尽调阶段，按批准政策处理；
- [ ] 是否有进口中国商品/相关食品饮料经验，必须有证据；没有证据填 `unknown`；
- [ ] 是否有采购/品类/F&B/进口职责的业务入口，不能用私人联系人替代；
- [ ] 来源、DNC、删除、保留、去重、人工审核和数据责任人完整；
- [ ] B2C 只作为渠道客户分析，绝不建立个人消费者联系人名单。

### 11.2 汾酒专用

- [ ] 产品卡、授权、可售状态、库存、价格、价格有效期和配送责任有当前书面版本；
- [ ] 当地主体、酒类相关资格、年龄/地域限制、平台和导流边界已由责任人确认；
- [ ] 客户具备成人餐饮、酒类渠道、商务礼赠或酒店 F&B 的可验证场景；
- [ ] 不以“高端”“国际化”“中国相关”等模糊词直接判断采购能力；
- [ ] 不面对未成年人，不主张健康功效，不鼓励过量饮酒；
- [ ] 第一次接触前由人工选择对话目的，且不在缺事实时生成价格、库存、交期或合规承诺。

### 11.3 海鲜专用

- [ ] SKU/产品族、规格、净重、标签、批次、保质期、原产地、过敏原、温度要求与食品资料有供应链证据；
- [ ] 客户的冷冻储存、收货、配送、温控、验收和异常处理能力有可核验证据；
- [ ] 进口/食品登记/许可责任主体与当前状态明确，不从客户类型推断；
- [ ] 客户是否需要大宗、分销、门店零售或餐饮菜单用途清晰；
- [ ] 采购频率、最小订量、季节性、损耗和对账方式只记录已确认的企业信息；
- [ ] 任何不满足冷链或食品安全底线的候选都不能被高产品匹配分数覆盖。

## 12. 反馈闭环与版本更新

每个未来真实阶段都必须把下列**聚合且脱敏**反馈写入评估，而不是只积累名单：

```text
source_acceptance_rate
duplicate_rate
manual_review_pass_rate
missing_evidence_rate
grade_distribution
contact_processing_rejection_rate
DNC_or_delete_rate
draft_approval_rate
reply_rate               # 仅在独立授权的 future live-pilot 后才启用
qualified_opportunity_rate
reason_code_outcomes
```

在经授权的 future live-pilot（受控真实试点）中，每个候选的受控 `outcome_metrics_ref` 至少应能关联以下状态码，而非保存原始邮件或聊天正文：`contact_attempt_count`、`last_outcome`、`not_interested_reason_code`、`human_handoff_required`、`qualified_opportunity`、`suppressed_dnc`。这些字段没有成为真实外联授权前必须保持空值。

评分模型的调整必须：

1. 有新的 `score_version`、变更理由和前后对比；
2. 不降低 DNC、处理依据、业务闸门或跨线隔离要求；
3. 不用少量回复或成交案例把策略假设升级为普遍事实；
4. 通过人工审核和独立复核后才应用于下一批；
5. 保留停止线：数据质量、投诉/DNC、合规、冷链或供应链事实不达标时，立即暂停扩大范围。

## 13. 后续执行前置条件与交接顺序

### 13.1 正确顺序

```text
本规范（业务定义）
  -> 用户重新确认真实获客是否进入正式范围
  -> 来源与数据治理书面输入
  -> P08 真实供应链资料进入与批准事实
  -> P08-RAB-01：value-free 来源/隐私合同
  -> P08-RAB-02：受审候选、评分、内部 CRM 准入与草稿合同
  -> P08-RAB-03：fake/sandbox Gmail outbox 与回复合同
  -> 单独授权的受控 live pilot
```

### 13.2 本规范不能解除的阻断

本规范完成后，以下仍为 `BLOCKED`：真实来源采集、联系人处理、CRM 写入、Gmail OAuth、邮件发送、回复处理、真实报价/订单、汾酒公开酒类营销、海鲜进口/冷链履约。它使未来工作“知道该判断什么”，不使任何业务行为自动合法、可行或已获授权。

## 14. 资料来源与可复核引用

- 项目范围、业务状态、事实源和业务线隔离：仓库 `AGENTS.md`、`PROJECT_ENTRY.md`、`docs/project/BUSINESS_STATUS.md`、`docs/project/CURRENT_STATUS.md`、`docs/project/SOURCE_OF_TRUTH.md`、`docs/project/SCOPE_AND_BOUNDARIES.md`、`GPT项目资料同步包_gpt_project_mechanism_sync/10_汾酒与海鲜业务线隔离机制_business_line_isolation.md`。
- 真实获客桥接的当前技术边界：`docs/implementation/PHASE_8_REAL_ACQUISITION_BRIDGE_PLAN.md`。该文件已明确当前 real crawl、真实联系人和 Gmail 外发未获授权。
- 海鲜产品结构：用户上传《尼泊尔市场冻品2026年第一批次进货清单》（5 页，2026-08-23 视觉与文本提取核验）；该原始附件不提交到仓库。
- 地域研究入口： [National Population and Housing Census 2021](https://censusresults.nsonepal.gov.np/)；[Nepal Tourism Board Statistics](https://trade.ntb.gov.np/downloads-cat/nepal-tourism-statistics/)。
- 海鲜食品/进口待核验入口： [DFTQC Annual Bulletin](https://www.dftqc.gov.np/downloadfiles/DFTQC-Annual-Bulletin-Eng-2082-Book-for-WEB-%281%29-1779272721.pdf)；[DFTQC product registration format](https://www.dftqc.gov.np/noticefiles/46-1742812951.pdf)。这些官方资料仅说明存在相关流程，不能替代本项目的产品级合规结论。
- Google Maps 禁止路线： [Google Maps Platform Terms](https://cloud.google.com/maps-platform/terms)，其中禁止把 Maps 内容导出、提取或抓取供服务外使用。

---

## 15. 实施设计层（供未来 Codex 任务卡引用）

| 字段 | 本任务的确定内容 |
|---|---|
| `primary_route` | 经批准的 A/B 级来源 -> 公司候选 -> 来源/范围/去重/人工审核 -> 未来私有 CRM 准入；先无联系人、无发送。 |
| `fallback_route` | 由用户/供应链提供的、书面许可的最小企业名单或 CSV，在私有受控导入中按同一 schema 审核；不把 raw 数据写入 Git。 |
| `capability_status` | `specification_ready`; `real_discovery_not_authorized`; `real_contact_processing_blocked`; `real_send_blocked`。 |
| `probe_required` | 是。先以 value-free fake contracts 验证来源、范围、DNC、保留和评分；再由批准来源进行最小人工质量探测。 |
| `allowed_codex_autonomy` | 读取本规范、生成查询设计、检查 schema、对已经获得批准的私有候选做去重/评分建议和脱敏报告。 |
| `forbidden_codex_guessing` | SKU、价格、库存、客户许可、付款能力、联系人身份/邮箱、冷链能力、合规、来源授权、DNC、发送许可、业务线归属。 |
| `required_inputs` | 单业务线运行包、产品范围、城市集群、目标客户类型、允许来源、数据治理/处理依据、业务闸门事实版本。 |
| `required_outputs` | 脱敏候选审核汇总、来源质量、评分理由、风险/阻断计数、人工复核队列；不输出/提交 raw 联系人。 |
| `execution_entrypoints` | 未来 `P08-RAB-01` 到 `P08-RAB-03` 独立任务卡；当前无需新增代码或 provider。 |
| `validation_commands` | 未来需覆盖 source policy、business-line isolation、DNC、retention/deletion、score replay、raw PII/secret/path scan、zero-fetch/zero-send 回归。 |
| `blocked_if_missing` | 范围确认、来源 owner/条款、联系人处理依据、DNC/保留/删除、供应链批准事实、当地责任主体/合规、私有存储、人工审批或用户外部动作授权任一缺失。 |
