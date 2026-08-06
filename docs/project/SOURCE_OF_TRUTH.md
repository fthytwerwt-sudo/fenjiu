# 事实源地图｜SOURCE_OF_TRUTH

发生冲突时按下表读取。派生产物、截图、口头转述、聊天摘要和旧同步包不能覆盖排名更高且较新的原始来源。

| 信息类型 | 当前事实源 | 状态与说明 |
|---|---|---|
| 当前正式业务范围、阶段、职责、未知与业务阻断 | docs/project/BUSINESS_STATUS.md | **CONFIRMED** 的范围和职责来自用户明确确认（2026-08-05）；供应链实际交付仍须原始书面证据 |
| 项目总览与路由 | docs/project/CURRENT_STATUS.md | 短摘要；不替代业务或协作详细状态 |
| 协作、Git、同步包与远端回读 | docs/collaboration/COLLABORATION_STATUS.md | 远端 branch、commit、默认分支和 visibility 仅以最终回读为准 |
| 协作规则与阅读顺序 | AGENTS.md、PROJECT_ENTRY.md | **CONFIRMED** 的仓库规则和导航 |
| 当前执行范围 | docs/project/PROJECT_GOAL.md、SCOPE_AND_BOUNDARIES.md | **CONFIRMED**；旧研究不覆盖当前范围 |
| 已采用的业务与机制取舍 | docs/project/DECISIONS.md | **CONFIRMED**；每条决定须保留来源、日期、影响和状态 |
| 待补业务输入、阻断与顺序 | OPEN_QUESTIONS.md、RISKS_AND_BLOCKERS.md、NEXT_ACTIONS.md | **UNKNOWN/BLOCKED**；收到书面证据后再更新 |
| 汾酒市场、渠道和合规研究 | research_root.json、research_execution.json、research_culture_compliance.json | 资料存在为 **CONFIRMED**；涉及 B2B、多平台、90 天方案的内容为 **SUPERSEDED**（仅当前执行范围层面被替代），保留为历史市场背景，须由用户重新确认才可恢复 |
| 汾酒供应链启动模板 | 任务相关的汾酒供应链原始文件 | 模板和字段存在为 **CONFIRMED**；未签署、未回执或未回传的字段不得写为已确认 |
| 尼泊尔海鲜业务资料 | 海鲜原始资料线与对应供应链文件 | 独立资料线；不得自动用于汾酒结论 |
| 生成逻辑 | 根目录生成脚本与 scripts | 脚本存在/运行结果不等于业务事实 |
| P01 local-only runtime 与 control plane 验证 | `docker-compose.yml`、`Makefile`、`apps/*/local_runtime.py`、`core/security/`、`observability/`、`tests/local_runtime/`、`tests/control_plane/`、`docs/implementation/P01-02_LOCAL_RUNTIME_AND_MAKE_ENTRYPOINTS_REPORT.md`、`docs/implementation/P01-03_CONFIG_FLAGS_HEALTH_AND_OBSERVABILITY_REPORT.md` | **CONFIRMED（工程）**：`main` 代码已远端回读；仅证明 local-only runtime、disabled flags、not-ready control plane 和日志脱敏边界，不代表数据库接入、远端 CI、供应链、合规或业务执行成立 |
| 派生产物 | outputs、交付物、qa、渲染和媒体 | 仅作结果或质量线索；必须回读源数据与脚本 |
| 本地私有配置和线索 | 本地受控资料 | 不进入 Git 或同步包；不能当作对外联系授权或共享事实源 |

## 更新规则

1. 新事实须有来源、日期、责任人和事实分级。
2. 原始资料与状态冲突时，记录冲突并暂停升级，不静默挑选。
3. 新决定替代旧决定时，在 DECISIONS 中标记 SUPERSEDED，并保留原始资料。
4. 法律、平台、价格、库存、主体、账号和联系方式均应在执行前重新核验，不可仅依赖历史研究。
