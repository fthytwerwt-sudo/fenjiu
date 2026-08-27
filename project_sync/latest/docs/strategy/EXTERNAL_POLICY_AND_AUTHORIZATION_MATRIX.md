# External Policy & Authorization Matrix｜外部政策与授权矩阵

- **检索日期**：2026-08-28（官方页面在 2026-08-27 读取）
- **用途**：只记录适用于 Sales-First 规划的官方资料候选；不构成法律意见，也不证明项目账号、许可、市场或用户授权已经满足。
- **四层规则**：`technical_capability` ≠ `platform_policy` ≠ `local_legal_status` ≠ `project_authorization`。四层必须同时满足，才可能进入一个受控外部动作。

## 1. 能力与政策矩阵

| 渠道/地区 | technical_capability | platform_policy | local_legal_status | project_authorization | 现在的行动结论 |
|---|---|---|---|---|---|
| TikTok | `CONFIRMED`：开发者公开列出 Login、Share、Content Posting、Display、Commercial Content 等 API | `CONFIRMED`：酒类广告须符合当地法律、年龄定向、必要执照和负责任饮酒要求；具体市场要求需再核验 | `UNKNOWN`：尼泊尔广告规则未在本轮形成可执行结论 | `UNKNOWN`：账号归属、目标市场、许可、广告/内容批准均未证实 | 不公开发布、不投放、不导流；只保留内部内容/账号核验设计。 |
| Instagram / Facebook | `CONFIRMED`：Instagram business/creator API 和消息 API 公开存在 | `CONFIRMED`：酒类广告受地区/年龄等限制；Meta commerce channels 不允许销售酒类 | `UNKNOWN`：尼泊尔广告/商业路径需单独核验 | `UNKNOWN`：项目账号、区域、商业权限、用户授权缺失 | 不经 Meta commerce 销售酒类；任何内容/广告/消息均待单独批准。 |
| WhatsApp Business | `CONFIRMED`：WABA 支持收发消息与 template 管理 | `CONFIRMED`：business 不得 transact in the sale of alcohol | `UNKNOWN`：本地沟通/消费者保护要求需核验 | `UNKNOWN`：WABA、同意、模板、数据责任和用户授权均未证实 | **禁止作为酒类交易/下单/付款通道**；是否可作为非交易询盘/人工客服承接需在正式使用前逐条核验。 |
| Gmail / Business Email | `CONFIRMED`：Gmail API 支持 mailbox 管理、发送，且有 quota；官方有反垃圾/认证/退订要求 | `CONFIRMED`：发送方反滥用规则；酒类专门限制在本轮未核实，记 `UNKNOWN` | `UNKNOWN`：尼泊尔营销邮件/隐私规则需核验 | `UNKNOWN`：发件域名、联系人处理依据、DNC、发送授权、回复对账未证实 | 不发信；仅在 SR-6 的人工审批 B2B 小样本中重新评估。 |
| Nepal alcohol sale | 不适用 | 不适用 | `CONFIRMED`：官方《Madira Act, 2031》构成对生产、销售/分销、进出口的许可框架，并含未满 18 岁保护 | `UNKNOWN`：本项目是否有适用主体、许可证、品牌授权和本地履约证据未确认 | 无许可/主体/年龄/履约证据时，真实酒类销售、收款、订单与履约 `BLOCKED`。 |

## 2. 官方资料链接

- TikTok developer capabilities: <https://developers.tiktok.com/>
- TikTok alcohol advertising policy: <https://ads.tiktok.com/help/article/tiktok-ads-policy-alcohol>
- TikTok alcohol market-specific requirements: <https://ads.tiktok.com/help/article/alcohol-market-specific-requirements>
- Instagram Platform: <https://developers.facebook.com/documentation/instagram-platform/overview>
- Instagram Messaging API: <https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/messaging-api>
- Meta Advertising Standards: <https://transparency.fb.com/policies/ad-standards/>
- Meta alcohol ads policy: <https://www.facebook.com/business/help/1145883309641178>
- Meta commerce policy overview: <https://en-gb.facebook.com/business/help/4718253321552152>
- WhatsApp Business Accounts: <https://developers.facebook.com/documentation/business-messaging/whatsapp/whatsapp-business-accounts>
- WhatsApp policy violations: <https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement-violations/>
- Gmail API guides: <https://developers.google.com/workspace/gmail/api/guides>
- Gmail API sending: <https://developers.google.com/workspace/gmail/api/guides/sending>
- Gmail sender guidelines: <https://support.google.com/mail/answer/81126?hl=en>
- Nepal Law Commission, Madira Act: <https://lawcommission.gov.np/content/13414/the-madira-act--2031/>

## 3. 授权检查清单

每一个拟执行动作必须单独记录：渠道、动作、Offer、业务线、账号/资产 owner、平台政策链接/日期、当地许可/专业意见、年龄/地域限制、数据处理与 DNC、人工负责人、用户明确授权、停止条件与审计位置。任一项缺失为 `BLOCKED`。

本轮未完成：平台后台实测、账号地区/权限验证、广告资格验证、尼泊尔广告专项法律审查、用户外发/发布授权、真实消息/订单/付款/履约。不得把本文件的官方链接或技术能力当成这些事实的替代品。
