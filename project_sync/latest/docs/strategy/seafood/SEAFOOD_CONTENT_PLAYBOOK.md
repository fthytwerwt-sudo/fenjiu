# Nepal Seafood Content Playbook｜尼泊尔海鲜内容与 AI 视频执行手册

> **业务线：** `seafood_nepal`
> **制作方式：** AI 视频生成，目标为真实 `iPhone Natural Look`；不冒充实拍产品、门店、客户或当地履约。
> **发布状态：** `publish_blocked_pending_business_gates`。B2B 卡须 SF-2 解锁，B2C 卡须 SF-6 解锁。

## 1. 内容与销售路线必须分开

| Route | 首要客户问题 | 内容的唯一工作 | 进入条件 |
|---|---|---|---|
| B2B（Primary） | 规格、包装、菜单适配、储存、收货、损耗、交接与供货事实是否清楚？ | 帮采购方提出正确核验问题，推动合格采购对话 | 已批准 SKU、食品/冷链/商业/履约事实与接触授权。 |
| B2C（Secondary） | 怎样选择、储存、准备和使用已批准的冷冻海鲜？ | 建立真实产品/烹饪/服务信息的信任，导向合格询盘 | 已批准零售 SKU、标签、价格、库存、支付、配送、售后与外部授权。 |

产品卡中的 `SM-01` 至 `SM-20` 是货品单候选引用，不是可公开使用的品牌/产品资产。`asset_rights=UNKNOWN` 时，AI 不能复制包装、标签、产品图片或任何可辨认商标。

## 2. 客群与内容支柱

### 2.1 B2B 客群

| 客户类型 | 优先级 | 理由 | 需要验证的事实 |
|---|---|---|---|
| 酒店采购 / Hotel F&B | `P1 HYPOTHESIS` | 多 SKU、宴会与后厨可能有批量需求 | 菜单、冷冻存储、采购入口、收货/验收能力。 |
| 海鲜餐厅 / 中餐厅 / 火锅 | `P1 HYPOTHESIS` | 产品族可能存在菜单场景 | 菜单、后厨冷冻、规格偏好、收货能力。 |
| 冻品批发 / Foodservice | `P2 HYPOTHESIS` | 可能承接箱规与再分销 | 冷库、配送、食品主体、结算和退货。 |
| 食品进口 / 冷链 | `P2 HYPOTHESIS` | 可能协助合规/仓配链条 | 资质、当前品类、冷链、责任边界。 |

### 2.2 B2C 客群

所有 B2C 人群都为 `HYPOTHESIS`，不得称为已验证客户群。

- Kathmandu Valley 城市家庭：可能需要家庭聚餐与便利烹饪场景。
- 高收入家庭与海鲜爱好者：可能关注品类、包装与品质信息。
- 火锅/中餐爱好者：可能需要与中餐食材相配的内容灵感。
- 国际餐饮消费群体：可能更容易理解冷冻食材的规格/烹饪教育。

### 2.3 内容支柱

| Pillar | B2B / B2C | 客户问题 | 必须有的事实 |
|---|---|---|---|
| `specification-literacy` | B2B | 规格、净重、包装、等级怎样影响采购？ | 经批准的 SKU 卡；否则只讲“应核验什么”。 |
| `cold-chain-readiness` | B2B | 收货、储存、温控异常怎样提问？ | 供应链冷链 SOP；不能自行设温度。 |
| `menu-and-kitchen-fit` | B2B | 哪类形态适合哪类菜品/后厨流程？ | 客户菜单与 SKU 技术资料；否则为提问模板。 |
| `product-literacy` | B2C | 买冷冻海鲜前看什么？ | 已批准的标签/过敏原/储存信息。 |
| `meal-inspiration` | B2C | 今晚做什么、怎样准备？ | 只在商品/食品事实可用后讲具体食材。 |
| `trust-by-process` | Both | 为什么事实、标签、批次和收货链先于广告？ | 真实流程，不写虚假合规/库存。 |

## 3. AI iPhone Natural Look for Seafood

### 3.1 手机质感基准

- `vertical 9:16`、1080×1920 或 4K、24/30fps、1× 镜头视角为主；只有产品细节才用 2×。
- 模拟日常厨房、家庭餐桌或**无标识的**餐饮后厨，窗光/顶灯混合、轻微手持、真实台面水汽和环境声。
- 普通手机自动曝光、轻微构图不完美、自然色温、食材纹理可见；不使用电影棚灯、超饱和食材、镜面无菌厨房或过度慢动作。
- 包装、原料、锅具和冰霜必须像真实物理物件；绝不依赖模型生成可读标签、中文文字或重量数字。

### 3.2 AI Prompt 骨架

```text
Vertical 9:16 phone-camera footage aesthetic, 1x smartphone lens, gentle
handheld micro-movement, ordinary clean kitchen or dining table, believable
window light and warm practical lights, natural food texture, subtle steam and
ambient kitchen sound. Documentary social-video pace, no studio food commercial,
no logos, no readable labels, no exaggerated seafood size, no text rendered by AI.
```

补充本卡 `scene`、`object`、`motion`、`sound`、`do_not_show`。只有素材权利和产品事实都批准后，才可用真实包装 reference；reference 仍不能被模型重绘、改字、改数量或用于虚构门店。

### 3.3 强制禁止项

- AI 巨型虾、虚构“活鲜”、不真实冰霜、错误鱼/贝类物种、假产地、假清真/食品认证、假客户评价。
- 错误手指、锅具/玻璃/水汽变形、食材从生变熟不合物理、背景人物漂移、模型生成文字、标签乱码。
- 假冷库、假配送车、假当地餐厅或“尼泊尔现货/配送”叙事；未授权实拍门店同样不得使用。
- 把 B2B 采购内容剪成消费者秒杀广告，或把 B2C 烹饪内容暗示产品已可销售。

## 4. Hook Libraries

### 4.1 Seafood B2B Hooks（30 条）

1. 酒店厨房采购虾仁，真正影响出品稳定的往往不是价格。
2. 同样叫虾仁，后厨为什么先问规格？
3. 冷冻海鲜入库前，这一张信息卡比图片更重要。
4. 采购一箱海鲜，先别跳过收货窗口。
5. 一款产品能不能进菜单，先看哪三个问题？
6. 规格写得清楚，为什么仍然不能直接报价？
7. 后厨最怕的不是新品，而是信息不完整的新产品。
8. 冷链交接里，哪些事不能靠“应该没问题”？
9. 一份菜单需求，怎样变成正确的采购问题？
10. 为什么同一类虾，不同包装可能走向不同后厨流程？
11. 采购冻品，标签、批次和责任人为什么要一起看？
12. 供应稳定不是一句话，它至少包含这些确认点。
13. 宴会厨房为什么不能只看单箱重量？
14. 一家餐厅是否适合冻品，先别只看菜单。
15. 采购方问“有货吗”时，专业回答前要先核验什么？
16. 冷库能力不是看到冷柜就能确认。
17. 采购海鲜时，损耗问题应该怎样问才有用？
18. 食材到货后，什么信息能让异常更容易追溯？
19. 火锅店想试新食材，第一步不该是批量下单。
20. 菜品适配不是一句“很适合”，而是一套核验。
21. 为什么食品内容也需要版本和有效期？
22. 一次样品沟通，如何避免把未知说成承诺？
23. 采购链条中，谁应该确认规格，谁应该确认配送？
24. 价格之外，MOQ 为什么需要先说清？
25. 供应商资料里最容易漏掉的一个收货问题。
26. 餐厅如何把“想试试”变成可执行的验收计划？
27. 冷链中断发生时，谁来决定下一步？
28. 食材不是内容道具：镜头前也要先核对事实。
29. 为什么 B2B 内容不该只追求播放量？
30. 一次专业采购对话，最后应该留下什么记录？

### 4.2 Seafood B2C Hooks（30 条）

1. 今晚不知道做什么菜？先别急着买，先学会看这张标签。
2. 冷冻海鲜，不只看大小，还要先看这一点。
3. 一袋食材能不能让晚餐更轻松，关键在准备前。
4. 家庭聚餐的海鲜，怎样先把信息问清楚？
5. 火锅里的海鲜，什么时候下锅才值得先确认？
6. 买冷冻食材前，哪些信息不能只靠图片猜？
7. 为什么包装好看，也不能替代产品卡？
8. 想做一顿海鲜晚餐，先从哪一个问题开始？
9. 冷冻食材的便利，不等于可以忽略储存说明。
10. 一份家庭菜单，怎么挑到更适合的食材形态？
11. 食材进冰箱前，哪件事必须由标签告诉你？
12. 海鲜的“新鲜感”，不应该由滤镜决定。
13. 做菜前先看规格，能少掉哪些麻烦？
14. 一份火锅食材清单，怎样问得更清楚？
15. 家庭料理不必复杂，但信息必须真实。
16. 冷冻海鲜的第一步，不是直接下锅。
17. 为什么过敏原信息值得被单独放大？
18. 一顿饭的安心感，从确认产品信息开始。
19. 看不懂包装时，应该向谁问什么？
20. 一次好的购买咨询，应该先得到哪些答案？
21. 海鲜烹饪灵感，也要先有真实食材基础。
22. 不是每种海鲜都适合用同一个做法。
23. 家庭餐桌上，怎样让每个人都知道这道菜是什么？
24. 10 分钟料理的前提，可能比 10 分钟更重要。
25. 烹饪视频里最该出现的，不只是成品画面。
26. 一个好食材故事，为什么不能编产地？
27. 做火锅前，先问清这三个储存问题。
28. 购物前的一个小问题，可能帮你避免一整晚的麻烦。
29. AI 可以做镜头，不可以替产品写标签。
30. 当信息还没核验时，最负责任的 CTA 是什么？

## 5. Caption、CTA 与语言控制

- **首发语言建议：** English，理由是面向尼泊尔市场的工作假设；Nepali 使用前必须 `native_review_required=true`；Chinese 只用于内部审核/供应链协作。
- **B2B 可用 CTA（SF-2 后）：** `Request the approved product-information checklist.`、`Tell us your menu, receiving and storage questions.`
- **B2C 可用 CTA（SF-6 后）：** `Ask for the verified product and storage information for your area.`
- **未解锁前 CTA：** `Save this verification guide.`、`What product information would you want checked first?`
- **绝对禁止：** 价格、即时库存、当天配送、温度/保质期数字、原产地、食品认证、过敏原、付款和下单 CTA，除非全部绑定有效的供应链事实。
- **Pinned comment：** `Product availability, food documentation, storage guidance, price and delivery details are only shared after the approved local product record is in place.`

## 6. First Content Batch｜24 张内容卡

**所有卡的共用控制：** `business_line=seafood_nepal`；`fact_lock_required=true`；`asset_rights_required=true`；`publish_status=publish_blocked_pending_business_gates`；不使用货品单照片作视频素材，除非供应链另行书面批准其使用权。

### 完整 B2B 卡 SF-C01｜采购虾仁，先别只问价格

- **Target / objective / funnel：** 酒店/餐厅采购候选；把问题从价格转向规格/验收；`B2B discovery`。
- **Platform / duration / opening：** SF-2 后的单一获准 B2B 信任触点；30 秒；“酒店厨房采购虾仁，真正影响出品稳定的往往不是价格。”
- **Full script / VO：** “价格当然重要，但它不能替代规格、净重、包装、批次、储存要求和收货标准。采购前先把这些问题问清楚，才能知道这款产品是否真的适合后厨。信息越完整，后面的沟通越有效。”
- **Shot list / AI visual prompt：** 无标识后厨备料台、成人手写六项核验卡、空白冷冻包装轮廓、电子秤但不显示数字；手机手持视角、自然顶灯、锅具环境声；`prohibit=logos, labels, real hotel, fake product.`
- **On-screen / caption / CTA：** `Spec. pack. batch. storage. receiving.` Caption：`For a kitchen, clarity is part of consistency.` CTA：`Save the procurement checklist.`
- **Proof needed / compliance / recording / metric：** 不提任何 SKU；SF-2 前只内部。AI 后期字幕人工制作；指标为 `qualified_procurement_question`，无合格对话/无接触授权则 Stop。

### 完整 B2B 卡 SF-C02｜菜单适配先问三件事

- **Target / objective / funnel：** 中餐/火锅/海鲜餐厅候选；采购资格教育；`B2B discovery`。
- **Duration / opening / script：** 25 秒；“一款冷冻海鲜能不能进菜单，先看三个地方。” VO：“第一，是菜单到底需要什么形态和规格。第二，是后厨有没有相应的储存和收货流程。第三，是供应链能否用当前资料把标签、批次、价格和交接说清楚。三个答案都在，才值得继续试。”
- **Shot / text / caption / CTA：** 无品牌菜单、空白规格卡、冰箱门外观但不冒充冷库；`Menu. kitchen. facts.`；`A menu fit is a verified conversation, not a guess.`；`What would your kitchen verify first?`
- **Proof / compliance / metric:** 需要 SF-1 的真实 SKU 才可替换通用表述；不说“适合火锅/餐厅”。测合格问题，政策/事实不全则不发布。

### 完整 B2B 卡 SF-C03｜收货窗口比你想的更重要

- **Target / objective / funnel：** 酒店/批发候选；强调履约核验；`trust`。
- **Duration / opening / script：** 30 秒；“采购一箱海鲜，先别跳过收货窗口。” VO：“产品能不能按时到，只是第一层。更重要的是谁收货、怎样验收、异常如何记录、温控和责任由谁确认。没有这些信息，‘可以配送’并不等于可履约。”
- **Shot / text / caption / CTA：** 无标识收货台、成人核对表、时钟、空白箱体；`Receiving is part of the product.`；`A delivery claim needs an acceptance path.`；`Save the receiving questions.`
- **Proof / compliance / metric：** 不说配送服务已存在；发布需 SF-1+SF-2；主指标为收货/履约类信息请求；无事实就回内部培训。

### 完整 B2B 卡 SF-C04｜标签不是最后一步

- **Target / objective / funnel：** 冻品渠道/餐饮采购；`trust → qualified conversation`。
- **Duration / opening / script：** 25 秒；“冷冻海鲜入库前，这一张信息卡比图片更重要。” VO：“图片能让人看见食材，标签和产品卡才能让人知道它是什么、来自哪一批、怎样保存、谁负责回答问题。对采购和后厨来说，清楚的信息比漂亮画面更有价值。”
- **Shot / text / caption / CTA：** 无文字包装背面抽象特写、后期信息卡；`A picture is not a product record.`；`Trust starts with a verifiable record.`；`Request the approved information checklist when available.`
- **Proof / compliance / metric：** 禁止用 AI 生成标签；B2B 的合规/产品事实未 READY 即不对外；评估资料请求质量。

### 完整 B2B 卡 SF-C05｜冷库不是一个假设

- **Target / objective / funnel：** 批发/冷链/餐饮候选；`B2B discovery`。
- **Duration / opening / script：** 25 秒；“看到冷柜，不等于冷链已经准备好了。” VO：“要确认的还有储存规则、配送过程、收货时间、异常处置和责任人。冷链不是一个镜头里的冰箱，它是一条被记录、被检查、能处理异常的流程。”
- **Shot / text / caption / CTA：** 无 logo 立式冷柜外观、温度计不显示数值、人工流程卡；`Cold chain is a process.`；`Ask for the evidence, not the impression.`；保存。
- **Proof / compliance / metric：** 不给温度数字；如出现冷链承诺需求，转供应链人工；无批准 SOP 不发布。

### 完整 B2B 卡 SF-C06｜样品前先锁定问题

- **Target / objective / funnel：** 餐厅/酒店候选；推动可审计试样；`qualified conversation`。
- **Duration / opening / script：** 30 秒；“火锅店想试一种新食材，第一步不该是批量下单。” VO：“先说清想验证什么：规格、菜单做法、收货、损耗还是客人反馈？然后确认当前产品信息、样品路径和下一步负责人。样品不是承诺，它是一个有边界的学习步骤。”
- **Shot / text / caption / CTA：** 无食材商标的试菜桌、纸上五个问题、成人手打勾；`Test one question at a time.`；`A good trial starts with a clear question.`；在允许后请求产品资料。
- **Proof / compliance / metric：** 不表示可送样/可供货；主指标为有明确试样目标的对话；缺货/许可不明即 Stop。

### 完整 B2C 卡 SF-C07｜买冷冻海鲜前，先看信息

- **Target / objective / funnel：** 家庭聚餐假设人群；教育产品信息；`B2C discovery`。
- **Platform / duration / opening：** SF-6 后的一个获准内容触点；25 秒；“买冷冻海鲜前，哪些信息不能只靠图片猜？”
- **Full script / VO：** “先看是什么产品、什么规格、净重和包装；再看标签上的储存、过敏原和日期信息；最后确认你的区域是否有已经批准的交接方式。好看的画面能给灵感，真实的信息才能帮助你决定。”
- **Shot / AI prompt：** 无标签冷冻食材轮廓、家庭餐桌、空白信息卡；自然窗光、手机手持；不让 AI 生成食材包装文字。
- **On-screen / caption / CTA：** `Picture. label. storage. handoff.` Caption：`A better dinner starts with a better product question.` CTA：`Save this check before you shop.`
- **Proof / compliance / metric：** B2C 前置未满足则内部；不能给储存/过敏原/配送实值；主指标为合格信息问题，不是 views。

### 完整 B2C 卡 SF-C08｜今晚吃什么，先别跳过准备

- **Target / objective / funnel：** 家庭聚餐/便利烹饪假设人群；`engagement`。
- **Duration / opening / script：** 20 秒；“今晚不知道做什么菜？先别急着下锅。” VO：“先确认你手里的食材是什么形态、标签怎样写、需要怎样准备。然后再选一道简单的家庭菜。省时间，不是跳过信息，而是先把正确的问题问清楚。”
- **Shot / text / caption / CTA：** 无品牌食材碗、切菜板、手机备忘录三问；`Prepare with facts.`；`Simple cooking starts before the pan.`；保存。
- **Proof / compliance / metric：** 没有具体 SKU 时不说解冻时间/烹饪温度；看保存与信息请求；政策不清不发布。

### 完整 B2C 卡 SF-C09｜火锅前的三个核验问题

- **Target / objective / funnel：** 火锅/中餐爱好者假设人群；`engagement → inquiry`。
- **Duration / opening / script：** 25 秒；“火锅里的海鲜什么时候下锅，先要确认这三件事。” VO：“第一，实际是什么产品和规格。第二，标签有没有给出储存和食品信息。第三，供应链是否已经确认了你所在区域的交接方式。信息齐全，再讨论烹饪；信息不全，就先核验。”
- **Shot / prompt：** 火锅蒸汽但不出现食材商标；空白三问卡；自然手机曝光；禁止虚构熟制时间。
- **On-screen / caption / CTA：** `Product. label. handoff.` Caption：`Questions protect the meal.` CTA：`Save the three checks.`
- **Proof / compliance / metric：** 禁止给出实际下锅/温度/产品承诺；B2C 未解锁前仅内部。

### 完整 B2C 卡 SF-C10｜包装好看不是产品卡

- **Target / objective / funnel：** 产品信息受众；`trust`。
- **Duration / opening / script：** 20 秒；“为什么包装好看，也不能替代产品卡？” VO：“因为真正需要知道的是规格、净重、标签、批次、过敏原、储存和谁负责回答问题。包装能吸引你停下，产品卡才能让你做决定。”
- **Shot / text / caption / CTA：** AI 只出无文字包装+后期合规信息卡；`Packaging is not proof.`；`Ask for the verified record.`；保存。
- **Proof / compliance / metric：** 无标签不暗示具体商品；看信息保存/产品卡请求；出现销售问询转人工。

### 完整 B2C 卡 SF-C11｜AI 不能替产品写标签

- **Target / objective / funnel：** 对 AI 内容敏感的家庭/渠道受众；`trust`。
- **Duration / opening / script：** 25 秒；“AI 可以做厨房镜头，但不可以替产品写标签。” VO：“模型能帮助我们规划镜头、字幕和菜单灵感。但它不知道你的这一袋产品的批次、配料、过敏原或储存要求。真正重要的信息，必须来自已经核验的产品记录。”
- **Shot / text / caption / CTA：** AI storyboard 与人工 fact checklist；`AI drafts. Product records decide.`；`Natural video still needs real facts.`；保存。
- **Proof / compliance / metric：** 通用流程事实；不得把 AI 画面称“实拍货品”；主指标为信任/信息互动。

### 完整 B2C 卡 SF-C12｜更好的 CTA 是核验

- **Target / objective / funnel：** 全体 B2C 假设受众；`engagement → qualified inquiry`。
- **Duration / opening / script：** 20 秒；“信息还没核验时，最负责任的 CTA 是什么？” VO：“不是催你下单，而是邀请你问一个更清楚的问题：这是什么产品？标签和储存信息在哪里？我的区域是否已经有批准的交接路径？当答案还不完整时，先核验就是最好的下一步。”
- **Shot / text / caption / CTA：** 手机打出三问、无品牌厨房桌；`Check first.`；`Clarity before conversion.`；`Save the questions.`
- **Proof / compliance / metric：** 不涉具体 SKU；合格问题数与 conversation rate 为指标；无有效入口不发布。

### 扩展卡 SF-C13 至 SF-C24（第二测试队列）

| ID | Route / target / opening | Script direction | AI shot / caption / CTA | Fact control / metric / stop |
|---|---|---|---|---|
| SF-C13 | B2B 酒店；“宴会厨房为什么不能只看单箱重量？” | 箱规、规格、收货、菜单与异常要一起问。 | 无标识箱体/空白验收单；`Weight is one question, not the answer.`；保存。 | 不推断重量=可用库存；看采购问题质量。 |
| SF-C14 | B2B 批发；“MOQ 之前还有什么？” | 讲价格有效期、库存、冷链、结算和退换。 | 无数字报价单；`MOQ needs a full offer.`；请求清单。 | SF-2 后；无商业事实不发布。 |
| SF-C15 | B2B 餐厅；“菜单适配不是一句‘适合’。” | 以菜单、形态、收货和损耗组成核验。 | 菜单与规格卡；`Fit is verified.`；留言。 | 无批准 SKU 不声称适配。 |
| SF-C16 | B2B 冷链；“异常发生时，谁确认下一步？” | 讲 owner、记录和停售/隔离机制。 | 空白异常流程卡；`Escalate, do not guess.`；保存。 | 无冷链 SOP 仅内部。 |
| SF-C17 | B2B 进口/渠道；“食品内容为什么需要版本？” | 标签、批次、有效期和负责人。 | 日期/版本卡；`Facts expire.`；资料 CTA。 | 不称已有进口资格；无权不触达。 |
| SF-C18 | B2B Foodservice；“一次采购对话该留下什么？” | owner、next action、product ref、outcome。 | CRM 风格抽象卡；`Record the next step.`；保存。 | 无数据依据不存真实联系人。 |
| SF-C19 | B2C 家庭；“海鲜的安心感从哪里开始？” | 产品记录、标签和交接问题。 | 家庭餐桌/清单；`Facts belong on the table.`；保存。 | 无 SKU/标签不发布。 |
| SF-C20 | B2C 海鲜爱好者；“海鲜的鲜感不由滤镜决定。” | 反对夸张画面，说明真实记录。 | 自然食材纹理、无品牌；`No fake freshness.`；分享。 | AI 不伪造品质/产地；失真即重做。 |
| SF-C21 | B2C 家庭聚餐；“一顿海鲜晚餐的第一件事？” | 先问产品、储存、交接。 | 无标签备餐镜头；`Question before cooking.`；保存。 | 不给温度/时长；看合格问题。 |
| SF-C22 | B2C 火锅；“为什么不是每种海鲜都用同一做法？” | 只说应看经批准的形态/产品卡，不给具体做法。 | 火锅桌/空白产品卡；`Read the record first.`；留言。 | 未批准不声称烹饪适配。 |
| SF-C23 | B2C 信息受众；“看不懂包装，该问什么？” | 三个可复制的客服问题。 | 手机备忘录；`Ask for verified information.`；保存。 | 由人工审核任何销售问询。 |
| SF-C24 | Both；“内容的作用不是替代食品事实。” | 内容、产品卡、交接和数据各自的角色。 | AI 分镜 + 审核卡；`Content explains. Facts approve.`；保存。 | 不把视频当产品证据；看合格信息请求。 |

## 7. 发布与审核 SOP（解锁后才执行）

`target segment → one hypothesis → fact/asset/policy lock → script → AI visual prompt → generation → technical QC → content QC → business QC → approval → publish → human reply → log → review → Keep/Improve/Stop`

| Step | Owner | Required input | Output / Done when |
|---|---|---|---|
| Hypothesis | 用户 + 销售 owner | 一条路线、一个客户问题、一个变量 | `content_brief` 明确提升哪一个漏斗指标。 |
| Fact lock | 供应链 + 审核人 | SKU、标签、批次、食品/冷链、价格/履约与素材权利 | 任一未知/过期/冲突则 STOP。 |
| AI video | 内容制作人 | 审过的脚本与手机质感 Prompt | 内部候选；不含假标签/场景/人物。 |
| QC | 内容/业务审核人 | 视频、字幕、CTA、当前事实 | technical + content + business QC 均通过。 |
| External action | 用户指定 owner | action-time 渠道/发布授权 | 内容 ID、CTA、入口和回联 owner 记录完整。 |
| Review | 用户 + 销售 owner | 内容/询盘/交接/失单记录 | 只决策一个下一轮变量。 |

## 8. 海鲜内容数据合同

所有内容记录：`content_id`、`business_line`、`route`、`product_ref`、`channel`、`publish_time`、`target_customer`、`pillar`、`hook_type`、`duration`、`cta_type`、`fact_lock_ref`、`asset_rights_ref`、`views`、`3s_hold`、`avg_watch_time`、`completion_rate`、`inquiry`、`qualified_inquiry`、`qualified_procurement_conversation`、`offer_request`、`offer`、`handoff`、`order`、`fulfilment_outcome`、`lost_reason`。

无合法、可审计数据的字段填 `UNKNOWN`。B2B 首轮主指标是 `qualified_procurement_conversation_rate`；B2C 首轮主指标是 `qualified_household_inquiry_rate`、已核验交接和投诉/温控异常。播放量只用于定位 Hook 是否被看见，不能作为销售成功或扩渠道依据。
