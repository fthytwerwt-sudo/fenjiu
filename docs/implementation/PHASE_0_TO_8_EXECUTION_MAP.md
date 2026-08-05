# Phase 0–8 执行图、依赖与验收

> **状态：PLANNED。** 本文件是后续按小任务下发 Codex 的顺序合同；任何任务执行时仍须回读当前 `AGENTS.md`、项目状态和远端事实。

## 1. 第一批下发顺序

1. `P00-01` 工程事实与资产基线审计。
2. `P00-02` 冻结目录、依赖方向与 ADR（依赖 P00-01）。
3. `P00-03` 建立非侵入式验证/敏感扫描基线（依赖 P00-01，可与 P00-02 并行）。
4. `P01-01` 创建模块化单体骨架（依赖 Phase 0 全部）。
5. `P01-02` 本地 Compose、迁移、Make 命令与 CI 入口（依赖 P01-01）。

在 Phase 0 验收前，禁止创建运行时工程目录；在 Phase 1 验收前，禁止数据 migration；在 Phase 2 验收前，禁止任何真实资料导入。

## 2. 逐阶段地图

| Phase | 任务卡 | 主要写入范围（实施时） | 关键验收 | 回退点 |
|---|---|---|---|---|
| 0 | `P00-01`~`P00-03` | `docs/implementation/`、验证脚本/报告 | legacy 文件未改、禁区和风险可读、ADR 已冻结 | 丢弃新规划分支；不动原始资料。 |
| 1 | `P01-01`~`P01-03` | `apps/ core/ modules/ adapters/ workflows/ fixtures/ migrations/ tests/`、Compose、Makefile | 空环境启动/停止、health、config、feature flags、CI | feature flags 关闭并回退本阶段明确 commit。 |
| 2 | `P02-01`~`P02-03` | contracts、schema、migration、scope guards | 每个核心实体有 scope/source/version/state；跨线和 fixture 泄漏失败 | expand/contract migration；事实不删除。 |
| 3 | `P03-01`~`P03-03` | ingestion、private storage port、mapping、approval | 合成 XLSX/DOCX/PDF/图片/JSON 同 hash 幂等；冲突不静默批准 | job 停止、候选留存、approved 以 supersede 撤销。 |
| 4 | `P04-01`~`P04-03` | workflow、RBAC、approval、audit、metrics | checkpoint/resume 不重复副作用；高风险默认 `off` | disable workflow/worker，保留 audit/DLQ。 |
| 5 | `P05-01`~`P05-03` | crawl port、leads、CRM、draft only | 每源一 adapter；DNC 和无授权零发送 | disable crawler/CRM adapter，导出 scoped 数据。 |
| 6 | `P06-01`~`P06-03` | conversations、policy、retrieval、support adapter | 无 approved 真值不猜；高风险一律 handoff；0 自动发送 | disable inbox/AI adapter，人工队列接管。 |
| 7 | `P07-01`~`P07-03` | content/video contracts、legacy wrapper、QC | legacy 脚本 hash/CLI 保持；只内部样片，未审批不能导出 | 停止 worker，保留 manifest/QC，不删除原输出。 |
| 8 | `P08-01`~`P08-03` | 私有导入运行记录、批准版本、报告 | 真实资料 approved、fixture 隔离、全链回归、run-ready 报告 | data version supersede/revoke + flag off + 下游缓存失效。 |

## 3. 可以与不可以并行的边界

| 关系 | 规则 | 原因 |
|---|---|---|
| P00-02 ∥ P00-03 | 可以，在 P00-01 资产基线后 | 分别拥有架构文档与验证基线；不写同一文件。 |
| P03-01 ∥ P03-02 | 不可以 | mapping 需要稳定的原始登记、提取定位和状态合同。 |
| P05 ∥ P06 ∥ P07 | 可以，但都必须依赖 P02/P04 | 三者共享 approved 真值与 policy，不能各自定义 state 或 approval。 |
| Phase 8 与 5/6/7 | 不可以 | fixture 替换与真实资料回归必须等所有下游 contract 已验收。 |
| 任意两张任务卡写相同 migration/contract | 不可以 | 先由依赖任务冻结接口；后续只能补兼容变更。 |
| 真实采集/真实消息/真实视频调用 | 不可以与常规实现并行 | 需要独立来源、授权、成本、合规和 rollback 审查。 |

## 4. 每阶段的进入与失败判定

| Phase | 进入条件 | 失败即停止 | 下一阶段准入 |
|---|---|---|---|
| 0 | 当前仓库与工作树已核验 | 发现不明敏感数据、错误 remote、无可读事实源 | 资产分类、ADR、验证入口可回读。 |
| 1 | Phase 0 通过 | 需要真实密钥/云资源才能证明基础启动 | local-only 开发入口、默认关闭 flags、CI 基线通过。 |
| 2 | Phase 1 通过 | scope/version/source/approval 任一可绕过 | 核心实体 contracts + negative tests 完整。 |
| 3 | Phase 2 通过 | 解析器直接覆盖原件、自动批准冲突/高风险字段 | fixture 导入到 approved synthetic truth 的 E2E 可重复。 |
| 4 | Phase 2/3 的审批对象可用 | retry/resume 可重复外部副作用或审计可删 | action policy、RBAC、append-only audit 和 observability 测试通过。 |
| 5/6/7 | Phase 4 通过 | 需要真实账号、私有资料或外部发送 | fake adapter 和模块 E2E 均证明外部动作数为 0。 |
| 8 | 3–7 完成且真实资料到达 | 缺字段/冲突/过期、数据混入 fixture、任一回归失败 | 三层状态分开报告，只有技术/数据状态可提升。 |

## 5. 统一任务完成定义

每张任务卡必须证明：文件范围明确；原始业务资料、媒体、`.env`、`research_channels.json`、`outputs/`、AppleDouble 未被写入；测试包含正常与失败路径；仅暂存该卡路径；commit/push/remote readback 完成或如实标记 `local_only_not_completed` / `blocked_push_failed`。技术完成永不自动更新供应链、合规或外部销售状态。
