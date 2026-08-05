# 公开资料、Leads、CRM 与外联草稿计划

> **状态：PLANNED / draft-only。** 汾酒的当前外部主线不是旧 B2B 自动找客；Phase 5 只建设可共享、默认关闭的内部候选/草稿能力，绝不自动发送。

## 1. 标准流程

```text
来源配置 → 合规/robots/频率检查 → 页面快照 → 信息提取 → 来源/日期保存
→ 企业去重 → 可解释评分 → 人工审核 → CRM 入库 → 外联草稿 → 人工批准 → 手动发送（默认未启用）
```

每个 domain/source 一个 crawl adapter、一个 source policy 和一个 rate limit。`build_research_channels.py` 与其 JSON 只是历史人工研究工具/字段候选，不能自动导入真实 CRM，也不是获准 crawler。

## 2. source policy 与采集边界

source policy 必填：业务线、目的、owner、公开 URL allowlist、robots/terms 结果、允许字段、最大频率、认证禁止/允许、保留期、人工审核条件、停止条件。robots 拒绝、条款不明、登录墙、CAPTCHA、私有目录、个人社交资料、未授权 API 或访问异常时停止并写 source/audit 状态；不绕过、不换代理、不伪装。

`CrawlPort` contract 是 `FetchSnapshot(url, policy_id) -> content_hash/location/retrieved_at/http_policy_result` 和 `ExtractPublicFields(snapshot_ref) -> candidates/evidence locators`。Crawl4AI 只是在 policy 已批准后可选 adapter；CSV/人工导入是永久 fallback。网页内容的 snapshot 和 evidence 不能自动升级为企业真实性或可联系授权。

## 3. lead / CRM 数据边界

| 对象 | 允许自动化 | 人工决定 | 强制保护 |
|---|---|---|---|
| `lead` | 公开业务字段提取、fingerprint、评分理由、重复候选 | accept/merge/reject、资料可信度 | 每条保留 URL/date/snapshot，禁止隐私字段推断。 |
| `organization` | 规范化名字/域名、同名候选 | 创建/合并/关联 | 无 `approved lead` 不建正式 organization。 |
| `contact` | 公共字段识别、格式校验 | 合法性/适当性、创建/更新 | 最小化、consent/source、DNC、删除/匿名请求。 |
| `opportunity/stage` | 建议 stage/next step | stage、金额、承诺、owner | 不以 AI 评分代替商机事实。 |
| `interaction` | 草稿摘要 | 真实发送/来往记录 | 外发由人工记录；系统默认 `sent_count=0`。 |

联系人可被处理的最低门槛为公开业务来源或可审计同意；`do_not_contact`、拒绝跟进、投诉、数据删除请求覆盖所有草稿和未来 adapter。DNC 不能被模型提示、管理员页面或重跑绕过。

## 4. CRM 可替换与导出

第一版以 PostgreSQL CRM domain + 极简 admin 为真值，提供 scoped JSON/CSV export 和 import interaction contract。Twenty 是后期 `DEFER` 的 UI/adapter 候选，而不是 CRM 真值；若引入，必须先验证其具体许可证、webhook、导出、tenant mapping 和 one-way 同步。停用任何 CRM adapter 后，本系统仍必须能读取 organization/contact/opportunity/interaction/DNC 和审计历史。

## 5. 外联草稿的硬边界

草稿生成仅使用 approved facts，必须显示 used fact version、policy、风险旗标和人工编辑位。没有 approved price/inventory 时可生成“需要确认”的内部建议，不能写金额、库存或交期。批准草稿并不发送消息；真实外发需要未来 Phase 9 的用户授权、合规/渠道证据和 `external_send_enabled=true`，当前一律保持 `false`。海鲜未来若启用，也需其业务线的独立授权，不能复用汾酒权限。
