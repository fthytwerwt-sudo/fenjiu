# P00-03｜验证、敏感扫描与 legacy 回归基线

| 元数据 | 值 |
|---|---|
| task_id / phase | `P00-03` / `phase_00` |
| depends_on / can_run_in_parallel_with | `P00-01` / `P00-02` |
| writes_to | `tests/regression/`、`scripts/`、`docs/implementation/`（实施时） |
| forbidden_paths | legacy 业务脚本实现、`.env*`、原始资料、媒体、`outputs/` |
| estimated_risk / recommended_executor | medium / Codex 5.6 Thinking + GPT review |

## Goal

设计并实现后续可复用的安全验证基线：Markdown/链接/非空、敏感/绝对路径/AppleDouble、fixture 泄漏和 legacy 的干运行回归；不得改变 legacy 行为。

## Context

外置盘含 AppleDouble，仓库严格 allowlist；HappyHorse 等脚本可能需 `.env`/真实 API，测试必须是 dry-safe。

## Constraints

允许新增不联网的验证脚本/测试和文档；禁止读/打印密钥、调用模型、写输出、改 legacy、删除 `._*`。

## 六层需求确认

- 目标层：防回归/泄露，不建业务功能。
- 机制层：扫描失败 fail-closed；秘密值不回显。
- 实现设计层：`primary_route=stdlib/static+CLI-help`；`fallback_route=hash/static manifest`；`capability_status=planned`；`probe_required=no`。
- 流程层：每个未来 task 先跑→变更→再跑。
- 判断标准层：检测到禁止项必须非零退出并给类别。
- 反馈层：命中秘密停止、提示轮换/人工处理。

## Impact check

确认测试不会误触发 `.env`、网络、视频、DOCX/XLSX 渲染或同步包大文件；不把忽略文件 stage。

## Must read

`P00-01`、`.gitignore`、`TEST_ACCEPTANCE_ROLLBACK_MATRIX.md`、`ARCHITECTURE_AND_MODULE_BOUNDARIES.md`、现有同步包验证脚本。

## Execution contract

- Capability status：planned validation baseline; no business capability。
- Probe required：yes — dry-safe legacy/scan probe。

- Primary route：hash/CLI-help/static fixture/`git check-ignore`。
- Fallback route：不能安全运行的 legacy 记录跳过原因和不可变 hash。
- Allowed Codex autonomy：新增测试/扫描、最小 docs。
- Forbidden Codex guessing：`.env` 格式、真实 API 行为、媒体内容。
- Required inputs：legacy 路径、ignore 规则、已批准 test scope。
- Required outputs：可重复 command、baseline manifest、negative tests。
- Execution entrypoints：`make regression`（待 Phase 1）或明确脚本路径。

## Execution steps

1. 定义扫描范围和允许误报处理。
2. 建立 legacy hash/CLI baseline 和 fixture leak tests。
3. 测试 secret/path/AppleDouble/media/absolute path 阻断。
4. 记录安全执行与跳过项。

## Validation commands

新扫描器自身测试；`git check-ignore .env '._x'`；对 legacy `--help` 或静态 hash；`git diff --check`。

## Done when

后续任务能用同一入口证明未碰 legacy/秘密/本机路径；无网络/真实模型调用。

## Blocked if

唯一可验证路径需 `.env`、生产账号或生成媒体，或扫描器会回显敏感内容。

## Output 回报格式

扫描覆盖/跳过、命中类别、legacy 基线、验证、Git 和 Phase 1 进入结论。

## Git completion

只 stage 新 tests/scripts/docs；commit/push/readback 或按实际标记失败。
