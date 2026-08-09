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
    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'fenjiu_contract' AND table_type = 'BASE TABLE'")
test "$schema_table_count" -eq 13

migration_row_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM fenjiu_contract.schema_migrations WHERE version IN ('0001', '0002', '0003')")
test "$migration_row_count" -eq 3

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
),
(
    '00000000-0000-4000-8000-000000000303',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000202', 'synthetic_fixture', 'v3',
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
),
(
    '00000000-0000-4000-8000-000000000403',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000202',
    '00000000-0000-4000-8000-000000000303', 1,
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

INSERT INTO fenjiu_contract.tenants (
    id, slug, sensitivity, is_synthetic, external_execution_allowed,
    created_at, updated_at, created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000000901', 'contract_tenant',
    'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
);

INSERT INTO fenjiu_contract.projects (
    id, tenant_id, slug, sensitivity, is_synthetic,
    external_execution_allowed, created_at, updated_at, created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000901', 'contract_project',
    'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
);

INSERT INTO fenjiu_contract.business_lines (
    id, tenant_id, project_id, slug, sensitivity, is_synthetic,
    external_execution_allowed, created_at, updated_at, created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000000921',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911', 'contract_line',
    'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
);

INSERT INTO fenjiu_contract.source_refs (
    id, tenant_id, project_id, business_line_id, source_kind, source_version,
    data_state, sensitivity, is_synthetic, external_execution_allowed,
    created_at, updated_at, created_by, correlation_id
) VALUES
(
    '00000000-0000-4000-8000-000000000310',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921', 'contract_probe', 'v1',
    'staging', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
),
(
    '00000000-0000-4000-8000-000000000320',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921', 'contract_probe', 'v2',
    'staging', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
),
(
    '00000000-0000-4000-8000-000000000330',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921', 'contract_probe', 'v3',
    'staging', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
),
(
    '00000000-0000-4000-8000-000000000340',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921', 'contract_probe', 'v4',
    'staging', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
),
(
    '00000000-0000-4000-8000-000000000350',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921', 'contract_probe', 'v5',
    'staging', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
);

INSERT INTO fenjiu_contract.data_versions (
    id, tenant_id, project_id, business_line_id, source_ref_id, version_no,
    data_state, sensitivity, is_synthetic, external_execution_allowed,
    created_at, updated_at, created_by, correlation_id
) VALUES
(
    '00000000-0000-4000-8000-000000000410',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921',
    '00000000-0000-4000-8000-000000000310', 1,
    'conflict', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
),
(
    '00000000-0000-4000-8000-000000000420',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921',
    '00000000-0000-4000-8000-000000000320', 1,
    'blocked', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
),
(
    '00000000-0000-4000-8000-000000000430',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921',
    '00000000-0000-4000-8000-000000000330', 1,
    'expired', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
),
(
    '00000000-0000-4000-8000-000000000440',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921',
    '00000000-0000-4000-8000-000000000340', 1,
    'superseded', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
),
(
    '00000000-0000-4000-8000-000000000450',
    '00000000-0000-4000-8000-000000000901',
    '00000000-0000-4000-8000-000000000911',
    '00000000-0000-4000-8000-000000000921',
    '00000000-0000-4000-8000-000000000350', 2,
    'approved', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'contract_probe'
);

INSERT INTO fenjiu_contract.truth_versions (
    id, tenant_id, project_id, business_line_id, entity_kind, subject_ref,
    version_no, data_state, source_ref_id, data_version_id, payload_hash, diff_hash,
    changed_fields, sensitivity, is_synthetic, external_execution_allowed,
    created_at, updated_at, created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000000701',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201', 'product',
    'synthetic_subject', 1, 'fixture',
    '00000000-0000-4000-8000-000000000301',
    '00000000-0000-4000-8000-000000000401',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    '1111111111111111111111111111111111111111111111111111111111111111',
    ARRAY['contract_field'], 'internal', true, false,
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test',
    'synthetic_correlation'
);
SQL

current_truth_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM fenjiu_contract.current_approved_truth")
test "$current_truth_count" -eq 0

body_column_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'fenjiu_contract' AND table_name IN ('support_conversations', 'support_messages', 'support_intents', 'support_draft_replies', 'support_handoff_cases') AND column_name ~ '(body|payload|attachment|raw|content_text)'")
test "$body_column_count" -eq 0

psql_database "$TEST_DATABASE" >/dev/null <<'SQL'
INSERT INTO fenjiu_contract.support_conversations (
    id, tenant_id, project_id, business_line_id, channel_ref,
    external_conversation_id, status, data_state, source_ref_id,
    data_version_id, sensitivity, is_synthetic, external_execution_allowed,
    retention_policy_ref, consent_ref, created_at, updated_at,
    created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000001001',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'channel:tiktok.synthetic', 'external_conversation_1', 'active',
    'fixture', '00000000-0000-4000-8000-000000000301',
    '00000000-0000-4000-8000-000000000401', 'restricted',
    true, false, 'retention_policy:p06_synthetic',
    'consent:synthetic_present', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.support_messages (
    id, conversation_id, tenant_id, project_id, business_line_id,
    direction, external_message_id, content_hash, content_ref,
    received_at, received_by, data_state, source_ref_id, data_version_id,
    sensitivity, is_synthetic, external_execution_allowed,
    retention_policy_ref, redaction_ref, consent_ref, created_at,
    updated_at, created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000001101',
    '00000000-0000-4000-8000-000000001001',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'inbound', 'external_message_1',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'ref:conversation:synthetic_body_1', CURRENT_TIMESTAMP,
    'synthetic_channel', 'fixture',
    '00000000-0000-4000-8000-000000000301',
    '00000000-0000-4000-8000-000000000401', 'restricted',
    true, false, 'retention_policy:p06_synthetic',
    'redaction:hash_only', 'consent:synthetic_present',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test',
    'synthetic_correlation'
);

INSERT INTO fenjiu_contract.support_intents (
    id, message_id, tenant_id, project_id, business_line_id,
    intent_label, risk_level, policy_version, model_ref, data_state,
    source_ref_id, data_version_id, sensitivity, is_synthetic,
    external_execution_allowed, created_at, updated_at, created_by,
    correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000001201',
    '00000000-0000-4000-8000-000000001101',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'faq_general', 'low', 'support_contract_v1',
    'synthetic_classifier_v1', 'fixture',
    '00000000-0000-4000-8000-000000000301',
    '00000000-0000-4000-8000-000000000401', 'restricted',
    true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.support_draft_replies (
    id, message_id, tenant_id, project_id, business_line_id,
    draft_ref, fact_version_set_hash, policy_version, state, data_state,
    source_ref_id, data_version_id, sensitivity, is_synthetic,
    external_execution_allowed, created_at, updated_at, created_by,
    correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000001301',
    '00000000-0000-4000-8000-000000001101',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'ref:draft:synthetic_1',
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    'support_contract_v1', 'draft_only', 'fixture',
    '00000000-0000-4000-8000-000000000301',
    '00000000-0000-4000-8000-000000000401', 'restricted',
    true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.support_handoff_cases (
    id, conversation_id, message_id, tenant_id, project_id,
    business_line_id, reason, status, policy_version, data_state,
    source_ref_id, data_version_id, sensitivity, is_synthetic,
    external_execution_allowed, created_at, updated_at, created_by,
    correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000001401',
    '00000000-0000-4000-8000-000000001001',
    '00000000-0000-4000-8000-000000001101',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'privacy_review_required', 'open', 'support_contract_v1',
    'fixture', '00000000-0000-4000-8000-000000000301',
    '00000000-0000-4000-8000-000000000401', 'restricted',
    true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);
SQL

expect_sql_failure "support message replay external id is unique" \
    "INSERT INTO fenjiu_contract.support_messages (id, conversation_id, tenant_id, project_id, business_line_id, direction, external_message_id, content_hash, content_ref, received_at, received_by, data_state, source_ref_id, data_version_id, sensitivity, is_synthetic, external_execution_allowed, retention_policy_ref, redaction_ref, consent_ref, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000001102', '00000000-0000-4000-8000-000000001001', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'inbound', 'external_message_1', 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', 'ref:conversation:synthetic_body_2', CURRENT_TIMESTAMP, 'synthetic_channel', 'fixture', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000401', 'restricted', true, false, 'retention_policy:p06_synthetic', 'redaction:hash_only', 'consent:synthetic_present', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "support message cannot cross conversation scope" \
    "INSERT INTO fenjiu_contract.support_messages (id, conversation_id, tenant_id, project_id, business_line_id, direction, external_message_id, content_hash, content_ref, received_at, received_by, data_state, source_ref_id, data_version_id, sensitivity, is_synthetic, external_execution_allowed, retention_policy_ref, redaction_ref, consent_ref, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000001103', '00000000-0000-4000-8000-000000001001', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000202', 'inbound', 'external_message_cross_scope', 'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd', 'ref:conversation:synthetic_body_3', CURRENT_TIMESTAMP, 'synthetic_channel', 'fixture', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000401', 'restricted', true, false, 'retention_policy:p06_synthetic', 'redaction:hash_only', 'consent:synthetic_present', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "support content ref must be opaque reference" \
    "INSERT INTO fenjiu_contract.support_messages (id, conversation_id, tenant_id, project_id, business_line_id, direction, external_message_id, content_hash, content_ref, received_at, received_by, data_state, source_ref_id, data_version_id, sensitivity, is_synthetic, external_execution_allowed, retention_policy_ref, redaction_ref, consent_ref, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000001104', '00000000-0000-4000-8000-000000001001', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'inbound', 'external_message_bad_ref', 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', 'not_a_ref', CURRENT_TIMESTAMP, 'synthetic_channel', 'fixture', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000401', 'restricted', true, false, 'retention_policy:p06_synthetic', 'redaction:hash_only', 'consent:synthetic_present', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "support draft cannot enable external execution" \
    "INSERT INTO fenjiu_contract.support_draft_replies (id, message_id, tenant_id, project_id, business_line_id, draft_ref, fact_version_set_hash, policy_version, state, data_state, source_ref_id, data_version_id, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000001302', '00000000-0000-4000-8000-000000001101', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'ref:draft:synthetic_2', 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 'support_contract_v1', 'draft_only', 'fixture', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000401', 'restricted', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "support messages are append only" \
    "UPDATE fenjiu_contract.support_messages SET content_hash = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff' WHERE id = '00000000-0000-4000-8000-000000001101'"

expect_sql_failure "support handoff cases are append only" \
    "DELETE FROM fenjiu_contract.support_handoff_cases WHERE id = '00000000-0000-4000-8000-000000001401'"

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

expect_sql_failure "approved truth requires complete approval evidence" \
    "INSERT INTO fenjiu_contract.truth_versions (id, tenant_id, project_id, business_line_id, entity_kind, subject_ref, version_no, parent_version_id, data_state, source_ref_id, data_version_id, payload_hash, diff_hash, changed_fields, effective_from, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000702', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'price', 'synthetic_subject', 2, '00000000-0000-4000-8000-000000000401', 'approved', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000401', 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', '2222222222222222222222222222222222222222222222222222222222222222', ARRAY['contract_field'], CURRENT_TIMESTAMP, 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "conflict truth root is forbidden" \
    "INSERT INTO fenjiu_contract.truth_versions (id, tenant_id, project_id, business_line_id, entity_kind, subject_ref, version_no, data_state, source_ref_id, data_version_id, payload_hash, diff_hash, changed_fields, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000710', '00000000-0000-4000-8000-000000000901', '00000000-0000-4000-8000-000000000911', '00000000-0000-4000-8000-000000000921', 'product', 'conflict_root', 1, 'conflict', '00000000-0000-4000-8000-000000000310', '00000000-0000-4000-8000-000000000410', '1010101010101010101010101010101010101010101010101010101010101010', '1111111111111111111111111111111111111111111111111111111111111111', ARRAY['contract_field'], 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'contract_probe')"

expect_sql_failure "blocked truth root is forbidden" \
    "INSERT INTO fenjiu_contract.truth_versions (id, tenant_id, project_id, business_line_id, entity_kind, subject_ref, version_no, data_state, source_ref_id, data_version_id, payload_hash, diff_hash, changed_fields, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000720', '00000000-0000-4000-8000-000000000901', '00000000-0000-4000-8000-000000000911', '00000000-0000-4000-8000-000000000921', 'product', 'blocked_root', 1, 'blocked', '00000000-0000-4000-8000-000000000320', '00000000-0000-4000-8000-000000000420', '2020202020202020202020202020202020202020202020202020202020202020', '2222222222222222222222222222222222222222222222222222222222222222', ARRAY['contract_field'], 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'contract_probe')"

expect_sql_failure "expired truth root is forbidden" \
    "INSERT INTO fenjiu_contract.truth_versions (id, tenant_id, project_id, business_line_id, entity_kind, subject_ref, version_no, data_state, source_ref_id, data_version_id, payload_hash, diff_hash, changed_fields, effective_from, effective_until, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000730', '00000000-0000-4000-8000-000000000901', '00000000-0000-4000-8000-000000000911', '00000000-0000-4000-8000-000000000921', 'product', 'expired_root', 1, 'expired', '00000000-0000-4000-8000-000000000330', '00000000-0000-4000-8000-000000000430', '3030303030303030303030303030303030303030303030303030303030303030', '3333333333333333333333333333333333333333333333333333333333333333', ARRAY['contract_field'], CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 day', 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'contract_probe')"

expect_sql_failure "superseded truth root is forbidden" \
    "INSERT INTO fenjiu_contract.truth_versions (id, tenant_id, project_id, business_line_id, entity_kind, subject_ref, version_no, data_state, source_ref_id, data_version_id, payload_hash, diff_hash, changed_fields, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000740', '00000000-0000-4000-8000-000000000901', '00000000-0000-4000-8000-000000000911', '00000000-0000-4000-8000-000000000921', 'product', 'superseded_root', 1, 'superseded', '00000000-0000-4000-8000-000000000340', '00000000-0000-4000-8000-000000000440', '4040404040404040404040404040404040404040404040404040404040404040', '4444444444444444444444444444444444444444444444444444444444444444', ARRAY['contract_field'], 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'contract_probe')"

expect_sql_failure "approved child cannot follow rejected conflict root" \
    "INSERT INTO fenjiu_contract.truth_versions (id, tenant_id, project_id, business_line_id, entity_kind, subject_ref, version_no, parent_version_id, data_state, source_ref_id, data_version_id, payload_hash, diff_hash, changed_fields, effective_from, approval_evidence_id, approval_actor_ref, approval_decision_ref, approval_evidence_ref, approval_policy_version, approved_at, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000750', '00000000-0000-4000-8000-000000000901', '00000000-0000-4000-8000-000000000911', '00000000-0000-4000-8000-000000000921', 'product', 'conflict_root', 2, '00000000-0000-4000-8000-000000000410', 'approved', '00000000-0000-4000-8000-000000000350', '00000000-0000-4000-8000-000000000450', '5050505050505050505050505050505050505050505050505050505050505050', '5555555555555555555555555555555555555555555555555555555555555555', ARRAY['contract_field'], CURRENT_TIMESTAMP, '00000000-0000-4000-8000-000000000850', 'synthetic_reviewer', 'decision_750', 'evidence_750', 'policy_v1', CURRENT_TIMESTAMP, 'internal', NOT TRUE, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'contract_probe')"

current_truth_after_rejected_root=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM fenjiu_contract.current_approved_truth")
test "$current_truth_after_rejected_root" -eq 0

expect_sql_failure "truth version number is unique within scope and subject" \
    "INSERT INTO fenjiu_contract.truth_versions (id, tenant_id, project_id, business_line_id, entity_kind, subject_ref, version_no, data_state, source_ref_id, data_version_id, payload_hash, diff_hash, changed_fields, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000703', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'product', 'synthetic_subject', 1, 'fixture', '00000000-0000-4000-8000-000000000302', '00000000-0000-4000-8000-000000000402', 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '3333333333333333333333333333333333333333333333333333333333333333', ARRAY['contract_field'], 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "truth parent cannot cross business line" \
    "INSERT INTO fenjiu_contract.truth_versions (id, tenant_id, project_id, business_line_id, entity_kind, subject_ref, version_no, parent_version_id, data_state, source_ref_id, data_version_id, payload_hash, diff_hash, changed_fields, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000704', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000202', 'product', 'synthetic_subject', 2, '00000000-0000-4000-8000-000000000401', 'fixture', '00000000-0000-4000-8000-000000000303', '00000000-0000-4000-8000-000000000403', 'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd', '4444444444444444444444444444444444444444444444444444444444444444', ARRAY['contract_field'], 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "fixture truth state transition is forbidden" \
    "INSERT INTO fenjiu_contract.truth_versions (id, tenant_id, project_id, business_line_id, entity_kind, subject_ref, version_no, parent_version_id, data_state, source_ref_id, data_version_id, payload_hash, diff_hash, changed_fields, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000000705', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'product', 'synthetic_subject', 2, '00000000-0000-4000-8000-000000000401', 'fixture', '00000000-0000-4000-8000-000000000302', '00000000-0000-4000-8000-000000000402', 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', '5555555555555555555555555555555555555555555555555555555555555555', ARRAY['contract_field'], 'internal', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "truth history cannot be updated" \
    "UPDATE fenjiu_contract.truth_versions SET payload_hash = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff' WHERE id = '00000000-0000-4000-8000-000000000701'"

expect_sql_failure "truth history cannot be deleted" \
    "DELETE FROM fenjiu_contract.truth_versions WHERE id = '00000000-0000-4000-8000-000000000701'"

printf 'P02/P06 migration replay and negative constraints passed.\n'
