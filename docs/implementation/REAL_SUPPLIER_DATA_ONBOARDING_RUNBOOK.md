# 真实供应链资料入场、fixture 替换与受控运行 Runbook

> **状态：PLANNED，Phase 8 执行入口。** 本 runbook 只在 Phase 0–7 技术验收、真实资料实际到达且运行环境准备好后使用。它完成后最多证明技术/数据 `run-ready`，不代表已获准公开销售。

## 1. 入场 checklist

接收人先为资料包创建不可变 receiving record，逐项记录来源、日期、交付人、业务线、文件 hash、保密级别、负责人和缺口：

- 商品：SKU、名称/系列、酒精度、容量、包装、条码、批次/有效期、照片、标签、品牌素材与使用权；
- 价格：成本/各档价格/建议零售/最低价/活动价、币种、税/运费/佣金、有效期、结算；
- 库存：可用量、库位/区域、库存时间、补货周期、负责人；
- 资质：当地主体、进口/销售许可、品牌授权、标签/年龄/地区要求，均含适用范围与到期；
- 账号和履约：主体/管理员（不收密码）、收款责任、仓储、配送、退款、售后、SLA/责任人；
- 文件质量：格式、完整性、加密/病毒扫描结果、可读性、是否有冲突/已过期/不清晰页。

任何缺项只会产生 missing report；不得以历史研究、模板、电话口述、AI 猜测或 fixture 补齐。密码、Token、2FA、私有客户资料不接受进导入包，改用受控授权渠道。

## 2. 运行命令语义（由 Phase 1–3 以后实现）

```text
make ingest FILE=<private-path> BUSINESS_LINE=fenjiu
make inspect-ingestion JOB_ID=<id>
make approve-ingestion JOB_ID=<id>
make regression
make demo-run BUSINESS_LINE=fenjiu
make run-ready-report BUSINESS_LINE=fenjiu
```

`ingest` 只登记私有路径/reference，先 hash 与 quarantine；它不发布或覆盖 approved truth。`inspect-ingestion` 输出字段 mapping、location、confidence、missing/conflict/expiry 和 AI 建议的脱敏报告。`approve-ingestion` 必须由有权限的不同人类 reviewer 对版本化候选逐项 approve/reject/revise；无 pending approval、过期或冲突时返回非零状态。命令使用 ID/reference，日志不得回显正文、敏感图片、价格或账号。

## 3. 标准执行路径

1. **接收与归档：** 注册资料包和每一成员文件，保存私有 storage reference/hash；病毒/格式/敏感分类不通过先 quarantine。
2. **提取与清洗：** 依据 file type adapter 提取文本、表格、图片 OCR 或 JSON；保留页/Sheet/row/cell/bbox，生成原值与规范化候选。
3. **mapping 建议：** 匹配已有 profile 或提出 mapping candidate；所有新字段、未知单位/币种、低置信 OCR 均入 review。
4. **质量/冲突：** 运行 required、格式、唯一、日期、货币、版本、跨业务线、与有效 approved truth 的冲突及 freshness 检查；生成 supplier 补资料单。
5. **补资料循环：** 供应链回传的新文件作为新 source/version；不得修改原 job 使其看似完整。
6. **人工批准：** 检查 evidence、适用范围、有效期和责任；价格、库存、配送、资质、素材权利、账号/收款/履约一律人工批准。
7. **发布真值：** 生成 `approved_fact/data_version`，旧版只标记 `superseded/expired/revoked`；刷新/失效下游未发草稿和缓存。
8. **fixture 切换：** 仅在该业务线全部 required real approved truth 满足时启用 `data_origin=real` 的内部模块配置；fixtures 不删除、不迁移、不混合，仍只在 test/demo environment。
9. **全链回归：** 按本 runbook 的测试矩阵运行；失败即 flag off、记录差异、回到相应 source/mapping/approval，不继续 demo。
10. **受控内部运行：** synthetic or designated test recipient 会话、内部内容/video task、CRM 草稿、audit/rollback 演练；没有 Phase 9 证据时，外部动作数必须为 0。
11. **报告：** 生成 run-ready report，独立写三层状态、缺口、证据、flags 和下一步。

## 4. fixture 切换与正式数据 rollback

| 情况 | 行为 |
|---|---|
| real data 只覆盖一部分实体 | 只启用已 approved 的内部 read paths；缺项的客服/内容/CRM capability 自动关闭或 handoff，不能回落到 fixture 伪装答案。 |
| real price/inventory/资质发生冲突或过期 | 将相关 fact/草稿/task 标 `conflict/expired`，关闭 quote/content/export dependent capability，等待新批准版本。 |
| 误批准/来源错误 | 追加 `revoke/supersede` data version，失效所有未执行下游草稿/缓存；不删除 source/audit。 |
| 回归失败/权限日志失败 | 全部 `real_*` internal feature flags off，保留数据、job、DLQ 和审计；恢复到上一个 approved version 或 manual-only。 |
| fixture | 永不删作测试；在任何 real environment、external action 或正式报告中显式拒绝。 |

## 5. 回归矩阵

| 域 | 必过证据 |
|---|---|
| 导入/映射 | hash 幂等、原值/locator 可追踪、单位/币种/日期规范、missing/conflict/expiry 报告、无错误自动批准。 |
| 真值/隔离 | 每个 approved fact 有 source/version/reviewer；跨 business-line/tenant 失败；fixture 不可读取为 real。 |
| 客服 | 普通 approved FAQ 只产草稿；价格/库存/配送若有效可草稿；酒类/报价/退款/投诉/订单/缺事实强制 handoff。 |
| CRM/外联 | source evidence、DNC、export、0 自动发送；无 approved facts 不承诺。 |
| 内容/视频 | approved facts/assets lock、禁语检查、legacy wrapper fake/QC、人工批准、0 外部发布。 |
| 工作流/审计 | retry/resume 无重复副作用；approval/RBAC/flag 拒绝路径；audit append-only、日志脱敏、DLQ/metrics 可查。 |
| 回退 | flag off、version supersede、cache invalidation、adapter shutdown、重新运行无残留外部 action。 |

## 6. 模块启用判定

| 数据情况 | 可运行 | 自动关闭/转人工 |
|---|---|---|
| 仅 product/spec approved | 内部内容/FAQ 草稿（不报价） | 价格、库存、配送、订单、公开内容。 |
| 价格有效但库存缺失/过期 | 内部价格校验报告 | 所有可售、交期、报价、客服价格回答。 |
| 商品/价格/库存 complete，但资质/履约/平台边界缺失 | 内部 CRM/客服/视频受控 demo | 发布、外联、收款、下单、发货、广告。 |
| 全部资料 approved，外部前置仍未核 | `technical_ready` + `data_ready` 可以为 true | `business_external_ready` 与 `external_execution_allowed` 均保持 false。 |

## 7. 周期性真实对话数据更新

仅在具有数据处理授权、私有导出和 retention policy 时运行周期批次：脱敏/最小化 → 意图与 unanswered FAQ 聚类 → false-handoff/false-answer 标注 → FAQ/intent/mapping candidate → reviewer 批准 → contract + adversarial regression → versioned deploy。每批保留样本选择规则、版本、指标和回滚；不得把原始对话、联系人或模型训练数据写入 Git。
