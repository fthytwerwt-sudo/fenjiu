# P01-02｜本地运行、Make 入口与 CI 基线

| 元数据 | 值 |
|---|---|
| task_id / phase | `P01-02` / `phase_01` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | `P01-01` / 无 |
| writes_to | `docker-compose.yml`、`Makefile`、`.env.example`、CI/test config、docs |
| forbidden_paths | `.env`、生产 secrets、legacy 脚本、原始/媒体/outputs、同步包 |
| estimated_risk / recommended_executor | medium / Codex 5.6 Thinking |

## Goal

实现 local-only PostgreSQL/broker/API/worker/admin 的可启动骨架与统一 Make 命令，默认不加载数据、不接外部服务。

## Context

统一命令语义在总计划已冻结；真实资料、账号与外部行为仍 blocked。

## Constraints

Compose 仅相对 volume/local ports；`.env.example` 只有占位键；不得 pull/use proprietary production image、不得用真实 credentials 或把 broker 当真值。

## 六层需求确认

- 目标层：可启动开发底座，不开发业务流程。
- 机制层：`dev-up` 不隐式 ingest/send/model call。
- 实现设计层：`primary_route=Docker Compose+Make`；`fallback_route=documented local test harness`；`capability_status=local-only`；`probe_required=up/down/health`。
- 流程层：Codex 启停→测试→人工审阅日志。
- 判断标准层：health green、migrate/fixtures commands有安全拒绝。
- 反馈层：容器/外置盘问题时停于 doc fallback，不改系统范围。

## Impact check

检查 macOS/AppleDouble、port collision、ignore、license images、同步包不收 `.env.example` 之外的配置；legacy 独立。

## Must read

`P01-01`、`ARCHITECTURE_AND_MODULE_BOUNDARIES.md`、`OPEN_SOURCE_SELECTION_AND_EXIT_STRATEGY.md`、安全扫描基线。

## Execution contract

- Capability status：local-only runtime; no data or external action。
- Probe required：yes — Compose lifecycle and health probe。

- Primary route：Make targets bootstrap/dev-up/dev-down/migrate/load-fixtures/regression 的 safe implementation。
- Fallback route：Docker 不可用时只验证 config/render，报告 BLOCKED。
- Allowed Codex autonomy：新 local config、docs、CI config。
- Forbidden Codex guessing：公网端口、生产数据库 URL、账号/secret、real ingest path。
- Required inputs：skeleton、approved local dependency choices。
- Required outputs：compose render、Make help、health endpoint、CI baseline。
- Execution entrypoints：`make bootstrap/dev-up/dev-down/migrate/load-fixtures/regression`。

## Execution steps

1. 写 typed config 与 placeholders。
2. 写 local Compose 和 Make commands，全部 default safe。
3. 启动/health/停止以及 migration 空路径测试。
4. 运行 CI/local scan，记录无 external action。

## Validation commands

`make bootstrap`、`make dev-up`、health probe、`make migrate`、`make dev-down`、`make regression`、compose config render。

## Done when

空环境生命周期可复现；未加载 fixture/真实资料；日志无 secret/absolute path；CI 可运行。

## Blocked if

Docker/端口/架构不支持，或任一命令需要真实密钥/网络/资料。

## Output 回报格式

命令结果、容器/版本、默认 flags、scan、Git、未验证/阻断与 P01-03。

## Git completion

只 stage Compose/Make/example config/CI/docs；禁止 stage `.env`。
