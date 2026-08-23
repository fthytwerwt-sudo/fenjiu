# Fenjiu Source Catalog｜汾酒真实客户来源目录

> **状态：** `source_catalog_ready`（仅来源研究完成）
> **业务线：** `fenjiu_nepal`
> **版本：** `2026-08-23 / v1`
> **本目录不做：** 不建立企业名单、不处理联系人、不写 CRM、不发送信息、不改变汾酒当前 TikTok 上线准备范围。

## 1. 使用边界

本目录只回答未来最小企业发现测试应从哪里开始，以及每个来源能否用于三种不同动作：

1. `Discovery Permission`：发现企业名称及企业存在；
2. `Company Data Use`：将最小化的公司级字段写入未来私有 candidate store（候选存储）；
3. `Contact Processing`：处理企业邮箱、电话或 WhatsApp 等联系方式。

三项不是同一授权。任何来源公开展示联系方式，都**不**自动使 `Contact Processing=allowed`。

本目录不确认汾酒 20 年/30 年的 SKU、规格、价格、库存、授权、当地可售性或任何客户的酒类资格；这些仍是 `BLOCKED` 的业务闸门。

## 2. 研究结果摘要

| 指标 | 数量 | 说明 |
|---|---:|---|
| 实际研究来源 | 10 | 每项均已打开其主页/目录、可得条款或访问说明；缺条款也显式记录。 |
| `APPROVED_FOR_DISCOVERY` | 1 | 仅限 OpenStreetMap 的低频、可归因企业发现；不能使用公共 Nominatim 做系统化名单下载。 |
| `CONDITIONAL` | 4 | 关联目录真实且有价值，但第三方复用/存储许可未明确，或需要来源方书面确认。 |
| `MANUAL_ONLY` | 3 | 只可作为人工找线索或定位协会入口，必须回公司自有官网或获许可来源交叉验证。 |
| `REJECTED` | 2 | 明确禁止自动化/商业复用，或不适合商业获客用途。 |

## 3. 来源目录

| ID | 来源、Owner（运营方）与入口 | 适配客户类型 | 可见公司字段 | 企业数据 / 联系人处理 | 裁决与原因 |
|---|---|---|---|---|---|
| `FEN-OSM-POI-NP` | [OpenStreetMap](https://www.openstreetmap.org/)；OpenStreetMap Foundation；[ODbL 许可](https://www.openstreetmap.org/copyright)、[Nominatim 使用政策](https://operations.osmfoundation.org/policies/nominatim/) | 酒店、餐饮、酒类零售等可映射企业 POI（兴趣点） | 名称、类别、位置、部分网站/营业时间标签；质量逐项不保证 | 公司字段：`conditional`，须保留 ODbL 归因并评估 derivative database（衍生数据库）义务；联系人：`prohibited` | `APPROVED_FOR_DISCOVERY`。只允许低频、单企业/单查询的发现与回官网验证；Nominatim 明确反对系统化查询和完整 POI 下载。 |
| `FEN-HAN-MEMBER-DB` | [Hotel Association Nepal](https://hotelassociationnepal.org.np/)；[Membership Database](https://hotelassociationnepal.org.np/storage/Membership%20database.pdf) | 高端酒店、酒店 F&B、宴会 | 酒店名称、星级/类别；目录版本未标明最新日期 | 公司字段：`conditional`；联系人：`prohibited` | `CONDITIONAL`。协会 owner、会员目录和酒店类别可核验，但网站未发现可复用条款/隐私页；需 HAN 书面确认后才允许候选池存储。 |
| `FEN-FNCCI-MEMBER-DB` | [FNCCI](https://www.fncci.org/) Member Database；包含餐饮协会、双边商会、行业协会等组织目录 | 餐饮协会、双边商会、品类协会、区域商会 | 组织名、类别、地区、部分官网与组织联系信息 | 公司字段：`conditional`；联系人：`prohibited` | `CONDITIONAL`。FNCCI 是明确 owner，目录可发现组织和验证协会存在；主页未发布可复用条款，且组织页可能含个人资料，不能导出或处理联系人。 |
| `FEN-CNI-MEMBERS` | [Confederation of Nepalese Industries (CNI) Members](https://cni.org.np/members)；[Privacy Policy](https://cni.org.np/privacy-policy) | 酒类/饮料相关企业、分销/贸易企业、酒店/活动相关企业、企业礼赠候选 | 公司名、会员类别、地址、部分代表/业务字段 | 公司字段：`conditional`；联系人：`prohibited` | `CONDITIONAL`。官方行业组织的公司目录可用于人工筛选；已阅读隐私页，但未定位明确的第三方数据复用许可，因此不得把页面中的人员、电话或邮箱写入候选池。 |
| `FEN-LAK-MEMBER-DIRECTORY` | [Liquor Association of Kathmandu (LAK)](https://lak.org.np/)；[Terms](https://lak.org.np/legal/terms-and-conditions)；网站含 Members / Trade Directory 入口 | 酒类零售、分销、行业网络 | 会员/目录的公开公司级字段取决于登录外页面，当前未完成目录读取 | 公司字段：`conditional`；联系人：`prohibited` | `CONDITIONAL`。目标客户类型匹配度高，且网站明确由 LAK 提供服务；条款保留服务文本和设计的复制/再利用权，成员页读取又出现超时，故只可在 LAK 书面许可或人工审核下使用。 |
| `FEN-REBAN-ASSOCIATION` | [Restaurant & Bar Association of Nepal (REBAN)](https://rebannepal.com/)；[Membership page](https://rebannepal.com/memberships)；可由 [FNCCI REBAN 条目](https://fncci.org/member/anca.php)交叉验证协会存在 | 餐厅、酒吧、酒店 F&B 的协会入口 | 协会/章节和会员资格说明；未得到可复用的逐店会员目录 | 公司字段：`unknown`；联系人：`prohibited` | `MANUAL_ONLY`。可人工定位餐饮行业入口，再从公司自有官网或批准来源验证；不将协会页面或入会表单信息存入候选池。 |
| `FEN-NTB-ACCOMMODATION` | [Nepal Tourism Board Accommodation](https://trade.ntb.gov.np/travel-essentials/accommodations/) | 酒店、度假村、宴会场地的官方验证入口 | 行业/住宿类别信息；页面指向 HAN 和 NTB 自身酒店目录入口 | 公司字段：`unknown`；联系人：`prohibited` | `MANUAL_ONLY`。政府/旅游机构 owner 清晰，但该页面不是可复用客户数据库；只用于找到 HAN 或企业自有站点并验证行业相关性。 |
| `FEN-TEPC-CCI-DIRECTORY` | [Trade and Export Promotion Centre Useful Addresses](https://tepc.gov.np/pages/useful-addresses-in-nepal) | 区域商会、进口/贸易组织、Pokhara/Chitwan 等区域 fallback | 商会名称、地区、官方网站入口 | 公司字段：`unknown`；联系人：`prohibited` | `MANUAL_ONLY`。用于定位地方商会/贸易协会，再请求其许可或转企业官网；不是直接企业名单。 |
| `FEN-NEPALYP` | [Nepal Business Directory](https://www.nepalyp.com/)；[Terms](https://www.nepalyp.com/terms-of-use)；[Privacy](https://www.nepalyp.com/privacy-policy) | 理论上覆盖酒店、餐饮、酒类企业 | 企业资料、地址、联系方式等可能可见 | 公司字段：`prohibited`；联系人：`prohibited` | `REJECTED`。条款禁止脚本/crawler、商业复制或利用数据库内容；目录 owner 为 GBD，且资料可能含个人信息。不能用于未来 Codex 候选池。 |
| `FEN-OPENCORPORATES` | [OpenCorporates data-access notice](https://knowledge.opencorporates.com/knowledge-base/website-data-access-changes/) | 法人身份辅助核验（非行业发现） | 公司法定实体属性，具体访问依赖覆盖范围/登录 | 公司字段：`conditional`；联系人：`prohibited` | `REJECTED`。部分公司数据需注册，商业使用可能收费；本目录没有确认 Nepal 覆盖与商业数据许可，不能作为本项目的来源。 |

### 3.1 明确排除的来源方式

- Google Maps / Places 内容抓取、导出、缓存或用作名单：`REJECTED`；Google 条款禁止将其企业名称、地址、评论等内容导出/提取供服务外使用。
- 登录绕过、验证码绕过、私人社交资料、付费贸易数据库的联系人产品、泄露名单：`REJECTED`。
- 将协会负责人、委员会成员、个人电话或邮箱当作企业采购联系人：`REJECTED`。

## 4. Primary + Fallback（主来源与备用来源）

| 目标客户类型 | Primary | Fallback 1 | Fallback 2 | 当前限制 |
|---|---|---|---|---|
| 高端酒店 / Hotel F&B / 宴会 | `FEN-OSM-POI-NP` | `FEN-HAN-MEMBER-DB` | `FEN-NTB-ACCOMMODATION` | 只有 OSM 的低频公司发现获批准；HAN/NTB 都须回官网或取得书面许可。 |
| 高端中餐 / 泛亚洲餐饮 | `FEN-OSM-POI-NP` | `FEN-REBAN-ASSOCIATION` | `FEN-FNCCI-MEMBER-DB` | REBAN/FNCCI 只定位协会或人工线索，不能直接复制企业/联系人资料。 |
| 酒类进口 / 分销 / 精品零售 | `FEN-OSM-POI-NP` | `FEN-LAK-MEMBER-DIRECTORY` | `FEN-CNI-MEMBERS` | 酒类执照、进口资格、品牌授权必须另行书面核验；目录不构成许可。 |
| 企业礼赠 / 会展 / 商务场景 | `FEN-CNI-MEMBERS` | `FEN-FNCCI-MEMBER-DB` | `FEN-TEPC-CCI-DIRECTORY` | **没有本轮已批准的直接来源。** 只能人工建立来源许可路径，不能进入最小自动发现测试。 |

## 5. Nepali（尼泊尔语）关键词实际检索验证

搜索引擎只用于发现来源，不是候选数据来源。实际测试显示，本地语言词经常返回法规、消费者内容、跨国/非尼泊尔结果或一般目录，因此英文查询仍是首选；下列词仅保留为人工辅助，不进入自动批量查询。

| 关键词组 | `search_result_fit` | `recommended` | 结论 |
|---|---|---:|---|
| `चिनियाँ रेस्टुरेन्ट`、`उच्चस्तरीय रेस्टुरेन्ट`、`भोज रेस्टुरेन्ट` | `mixed` | false | 能发现餐饮相关页面，但结果跨国/泛消费混杂，先用英文城市组合，必要时人工复核。 |
| `मदिरा आयातकर्ता`、`मदिरा वितरक`、`पेय पदार्थ वितरक` | `mixed` | false | 更常出现酒类法规、协会或新闻，而非可许可的企业目录；用于协会/监管研究，不用于自动发现。 |
| `पाँच तारे होटल`、`बुटिक होटल`、`होटल खाद्य तथा पेय` | `mixed` | false | 酒店/餐饮语义合理，但采购/F&B 词无法稳定返回企业采购入口；使用 HAN/NTB/企业官网路线。 |
| `कर्पोरेट उपहार`、`व्यावसायिक उपहार`、`कार्यक्रम उपहार` | `poor` | false | 结果不足以稳定识别企业礼赠或会展客户。 |
| `मदिरा पसल`、`वाइन पसल`、`विशेष पेय पसल` | `mixed` | false | 能指向零售相关页面，但无法证明主体、许可或目录复用权；先从 LAK 的许可路径人工核验。 |

## 6. 最小真实客户发现测试的允许边界

本目录使 `source_catalog_ready` 成立，但只允许未来单独任务在下列窄范围内测试：

```yaml
business_line: fenjiu_nepal
approved_source_ids:
  - FEN-OSM-POI-NP
allowed_action: low-frequency company discovery followed by company-owned-website verification
result_handling: transient_discovery_only; no candidate-store persistence
prohibited_action:
  - systematic Nominatim queries
  - bulk POI download
  - contact collection
  - CRM write
  - external outreach
  - quotation or product commitment
```

若不能满足 ODbL attribution（归因）和公共服务使用政策，或无法回企业自有官网验证，则停止并输出 `hold_missing_evidence`。

## 7. 事实等级与未解除阻断

- **已确认**：以上来源的 owner、入口、可见字段和已公开的条款/访问限制，均在 2026-08-23 实际打开核验。
- **部分成立**：`FEN-OSM-POI-NP` 可用于有限企业发现，但字段完整度、数据新鲜度和每个企业的真实性仍须逐项验证。
- **待验证**：HAN、FNCCI、CNI、LAK 的企业级数据存储许可；所有联系方式处理依据；任何目标企业的采购能力和酒类资格。
- **BLOCKED**：真实联系人、CRM、Gmail、产品事实/报价、当地酒类合规与外部触达。
