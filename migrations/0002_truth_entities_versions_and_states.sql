BEGIN;

DO $$
BEGIN
    CREATE TYPE fenjiu_contract.truth_entity_kind AS ENUM (
        'product', 'sku', 'price', 'inventory', 'delivery_rule',
        'compliance_document', 'content_asset', 'approved_fact',
        'forbidden_expression'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

CREATE UNIQUE INDEX IF NOT EXISTS data_versions_truth_lineage_key
    ON fenjiu_contract.data_versions (
        tenant_id, project_id, business_line_id, source_ref_id, id,
        is_synthetic, data_state
    );

CREATE TABLE IF NOT EXISTS fenjiu_contract.truth_versions (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    entity_kind fenjiu_contract.truth_entity_kind NOT NULL,
    subject_ref text NOT NULL
        CHECK (subject_ref ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    version_no integer NOT NULL CHECK (version_no > 0),
    parent_version_id uuid,
    data_state fenjiu_contract.data_state NOT NULL,
    source_ref_id uuid NOT NULL,
    data_version_id uuid NOT NULL,
    payload_hash text NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    diff_hash text NOT NULL CHECK (diff_hash ~ '^[0-9a-f]{64}$'),
    changed_fields text[] NOT NULL CHECK (cardinality(changed_fields) > 0),
    effective_from timestamptz,
    effective_until timestamptz,
    approval_evidence_id uuid,
    approval_actor_ref text,
    approval_decision_ref text,
    approval_evidence_ref text,
    approval_policy_version text,
    approved_at timestamptz,
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL
        CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL
        CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT truth_versions_external_execution_disabled
        CHECK (external_execution_allowed = false),
    CONSTRAINT truth_versions_synthetic_state CHECK (
        (is_synthetic AND data_state IN ('fixture', 'mock')) OR
        (NOT is_synthetic AND data_state NOT IN ('fixture', 'mock'))
    ),
    CONSTRAINT truth_versions_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT truth_versions_effective_window CHECK (
        effective_until IS NULL OR
        (effective_from IS NOT NULL AND effective_until > effective_from)
    ),
    CONSTRAINT truth_versions_expired_window CHECK (
        data_state <> 'expired' OR effective_until IS NOT NULL
    ),
    CONSTRAINT truth_versions_approval_fields_atomic CHECK (
        (
            approval_evidence_id IS NULL AND approval_actor_ref IS NULL AND
            approval_decision_ref IS NULL AND approval_evidence_ref IS NULL AND
            approval_policy_version IS NULL AND approved_at IS NULL
        ) OR (
            approval_evidence_id IS NOT NULL AND approval_actor_ref IS NOT NULL AND
            approval_decision_ref IS NOT NULL AND approval_evidence_ref IS NOT NULL AND
            approval_policy_version IS NOT NULL AND approved_at IS NOT NULL
        )
    ),
    CONSTRAINT truth_versions_approved_evidence_required CHECK (
        data_state <> 'approved' OR (
            approval_evidence_id IS NOT NULL AND effective_from IS NOT NULL AND
            parent_version_id IS NOT NULL AND NOT is_synthetic
        )
    ),
    CONSTRAINT truth_versions_unapproved_has_no_approval CHECK (
        data_state NOT IN ('fixture', 'mock', 'staging') OR
        approval_evidence_id IS NULL
    ),
    CONSTRAINT truth_versions_initial_root_shape CHECK (
        (version_no = 1 AND parent_version_id IS NULL AND (
            (is_synthetic AND data_state IN ('fixture', 'mock')) OR
            (NOT is_synthetic AND data_state = 'staging')
        )) OR
        (version_no > 1 AND parent_version_id IS NOT NULL)
    ),
    CONSTRAINT truth_versions_scope_version_unique UNIQUE (
        tenant_id, project_id, business_line_id, entity_kind,
        subject_ref, version_no
    ),
    CONSTRAINT truth_versions_parent_single_child UNIQUE (parent_version_id),
    CONSTRAINT truth_versions_scope_key UNIQUE (
        tenant_id, project_id, business_line_id, entity_kind,
        subject_ref, id, is_synthetic
    ),
    CONSTRAINT truth_versions_parent_key UNIQUE (
        tenant_id, project_id, business_line_id, entity_kind,
        subject_ref, data_version_id, is_synthetic
    ),
    CONSTRAINT truth_versions_source_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id,
        is_synthetic
    ) REFERENCES fenjiu_contract.source_refs (
        tenant_id, project_id, business_line_id, id,
        is_synthetic
    ),
    CONSTRAINT truth_versions_data_version_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id,
        data_version_id, is_synthetic, data_state
    ) REFERENCES fenjiu_contract.data_versions (
        tenant_id, project_id, business_line_id, source_ref_id,
        id, is_synthetic, data_state
    ),
    CONSTRAINT truth_versions_parent_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, entity_kind,
        subject_ref, parent_version_id, is_synthetic
    ) REFERENCES fenjiu_contract.truth_versions (
        tenant_id, project_id, business_line_id, entity_kind,
        subject_ref, data_version_id, is_synthetic
    )
);

CREATE OR REPLACE FUNCTION fenjiu_contract.validate_truth_version_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    parent_record fenjiu_contract.truth_versions%ROWTYPE;
BEGIN
    IF NEW.parent_version_id IS NULL THEN
        IF NEW.version_no <> 1 OR NOT (
            (NEW.is_synthetic AND NEW.data_state IN ('fixture', 'mock')) OR
            (NOT NEW.is_synthetic AND NEW.data_state = 'staging')
        ) THEN
            RAISE EXCEPTION 'invalid initial truth state';
        END IF;
        RETURN NEW;
    END IF;

    SELECT * INTO parent_record
    FROM fenjiu_contract.truth_versions
    WHERE data_version_id = NEW.parent_version_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'truth parent version not found';
    END IF;
    IF parent_record.tenant_id <> NEW.tenant_id OR
       parent_record.project_id <> NEW.project_id OR
       parent_record.business_line_id <> NEW.business_line_id OR
       parent_record.entity_kind <> NEW.entity_kind OR
       parent_record.subject_ref <> NEW.subject_ref OR
       parent_record.is_synthetic <> NEW.is_synthetic THEN
        RAISE EXCEPTION 'truth parent scope mismatch';
    END IF;
    IF NEW.version_no <> parent_record.version_no + 1 THEN
        RAISE EXCEPTION 'truth version sequence invalid';
    END IF;
    IF NOT (
        (parent_record.data_state = 'staging' AND NEW.data_state IN (
            'approved', 'blocked', 'conflict', 'superseded'
        )) OR
        (parent_record.data_state = 'approved' AND NEW.data_state IN (
            'expired', 'blocked', 'conflict', 'superseded'
        )) OR
        (parent_record.data_state = 'expired' AND NEW.data_state = 'staging') OR
        (parent_record.data_state = 'blocked' AND NEW.data_state = 'staging') OR
        (parent_record.data_state = 'conflict' AND NEW.data_state IN (
            'staging', 'approved'
        )) OR
        (parent_record.data_state = 'superseded' AND NEW.data_state = 'staging')
    ) THEN
        RAISE EXCEPTION 'truth state transition forbidden';
    END IF;
    RETURN NEW;
END
$$;

CREATE OR REPLACE FUNCTION fenjiu_contract.prevent_truth_history_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'truth history is append only';
END
$$;

DROP TRIGGER IF EXISTS truth_versions_validate_insert
    ON fenjiu_contract.truth_versions;
CREATE TRIGGER truth_versions_validate_insert
BEFORE INSERT ON fenjiu_contract.truth_versions
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.validate_truth_version_insert();

DROP TRIGGER IF EXISTS truth_versions_prevent_mutation
    ON fenjiu_contract.truth_versions;
CREATE TRIGGER truth_versions_prevent_mutation
BEFORE UPDATE OR DELETE ON fenjiu_contract.truth_versions
FOR EACH ROW EXECUTE FUNCTION fenjiu_contract.prevent_truth_history_mutation();

CREATE OR REPLACE VIEW fenjiu_contract.current_approved_truth AS
SELECT current_version.*
FROM fenjiu_contract.truth_versions AS current_version
WHERE current_version.data_state = 'approved'
  AND current_version.approval_evidence_id IS NOT NULL
  AND current_version.effective_from <= CURRENT_TIMESTAMP
  AND (
      current_version.effective_until IS NULL OR
      CURRENT_TIMESTAMP < current_version.effective_until
  )
  AND NOT EXISTS (
      SELECT 1
      FROM fenjiu_contract.truth_versions AS child_version
      WHERE child_version.parent_version_id = current_version.data_version_id
  );

INSERT INTO fenjiu_contract.schema_migrations (version, description)
VALUES ('0002', 'truth entities immutable versions states and guarded current view')
ON CONFLICT (version) DO NOTHING;

COMMIT;
