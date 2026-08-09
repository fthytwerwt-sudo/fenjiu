BEGIN;

DO $$
BEGIN
    CREATE TYPE fenjiu_contract.crm_review_decision AS ENUM (
        'approved', 'rejected', 'merge_candidate'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE fenjiu_contract.crm_dedupe_result AS ENUM (
        'new', 'duplicate', 'merge_candidate'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE fenjiu_contract.crm_stage AS ENUM (
        'reviewed', 'manual_review', 'closed_blocked'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE fenjiu_contract.crm_interaction_kind AS ENUM (
        'internal_note', 'draft', 'send_attempt'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE fenjiu_contract.crm_retention_intent AS ENUM (
        'delete_requested', 'anonymize_requested', 'retain_minimized'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

CREATE TABLE IF NOT EXISTS fenjiu_contract.lead_candidates (
    lead_ref text PRIMARY KEY
        CHECK (lead_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    source_policy_id text NOT NULL
        CHECK (source_policy_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    snapshot_ref text NOT NULL
        CHECK (snapshot_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    source_url_hash text NOT NULL CHECK (source_url_hash ~ '^[0-9a-f]{64}$'),
    organization_fingerprint text NOT NULL CHECK (organization_fingerprint ~ '^[0-9a-f]{64}$'),
    field_fingerprint_hash text NOT NULL CHECK (field_fingerprint_hash ~ '^[0-9a-f]{64}$'),
    data_state fenjiu_contract.data_state NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    business_external_ready boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    created_by text NOT NULL
        CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL
        CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT lead_candidates_fixture_only CHECK (
        data_state = 'fixture' AND is_synthetic = true
    ),
    CONSTRAINT lead_candidates_external_disabled CHECK (
        external_execution_allowed = false AND business_external_ready = false
    ),
    CONSTRAINT lead_candidates_scope_key UNIQUE (
        tenant_id, project_id, business_line_id, lead_ref
    ),
    CONSTRAINT lead_candidates_source_fingerprint_unique UNIQUE (
        tenant_id, project_id, business_line_id, source_policy_id,
        source_url_hash, organization_fingerprint, field_fingerprint_hash
    ),
    CONSTRAINT lead_candidates_business_line_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, is_synthetic
    ) REFERENCES fenjiu_contract.business_lines (
        tenant_id, project_id, id, is_synthetic
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.lead_reviews (
    review_ref text PRIMARY KEY
        CHECK (review_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    lead_ref text NOT NULL
        CHECK (lead_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    decision fenjiu_contract.crm_review_decision NOT NULL,
    review_evidence_ref text NOT NULL
        CHECK (review_evidence_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    reviewer_ref text NOT NULL
        CHECK (reviewer_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    dedupe_result fenjiu_contract.crm_dedupe_result NOT NULL,
    created_at timestamptz NOT NULL,
    correlation_id text NOT NULL
        CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT lead_reviews_scope_key UNIQUE (
        tenant_id, project_id, business_line_id, review_ref
    ),
    CONSTRAINT lead_reviews_candidate_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, lead_ref
    ) REFERENCES fenjiu_contract.lead_candidates (
        tenant_id, project_id, business_line_id, lead_ref
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.organizations (
    organization_ref text PRIMARY KEY
        CHECK (organization_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    review_ref text NOT NULL
        CHECK (review_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    organization_fingerprint text NOT NULL CHECK (organization_fingerprint ~ '^[0-9a-f]{64}$'),
    source_policy_id text NOT NULL
        CHECK (source_policy_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    source_url_hash text NOT NULL CHECK (source_url_hash ~ '^[0-9a-f]{64}$'),
    dnc_subject_hash text NOT NULL CHECK (dnc_subject_hash ~ '^[0-9a-f]{64}$'),
    data_state fenjiu_contract.data_state NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    business_external_ready boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    created_by text NOT NULL
        CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL
        CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT organizations_fixture_only CHECK (
        data_state = 'fixture' AND is_synthetic = true
    ),
    CONSTRAINT organizations_external_disabled CHECK (
        external_execution_allowed = false AND business_external_ready = false
    ),
    CONSTRAINT organizations_scope_key UNIQUE (
        tenant_id, project_id, business_line_id, organization_ref
    ),
    CONSTRAINT organizations_review_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, review_ref
    ) REFERENCES fenjiu_contract.lead_reviews (
        tenant_id, project_id, business_line_id, review_ref
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.contacts (
    contact_ref text PRIMARY KEY
        CHECK (contact_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    organization_ref text NOT NULL
        CHECK (organization_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    subject_hash text NOT NULL CHECK (subject_hash ~ '^[0-9a-f]{64}$'),
    source_evidence_ref text NOT NULL
        CHECK (source_evidence_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    consent_granted boolean NOT NULL,
    dnc_blocked boolean NOT NULL,
    data_state fenjiu_contract.data_state NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    business_external_ready boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    created_by text NOT NULL
        CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL
        CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT contacts_source_consent_required CHECK (
        consent_granted = true AND dnc_blocked = false
    ),
    CONSTRAINT contacts_fixture_only CHECK (
        data_state = 'fixture' AND is_synthetic = true
    ),
    CONSTRAINT contacts_external_disabled CHECK (
        external_execution_allowed = false AND business_external_ready = false
    ),
    CONSTRAINT contacts_organization_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, organization_ref
    ) REFERENCES fenjiu_contract.organizations (
        tenant_id, project_id, business_line_id, organization_ref
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.dnc_records (
    dnc_ref text PRIMARY KEY
        CHECK (dnc_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    subject_hash text NOT NULL CHECK (subject_hash ~ '^[0-9a-f]{64}$'),
    evidence_ref text NOT NULL
        CHECK (evidence_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    actor_ref text NOT NULL
        CHECK (actor_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    reason_code text NOT NULL
        CHECK (reason_code ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    created_at timestamptz NOT NULL,
    correlation_id text NOT NULL
        CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT dnc_records_subject_unique UNIQUE (
        tenant_id, project_id, business_line_id, subject_hash
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.opportunities (
    opportunity_ref text PRIMARY KEY
        CHECK (opportunity_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    organization_ref text NOT NULL
        CHECK (organization_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    stage fenjiu_contract.crm_stage NOT NULL,
    amount_state text NOT NULL
        CHECK (amount_state ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    external_execution_allowed boolean NOT NULL DEFAULT false,
    business_external_ready boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    created_by text NOT NULL
        CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL
        CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT opportunities_external_disabled CHECK (
        external_execution_allowed = false AND business_external_ready = false
    ),
    CONSTRAINT opportunities_organization_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, organization_ref
    ) REFERENCES fenjiu_contract.organizations (
        tenant_id, project_id, business_line_id, organization_ref
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.interactions (
    interaction_ref text PRIMARY KEY
        CHECK (interaction_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    organization_ref text NOT NULL
        CHECK (organization_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    kind fenjiu_contract.crm_interaction_kind NOT NULL,
    subject_hash text NOT NULL CHECK (subject_hash ~ '^[0-9a-f]{64}$'),
    sent_count integer NOT NULL,
    external_sent boolean NOT NULL,
    data_state fenjiu_contract.data_state NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    business_external_ready boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    created_by text NOT NULL
        CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL
        CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT interactions_no_send CHECK (
        kind <> 'send_attempt' AND sent_count = 0 AND external_sent = false
    ),
    CONSTRAINT interactions_fixture_only CHECK (
        data_state = 'fixture' AND is_synthetic = true
    ),
    CONSTRAINT interactions_external_disabled CHECK (
        external_execution_allowed = false AND business_external_ready = false
    ),
    CONSTRAINT interactions_organization_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, organization_ref
    ) REFERENCES fenjiu_contract.organizations (
        tenant_id, project_id, business_line_id, organization_ref
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.retention_intents (
    retention_ref text PRIMARY KEY
        CHECK (retention_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    subject_ref text NOT NULL
        CHECK (subject_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    intent fenjiu_contract.crm_retention_intent NOT NULL,
    evidence_ref text NOT NULL
        CHECK (evidence_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    actor_ref text NOT NULL
        CHECK (actor_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    created_at timestamptz NOT NULL,
    correlation_id text NOT NULL
        CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$')
);

CREATE OR REPLACE FUNCTION fenjiu_contract.validate_crm_organization_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    review_record fenjiu_contract.lead_reviews%ROWTYPE;
BEGIN
    SELECT * INTO review_record
    FROM fenjiu_contract.lead_reviews
    WHERE tenant_id = NEW.tenant_id
      AND project_id = NEW.project_id
      AND business_line_id = NEW.business_line_id
      AND review_ref = NEW.review_ref;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'lead review scope mismatch';
    END IF;
    IF review_record.decision <> 'approved' OR review_record.dedupe_result <> 'new' THEN
        RAISE EXCEPTION 'lead review required before crm';
    END IF;
    RETURN NEW;
END
$$;

CREATE OR REPLACE FUNCTION fenjiu_contract.prevent_contact_when_dnc()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM fenjiu_contract.dnc_records
        WHERE tenant_id = NEW.tenant_id
          AND project_id = NEW.project_id
          AND business_line_id = NEW.business_line_id
          AND subject_hash = NEW.subject_hash
    ) THEN
        RAISE EXCEPTION 'dnc blocked';
    END IF;
    RETURN NEW;
END
$$;

CREATE OR REPLACE FUNCTION fenjiu_contract.prevent_draft_when_dnc()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.kind = 'draft' AND EXISTS (
        SELECT 1
        FROM fenjiu_contract.dnc_records
        WHERE tenant_id = NEW.tenant_id
          AND project_id = NEW.project_id
          AND business_line_id = NEW.business_line_id
          AND subject_hash = NEW.subject_hash
    ) THEN
        RAISE EXCEPTION 'dnc blocked';
    END IF;
    RETURN NEW;
END
$$;

CREATE OR REPLACE FUNCTION fenjiu_contract.prevent_crm_immutable_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'crm immutable record cannot be changed';
END
$$;

DROP TRIGGER IF EXISTS organizations_validate_insert
    ON fenjiu_contract.organizations;
CREATE TRIGGER organizations_validate_insert
BEFORE INSERT ON fenjiu_contract.organizations
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.validate_crm_organization_insert();

DROP TRIGGER IF EXISTS contacts_prevent_dnc
    ON fenjiu_contract.contacts;
CREATE TRIGGER contacts_prevent_dnc
BEFORE INSERT ON fenjiu_contract.contacts
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_contact_when_dnc();

DROP TRIGGER IF EXISTS interactions_prevent_dnc
    ON fenjiu_contract.interactions;
CREATE TRIGGER interactions_prevent_dnc
BEFORE INSERT ON fenjiu_contract.interactions
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_draft_when_dnc();

DROP TRIGGER IF EXISTS dnc_records_prevent_mutation
    ON fenjiu_contract.dnc_records;
CREATE TRIGGER dnc_records_prevent_mutation
BEFORE UPDATE OR DELETE ON fenjiu_contract.dnc_records
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_crm_immutable_update();

DROP TRIGGER IF EXISTS retention_intents_prevent_mutation
    ON fenjiu_contract.retention_intents;
CREATE TRIGGER retention_intents_prevent_mutation
BEFORE UPDATE OR DELETE ON fenjiu_contract.retention_intents
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_crm_immutable_update();

INSERT INTO fenjiu_contract.schema_migrations (version, description)
VALUES ('0003', 'synthetic leads crm dnc retention and scoped export contracts')
ON CONFLICT (version) DO NOTHING;

COMMIT;
