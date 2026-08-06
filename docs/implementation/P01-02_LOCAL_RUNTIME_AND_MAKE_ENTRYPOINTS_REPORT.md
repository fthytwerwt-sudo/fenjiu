# P01-02｜本地运行、Make 入口与 CI 基线报告

> **状态：completed_on_task_branch**
> **执行日期：2026-08-06**
> **任务卡：** `docs/implementation/codex_tasks/phase_01/P01-02_local_runtime_and_make_entrypoints.md`
> **基线提交：** `8b349b539c169a17bd280bc3f3ebfdd58c5ee0d2`
> **范围边界：** 本报告只记录 local-only runtime、Make 入口、CI 静态验证和扫描兼容；不接数据库连接、不读取环境变量、不加载真实资料、不调用外部 HTTP、模型、采集、发送、发布、报价、付款、订单或退款。

## 1. 结论

| 项目 | 状态 | 证据与边界 |
|---|---|---|
| Docker Compose | 已实现 | 使用固定镜像 `postgres:16.14-alpine3.24`、`valkey/valkey:8.1.9-alpine3.24`、`python:3.13.9-slim-bookworm`；无 host `ports`，仅 `expose` 与 named volumes。 |
| Make 入口 | 已实现 | `bootstrap`、`compose-config`、`dev-up`、`health`、`migrate`、`load-fixtures`、`dev-down`、`regression` 均为显式 target。 |
| Runtime entrypoints | 已实现 | `apps/api` 与 `apps/admin` 提供 stdlib health endpoint；`apps/worker` 提供 idle、health、migration no-op 与 fixture no-op。 |
| 数据与外部动作 | 已确认关闭 | entrypoints 不读取 `.env`，不连接数据库，不连接 broker，不外发、不采集、不发布、不调用模型，不写入数据。 |
| `.env.example` | 已实现 | 只包含 local-only placeholder 与 fail-closed flags；不被命令复制为 `.env`。 |
| CI baseline | BLOCKED（远端权限）/ 本地等价验证已实现 | GitHub 拒绝创建 `.github/workflows/local-runtime.yml`，原因是当前推送凭据缺少 `workflow` scope；本任务保留本地 `make regression` 与 compose render 作为等价静态验证，不执行 Docker pull/up。 |
| P00 scanner 兼容 | 已实现 | 扫描器只放行根目录 `.env.example`，其他 `.env*` 仍按 forbidden path fail-closed。 |

## 2. 安全限制

`make help` 显式说明本地入口不会安装依赖、复制 `.env`、暴露 host ports、ingest、send、crawl、model call、quote、payment、order、refund 或 publish。`migrate` 和 `load-fixtures` 只在 worker 容器内打印 JSON no-op 结果，字段 `writes_data=false`、`loads_fixtures=false`。

## 3. 验收命令

```text
make help
make bootstrap
docker compose -f docker-compose.yml config --quiet
make dev-up
make health
make migrate
make load-fixtures
make dev-down
make regression
python3 -m unittest discover -s tests/architecture
python3 -m unittest discover -s tests/regression
python3 scripts/validate_regression_baseline.py --base-sha 8b349b539c169a17bd280bc3f3ebfdd58c5ee0d2
python3 scripts/validate_regression_baseline.py --base-sha 8b349b539c169a17bd280bc3f3ebfdd58c5ee0d2 --all-files
git diff --check
```

## 4. 业务状态边界

本任务只证明 local-only 工程底座可启动。它不解除 SKU、价格、库存、主体/资质、账号、收款、履约或 TikTok 酒类边界的业务闸门；`external_send=false`、`public_publish=false`、`real_quote=false`、`payment=false`、`order_create=false`、`refund=false`、`external_execution_allowed=false`、`business_external_ready=false` 继续保持关闭。

## 5. 后续

P01-03 可在此基础上补配置、健康检查和观测合同，但仍不得接真实 secret、provider、业务资料或外部动作。若后续需要提交 GitHub Actions workflow，必须先使用具备 `workflow` scope 的凭据或由有权限的人单独提交。
