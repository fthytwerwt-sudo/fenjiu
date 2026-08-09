BEGIN;

CREATE TABLE IF NOT EXISTS fenjiu_contract.support_conversations (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    channel_ref text NOT NULL CHECK (channel_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    external_conversation_id text NOT NULL
        CHECK (external_conversation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    status text NOT NULL CHECK (status IN ('active', 'held', 'handoff_required')),
    data_state fenjiu_contract.data_state NOT NULL,
    source_ref_id uuid NOT NULL,
    data_version_id uuid NOT NULL,
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    retention_policy_ref text NOT NULL
        CHECK (retention_policy_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    consent_ref text NOT NULL CHECK (consent_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT support_conversations_external_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT support_conversations_synthetic_only CHECK (
        is_synthetic = true AND data_state IN ('fixture', 'mock')
    ),
    CONSTRAINT support_conversations_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT support_conversations_scope_key UNIQUE (id, tenant_id, project_id, business_line_id),
    CONSTRAINT support_conversations_external_unique UNIQUE (
        tenant_id, project_id, business_line_id, channel_ref,
        external_conversation_id
    ),
    CONSTRAINT support_conversations_source_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id, is_synthetic
    ) REFERENCES fenjiu_contract.source_refs (
        tenant_id, project_id, business_line_id, id, is_synthetic
    ),
    CONSTRAINT support_conversations_version_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id,
        data_version_id, is_synthetic
    ) REFERENCES fenjiu_contract.data_versions (
        tenant_id, project_id, business_line_id, source_ref_id,
        id, is_synthetic
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.support_messages (
    id uuid PRIMARY KEY,
    conversation_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    direction text NOT NULL CHECK (direction = 'inbound'),
    external_message_id text NOT NULL
        CHECK (external_message_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    content_hash text NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    content_ref text NOT NULL CHECK (content_ref ~ '^ref:[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    received_at timestamptz NOT NULL,
    received_by text NOT NULL CHECK (received_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    data_state fenjiu_contract.data_state NOT NULL,
    source_ref_id uuid NOT NULL,
    data_version_id uuid NOT NULL,
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    retention_policy_ref text NOT NULL
        CHECK (retention_policy_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    redaction_ref text NOT NULL CHECK (redaction_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    consent_ref text NOT NULL CHECK (consent_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT support_messages_external_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT support_messages_synthetic_only CHECK (
        is_synthetic = true AND data_state IN ('fixture', 'mock')
    ),
    CONSTRAINT support_messages_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT support_messages_external_unique UNIQUE (
        conversation_id, external_message_id
    ),
    CONSTRAINT support_messages_conversation_fk FOREIGN KEY (
        conversation_id, tenant_id, project_id, business_line_id
    ) REFERENCES fenjiu_contract.support_conversations (
        id, tenant_id, project_id, business_line_id
    ),
    CONSTRAINT support_messages_source_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id, is_synthetic
    ) REFERENCES fenjiu_contract.source_refs (
        tenant_id, project_id, business_line_id, id, is_synthetic
    ),
    CONSTRAINT support_messages_version_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id,
        data_version_id, is_synthetic
    ) REFERENCES fenjiu_contract.data_versions (
        tenant_id, project_id, business_line_id, source_ref_id,
        id, is_synthetic
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.support_intents (
    id uuid PRIMARY KEY,
    message_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    intent_label text NOT NULL CHECK (intent_label ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    risk_level text NOT NULL CHECK (risk_level IN ('low', 'high')),
    policy_version text NOT NULL CHECK (policy_version ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    model_ref text NOT NULL CHECK (model_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    data_state fenjiu_contract.data_state NOT NULL,
    source_ref_id uuid NOT NULL,
    data_version_id uuid NOT NULL,
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT support_intents_external_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT support_intents_synthetic_only CHECK (
        is_synthetic = true AND data_state IN ('fixture', 'mock')
    ),
    CONSTRAINT support_intents_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT support_intents_message_policy_unique UNIQUE (message_id, policy_version),
    CONSTRAINT support_intents_message_fk FOREIGN KEY (
        message_id
    ) REFERENCES fenjiu_contract.support_messages (id),
    CONSTRAINT support_intents_source_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id, is_synthetic
    ) REFERENCES fenjiu_contract.source_refs (
        tenant_id, project_id, business_line_id, id, is_synthetic
    ),
    CONSTRAINT support_intents_version_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id,
        data_version_id, is_synthetic
    ) REFERENCES fenjiu_contract.data_versions (
        tenant_id, project_id, business_line_id, source_ref_id,
        id, is_synthetic
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.support_draft_replies (
    id uuid PRIMARY KEY,
    message_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    draft_ref text NOT NULL CHECK (draft_ref ~ '^ref:[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    fact_version_set_hash text NOT NULL CHECK (fact_version_set_hash ~ '^[0-9a-f]{64}$'),
    policy_version text NOT NULL CHECK (policy_version ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    state text NOT NULL CHECK (state = 'draft_only'),
    data_state fenjiu_contract.data_state NOT NULL,
    source_ref_id uuid NOT NULL,
    data_version_id uuid NOT NULL,
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT support_drafts_external_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT support_drafts_synthetic_only CHECK (
        is_synthetic = true AND data_state IN ('fixture', 'mock')
    ),
    CONSTRAINT support_drafts_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT support_drafts_replay_unique UNIQUE (
        message_id, policy_version, fact_version_set_hash
    ),
    CONSTRAINT support_drafts_message_fk FOREIGN KEY (
        message_id
    ) REFERENCES fenjiu_contract.support_messages (id),
    CONSTRAINT support_drafts_source_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id, is_synthetic
    ) REFERENCES fenjiu_contract.source_refs (
        tenant_id, project_id, business_line_id, id, is_synthetic
    ),
    CONSTRAINT support_drafts_version_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id,
        data_version_id, is_synthetic
    ) REFERENCES fenjiu_contract.data_versions (
        tenant_id, project_id, business_line_id, source_ref_id,
        id, is_synthetic
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.support_handoff_cases (
    id uuid PRIMARY KEY,
    conversation_id uuid NOT NULL,
    message_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    reason text NOT NULL CHECK (
        reason IN ('unknown_scope', 'dnc_blocked', 'privacy_review_required', 'high_risk')
    ),
    status text NOT NULL CHECK (status = 'open'),
    policy_version text NOT NULL CHECK (policy_version ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    data_state fenjiu_contract.data_state NOT NULL,
    source_ref_id uuid NOT NULL,
    data_version_id uuid NOT NULL,
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT support_handoffs_external_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT support_handoffs_synthetic_only CHECK (
        is_synthetic = true AND data_state IN ('fixture', 'mock')
    ),
    CONSTRAINT support_handoffs_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT support_handoffs_message_reason_unique UNIQUE (
        message_id, reason, policy_version
    ),
    CONSTRAINT support_handoffs_conversation_fk FOREIGN KEY (
        conversation_id, tenant_id, project_id, business_line_id
    ) REFERENCES fenjiu_contract.support_conversations (
        id, tenant_id, project_id, business_line_id
    ),
    CONSTRAINT support_handoffs_message_fk FOREIGN KEY (
        message_id
    ) REFERENCES fenjiu_contract.support_messages (id),
    CONSTRAINT support_handoffs_source_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id, is_synthetic
    ) REFERENCES fenjiu_contract.source_refs (
        tenant_id, project_id, business_line_id, id, is_synthetic
    ),
    CONSTRAINT support_handoffs_version_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id,
        data_version_id, is_synthetic
    ) REFERENCES fenjiu_contract.data_versions (
        tenant_id, project_id, business_line_id, source_ref_id,
        id, is_synthetic
    )
);

CREATE OR REPLACE FUNCTION fenjiu_contract.prevent_support_history_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'support history is append only';
END
$$;

DROP TRIGGER IF EXISTS support_conversations_prevent_mutation
    ON fenjiu_contract.support_conversations;
CREATE TRIGGER support_conversations_prevent_mutation
BEFORE UPDATE OR DELETE ON fenjiu_contract.support_conversations
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_support_history_mutation();

DROP TRIGGER IF EXISTS support_messages_prevent_mutation
    ON fenjiu_contract.support_messages;
CREATE TRIGGER support_messages_prevent_mutation
BEFORE UPDATE OR DELETE ON fenjiu_contract.support_messages
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_support_history_mutation();

DROP TRIGGER IF EXISTS support_intents_prevent_mutation
    ON fenjiu_contract.support_intents;
CREATE TRIGGER support_intents_prevent_mutation
BEFORE UPDATE OR DELETE ON fenjiu_contract.support_intents
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_support_history_mutation();

DROP TRIGGER IF EXISTS support_drafts_prevent_mutation
    ON fenjiu_contract.support_draft_replies;
CREATE TRIGGER support_drafts_prevent_mutation
BEFORE UPDATE OR DELETE ON fenjiu_contract.support_draft_replies
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_support_history_mutation();

DROP TRIGGER IF EXISTS support_handoffs_prevent_mutation
    ON fenjiu_contract.support_handoff_cases;
CREATE TRIGGER support_handoffs_prevent_mutation
BEFORE UPDATE OR DELETE ON fenjiu_contract.support_handoff_cases
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_support_history_mutation();

INSERT INTO fenjiu_contract.schema_migrations (version, description)
VALUES ('0003', 'support conversation message privacy and handoff contracts')
ON CONFLICT (version) DO NOTHING;

COMMIT;
