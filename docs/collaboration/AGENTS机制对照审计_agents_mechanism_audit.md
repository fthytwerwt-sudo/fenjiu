# AGENTS 机制对照审计

- **审计日期**：2026-08-06
- **目标仓库**：`fthytwerwt-sudo/fenjiu`
- **目标分支**：`main`
- **审计对象**：根目录 `AGENTS.md`、`PROJECT_ENTRY.md`、GPT Project 配合机制同步包、参考仓库 `fthytwerwt-sudo/-` 与 `fthytwerwt-sudo/lanxinse--`
- **结论**：当前汾酒 `AGENTS.md` 原本已具备项目身份、范围、角色、事实分级、敏感信息和 Git 基础纪律；本轮补齐四层协作结构、P0/P1/P2、GPT Project 机制包入口、六层需求确认、实现设计字段、工作区/远端硬约束、AGENTS 镜像和两个同步包边界。

## 参考来源

| 来源 | 本轮读取 | 采用方式 | 禁止迁移 |
|---|---|---|---|
| `fthytwerwt-sudo/-` 根 `AGENTS.md` | 多项目入口、GPT Project 上传包地址规则、状态边界和 Git 完成闸门 | 只采用“入口先裁决、静态包不等于 UI 上传、Git 完成需远端回读”的机制 | 视频工厂身份、素材、模型、API、运营状态 |
| `4b535efbaf2143bca9d826a1411974e5c363a9fe` | 完整 GPT Project 包、`project_entry/AGENTS.md`、GPT 数据源、Codex 镜像、上传 Manifest | 采用完整包结构和 AGENTS 镜像思路 | OPC / 视频工厂业务事实 |
| `8a1350b7690c09b372f07f3c20c7b2b1b300ecc7` | 实现设计层和 Codex 阻断机制 | 采用六层需求确认、实现设计字段和 blocked 条件 | 参考项目工具路线和媒体能力结论 |
| `74022503311c204f6248830c89d6df142d792077` | 上传包已生成但用户未上传 GPT Project UI 的状态边界 | 采用 `user_uploaded_to_gpt_project_ui = false` | 参考项目同步状态 |
| `fthytwerwt-sudo/lanxinse--` 根 `AGENTS.md` 和同名 GPT Project 包 | 四层结构、P0/P1/P2、工作区/远端硬约束、六层闸门、Codex 执行单模板 | 采用结构与表达层次 | 澜心社直播切片业务事实 |

## 逐项审计

| # | 审计项 | 修改前是否存在 | 当前文件位置 | 当前是否正确 | 参考来源 | 是否修改 | 修改原因 | 禁止复制内容 |
|---:|---|---|---|---|---|---|---|---|
| 1 | 项目身份和当前正式范围 | 存在 | `AGENTS.md` 1 节、`PROJECT_ENTRY.md` | 正确 | 汾酒当前事实源 | 否 | 已明确 TikTok 主线和供应链启动阶段 | 不复制旧项目身份 |
| 2 | 汾酒与海鲜业务线隔离 | 存在 | `AGENTS.md` 1/5 节、包 10 号文件 | 正确 | 当前业务决策 | 补强 | GPT 包内同步了隔离机制 | 不迁移海鲜事实到汾酒 |
| 3 | 用户、供应链、GPT、Codex 职责 | 存在 | `AGENTS.md` 3 节、`PROJECT_ENTRY.md` | 正确 | 当前业务状态 | 否 | 原文件已清楚 | 不写成资料已交付 |
| 4 | 账号记忆、GPT Project、GitHub、Codex 四层边界 | 缺失 | `AGENTS.md` 3A、包 03 号文件 | 正确 | `lanxinse--` AGENTS | 是 | 新增四层协作结构 | 不迁移澜心社业务状态 |
| 5 | 用户本轮输入为 P0 | 缺失 | `AGENTS.md` 2/3B、`PROJECT_ENTRY.md` | 正确 | `lanxinse--` AGENTS | 是 | 防止旧事实覆盖用户本轮目标 | 不把 P0 当永久事实，需落库 |
| 6 | P0 > P1 > P2 | 缺失 | `AGENTS.md` 3B、包 04 号文件 | 正确 | `lanxinse--` AGENTS | 是 | 明确冲突裁决 | 不复制旧项目事实 |
| 7 | GPT Project 机制包读取入口 | 缺失 | `AGENTS.md` 2/3C、`PROJECT_ENTRY.md`、`README.md` | 正确 | 补充参考同名包 | 是 | AGENTS 需先读机制包 | 不把机制包当事实库 |
| 8 | GitHub 项目事实读取入口 | 存在 | `AGENTS.md` 2、`SOURCE_OF_TRUTH.md`、包 05 号文件 | 正确 | 当前仓库规则 | 补强 | 与机制包入口并列 | 不用旧同步包覆盖 main |
| 9 | 真实意图澄清闸门 | 部分存在 | `AGENTS.md` 4A、包 12/13 号文件 | 正确 | `8a1350b`、`lanxinse--` | 是 | 用六层机制覆盖方向型输入 | 不复制视频工厂触发词 |
| 10 | 六层需求确认 | 缺失 | `AGENTS.md` 4A、包 13 号文件 | 正确 | `8a1350b` | 是 | 复杂任务下发前必须确认 | 不迁移参考项目业务流程 |
| 11 | 实现设计层 | 缺失 | `AGENTS.md` 4A、包 13 号文件 | 正确 | `8a1350b` | 是 | 防止 Codex 猜路线 | 不迁移工具能力结论 |
| 12 | `primary_route`、`fallback_route` | 缺失 | `AGENTS.md` 4A、包 13/14 号文件 | 正确 | `8a1350b` | 是 | 补齐实现设计字段 | 不复制参考项目 route |
| 13 | `capability_status`、`probe_required` | 缺失 | `AGENTS.md` 4A、包 13/14 号文件 | 正确 | `8a1350b` | 是 | 区分已确认和待验证能力 | 不写未验证能力为已确认 |
| 14 | `allowed_codex_autonomy` | 缺失 | `AGENTS.md` 4A、包 13/14 号文件 | 正确 | `8a1350b` | 是 | 明确 Codex 自主范围 | 不扩大到外部执行 |
| 15 | `forbidden_codex_guessing` | 缺失 | `AGENTS.md` 4A、包 13/14 号文件 | 正确 | `8a1350b` | 是 | 禁止猜价格、库存、资质、账号 | 不猜供应链确认 |
| 16 | Codex 完整执行单栏目 | 部分存在 | `AGENTS.md` 5 节、`TASK_HANDOFF_TEMPLATE.md`、包 14 号文件 | 正确 | `lanxinse--` 执行单模板 | 是 | 增加 Must read 和 Validation commands | 不复制澜心社路径 |
| 17 | 当前工作目录硬约束 | 缺失 | `AGENTS.md` 7 节 | 正确 | `lanxinse--` AGENTS | 是 | 防止错工作区写入 | 不写入其他项目 |
| 18 | 唯一远端仓库硬约束 | 缺失 | `AGENTS.md` 7 节 | 正确 | `lanxinse--` AGENTS | 是 | 明确只允许 `fthytwerwt-sudo/fenjiu` | 不 push 到参考仓库 |
| 19 | 禁止 `git add .` | 存在 | `AGENTS.md` 7 节、包 17 号文件 | 正确 | 当前仓库规则 | 否 | 原文件已明确 | 不 stage 无关文件 |
| 20 | commit、push、remote HEAD 验证 | 存在但可加强 | `AGENTS.md` 7 节、包 17 号文件 | 正确 | `7402250`、参考 AGENTS | 是 | 补完成状态条件 | 不把 local-only 写 completed |
| 21 | 受控状态词 | 存在 | `AGENTS.md` 4 节、包 16 号文件 | 正确 | 当前用户 overlay | 否 | 原文件已有事实分级 | 不用模糊完成词 |
| 22 | GPT Project 包与 GitHub 事实包区别 | 缺失 | `AGENTS.md` 3C、`README.md`、包 00/18 号文件 | 正确 | `4b535ef`、`7402250` | 是 | 防止两个包混用 | 不把 UI 上传写成已完成 |
| 23 | GPT Project 包缺失时阻断方式 | 缺失 | `AGENTS.md` 3C、验证脚本 | 正确 | 补充任务 P0 | 是 | 明确 `blocked_gpt_project_mechanism_missing` | 不凭聊天记忆补机制 |
| 24 | AGENTS 更新后同步包维护规则 | 缺失 | `AGENTS.md` 5 节、包 20 号文件 | 正确 | 补充任务 P0 | 是 | 要求同步镜像、Manifest、验证报告 | 不留下旧镜像 |
| 25 | 中文与英文术语备注规则 | 存在 | `AGENTS.md` 事实分级、包 16 号文件 | 正确 | 用户 overlay | 补强 | GPT 包内同步输出硬规则 | 不改英文 key |
| 26 | 旧项目只迁移机制、不迁移事实 | 存在但分散 | `AGENTS.md` 5 节、学习报告、包 00/11/18 号文件 | 正确 | 主参考和补充参考 | 补强 | 明确参考仓库只作机制来源 | 不迁移视频工厂/澜心社业务事实 |

## 实际修改摘要

- `AGENTS.md`：补齐四层协作结构、P0/P1/P2、GPT Project 机制包缺失阻断、六层需求确认、实现设计字段、workspace/remote 硬约束、完成度状态。
- `PROJECT_ENTRY.md`、`README.md`、`CHATGPT_CODEX_WORKFLOW.md`、`TASK_HANDOFF_TEMPLATE.md`：同步读取顺序、机制包边界和六层下发要求。
- `GPT项目资料同步包_gpt_project_mechanism_sync/`：新增 `project_entry/AGENTS.md` 镜像，上传说明和 AGENTS 边界文件已说明镜像权威关系。
- `scripts/validate_gpt_project_mechanism_sync.py`：新增根 AGENTS、镜像 SHA、AGENTS 关键机制、两个同步包边界和冲突检查。

## 哈希与一致性

- **根 AGENTS SHA-256**：`658501d453e8e35ea269e536f53d88bae4e891bd8f239c3310ef0baa7b5183cf`
- **GPT Project 镜像 SHA-256**：`658501d453e8e35ea269e536f53d88bae4e891bd8f239c3310ef0baa7b5183cf`
- **是否一致**：`true`
- **四层架构检查**：`passed`
- **P0/P1/P2 检查**：`passed`
- **六层闸门检查**：`passed`
- **Git 完成闸门检查**：`passed`

## 边界

本审计只说明 AGENTS、Project 入口和 GPT Project 配合机制包已对齐，不表示用户已上传 GPT Project UI，不表示供应链资料已补齐，不表示 TikTok 酒类边界已确认，也不表示业务上线、销售或履约成立。
