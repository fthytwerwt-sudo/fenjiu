#!/bin/sh
set -eu

cd "$(dirname "$0")/../.."

WORKTREE_PATH=$(pwd -P)
COMPOSE_PROJECT_SUFFIX=$(printf '%s\n' "$WORKTREE_PATH" | cksum | awk '{print $1}')
COMPOSE_PROJECT_NAME="fenjiu-local-runtime-$COMPOSE_PROJECT_SUFFIX"
TEST_DATABASE="fenjiu_p02_01_contract_test"

compose() {
    COMPOSE_PROJECT_NAME="$COMPOSE_PROJECT_NAME" docker compose -f docker-compose.yml "$@"
}

psql_database() {
    database=$1
    shift
    compose exec -T postgres psql \
        -X -v ON_ERROR_STOP=1 -h 127.0.0.1 \
        -U fenjiu_local -d "$database" "$@"
}

cleanup() {
    psql_database postgres \
        -c "DROP DATABASE IF EXISTS $TEST_DATABASE WITH (FORCE)" \
        >/dev/null 2>&1 || true
}

expect_sql_failure() {
    label=$1
    sql=$2
    if printf '%s\n' "$sql" | psql_database "$TEST_DATABASE" >/dev/null 2>&1; then
        printf 'expected SQL failure did not occur: %s\n' "$label" >&2
        exit 1
    fi
    printf 'negative constraint passed: %s\n' "$label"
}

trap cleanup EXIT HUP INT TERM
cleanup
psql_database postgres -c "CREATE DATABASE $TEST_DATABASE" >/dev/null

for replay_pass in 1 2; do
    for migration in migrations/[0-9][0-9][0-9][0-9]_*.sql; do
        test -f "$migration"
        psql_database "$TEST_DATABASE" < "$migration" >/dev/null
    done
    printf 'migration replay pass %s complete\n' "$replay_pass"
done

schema_table_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'fenjiu_contract'")
test "$schema_table_count" -eq 7

migration_row_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM fenjiu_contract.schema_migrations WHERE version = '0001'")
test "$migration_row_count" -eq 1

psql_database "$TEST_DATABASE" >/dev/null <<'SQL'
INSERT INTO fenjiu_contract.tenants (
    id, slug, sensitivity, is_synthetic, external_execution_allowed,
    created_at, updated_at, created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000000001', 'synthetic_tenant',
    'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.projects (
    id, tenant_id, slug, sensitivity, is_synthetic,
    external_execution_allowed, created_at, updated_at, created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000001', 'synthetic_project',
    'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.business_lines (
    id, tenant_id, project_id, slug, sensitivity, is_synthetic,
    external_execution_allowed, created_at, updated_at, created_by, correlation_id
) VALUES
(
    '00000000-0000-4000-8000-000000000201',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101', 'synthetic_line_a',
    'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
),
(
    '00000000-0000-4000-8000-000000000202',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101', 'synthetic_line_b',
    'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.source_refs (
    id, tenant_id, project_id, business_line_id, source_kind, source_version,
    data_state, sensitivity, is_synthetic, external_execution_allowed,
    created_at, updated_at, created_by, correlation_id
) VALUES
(
    '00000000-0000-4000-8000-000000000301',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201', 'synthetic_fixture', 'v1',
    'fixture', 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
),
(
    '00000000-0000-4000-8000-000000000302',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201', 'synthetic_fixture', 'v2',
    'fixture', 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.data_versions (
    id, tenant_id, project_id, business_line_id, source_ref_id, version_no,
    data_state, sensitivity, is_synthetic, external_execution_allowed,
    created_at, updated_at, created_by, correlation_id
) VALUES
(
    '00000000-0000-4000-8000-000000000401',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    '00000000-0000-4000-8000-000000000301', 1,
    'fixture', 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
),
(
    '00000000-0000-4000-8000-000000000402',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    '00000000-0000-4000-8000-000000000302', 1,
    'fixture', 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.entity_metadata (
    id, tenant_id, project_id, business_line_id, data_state,
    source_ref_id, data_version_id, sensitivity, is_synthetic,
    external_execution_allowed, created_at, updated_at, created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000000501',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201', 'fixture',
    '00000000-0000-4000-8000-000000000301',
    '00000000-0000-4000-8000-000000000401',
    'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);
SQL

expect_sql_failure "missing mandatory metadata" \
    "INSERT INTO fenjiu_contract.entity_metadata (id) VALUES ('00000000-0000-4000-8000-000000000601')"

expect_sql_failure "cross business line source" \
    "INSERT INTO fenjiu_contract.data_versions (id, tenant_id, project_id, business_line_id, source_ref_id, version_no, data_state, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000602', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000202', '00000000-0000-4000-8000-000000000301', 1, 'fixture', 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "synthetic fixture cannot become approved" \
    "INSERT INTO fenjiu_contract.source_refs (id, tenant_id, project_id, business_line_id, source_kind, source_version, data_state, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000603', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'synthetic_fixture', 'v3', 'approved', 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "fixture cannot enable external execution" \
    "INSERT INTO fenjiu_contract.source_refs (id, tenant_id, project_id, business_line_id, source_kind, source_version, data_state, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000604', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'synthetic_fixture', 'v4', 'fixture', 'internal', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "source and version must match" \
    "INSERT INTO fenjiu_contract.entity_metadata (id, tenant_id, project_id, business_line_id, data_state, source_ref_id, data_version_id, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000605', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'fixture', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000402', 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

printf 'P02-01 migration replay and negative constraints passed.\n'
