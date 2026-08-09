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
test "$schema_table_count" -eq 22

expected_migration_versions=$(cat <<'EOF'
0001
0002
0003
0004
EOF
)
actual_migration_versions=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT version FROM fenjiu_contract.schema_migrations ORDER BY version")
if ! test "$actual_migration_versions" = "$expected_migration_versions"; then
    printf 'schema_migrations version order mismatch\nexpected:\n%s\nactual:\n%s\n' \
        "$expected_migration_versions" "$actual_migration_versions" >&2
    exit 1
fi

for migration_version in 0001 0002 0003 0004; do
    migration_version_count=$(psql_database "$TEST_DATABASE" -Atc \
        "SELECT count(*) FROM fenjiu_contract.schema_migrations WHERE version = '$migration_version'")
    test "$migration_version_count" -eq 1
done

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

psql_database "$TEST_DATABASE" >/dev/null <<'SQL'
INSERT INTO fenjiu_contract.lead_candidates (
    lead_ref, tenant_id, project_id, business_line_id, source_policy_id,
    snapshot_ref, source_url_hash, organization_fingerprint,
    field_fingerprint_hash, data_state, is_synthetic,
    external_execution_allowed, business_external_ready,
    created_at, created_by, correlation_id
) VALUES (
    'lead_candidate_sql_1',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'source_policy_v1', 'snapshot_ref_sql_1',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'fixture', true, false, false, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.lead_reviews (
    review_ref, lead_ref, tenant_id, project_id, business_line_id,
    decision, review_evidence_ref, reviewer_ref, dedupe_result,
    created_at, correlation_id
) VALUES (
    'lead_review_sql_1', 'lead_candidate_sql_1',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'approved', 'review_evidence_ref_sql', 'reviewer.synthetic',
    'new', CURRENT_TIMESTAMP, 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.organizations (
    organization_ref, review_ref, tenant_id, project_id, business_line_id,
    organization_fingerprint, source_policy_id, source_url_hash,
    dnc_subject_hash, data_state, is_synthetic,
    external_execution_allowed, business_external_ready,
    created_at, created_by, correlation_id
) VALUES (
    'organization_sql_1', 'lead_review_sql_1',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    'source_policy_v1',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
    'fixture', true, false, false, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.contacts (
    contact_ref, organization_ref, tenant_id, project_id, business_line_id,
    subject_hash, source_evidence_ref, consent_granted, dnc_blocked,
    data_state, is_synthetic, external_execution_allowed,
    business_external_ready, created_at, created_by, correlation_id
) VALUES (
    'party_sql_1', 'organization_sql_1',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
    'party_source_evidence_ref', true, false, 'fixture', true,
    false, false, CURRENT_TIMESTAMP, 'synthetic_test',
    'synthetic_correlation'
);

INSERT INTO fenjiu_contract.dnc_records (
    dnc_ref, tenant_id, project_id, business_line_id, subject_hash,
    evidence_ref, actor_ref, reason_code, created_at, correlation_id
) VALUES (
    'dnc_sql_1',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
    'withdrawal_evidence_ref', 'support_agent.synthetic',
    'withdrawal', CURRENT_TIMESTAMP, 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.retention_intents (
    retention_ref, tenant_id, project_id, business_line_id, subject_ref,
    intent, evidence_ref, actor_ref, created_at, correlation_id
) VALUES (
    'retention_sql_1',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'party_sql_1', 'delete_requested', 'retention_evidence_ref',
    'support_agent.synthetic', CURRENT_TIMESTAMP, 'synthetic_correlation'
);
SQL

expect_sql_failure "contact requires source and consent" \
    "INSERT INTO fenjiu_contract.contacts (contact_ref, organization_ref, tenant_id, project_id, business_line_id, subject_hash, source_evidence_ref, consent_granted, dnc_blocked, data_state, is_synthetic, external_execution_allowed, business_external_ready, created_at, created_by, correlation_id) VALUES ('party_sql_no_consent', 'organization_sql_1', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 'party_source_evidence_ref', false, false, 'fixture', true, false, false, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "crm organization cannot cross business line review" \
    "INSERT INTO fenjiu_contract.organizations (organization_ref, review_ref, tenant_id, project_id, business_line_id, organization_fingerprint, source_policy_id, source_url_hash, dnc_subject_hash, data_state, is_synthetic, external_execution_allowed, business_external_ready, created_at, created_by, correlation_id) VALUES ('organization_cross_line_sql', 'lead_review_sql_1', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000202', 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 'source_policy_v1', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd', 'fixture', true, false, false, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "dnc records are immutable" \
    "UPDATE fenjiu_contract.dnc_records SET reason_code = 'changed' WHERE dnc_ref = 'dnc_sql_1'"

expect_sql_failure "dnc records cannot be deleted" \
    "DELETE FROM fenjiu_contract.dnc_records WHERE dnc_ref = 'dnc_sql_1'"

expect_sql_failure "crm rows cannot enable external execution" \
    "INSERT INTO fenjiu_contract.interactions (interaction_ref, organization_ref, tenant_id, project_id, business_line_id, kind, subject_hash, sent_count, external_sent, data_state, is_synthetic, external_execution_allowed, business_external_ready, created_at, created_by, correlation_id) VALUES ('interaction_external_sql', 'organization_sql_1', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'draft', 'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd', 0, false, 'fixture', true, true, false, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

body_column_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'fenjiu_contract' AND table_name IN ('support_conversations', 'support_messages', 'support_intents', 'support_draft_replies', 'support_handoff_cases', 'support_unknown_scope_quarantines') AND column_name ~ '(body|payload|attachment|raw|content_text)'")
test "$body_column_count" -eq 0

unknown_scope_link_column_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'fenjiu_contract' AND table_name = 'support_unknown_scope_quarantines' AND column_name IN ('conversation_id', 'message_id', 'tenant_id', 'project_id', 'business_line_id')")
test "$unknown_scope_link_column_count" -eq 0

raw_external_id_column_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'fenjiu_contract' AND table_name IN ('support_conversations', 'support_messages') AND column_name IN ('external_conversation_id', 'external_message_id')")
test "$raw_external_id_column_count" -eq 0

known_scope_external_ref_column_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'fenjiu_contract' AND table_name IN ('support_conversations', 'support_messages') AND column_name IN ('external_conversation_ref', 'external_message_ref')")
test "$known_scope_external_ref_column_count" -eq 2

psql_database "$TEST_DATABASE" >/dev/null <<'SQL'
INSERT INTO fenjiu_contract.support_conversations (
    id, tenant_id, project_id, business_line_id, channel_ref,
    external_conversation_ref, status, data_state, source_ref_id,
    data_version_id, sensitivity, is_synthetic, external_execution_allowed,
    retention_policy_ref, consent_ref, created_at, updated_at,
    created_by, correlation_id
) VALUES (
    '00000000-0000-4000-8000-000000001001',
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000101',
    '00000000-0000-4000-8000-000000000201',
    'channel:tiktok.synthetic',
    'ref:external_conversation:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'active',
    'fixture', '00000000-0000-4000-8000-000000000301',
    '00000000-0000-4000-8000-000000000401', 'restricted',
    true, false, 'retention_policy:p06_synthetic',
    'consent:synthetic_present', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    'synthetic_test', 'synthetic_correlation'
);

INSERT INTO fenjiu_contract.support_messages (
    id, conversation_id, tenant_id, project_id, business_line_id,
    direction, external_message_ref, content_hash, content_ref,
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
    'inbound', 'ref:external_message:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
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

INSERT INTO fenjiu_contract.support_unknown_scope_quarantines (
    id, channel_ref, external_conversation_ref, external_message_ref,
    content_hash, content_ref, reason, status, policy_version,
    correlation_id, retention_policy_ref, redaction_ref, received_at,
    received_by, is_synthetic, external_execution_allowed, created_at,
    updated_at, created_by
) VALUES (
    '00000000-0000-4000-8000-000000001501',
    'channel:tiktok.synthetic',
    'ref:external_conversation:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'ref:external_message:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'ref:conversation:synthetic_unknown_body_1',
    'unknown_scope', 'open', 'support_contract_v1',
    'unknown_scope', 'retention_policy:p06_synthetic',
    'redaction:hash_only', CURRENT_TIMESTAMP, 'synthetic_channel',
    true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test'
);
SQL

unknown_quarantine_count=$(psql_database "$TEST_DATABASE" -Atc \
    "SELECT count(*) FROM fenjiu_contract.support_unknown_scope_quarantines WHERE reason = 'unknown_scope' AND status = 'open'")
test "$unknown_quarantine_count" -eq 1

expect_sql_failure "support message replay external ref is unique" \
    "INSERT INTO fenjiu_contract.support_messages (id, conversation_id, tenant_id, project_id, business_line_id, direction, external_message_ref, content_hash, content_ref, received_at, received_by, data_state, source_ref_id, data_version_id, sensitivity, is_synthetic, external_execution_allowed, retention_policy_ref, redaction_ref, consent_ref, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000001102', '00000000-0000-4000-8000-000000001001', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'inbound', 'ref:external_message:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', 'ref:conversation:synthetic_body_2', CURRENT_TIMESTAMP, 'synthetic_channel', 'fixture', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000401', 'restricted', true, false, 'retention_policy:p06_synthetic', 'redaction:hash_only', 'consent:synthetic_present', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "support message cannot cross conversation scope" \
    "INSERT INTO fenjiu_contract.support_messages (id, conversation_id, tenant_id, project_id, business_line_id, direction, external_message_ref, content_hash, content_ref, received_at, received_by, data_state, source_ref_id, data_version_id, sensitivity, is_synthetic, external_execution_allowed, retention_policy_ref, redaction_ref, consent_ref, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000001103', '00000000-0000-4000-8000-000000001001', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000202', 'inbound', 'ref:external_message:cccccccccccccccccccccccccccccccc', 'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd', 'ref:conversation:synthetic_body_3', CURRENT_TIMESTAMP, 'synthetic_channel', 'fixture', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000401', 'restricted', true, false, 'retention_policy:p06_synthetic', 'redaction:hash_only', 'consent:synthetic_present', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "support content ref must be opaque reference" \
    "INSERT INTO fenjiu_contract.support_messages (id, conversation_id, tenant_id, project_id, business_line_id, direction, external_message_ref, content_hash, content_ref, received_at, received_by, data_state, source_ref_id, data_version_id, sensitivity, is_synthetic, external_execution_allowed, retention_policy_ref, redaction_ref, consent_ref, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000001104', '00000000-0000-4000-8000-000000001001', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'inbound', 'ref:external_message:dddddddddddddddddddddddddddddddd', 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', 'not_a_ref', CURRENT_TIMESTAMP, 'synthetic_channel', 'fixture', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000401', 'restricted', true, false, 'retention_policy:p06_synthetic', 'redaction:hash_only', 'consent:synthetic_present', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "support draft cannot enable external execution" \
    "INSERT INTO fenjiu_contract.support_draft_replies (id, message_id, tenant_id, project_id, business_line_id, draft_ref, fact_version_set_hash, policy_version, state, data_state, source_ref_id, data_version_id, sensitivity, is_synthetic, external_execution_allowed, created_at, updated_at, created_by, correlation_id) VALUES ('00000000-0000-4000-8000-000000001302', '00000000-0000-4000-8000-000000001101', '00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000101', '00000000-0000-4000-8000-000000000201', 'ref:draft:synthetic_2', 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 'support_contract_v1', 'draft_only', 'fixture', '00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000401', 'restricted', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test', 'synthetic_correlation')"

expect_sql_failure "support messages are append only" \
    "UPDATE fenjiu_contract.support_messages SET content_hash = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff' WHERE id = '00000000-0000-4000-8000-000000001101'"

expect_sql_failure "support handoff cases are append only" \
    "DELETE FROM fenjiu_contract.support_handoff_cases WHERE id = '00000000-0000-4000-8000-000000001401'"

expect_sql_failure "unknown scope quarantine external message ref is unique" \
    "INSERT INTO fenjiu_contract.support_unknown_scope_quarantines (id, channel_ref, external_conversation_ref, external_message_ref, content_hash, content_ref, reason, status, policy_version, correlation_id, retention_policy_ref, redaction_ref, received_at, received_by, is_synthetic, external_execution_allowed, created_at, updated_at, created_by) VALUES ('00000000-0000-4000-8000-000000001502', 'channel:tiktok.synthetic', 'ref:external_conversation:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'ref:external_message:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd', 'ref:conversation:synthetic_unknown_body_2', 'unknown_scope', 'open', 'support_contract_v1', 'unknown_scope', 'retention_policy:p06_synthetic', 'redaction:hash_only', CURRENT_TIMESTAMP, 'synthetic_channel', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test')"

expect_sql_failure "unknown scope quarantine content ref must be opaque" \
    "INSERT INTO fenjiu_contract.support_unknown_scope_quarantines (id, channel_ref, external_conversation_ref, external_message_ref, content_hash, content_ref, reason, status, policy_version, correlation_id, retention_policy_ref, redaction_ref, received_at, received_by, is_synthetic, external_execution_allowed, created_at, updated_at, created_by) VALUES ('00000000-0000-4000-8000-000000001503', 'channel:tiktok.synthetic', 'ref:external_conversation:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', 'ref:external_message:ffffffffffffffffffffffffffffffff', 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', 'not_a_ref', 'unknown_scope', 'open', 'support_contract_v1', 'unknown_scope', 'retention_policy:p06_synthetic', 'redaction:hash_only', CURRENT_TIMESTAMP, 'synthetic_channel', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test')"

expect_sql_failure "unknown scope quarantine cannot enable external execution" \
    "INSERT INTO fenjiu_contract.support_unknown_scope_quarantines (id, channel_ref, external_conversation_ref, external_message_ref, content_hash, content_ref, reason, status, policy_version, correlation_id, retention_policy_ref, redaction_ref, received_at, received_by, is_synthetic, external_execution_allowed, created_at, updated_at, created_by) VALUES ('00000000-0000-4000-8000-000000001504', 'channel:tiktok.synthetic', 'ref:external_conversation:11111111111111111111111111111111', 'ref:external_message:22222222222222222222222222222222', 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 'ref:conversation:synthetic_unknown_body_3', 'unknown_scope', 'open', 'support_contract_v1', 'unknown_scope', 'retention_policy:p06_synthetic', 'redaction:hash_only', CURRENT_TIMESTAMP, 'synthetic_channel', true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'synthetic_test')"

expect_sql_failure "unknown scope quarantine is append only" \
    "UPDATE fenjiu_contract.support_unknown_scope_quarantines SET content_hash = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff' WHERE id = '00000000-0000-4000-8000-000000001501'"

expect_sql_failure "unknown scope quarantine cannot be deleted" \
    "DELETE FROM fenjiu_contract.support_unknown_scope_quarantines WHERE id = '00000000-0000-4000-8000-000000001501'"

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

printf 'P02/P05/P06 migration replay and negative constraints passed.\n'
