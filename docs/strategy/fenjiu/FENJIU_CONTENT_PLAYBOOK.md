# Fenjiu Nepal Content Playbook｜汾酒尼泊尔内容与 AI 视频执行手册

> **业务线：** `fenjiu_nepal`
> **制作方式：** AI 生成视频；目标视觉为 `iPhone Natural Look`，不是“像 AI 广告片”。
> **发布状态：** 所有卡片默认 `publish_blocked_pending_business_gates`。内容脚本可内部制作和审阅，不构成发布授权。

## 1. 内容的销售角色

内容不是独立 KPI。每一条先回答：**谁在什么成人场景里、带着什么问题、为什么愿意停留、相信什么、下一步做什么。**

`Target customer → scene/question → reason to watch → proof → non-transactional CTA → inquiry → qualified conversation → offer / outcome`

当前缺少本地 Offer、许可、账号与履约证据，因此首批内容只能使用教育/场景/流程性 CTA；不能做“现货、价格、立即购买、配送、销量、当地授权、健康功效”表达。

### 1.1 目标客户分层

| 客群 | 状态 | 可测试的问题 | 不可推断 |
|---|---|---|---|
| 成年中高消费餐饮人群 | `HYPOTHESIS` | 对正式中餐/成人晚餐的饮用场景是否有兴趣 | 已有购买意愿或支付能力。 |
| 商务宴请 / 礼赠需求 | `HYPOTHESIS` | 是否需要更好理解中国白酒的场景与礼仪 | 具体产品适合礼赠、价格可接受。 |
| 中餐 / 亚洲餐饮消费者 | `RESEARCH_SUPPORTED` 的候选方向 | 是否愿意看中餐搭配与小杯品饮教育 | 当地餐厅持牌或愿意采购。 |
| 酒类渠道 / 酒店 F&B | `HYPOTHESIS` | 是否需要产品资料、规格与合规路径的 B2B 内容 | 可联系、可报价或有采购权。 |

### 1.2 内容支柱

| Pillar | 客户问题 | 可用事实范围 | 目标漏斗 |
|---|---|---|---|
| `scene` | 正式中餐、成年人聚会、待客时怎样自然介绍中国白酒？ | 场景与礼仪；不承诺某个 SKU | discovery / engagement |
| `first-taste-education` | 第一次接触中国白酒，应该先理解什么？ | 通用、克制的品饮教育 | engaged inquiry |
| `table-culture` | 为什么小杯、慢饮、配餐值得被解释？ | 非功效型文化与服务场景 | trust |
| `product-literacy` | 拿到一瓶经批准的产品时该看什么？ | 只讲“核验标签/产品卡的方法” | inquiry readiness |
| `trust-by-process` | 一次合规的产品介绍需要哪些信息？ | 真实流程；不虚构授权/库存 | qualified inquiry |
| `B2B-use-case` | 酒店/餐厅采购前应先确认什么？ | 采购问题清单，不写价格或供货 | B2B conversation |

## 2. AI iPhone Natural Look Visual Bible

### 2.1 画面基准

- `format`: vertical 9:16；主交付 1080×1920 或 4K 后裁切；24 或 30 fps。
- `camera_language`: 以 1× 主镜头感为主，少量 2× 用于手部/桌面细节；不滥用 0.5× 超广角。
- `light`: 窗边、餐桌、走廊或厨房的柔和自然光；允许轻微曝光过渡，禁止影视级轮廓光。
- `movement`: 静止手持、轻微呼吸感、一次自然推近或桌面横移；不使用悬浮无人机、完美轨道或高频转场。
- `texture`: 真实桌面痕迹、自然玻璃反光、浅景深但不过度散焦、环境声或轻微房间底噪。
- `editing`: 前 2 秒提出问题；镜头 1–2 秒一换；仅在语义变化时切镜；字幕留安全边距并保持可读。

### 2.2 AI 生成正向 Prompt 骨架

```text
Vertical 9:16 smartphone footage aesthetic, natural handheld micro-movement,
1x phone lens perspective, soft window light, believable everyday dining table,
subtle exposure breathing, real fabric and glass reflections, unhurried adult
dinner preparation. Documentary social-video pacing, no commercial studio set,
no brand labels, no readable packaging, no claims text embedded in the image.
```

每次附上：`scene`、`time_of_day`、`hands/objects`、`camera movement`、`sound bed`、`prohibited elements`。成片字幕、事实和 CTA 在后期以可审阅文本叠加，不依赖模型渲染文字。

### 2.3 Product / people / place truth rules

| 情况 | 允许生成 | 禁止生成 |
|---|---|---|
| 供应链尚未批准实物与素材权利 | 无标签桌面、杯具、抽象中国餐桌氛围、手部和通用食物场景 | 任何“汾酒”瓶标、条码、包装、真实客户、真实门店、尼泊尔地标或销售成绩。 |
| 已批准真实产品素材 | 仅以真实提供的产品图片/视频作为 reference，生成不改变标签的辅助环境镜头 | 改写标签/度数/容量、凭空添加奖项/进口贴、把 AI 画面当实拍证据。 |
| 人物/场景 | 虚构但不冒充真实客户的成人演员式角色；不得有未成年人特征 | 虚构顾客评价、采购方、餐厅、当地顾客、授权活动或“真实销量”故事。 |

### 2.4 AI LOOK RED FLAGS

必须拒绝并重做：瓶标变形或模型自创中文、酒液违反物理、手指异常、杯口/玻璃变形、反射不连贯、人物跨镜变脸、背景重复纹理、假蒸汽、过度电影调色、全片完美对称、过度慢动作、模型生成字幕、虚构尼泊尔符号、未成年人或鼓励过量饮酒的画面。

## 3. Hook Library（30 条）

### Misconception / education

1. 很多人第一次接触中国白酒，先误会了这一件事。
2. 高度数不等于只能一口喝完。
3. 第一次喝中国白酒，别急着先问“像不像威士忌”。
4. 一杯酒的第一印象，常常在入口前就决定了。
5. 想了解中国白酒，先别从价格开始。
6. 为什么有些酒适合被慢慢讲，而不是被匆忙喝掉？

### Scene / table

7. 如果今晚是一桌正式中餐，这杯酒该什么时候出现？
8. 商务晚餐里，最重要的往往不是“喝多少”。
9. 朋友第一次尝试新酒，桌上应该先准备什么？
10. 一顿饭从热闹变得有记忆点，常常只差一个小仪式。
11. 招待客人时，怎样让一杯陌生的酒不显得有压力？
12. 礼赠之前，先看送礼的人最在意什么。

### Curiosity / culture

13. 为什么中国白酒常用小杯，而不是大杯？
14. 一张餐桌，怎么把“第一次尝试”变成舒服的体验？
15. 不是所有酒文化都靠大声介绍。
16. 如果你只用一个问题理解中国白酒，会问什么？
17. 一杯酒和一道菜，为什么需要先认识彼此？
18. 比起背品牌故事，这个桌边细节更值得先看。

### Product literacy / trust

19. 拿到一瓶新酒，先看懂哪三类信息？
20. 一张产品卡里，哪些信息必须清楚？
21. 为什么包装好看不等于可以直接承诺销售？
22. 真正值得相信的产品介绍，会先说明什么？
23. 选一瓶酒之前，别跳过这个核验步骤。
24. 任何认真介绍产品的人，都不该猜这四件事。

### B2B / sales intent (only after gates)

25. 餐厅考虑一款新酒，第一件事不是写菜单。
26. 酒店 F&B 在介绍新品前，为什么要先锁定事实？
27. 采购一款酒之前，哪些问题一定要有答案？
28. 一次合规产品沟通，不该从“现货”开始。
29. 客户想了解产品时，最有价值的下一步是什么？
30. 有些问题必须等资料齐全后才能回答，这反而是专业。

## 4. Caption / CTA / reply controls

- **首发语言建议：** English 为主（目标市场的假设性工作语言）；Nepali 仅在 `native_review_required=true` 的本地母语审核后使用；Chinese 用于内部审核/供应链沟通，不三语同帖。
- **允许 CTA（未销售准备期）：** `Save this guide.`、`Tell us which product fact you would want verified first.`、`For an approved product-information request, use the designated channel once it is announced.`
- **禁止 CTA：** `Buy now`、`in stock`、价格、私信下单、付款、配送时效、酒精促销、任何面向未成年人的提法。
- **Pinned comment：** `Product availability, price, delivery and transaction details are not announced here until the approved local product and compliance information is in place.`
- **回复模板：** `Thanks for your question. Before we discuss a specific product, we verify the approved product card, availability and local compliance path. Please share whether you are asking as an adult consumer, a restaurant/hotel or a licensed trade business, and what information you need.`

## 5. 脚本长度模板

| 时长 | 结构 | 用法 |
|---|---|---|
| 15 秒 | 0–2s Hook → 2–6s scene/question → 6–11s explanation/proof → 11–15s CTA | 一个简单教育点。 |
| 25–35 秒 | 0–3s Hook → 3–8s problem/scene → 8–18s explanation → 18–27s proof/process → 27–35s CTA | 首批核心内容。 |
| 45–60 秒 | Hook → context → three-part explanation → process proof → CTA | 文化、服务方式、产品卡解释；只在 facts locked 后涉及特定产品。 |

## 6. First Content Batch｜24 张内容卡

**通用卡片控制：** `business_line=fenjiu_nepal`；`platform=candidate C1 only`；`publish_status=publish_blocked_pending_business_gates`；`fact_lock_required=true`；`native_review_required=true`（如转 Nepali）。所有 AI 图像只可展示无品牌、无标签道具，除非后续获得真实授权素材。

### 完整卡 FJ-C01｜小杯不是压力，是节奏

- **Target customer / objective / funnel：** 对中国白酒陌生的成年人；降低理解门槛；`discovery → engaged`。
- **Duration / opening line：** 25–30 秒；“为什么中国白酒常常用小杯，而不是大杯？”
- **Full script / voice over：** “第一次见到小杯，很多人以为这是要喝得更快。其实恰好相反：小杯让你有时间先闻一闻、配着菜慢慢试，再决定自己喜欢怎样的节奏。认识一款陌生的酒，不必逞强，也不必比较。先让这一杯和餐桌相处一下。”
- **Shot list / AI prompt：** 窗边晚餐桌，成人手放下小瓷杯；轻微手持俯拍；杯中只见透明液体但不出现酒瓶；2× 杯沿细节；最后回到两人餐桌的无脸背影。使用第 2.2 节 Prompt，`prohibit=labels, faces, drinking contest`。
- **On-screen text：** `Small pour. Slow pace. Learn first.`
- **Caption / CTA：** `A new spirit does not need a big first move. Start with the setting, the food and a small pour. Save this table guide.` CTA：`Save this guide.`
- **Proof / product fact / compliance：** 不需要具体 SKU；需确认发布渠道允许的成人酒类教育表达。不得出现年龄不明人物/健康功效/过量饮酒。
- **Recording / editing rhythm：** AI 出片后添加真实手机轻微自动曝光与室内环境声；每 1.5–2 秒切镜，不加转场。
- **Success metric / stop line / cross-platform version：** `3s_hold`、保存、合格信息询问；没有下游询问或政策审核失败则不扩量。Instagram/Facebook 只在 C2 获准后裁为 4:5、保留同一 CTA。

### 完整卡 FJ-C02｜一桌正式中餐，酒什么时候出现？

- **Target / objective / funnel：** 成年中餐/亚洲餐饮消费者；把陌生品类放入餐桌场景；`engaged`。
- **Duration / opening：** 30 秒；“如果今晚是一桌正式中餐，这杯酒应该什么时候出现？”
- **Full script / VO：** “不是菜一上来就要急着介绍酒。先让客人坐好，让第一道菜打开话题。等大家都进入节奏，再用一句简单的话说：这是一种中国白酒，我们可以先用小杯，慢慢了解。好的餐桌体验，先给人选择，而不是压力。”
- **Shot list / AI prompt：** 无品牌中餐桌；手摆放餐具与小杯；热菜虚焦入画；不拍实际饮酒；自然桌面杂物；无可识别餐厅标志。
- **On-screen / caption / CTA：** `Start with the table, not the bottle.` Caption：`The best introduction gives people context and choice.` CTA：`What question would you ask before trying a new spirit?`
- **Proof / compliance：** 无具体产品事实；须通过成年人、无过量/社交成功暗示审核。
- **Recording / rhythm / metric：** 30fps、手持慢推、环境餐具声；看评论中的具体问题与合格询盘，不以 views 判断。无合格互动则改 Hook，不换平台。

### 完整卡 FJ-C03｜第一次尝试，先不用比较

- **Target / objective / funnel：** 有烈酒经验的成年人；避免不实对比；`discovery`。
- **Duration / opening：** 20–25 秒；“第一次喝中国白酒，别急着先问‘像不像威士忌’。”
- **Full script / VO：** “比较可以帮你找到参照，但不能替你体验。更有用的三个问题是：它适合什么餐桌？我想用怎样的节奏尝试？我需要先核对哪些产品信息？先理解，再选择；而不是用一个熟悉的名字覆盖一个新体验。”
- **Shot list / prompt：** 两只无品牌玻璃杯并排、菜单纸、成人手写三个问题；自然台灯与窗光混合；不用任何瓶子。
- **On-screen / caption / CTA：** `Understand first. Compare later.` Caption：`A better first question changes the whole experience.` CTA：`Save the three questions.`
- **Proof / compliance / metric：** 不使用口感或竞品对比；测试保存率与“产品信息”类留言；无下游证据则不作销售内容。

### 完整卡 FJ-C04｜一瓶新酒，先看什么？

- **Target / objective / funnel：** 想了解产品的成年人；教育“产品卡先于销售”；`engaged → inquiry`。
- **Duration / opening：** 30 秒；“拿到一瓶新酒，先别急着问价格，先看这五件事。”
- **Full script / VO：** “第一，准确的产品名称和版本。第二，酒精度、容量和标签。第三，谁负责供应和售后。第四，价格和库存的有效期。第五，在哪些地区和渠道可以合法介绍。五件事没说清楚，最专业的下一步不是猜，而是先核验。”
- **Shot list / prompt：** 无品牌产品卡版式由后期文字制作；手翻空白核验清单；不让 AI 生成中文标签。
- **On-screen / caption / CTA：** `Name. label. owner. validity. permission.` Caption：`A product card is a trust document, not a decoration.` CTA：`Save this verification list.`
- **Proof / compliance / metric：** 需内部核验清单，不需 SKU；禁止借机暗示产品可售。目标是保存/合格信息请求；若被问价格，按第 4 节回复模板转人工。

### 完整卡 FJ-C05｜好的介绍会先给选择

- **Target / objective / funnel：** 成年朋友聚会场景；用克制方式建立信任；`trust`。
- **Duration / opening：** 25 秒；“招待朋友时，怎样让一杯陌生的酒不显得有压力？”
- **Full script / VO：** “先说它来自哪里、适合放在怎样的餐桌；再说可以怎么慢慢尝试；最后让对方决定要不要继续。没有人需要被说服喝酒。被尊重的选择，才会让一顿饭更舒服。”
- **Shot list / prompt：** 三名成人仅拍手部/肩部；小杯和菜肴；每人自由选择水或饮品；禁止干杯、豪饮、未成年人。
- **On-screen / caption / CTA：** `Context. Choice. Respect.` Caption：`Good hosting leaves room for a no.` CTA：`Share with the friend who hosts dinner.`
- **Proof / compliance / metric：** 仅成人且无饮酒鼓励；观察分享/保存和合格问题，政策不通过则 Stop。

### 完整卡 FJ-C06｜礼赠前的三个问题

- **Target / objective / funnel：** 成年礼赠候选；避免把礼赠写成事实；`discovery`。
- **Duration / opening：** 30 秒；“送一瓶酒之前，真正该先问的不是包装好不好看。”
- **Full script / VO：** “先问对方是否饮酒、是否达到法定年龄、场合是否合适。再问产品信息是否完整、来源是否清楚、当地规则是否允许。礼物的价值不在于逼人接受，而在于你有没有把尊重和信息一起带到桌上。”
- **Shot list / prompt：** 无品牌礼盒丝带、空白信息卡、成人手写三问；AI 不生成酒瓶/奖章。
- **On-screen / caption / CTA：** `Respect comes before presentation.` Caption：`A responsible gift starts with the recipient and the facts.` CTA：`Save the checklist.`
- **Proof / compliance / metric：** 不能称任何现有 20/30 年 SKU 为礼赠可选；如后续发布需核验年龄/地域/平台政策。主指标：有质量的产品卡请求。

### 完整卡 FJ-C07｜先闻、再聊、再决定

- **Target / objective / funnel：** 首次尝试的成年人；建立慢节奏心理预期；`engagement`。
- **Duration / opening：** 20 秒；“一杯陌生的酒，第一步不是喝。”
- **Full script / VO：** “先把杯子放近一点，闻一闻；再看看它适合怎样的餐桌；最后才决定要不要尝试。慢一点不是仪式感表演，而是让自己有选择。”
- **Shot list / prompt：** 无标签小杯、桌布、菜肴；轻微靠近镜头；不展示饮用动作。
- **On-screen / caption / CTA：** `Smell. Talk. Decide.` Caption：`Your pace is part of the experience.` CTA：`Save for your next dinner.`
- **Proof / compliance / metric：** 无产品事实；不说风味/健康；主指标：完成率与保存率，未到询盘层不升级渠道。

### 完整卡 FJ-C08｜餐厅为什么先问场景？

- **Target / objective / funnel：** 酒店/餐厅 F&B 候选；B2B 教育；`B2B discovery`。
- **Duration / opening：** 35 秒；“餐厅考虑一款新酒，第一件事不是把它写进菜单。”
- **Full script / VO：** “先问：客人是谁？是餐配、宴会还是礼赠？谁负责服务说明？产品资料、许可、库存和交接是否清楚？能回答这些问题，才值得进入下一步。菜单不是起点，事实和服务路径才是。”
- **Shot list / prompt：** 无品牌餐厅后台桌、空白采购问题卡、成人手圈选；不伪造真实酒店或采购方。
- **On-screen / caption / CTA：** `Scene. facts. service path.` Caption：`A responsible beverage conversation begins before the menu.` CTA：`For approved B2B information, use the designated channel when announced.`
- **Proof / compliance / metric：** B2B 只在 FJ-6 解锁；现阶段内部卡。测 `qualified_b2b_information_request`；无处理依据/授权则不得发布/联系。

### 完整卡 FJ-C09｜别让 AI 替你编标签

- **Target / objective / funnel：** 对 AI 内容敏感的成年人/渠道方；建立真实感规则；`trust`。
- **Duration / opening：** 25 秒；“AI 可以帮你做画面，但不应该替你编一张酒标。”
- **Full script / VO：** “真实感不是模型把画面做得多亮，而是它没有冒充真实。没有经批准的产品照片，就不用假瓶标；没有核验的当地场景，就不用假装在某家店卖得很好。AI 可以帮我们把故事讲清楚，不能替事实作证。”
- **Shot list / prompt：** 屏幕上的无标签生成分镜与人工核验表；后期放 `AI visual draft — not product proof`；不拍真实品牌。
- **On-screen / caption / CTA：** `AI helps draft. Facts approve.` Caption：`Natural-looking video still needs honest boundaries.` CTA：`Save the rule.`
- **Proof / compliance / metric：** 使用真实“内部制作边界”事实；目标为信任类互动，不把 AI 成片当销售证据。

### 完整卡 FJ-C10｜20 年和 30 年，先别急着比较

- **Target / objective / funnel：** 对两款名称有兴趣的成年人；防止 SKU 幻觉；`inquiry readiness`。
- **Duration / opening：** 30 秒；“听到‘20 年’和‘30 年’，先别急着判断哪一款更适合你。”
- **Full script / VO：** “名称本身不是完整产品卡。不同度数、容量、包装或地区版本，都可能改变我们需要确认的信息。更可靠的问法是：这一次具体是哪一个 SKU？标签和规格是什么？在这里能否合规提供？资料齐全后，再谈场景和选择。”
- **Shot list / prompt：** 两张无品牌卡片写 `20`、`30`，随后出现“SKU / label / capacity / approval”清单；禁止 AI 制作仿真汾酒瓶。
- **On-screen / caption / CTA：** `A name is not a product card.` Caption：`Ask for the exact approved SKU before comparing.` CTA：`Save this question list.`
- **Proof / compliance / metric：** 公开研究显示存在变体，但本地 SKU 未确认；只用作内部/审核通过后的教育；问价时转人工。

### 完整卡 FJ-C11｜不确定时，专业的回答是什么？

- **Target / objective / funnel：** 成年消费者与 B2B 候选；建立信任；`trust → qualified inquiry`。
- **Duration / opening：** 20 秒；“有些问题，专业的回答不是‘当然有’。”
- **Full script / VO：** “如果价格、库存、配送、许可或产品版本还没有最新确认，最正确的回答是：我先核验，再回复。短暂的等待比错误的承诺更可靠。真正的销售服务，不是把未知说得很确定。”
- **Shot list / prompt：** 无品牌客服笔记、核验状态从 `UNKNOWN` 到 `CHECKING`；不生成真实聊天截图。
- **On-screen / caption / CTA：** `Check first. Promise later.` Caption：`Accuracy is part of service.` CTA：`Ask for verified information.`
- **Proof / compliance / metric：** 不需要具体产品；看信息类询问质量与人工接管率；承诺性问题一律 fact recheck。

### 完整卡 FJ-C12｜内容的下一步不是成交，是清楚

- **Target / objective / funnel：** 所有目标人群；解释 CTA；`engagement → inquiry`。
- **Duration / opening：** 25 秒；“一条好内容的下一步，不一定是让你立刻下单。”
- **Full script / VO：** “对一款需要被理解的酒，下一步可以只是一个更清楚的问题：它是什么版本？适合什么场景？信息是否已经核验？先把问题问对，后面的选择才有基础。内容不是催促，它应该帮助人做更清楚的决定。”
- **Shot list / prompt：** 手机备忘录写三个问题，餐桌轻推，最后出现非交易 CTA；禁止付款/购物 UI。
- **On-screen / caption / CTA：** `Better question. Better next step.` Caption：`Clarity comes before conversion.` CTA：`Save the three questions.`
- **Proof / compliance / metric：** 无 SKU；以合格问题和 conversation rate 为主，不把播放量当成功。

### 扩展卡 FJ-C13 至 FJ-C24（第二测试队列）

| ID | Target / opening line | 15–35 秒脚本方向 | AI shot / caption / CTA | Proof / metric / stop |
|---|---|---|---|---|
| FJ-C13 | 成年待客；“招待客人，先准备什么？” | 三步：餐桌、选择、信息。 | 杯具/餐具无标签；`Hosting starts with care.`；保存。 | 无 SKU；看保存；无下游互动则换 Hook。 |
| FJ-C14 | 中餐爱好者；“一道菜和一杯酒，先认识谁？” | 讲配餐问题而不讲具体搭配结论。 | 菜品与空白配餐卡；`Ask, do not assume.`；留言场景。 | 禁止风味/产品断言；看具体场景评论。 |
| FJ-C15 | 成年初尝者；“第一次为什么要慢一点？” | 选择/节奏教育。 | 手部与小杯；`Your pace matters.`；保存。 | 无饮酒鼓励；低完成率即重剪。 |
| FJ-C16 | B2B 候选；“采购前为什么要问有效期？” | 事实版本影响报价与承接。 | 文件日期/复核动作；`Facts have dates.`；信息请求。 | FJ-6 前仅内部；无事实锁不发布。 |
| FJ-C17 | 成年礼赠；“包装之外还要看什么？” | 标签、授权、使用场景和收件人选择。 | 无品牌礼盒/清单；`Respect beats assumption.`；保存。 | 不称产品可礼赠；政策不通过即 Stop。 |
| FJ-C18 | 酒类渠道候选；“为什么不能先报一个大概价？” | 价/库存/税费/有效期须锁定。 | 空白报价单打叉；`No guesswork.`；B2B 信息 CTA。 | 仅 FJ-6 后可用；无授权不触达。 |
| FJ-C19 | 成年朋友聚会；“一顿饭不需要喝很多才有记忆点。” | 餐桌对话重于饮酒量。 | 无脸成人桌边；`Keep it considered.`；分享。 | 禁止过量暗示；审查失败即退回。 |
| FJ-C20 | 产品信息受众；“瓶身上每个数字都要问吗？” | 解释度数、容量、批次、标签的核验必要性。 | 后期信息卡；`Ask for the exact SKU.`；保存。 | 无仿真标签；看产品卡请求。 |
| FJ-C21 | 成年消费者；“不熟悉的酒，需要一个怎样的介绍？” | 不夸张、不强迫、可选择。 | 低调餐桌；`Context before pressure.`；留言。 | 只用通用事实；无合格互动不扩。 |
| FJ-C22 | 酒店 F&B；“服务团队先要知道什么？” | 成人场景、事实卡、许可、交接。 | 无品牌培训卡；`Service needs facts.`；B2B 信息 CTA。 | FJ-6 后；无合规/授权不发布。 |
| FJ-C23 | 内容审核者；“为什么真实质感不等于假真实？” | AI 画面与事实证明分开。 | AI 分镜 + 审核勾选；`Visual draft ≠ proof.`；保存。 | AI 内容不冒充实拍；失真则重做。 |
| FJ-C24 | 所有受众；“如果你只问一个问题，会问哪一个？” | 邀请提出产品/场景/合规问题。 | 手机文字输入的抽象镜头；`Ask a better question.`；评论。 | 留言出现交易请求转人工；无清晰问题不当销售信号。 |

## 7. 发布执行 SOP（获授权后才启用）

`Research → content hypothesis → script → fact check → AI shot prompt → generation → technical QC → content QC → business QC → publish approval → publish → human reply → log data → review → next experiment`

| Step | Owner | Input | Output | Done when |
|---|---|---|---|---|
| Research / hypothesis | 用户 + 人工 | 目标客户、单一变量、Offer 状态 | `content_brief` | 明确要验证的销售问题。 |
| Fact / policy check | 供应链 + 审核人 | 有效产品卡、素材权利、政策 | `fact_lock` | 未知/过期/冲突全部阻断。 |
| AI generation | 内容制作人 | 已审阅脚本、视觉 Prompt | 内部候选视频 | 无假标签、假人/店/评价。 |
| Three QC | 审核人 | 视频、字幕、CTA、事实锁 | `technical/content/business_qc` | 三项皆通过；否则不发布。 |
| Publish / reply | 用户指定 owner | action-time authorization | 发布/询盘记录 | 内容和每个回复均可归因。 |
| Review | 用户 + 销售 owner | 漏斗数据、失单原因 | Keep/Improve/Stop | 只决定一个下一变量。 |

## 8. 内容数据合同

每条内容记录：`content_id`、`business_line`、`channel`、`publish_time`、`target_customer`、`content_pillar`、`hook_type`、`creative_type`、`duration`、`cta_type`、`offer_ref`、`views`、`3s_hold`、`avg_watch_time`、`completion_rate`、`profile_visit`、`link_click`、`dm`、`inquiry`、`qualified_inquiry`、`conversation`、`offer_request`、`offer`、`order`、`revenue`、`gross_margin`、`lost_reason`。

未产生或未合法记录的数据一律为 `UNKNOWN`。第一轮主判断是 `qualified_inquiry_rate`、`conversation_rate` 与 `offer_request_rate`；曝光只用于诊断。任何 `order/revenue/gross_margin` 在可处理的真实订单出现前不得填数。
