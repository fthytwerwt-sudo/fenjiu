# 事实源地图｜SOURCE_OF_TRUTH

本表规定发生冲突时的读取顺序。派生产物、截图、口头转述、聊天摘要和旧同步包不能覆盖排名更高且较新的原始来源。

| 信息类型 | 当前事实源 | 状态与说明 |
|---|---|---|
| 协作规则与 Agent 阅读顺序 | `AGENTS.md`、`PROJECT_ENTRY.md` | `CONFIRMED`；本轮机制事实源 |
| 当前阶段、阻断与下一步 | `docs/project/CURRENT_STATUS.md`、`RISKS_AND_BLOCKERS.md`、`NEXT_ACTIONS.md` | `CONFIRMED`；业务状态必须附证据更新 |
| 已采用机制取舍 | `docs/project/DECISIONS.md` | `CONFIRMED`；不是商业决策总表 |
| 汾酒市场与渠道研究 | `research_root.json`、`research_execution.json`、`research_culture_compliance.json` | `CONFIRMED` 为资料存在；其中各条结论须服从源文件自己的标签、日期和限制 |
| 潜在线索与公开联系字段 | `research_channels.json`（本地受控） | `CONFIRMED` 为本地资料；不进入 Git/同步包，不能当作联系授权 |
| 汾酒供应链协作模板 | `供应链启动文件_最终版/汾酒尼泊尔线上销售_供应链启动配合清单.docx`、`汾酒海鲜_尼泊尔线上销售_供应链协同与资料交付体系/` 中汾酒文件 | `INFERRED`/模板；除非有签署或回执，不能写为合作方已确认 |
| 尼泊尔海鲜业务资料 | `尼泊尔海鲜AI线上销售系统/` 与对应供应链文件 | 独立资料线；不得自动用于汾酒结论 |
| 生成逻辑 | 根目录 `build_*.py`、`*_data.py`、`scripts/` | `CONFIRMED` 为现有脚本；运行成功不等于业务事实成立 |
| 派生产物 | `outputs/`、`交付物/`、`qa/`、`_qa*/` | 仅作结果/质量线索；回读源数据与脚本后才能引用 |
| 凭据与本地环境 | `.env` | 私有配置，不是可共享事实源，不得提交或打包 |

## 更新规则

1. 新事实必须有来源、日期、责任人和事实分级。
2. 若原始资料与当前状态冲突，先记录冲突，不静默挑选。
3. 若新决定推翻旧决定，在 `DECISIONS.md` 标记旧条目 `SUPERSEDED`。
4. 任何法律、平台、价格、库存、主体和联系方式应在执行前重新核验，不能只依赖历史研究。
