# Seafood Source Catalog｜海鲜真实客户来源目录

> **状态：** `source_catalog_ready`（仅来源研究完成）
> **业务线：** `seafood_nepal`
> **版本：** `2026-08-23 / v1`
> **产品范围：** `shrimp`、`fish`、`shellfish_mollusc`、`premium_specialty`、`crayfish`。
> **本目录不做：** 不创建客户名单、不收集联系人、不处理贸易数据库联系人、不写 CRM、不发信、不确认进口/食品/冷链履约。

## 1. 使用边界

海鲜 PDF 只能支持产品族匹配；它不支持价格、库存、温控、原产地、标签、保质期、食品许可或冷链履约结论。本目录同样将以下三项分开判断：

1. `Discovery Permission`：是否可发现企业名称和企业存在；
2. `Company Data Use`：最小公司字段能否进入未来私有 candidate store（候选存储）；
3. `Contact Processing`：邮箱、电话、WhatsApp 等业务联系信息能否被处理。

`Company Data Use` 即使为 `conditional`，也不允许联系人处理；食品进口、登记和冷链是独立业务闸门。

## 2. 研究结果摘要

| 指标 | 数量 | 说明 |
|---|---:|---|
| 实际研究来源 | 12 | 每项均已打开来源主页/目录、官方相关页面或条款，并记录其使用限制。 |
| `APPROVED_FOR_DISCOVERY` | 1 | 仅限受 ODbL 约束的 OpenStreetMap 低频企业发现；不含 Nominatim 系统化枚举。 |
| `CONDITIONAL` | 3 | 来源 owner 与目录价值明确，但复用/存储授权未充分明确。 |
| `MANUAL_ONLY` | 5 | 只能人工定位行业或企业自有官网，不能直接复制为 candidate data。 |
| `REJECTED` | 3 | 需要登录/付费/联系人产品，或条款禁止自动化/商业数据库复用，或根本不是公开企业发现目录。 |

## 3. 来源目录

| ID | 来源、Owner（运营方）与入口 | 适配客户类型 | 可见公司字段 | 企业数据 / 联系人处理 | 裁决与原因 |
|---|---|---|---|---|---|
| `SEA-OSM-POI-NP` | [OpenStreetMap](https://www.openstreetmap.org/)；OpenStreetMap Foundation；[ODbL](https://www.openstreetmap.org/copyright)、[Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/) | 酒店、餐饮、超市、冷库等可映射企业 POI | 名称、类别、位置、部分网站/营业信息；逐条完整性不保证 | 公司字段：`conditional`，须满足 ODbL 归因/衍生数据库处理；联系人：`prohibited` | `APPROVED_FOR_DISCOVERY`。只作低频单企业发现与企业自有官网验证；公共 Nominatim 禁止系统化区域 POI 下载。 |
| `SEA-HAN-MEMBER-DB` | [Hotel Association Nepal](https://hotelassociationnepal.org.np/)；[Membership Database](https://hotelassociationnepal.org.np/storage/Membership%20database.pdf) | 酒店采购、Hotel F&B、宴会餐饮 | 酒店名称、星级/类别 | 公司字段：`conditional`；联系人：`prohibited` | `CONDITIONAL`。官方行业协会的酒店/类别线索价值高，但未找到对第三方候选存储的许可；必须请求书面确认并回企业官网。 |
| `SEA-FNCCI-MEMBER-DB` | [FNCCI Member Database](https://www.fncci.org/)；含 [Association of Cold Storages of Nepal](https://fncci.org/member/anca.php) 等组织条目 | 冷库协会、食品/贸易/区域商会、行业入口 | 组织名、地区、协会类别、部分官网 | 公司字段：`conditional`；联系人：`prohibited` | `CONDITIONAL`。可发现协会和行业网络，不能把组织页中的个人资料或联系方式迁入候选记录。 |
| `SEA-CNI-MEMBERS` | [CNI Members](https://cni.org.np/members)；[Privacy Policy](https://cni.org.np/privacy-policy) | 食品企业、分销/贸易企业、酒店/零售相关企业 | 公司名、会员类别、地址及部分代表字段 | 公司字段：`conditional`；联系人：`prohibited` | `CONDITIONAL`。行业组织 owner 清晰，具有食品/贸易企业发现价值；未找到第三方商用复用授权，故须人工许可/官网复验。 |
| `SEA-COLD-STORAGE-ASSOCIATION` | Association of Cold Storages of Nepal，由 [FNCCI 组织目录](https://fncci.org/member/anca.php)和 [政府行业 profile](https://giwmscdnone.gov.np/media/pdf_upload/2_merged-1_aqcr2dn.pdf)交叉支持 | 冷库/冷链运营商 | 协会身份、地址、会员数量、覆盖地区；无公开会员企业清单 | 公司字段：`unknown`；联系人：`prohibited` | `MANUAL_ONLY`。可用于寻找协会许可或推荐的企业官网，不是冷库企业名单；绝不能据协会会员数推断具体企业能力。 |
| `SEA-REBAN-ASSOCIATION` | [REBAN](https://rebannepal.com/)；[Membership page](https://rebannepal.com/memberships)；FNCCI 条目可辅助验证 | 海鲜餐厅、中餐厅、火锅、酒店 F&B | 协会/章节与会员资格描述；没有可复用企业目录 | 公司字段：`unknown`；联系人：`prohibited` | `MANUAL_ONLY`。只作餐饮行业入口和人工研究线索，后续必须回到企业自有官网或获许可目录。 |
| `SEA-NTB-ACCOMMODATION` | [Nepal Tourism Board Accommodation](https://trade.ntb.gov.np/travel-essentials/accommodations/) | 酒店、度假村、餐饮设施 | 住宿行业说明、官方 HAN 路由 | 公司字段：`unknown`；联系人：`prohibited` | `MANUAL_ONLY`。官方旅游入口可辅助定位酒店验证路径，但不是允许的采购/客户数据目录。 |
| `SEA-TEPC-CCI-DIRECTORY` | [Trade and Export Promotion Centre Useful Addresses](https://tepc.gov.np/pages/useful-addresses-in-nepal) | 地方商会、贸易/进口组织、区域 fallback | 商会名、地区、官方网址入口 | 公司字段：`unknown`；联系人：`prohibited` | `MANUAL_ONLY`。适合找到区域商会/协会并取得许可，不直接产生食品进口商或冷库企业候选。 |
| `SEA-DIRECTORYOFNEPAL` | [DirectoryOfNepal Cold Storage category](https://www.directoryofnepal.com/category/553/cold-storage.html)；[Privacy Policy](https://www.directoryofnepal.com/about/3/privacy-policy.html) | 冷库、冻品分销、食品/饮料、酒店、超市 | 企业名、类别、地区、公开业务资料可能可见 | 公司字段：`unknown`；联系人：`prohibited` | `MANUAL_ONLY`。目录 owner 对业务信息及公开联系方式有隐私说明，但未定位允许第三方存储/复用的条款；只能人工发现后回企业官网核验。 |
| `SEA-NEPALYP` | [Nepal Business Directory](https://www.nepalyp.com/)；[Terms](https://www.nepalyp.com/terms-of-use)；[Privacy](https://www.nepalyp.com/privacy-policy) | 理论上覆盖食品、进口、冷库、餐饮和零售 | 企业资料与联系方式可能可见 | 公司字段：`prohibited`；联系人：`prohibited` | `REJECTED`。条款禁止自动化访问与商业利用/复制数据库数据，且网站数据库可能含个人信息。 |
| `SEA-DFTQC-NNSW` | [DFTQC 食品进口通知](https://www.dftqc.gov.np/noticefiles/113-1742816126.pdf)；NNSW 作为食品进口许可流程入口 | 食品进口合规核验，不是客户发现 | 许可流程/法规信息；没有本轮确认的公开企业目录 | 公司字段：`prohibited`；联系人：`prohibited` | `REJECTED`。它是监管/申请流程而不是可发现企业的公开目录；登录、主体权限或产品级适用性都不能绕过。 |
| `SEA-TRADE-INTELLIGENCE-PAID` | [Volza Frozen Fish Buyer page](https://www.volza.com/p/frozen-fish/buyers/buyers-in-nepal/)；同类付费贸易/决策人数据库 | 进口商/冻海鲜批发商理论上高度相关 | 贸易、价格、数量、公司和决策人资料可能可见 | 公司字段：`prohibited`；联系人：`prohibited` | `REJECTED`。页面推广付费公司/决策人数据和联系人产品；本轮禁止使用付费名单、真实联系人或贸易数据进行获客。 |

### 3.1 明确排除

- Google Maps / Places 抓取、导出、缓存或名单落库；
- 付费贸易情报平台的买家名单、价格、货量或决策人模块；
- 任何需要登录、验证码、爬虫绕过或个人资料的目录；
- 把新闻、论坛、餐饮点评网站、Google/Tripadvisor/Cybo 等搜索结果当企业事实或冷链证明；
- 将“海鲜/冻品相关”名称当成客户具备进口、食品登记、冷库或配送能力的事实。

## 4. Primary + Fallback（主来源与备用来源）

| 目标客户类型 | Primary | Fallback 1 | Fallback 2 | 当前限制 |
|---|---|---|---|---|
| 酒店采购 / Hotel F&B | `SEA-OSM-POI-NP` | `SEA-HAN-MEMBER-DB` | `SEA-NTB-ACCOMMODATION` | 只可低频发现企业后回官网；酒店存在不证明采购、冷库或食品收货能力。 |
| 海鲜餐厅 / 中餐 / 火锅 | `SEA-OSM-POI-NP` | `SEA-REBAN-ASSOCIATION` | `SEA-FNCCI-MEMBER-DB` | 餐饮类别仅为产品用途假设，必须逐店验证菜单/储存和企业主体。 |
| 冻品批发 / 冷库 / 冷链 | `SEA-OSM-POI-NP` | `SEA-COLD-STORAGE-ASSOCIATION` | `SEA-DIRECTORYOFNEPAL` | 只有 OSM 低频发现获批；协会/目录只作人工线索，不能写成冷库能力。 |
| 食品进口商 / 海鲜进口商 | `SEA-CNI-MEMBERS` | `SEA-FNCCI-MEMBER-DB` | `SEA-TEPC-CCI-DIRECTORY` | **没有本轮已批准的直接来源。** DFTQC/NNSW 是合规流程，不是企业名单。 |
| 超市 / 冻品零售 / foodservice | `SEA-OSM-POI-NP` | `SEA-CNI-MEMBERS` | `SEA-DIRECTORYOFNEPAL` | 门店或企业名不证明冷冻陈列、采购规模或配送条件。 |

## 5. Nepali（尼泊尔语）关键词实际检索验证

实际检索结果显示，本地语言词常返回法规、消费者内容、非企业目录或付费数据源。它们全部从正式 Codex 自动查询词库降级为 `manual_query_experiment_only`：可由人工尝试以发现协会/公司官网，但不能自动抓取、批量扩展或作为候选事实。

| 关键词组 | `search_result_fit` | `recommended` | 结论 |
|---|---|---:|---|
| `होटल खरिद विभाग`、`होटल खाद्य तथा पेय`、`होटल भान्सा` | `poor` | false | 未稳定定位公开采购/F&B 入口；改用英文 `hotel procurement` + 官网人工验证。 |
| `समुद्री खाना रेस्टुरेन्ट`、`माछा रेस्टुरेन्ट`、`हटपोट रेस्टुरेन्ट` | `mixed` | false | 能返回餐饮/点评内容，但不构成可复用企业目录。 |
| `फ्रोजन फूड वितरक`、`थोक वितरक`、`कोल्ड स्टोरेज`、`शीत भण्डार` | `mixed` | false | 冷库/冻品词能发现目录、协会和服务商，但来源许可与能力证明不稳定。 |
| `खाद्य आयातकर्ता`、`समुद्री खाना आयातकर्ता`、`फ्रोजन खाद्य आयातकर्ता` | `mixed` | false | 主要返回法规、付费贸易数据或泛进口信息；不可用作客户名单。 |
| `सुपरमार्केट`、`फ्रोजन फूड खुद्रा`、`किराना चेन` | `mixed` | false | 能发现零售相关内容，但不能验证门店冷柜、采购/进口能力或数据许可。 |

## 6. 最小真实客户发现测试的允许边界

```yaml
business_line: seafood_nepal
approved_source_ids:
  - SEA-OSM-POI-NP
allowed_action: low-frequency company discovery followed by company-owned-website verification
result_handling: transient_discovery_only; no candidate-store persistence
prohibited_action:
  - systematic Nominatim queries
  - bulk POI download
  - trade-intelligence database use
  - contact collection
  - CRM write
  - external outreach
  - import, food-safety, cold-chain, price, or inventory claims
```

未能满足 ODbL 归因/使用政策、来源证据或企业官网交叉验证时，必须输出 `hold_missing_evidence`，而不是继续收集资料。

## 7. 事实等级与未解除阻断

- **已确认**：来源 owner、入口、条款/访问限制与目录可见字段已经在 2026-08-23 实际打开研究。
- **部分成立**：`SEA-OSM-POI-NP` 可支持低频企业发现；并不证明数据完整、企业仍营业或经营海鲜相关业务。
- **待验证**：HAN/FNCCI/CNI/行业协会对公司级数据存储的许可；所有企业冷链、食品进口与采购事实。
- **BLOCKED**：联系人处理、真实 CRM、外发、食品/进口/产品登记、产品规格/温控、库存、价格、配送与履约。
