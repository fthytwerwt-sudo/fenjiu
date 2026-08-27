# Sales Effect Scorecard｜销售与 AI 效果指标体系

- **日期**：2026-08-28
- **规则**：真实基线未出现前，所有 target 与 stop-line 数值均为 `TO_BE_VALIDATED`；不得为了仪表盘编造数字。

## 1. 业务结果指标

| Level | 漏斗阶段 | 核心指标 | 记录单位 | 解释边界 |
|---|---|---|---|---|
| 1 | Discovery | views、reach、profile visits、website visits | content/channel/day | 只是曝光，不证明兴趣或销售。 |
| 2 | Engagement | watch time、completion、comment、save、share、DM、link click | content/channel | 必须与有效 CTA 和受众假设关联。 |
| 3 | Inquiry | WhatsApp/DM/web inquiry、qualified inquiry、首响时间 | inquiry | 询盘不是订单；qualification 要有人工标准。 |
| 4 | Sales Progress | qualified lead、product requested、offer requested、follow-up due/completed、purchase intent | opportunity | 管理“下一步”，不以字段数量代替进展。 |
| 5 | Conversion | order confirmed、revenue、gross margin、conversion rate | order | 仅在付款/订单/供应链责任的真实证据存在时计算。 |
| 6 | Fulfillment & Retention | fulfilled、refund、complaint、repeat order、referral | outcome | 只有履约交接后才可观察。 |

## 2. 归因最小合同

每一条询盘最低记录：`business_line`、`channel_source`、`content_or_campaign_ref`、`entry_point_ref`、`inquiry_at`、`customer_type`、`owner`、`stage`、`next_action_at`、`outcome_ref`。订单若合法处理，额外保存受控 `order_ref`、`offer_ref` 与 `fulfillment_ref`。

允许回答：哪类内容、哪个渠道、哪类客户最终产生合格询盘/订单。不能因为一次点击、最后一次接触或缺少记录而虚构准确归因；此时标记 `UNKNOWN / attribution_incomplete`。

## 3. AI 效果规则

| AI capability | 对应漏斗阶段 | 最小指标 | 人工 baseline | 目标/测量 | Keep / Improve / Stop |
|---|---|---|---|---|---|
| 内容选题/脚本建议 | Discovery/Engagement | 有效播放、合格询盘率 | 人工产出耗时和同类内容表现 | `TO_BE_VALIDATED`，按内容批次比较 | 有效且不增加审核风险才保留。 |
| 视频辅助 | Discovery → Inquiry | 合格内容产出时间、询盘率 | 人工制作时间/效果 | `TO_BE_VALIDATED` | 只看技术 QC 不足；无效则回人工。 |
| 客服回复草稿 | Inquiry | 首响时间、漏回复率、人工接受率 | 人工回复日志 | `TO_BE_VALIDATED` | 只建议，敏感/高风险必转人工。 |
| CRM 提醒/摘要 | Sales Progress | 到期跟进完成率、漏跟进 | 人工清单完成率 | `TO_BE_VALIDATED` | 若比表格更耗时，停止扩张。 |
| 客户/企业研究摘要 | Qualification/B2B | 人工核验时间、有效账户率 | 人工研究样本 | `TO_BE_VALIDATED` | 不能替代来源、联系人或合规判断。 |
| 漏斗分析 | Optimization | 可行动的复盘结论数、决策后改善 | 现有人工复盘 | `TO_BE_VALIDATED` | 数据不全时只报告不确定性。 |

## 4. 停止与回退规则

| 模块 | 停止线 | 回退到 |
|---|---|---|
| 内容渠道 | 预先定义观察窗口后无合格询盘或不可归因 | 受众、Offer、Hook、CTA 或渠道假设。 |
| B2B company discovery | 已批准小样本未形成有效对话/机会 | 目标账户、来源质量、价值主张与人工研究，不增加 crawl。 |
| CRM | 记录/维护成本高于实际防漏跟进收益 | 受控人工表格和最小字段。 |
| AI 视频/内容 | 未缩短生产时间且未改善下游效果 | 人工/半自动创作。 |
| AI 销售助手 | 人工接受率低、漏回复未改善或风险升高 | 人工回复与 SOP。 |
| 自动化 | 节省的人工时间低于维护、审计和错误成本 | 关闭 automation，保留手工流程。 |

所有数字阈值只有在真实、合规的数据样本出现后由用户和业务责任人定义；模型不得自行设定商业合格线。
