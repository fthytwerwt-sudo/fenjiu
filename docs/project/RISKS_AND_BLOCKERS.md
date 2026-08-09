# 风险与阻断｜RISKS_AND_BLOCKERS

| 编号 | 状态 | 风险/阻断 | 当前影响 | 安全处理 |
|---|---|---|---|---|
| R-01 | **BLOCKED / P0** | TikTok 酒类内容、广告、账号和转化边界未获当前书面核验 | 不得公开发布、投放、导流或开展真实销售 | 保持内部资料与草稿；取得平台和当地合规书面证据 |
| R-02 | **BLOCKED / P0** | SKU、价格、价格有效期、库存、补货和首批商品未确认 | 不得展示为可售、报价、承诺供货或决定首批上架 | 由供应链提供商品主数据并核验 |
| R-03 | **BLOCKED / P0** | 当地销售主体、产品合法可售、品牌授权和资质未确认 | 不得建立真实销售或对外承诺 | 取得当地实体、品牌方和持牌专业人士的当前书面文件 |
| R-04 | **BLOCKED / P0** | 账号权限、收款、仓储配送、售后和结算责任未确认 | 不得收款、下单、发货或处理真实售后 | 明确主体、负责人、SOP、SLA 和退出/交接规则 |
| R-05 | **INFERRED** | 历史 B2B、多平台和 90 天研究可能被误用为当前指令 | 范围漂移或错误投入 | 以 BUSINESS_STATUS、DECISIONS 和 SOURCE_OF_TRUTH 为准；旧研究仅作历史背景 |
| R-06 | **BLOCKED** | V2 的干净 main、远端默认分支、visibility 与同步包最终验证尚待最终远端回读 | 不能把仓库安全收口或远端状态写为已完成 | 以 COLLABORATION_STATUS 的最终远端回读更新为准 |
| R-07 | **CONFIRMED** | 本地存在私有配置、联系资料和大体积派生产物 | 可能泄露秘密/隐私或污染 Git/同步包 | 保持忽略、allowlist、敏感扫描和最小披露；发现真实凭据须评估轮换 |
| R-08 | **PARTIAL / local-workspace risk** | 外置盘根目录含既有 ignored AppleDouble、`.env*` 和其他禁入路径：带基线默认扫描 202 项、`--all-files` 1,262 项；干净 P00-03 task worktree 的 12 项测试和两种扫描均通过 | 不得在外置盘根目录运行 P00 default/`--all-files` 扫描；不阻断已跳过 AppleDouble 编译元数据的本地 `make regression`，也不阻断在新建、干净 task worktree 中继续工程任务 | 不读取 `.env*` 内容、不删除 `._*`；后续一任务一 worktree，扫描失败立即停止该任务分支 |
| R-09 | **PARTIAL / engineering governance** | 当前推送凭据缺少 GitHub `workflow` scope，P01-02 的静态 GitHub Actions workflow 被远端拒绝 | 远端 CI 尚未启用；本地 `make regression` 与 Compose render 不能写成远端 CI 通过 | 由具备 `workflow` scope 的授权凭据单独提交 workflow；提交后单独回读 workflow、Actions run 与分支保护状态 |
| R-10 | **PARTIAL / production boundary** | P02-01 至 P02-03、P03-01 至 P03-03、P04-01 至 P04-03、P05-01/P05-02、P06-01 与 P07-01 已在 `main` 远端回读；当前仅提供 local synthetic 的 workflow（工作流）、策略/审计、来源 snapshot（快照）、CRM/DNC（客户管理/拒绝联系）、客服隐私/转交与内容事实锁合同，仍缺 RLS、加密、retention（保留策略）、法域、真实 scope、authenticated identity/authorization（认证身份/授权）、database adapter/driver（数据库适配器/驱动）、真实 parser/OCR/storage（解析/文字识别/存储）、生产渠道/模型/视频服务、抓取/队列/审计与 production connection（生产连接） | 不得把 local migration、trigger、in-memory policy/read/audit、fake extraction、mapping fingerprint、isolated approved synthetic version、workflow、action-policy、observability、source-policy、CRM/DNC、客服草稿/转交或内容事实锁合同写成生产数据隔离、真实审批、真实客户服务、真实网站访问、可联系 lead/contact、视频生成/发布、数据合规或真实资料可导入 | 真实资料和生产路径须另行获得范围、合规、连接与用户授权；后续工程任务仍须从新干净 worktree 开始 |

R-01 至 R-04 不阻断内部资料、清单、核验和草稿准备；它们阻断的是公开传播、广告、真实销售、收款和履约。机制完成不得被描述为业务上线。
