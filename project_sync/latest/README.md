# 汾酒尼泊尔项目

这是“汾酒在尼泊尔市场的研究、合规前置、渠道/供应链协作与可验证执行准备”项目仓库。项目目录同时保存一条尼泊尔海鲜协作资料线；两条业务线不得互相覆盖事实、结论或对外口径。

## 先从哪里开始

新加入的用户、ChatGPT、Codex 或 Work 会话，先读：[PROJECT_ENTRY.md](PROJECT_ENTRY.md)。执行型 Agent 还必须先读：[AGENTS.md](AGENTS.md)。

## 当前阶段

`CONFIRMED`：已存在市场研究、执行设计、供应链协作资料和生成脚本。

`BLOCKED`：酒类公开传播、平台能力、SKU/价格/库存、当地主体与许可均没有在当前仓库中得到可执行层面的最终确认。因此本仓库不把研究或已生成文档写成已经上线、已获许可或已经销售。

完整状态见：[docs/project/CURRENT_STATUS.md](docs/project/CURRENT_STATUS.md)。

## 主要目录

| 位置 | 用途 | 默认是否进入同步包 |
|---|---|---|
| `docs/project/` | 目标、状态、事实源、边界、决策与下一步 | 是 |
| `docs/collaboration/` | 人与 Agent 的协作规则、模板和真实执行历史 | 是 |
| `scripts/` | 文档与同步包生成脚本 | 仅同步包构建脚本 |
| `project_sync/latest/` | 当前可交接的轻量同步包 | 是 |
| `research_*.json` | 汾酒研究与执行设计的机器可读源数据 | 否，作为事实源指针 |
| `供应链启动文件_最终版/`、`汾酒海鲜_尼泊尔线上销售_供应链协同与资料交付体系/` | 业务协作原始文档 | 否，按任务定向阅读 |
| `outputs/`、`qa/`、`_qa*/`、媒体文件 | 派生产物、渲染和检查材料 | 否 |

## 生成项目同步包

```bash
python3 scripts/build_project_sync_pack.py
```

它会更新 `project_sync/latest/`，并在本地 `dist/` 生成一个带时间戳的 ZIP。详情见：[docs/sync/README.md](docs/sync/README.md)。

## 安全边界

- `.env`、密钥、Token、Cookie 和恢复信息绝不提交。
- `research_channels.json` 含线索与联系方式，默认仅限本地受控使用。
- `outputs/`、视频、渲染和缓存不作为 Git 或同步包默认内容。
- 任何面向公众的酒类传播、广告、达人合作、直播、导流、电商或订单动作，均须以当前当地法律、平台和合作方的书面确认作为前置条件。
