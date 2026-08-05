# 汾酒尼泊尔｜仓库协作规则

## 1. 项目定位与当前范围

本仓库保存汾酒尼泊尔主线与尼泊尔海鲜独立资料线。当前正式执行范围仅为：汾酒在尼泊尔的 TikTok 线上销售准备；当前阶段为供应链启动资料收集与首批商品上线准备。它不是已上线、已成交、已履约或已获当地许可的证明。

海鲜可作为独立 B2B/B2C 业务线处理，但产品、客户、价格、资质、履约和业务结论不得与汾酒互推。没有明确任务时，默认只处理汾酒主线。

## 2. 进入后的强制阅读顺序

1. AGENTS.md
2. PROJECT_ENTRY.md
3. docs/project/BUSINESS_STATUS.md
4. docs/project/CURRENT_STATUS.md
5. docs/project/SOURCE_OF_TRUTH.md
6. docs/project/SCOPE_AND_BOUNDARIES.md
7. docs/collaboration/COLLABORATION_STATUS.md
8. 当前任务直接相关的原始业务文件或脚本
9. 修改前运行 git status --short --branch

不得跳过前五项，也不得只凭聊天记忆、派生产物或旧同步包改变项目事实。

## 3. 角色边界

| 角色 | 负责 | 不负责 |
|---|---|---|
| 用户 | 业务目标、优先级、线上销售执行、对外授权与最终验收 | 补猜合作方未提供的事实 |
| 供应链 | 当地合法销售、产品与履约所需资料及本地支持 | 代替用户运营线上销售 |
| ChatGPT | 外层总控、任务拆解与结果审查 | 代替本地读取、测试或 Git 远端验证 |
| Codex / Work | 读取、实现、整理、验证、Git 收尾与明确回报 | 擅自变更业务范围、对外发送或把推测写成事实 |
| 外部研究/审查 Agent | 只读证据、风险与建议 | 写入正式事实、提交、推送或代替最终判断 |

## 4. 事实分级

- **CONFIRMED**：当前仓库原始资料、Git 记录或用户明确确认直接支持。
- **INFERRED**：由资料推断，必须写明来源和适用边界。
- **UNKNOWN**：当前资料未找到，需用户、合作方或权威来源补充。
- **BLOCKED**：缺少关键条件，不能安全进入下一动作。
- **SUPERSEDED**：旧结论已被新的、有来源的决定替代；若仅当前执行范围被替代，必须明确写出该边界，原始资料仍保留。

生成文档、同步包、提交或推送均不等于业务事实、合规资格、合作确认、上线、销售或履约已成立。

## 5. 修改规则

1. 先写清 Goal、Context、Constraints、Impact check、Done when 与 Blocked if；使用 docs/collaboration/TASK_HANDOFF_TEMPLATE.md 或 SESSION_HANDOFF_TEMPLATE.md。
2. 不删除、批量移动或改写原始业务资料；不把海鲜资料写入汾酒事实。
3. 凭据、Cookie、账号恢复信息、私人联系方式、未审核线索、本地环境配置和大体积派生产物不得提交或打入同步包。
4. 不复制参考仓库的业务内容、绝对路径、账号、客户资料、结论或秘密；只能复用经审计的机制思路。
5. outputs、qa、渲染、媒体和截图只能作线索，不能在未回读源文件时充当唯一事实源。
6. SKU、价格、库存、主体、资质、账号权限、收款、订单、配送和售后必须依赖当前书面证据；缺失时标记 UNKNOWN 或 BLOCKED。
7. 未获用户明确授权和必要合规条件时，不外发、触达、发布、投放、下单、收款或处理真实付款。
8. 文档生成后实际打开或渲染检查；代码变更后运行相关检查。

## 6. 状态、决策与交接

实质任务完成后，按影响更新 BUSINESS_STATUS、CURRENT_STATUS、SOURCE_OF_TRUTH、DECISIONS、OPEN_QUESTIONS、RISKS_AND_BLOCKERS、NEXT_ACTIONS、COLLABORATION_STATUS 与 EXECUTION_HISTORY。

业务状态与协作机制状态必须分开写：前者不因脚本、文档或 Git 成功而升级；后者不替代供应链、平台或合规事实。决策须有来源、日期、影响和状态。

## 7. Git 与同步包

- 优先在独立分支进行可逆修改；不直接在默认分支做破坏性操作。
- 先查看完整 diff 和 Git 状态；只暂存明确路径，禁止使用 git add .。
- 提交说明为何改变，并遵循仓库适用的 Lore trailers。
- 推送后回读远端 branch、commit、default branch 与 visibility；未回读即为待验证。
- 同步包只包含 allowlist 的轻量上下文，ZIP 默认仅留在本地 dist；其 source_commit 是生成时的基线，不等于随后提交同步包目录的 commit。

## 8. 回报

不可仅因文件生成成功宣称完成。至少报告：实际修改、验证命令和结果、未验证项、事实分级、分支、commit、推送/远端回读、剩余阻断与下一步。使用 docs/collaboration/EXECUTION_REPORT_TEMPLATE.md。
