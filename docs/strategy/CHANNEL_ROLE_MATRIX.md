# Channel Role Matrix｜渠道角色矩阵

- **日期**：2026-08-28
- **状态说明**：本矩阵定义候选角色，不声明账号、API、酒类推广、消息、广告或本项目授权已经成立。所有政策状态都必须按 `technical_capability / platform_policy / local_legal_status / project_authorization` 四层逐项核验。

| Channel | 目标客户 | 角色 | 内容形式/动作 | 客户动作 | 承接位置 | 可自动化 | 必须人工 | 当前能力 | 政策状态 | 优先级 |
|---|---|---|---|---|---|---|---|---|---|---|
| TikTok | 潜在 B2C 受众 | 条件性内容发现、场景展示、兴趣测试 | 短视频、商品场景、可归因 CTA | profile/DM/链接点击 | 已核验的单一入口 | 仅草稿/数据整理，未默认发布 | 账号、内容、发布、回复、合规 | `NOT_IMPLEMENTED` | 广告需当地法律/年龄/执照；项目授权 `UNKNOWN` | 候选 P1 |
| Instagram | 品牌关注者、社交发现人群 | 条件性内容复用、展示、品牌信任 | Reels/主页/受控资料页 | DM/链接点击 | 与主入口统一 | 不默认自动发布或 DM | 帐号、内容、私信、审核 | `NOT_IMPLEMENTED` | API 存在；广告条件性，commerce 不售酒；项目授权 `UNKNOWN` | P3 验证后决定 |
| Facebook | 本地社区、品牌信任和候选客户 | 条件性 Page/社群/可信度触点 | Page、Reels、人工社群参与 | Messenger/链接/询盘 | 与主入口统一 | 不自动群发/加群/广告 | 社群参与、响应、政策核验 | `NOT_IMPLEMENTED` | 酒类广告受限制，commerce 不售酒；项目授权 `UNKNOWN` | P3 验证后决定 |
| WhatsApp Business | 已有兴趣的非交易询盘 | **非交易**沟通/人工客服候选，不承接酒类订单 | 人工对话、事实澄清、转向合规渠道 | 询盘、追问、确认下一步 | 仅在逐项核验后使用 | 仅提醒/草稿；不自动发送 | 账号、回复、DNC、升级 | `NOT_IMPLEMENTED` | WABA 已知；平台禁止酒类交易，项目授权 `UNKNOWN` | P1 仅作待核验承接候选 |
| Website | 需要核验品牌/商品资料的访问者 | 信任、FAQ、产品资料、转化页 | 最小品牌/Offer/FAQ/联系页 | 表单/CTA 点击 | 单一受控入口 | 静态内容生成可辅助，发布需审核 | 域名、事实、发布、表单处置 | `NOT_IMPLEMENTED` | `UNKNOWN` | P2 |
| Gmail / Business Email | 高价值酒店、餐饮、零售、采购候选 | 低频精准 B2B 开发 | 人工核验后的一对一邮件 | 回复/会谈/需求确认 | 人工销售 + CRM | 草稿、提醒、reply 分类；不自动发送 | 来源/联系人依据、审批、发送、回复 | `NOT_IMPLEMENTED` | 发送能力/反滥用规则已知；酒类项目授权 `UNKNOWN` | P6 后 |
| Google Search | 主动搜索者 | 需求捕获/信任发现 | 可索引官网与准确资料 | 访问/询盘 | Website/统一入口 | 不自动购买广告 | SEO/内容、合规、监测 | `NOT_IMPLEMENTED` | `UNKNOWN` | P3 后 |
| Company Website | B2B 目标企业 | 企业验证和官方资料交叉核验 | 人工查看允许页面 | 不直接等于联系许可 | 仅私有 research record | 不默认抓取 | 来源条款、企业验证、人工判断 | `NOT_IMPLEMENTED` | `UNKNOWN` | P6 受控 |
| Industry Directory | B2B 目标企业 | 已批准企业发现来源 | 低频 company-only discovery | 企业候选 | 私有审查队列 | 必须逐来源批准；不自动扩大 | terms、DNC、准入、去重 | `PLANNED_ONLY` | `UNKNOWN` | P6 受控 |
| Association | 可信 B2B 名单/活动线索 | 企业发现与信任来源 | 官方目录/活动资料的人工研究 | 企业候选/转介 | 私有审查队列 | 不自动接触会员 | 来源许可、联系人依据 | `PLANNED_ONLY` | `UNKNOWN` | P6 受控 |
| Referral / Offline | 已有客户、合作方或活动 | 信任/复购/转介绍 | 人工请求、服务交接 | 询盘/复购 | 统一 CRM | 提醒可辅助 | 同意、隐私、事实记录 | `NOT_IMPLEMENTED` | `UNKNOWN` | P4 后 |

## 使用规则

1. 首个真实试点只选一个**内容/信任触点**和一个**询盘承接点**，并给内容和 CTA 赋稳定 ID。
2. `technical_capability`（可做什么）不替代 `platform_policy`（平台允许什么）、`local_legal_status`（当地法律允许什么）或 `project_authorization`（本项目是否被授权）。
3. 酒类广告、付费推广、批量消息、自动 DM、自动群发、自动加群、自动采集或导入联系人均不因本矩阵出现而获准。
4. 表现指标必须跨到 `qualified inquiry`、`conversation`、`offer` 或 `order outcome`；仅 reach/views 不足以提升优先级。
