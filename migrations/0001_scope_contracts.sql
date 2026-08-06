BEGIN;

CREATE SCHEMA IF NOT EXISTS fenjiu_contract;

CREATE TABLE IF NOT EXISTS fenjiu_contract.schema_migrations (
    version text PRIMARY KEY,
    description text NOT NULL CHECK (btrim(description) <> ''),
    applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $$
BEGIN
    CREATE TYPE fenjiu_contract.data_state AS ENUM (
        'fixture', 'mock', 'staging', 'approved', 'expired',
        'blocked', 'conflict', 'superseded'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE fenjiu_contract.sensitivity AS ENUM (
        'internal', 'confidential', 'restricted', 'personal'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

CREATE TABLE IF NOT EXISTS fenjiu_contract.tenants (
    id uuid PRIMARY KEY,
    slug text NOT NULL UNIQUE CHECK (slug ~ '^[a-z][a-z0-9_]{0,63}$'),
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT tenants_external_execution_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT tenants_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT tenants_scope_key UNIQUE (id, is_synthetic)
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.projects (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    slug text NOT NULL CHECK (slug ~ '^[a-z][a-z0-9_]{0,63}$'),
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT projects_external_execution_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT projects_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT projects_tenant_slug_unique UNIQUE (tenant_id, slug),
    CONSTRAINT projects_scope_key UNIQUE (tenant_id, id, is_synthetic),
    CONSTRAINT projects_tenant_scope_fk FOREIGN KEY (tenant_id, is_synthetic)
        REFERENCES fenjiu_contract.tenants (id, is_synthetic)
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.business_lines (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    slug text NOT NULL CHECK (slug ~ '^[a-z][a-z0-9_]{0,63}$'),
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT business_lines_external_execution_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT business_lines_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT business_lines_scope_slug_unique UNIQUE (tenant_id, project_id, slug),
    CONSTRAINT business_lines_scope_key UNIQUE (tenant_id, project_id, id, is_synthetic),
    CONSTRAINT business_lines_project_scope_fk FOREIGN KEY (tenant_id, project_id, is_synthetic)
        REFERENCES fenjiu_contract.projects (tenant_id, id, is_synthetic)
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.source_refs (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    source_kind text NOT NULL CHECK (source_kind ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    source_version text NOT NULL CHECK (source_version ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    data_state fenjiu_contract.data_state NOT NULL,
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT source_refs_external_execution_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT source_refs_synthetic_state CHECK (
        (is_synthetic AND data_state IN ('fixture', 'mock')) OR
        (NOT is_synthetic AND data_state NOT IN ('fixture', 'mock'))
    ),
    CONSTRAINT source_refs_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT source_refs_scope_key UNIQUE (
        tenant_id, project_id, business_line_id, id, is_synthetic
    ),
    CONSTRAINT source_refs_business_line_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, is_synthetic
    ) REFERENCES fenjiu_contract.business_lines (
        tenant_id, project_id, id, is_synthetic
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.data_versions (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
    source_ref_id uuid NOT NULL,
    version_no integer NOT NULL CHECK (version_no > 0),
    data_state fenjiu_contract.data_state NOT NULL,
    sensitivity fenjiu_contract.sensitivity NOT NULL,
    is_synthetic boolean NOT NULL,
    external_execution_allowed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    correlation_id text NOT NULL CHECK (correlation_id ~ '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$'),
    CONSTRAINT data_versions_external_execution_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT data_versions_synthetic_state CHECK (
        (is_synthetic AND data_state IN ('fixture', 'mock')) OR
        (NOT is_synthetic AND data_state NOT IN ('fixture', 'mock'))
    ),
    CONSTRAINT data_versions_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT data_versions_source_version_unique UNIQUE (
        tenant_id, project_id, business_line_id, source_ref_id, version_no
    ),
    CONSTRAINT data_versions_scope_key UNIQUE (
        tenant_id, project_id, business_line_id, source_ref_id, id, is_synthetic
    ),
    CONSTRAINT data_versions_source_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id, is_synthetic
    ) REFERENCES fenjiu_contract.source_refs (
        tenant_id, project_id, business_line_id, id, is_synthetic
    )
);

CREATE TABLE IF NOT EXISTS fenjiu_contract.entity_metadata (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    business_line_id uuid NOT NULL,
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
    CONSTRAINT entity_metadata_external_execution_disabled CHECK (external_execution_allowed = false),
    CONSTRAINT entity_metadata_synthetic_state CHECK (
        (is_synthetic AND data_state IN ('fixture', 'mock')) OR
        (NOT is_synthetic AND data_state NOT IN ('fixture', 'mock'))
    ),
    CONSTRAINT entity_metadata_timestamp_order CHECK (updated_at >= created_at),
    CONSTRAINT entity_metadata_scope_key UNIQUE (tenant_id, project_id, business_line_id, id),
    CONSTRAINT entity_metadata_source_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id, is_synthetic
    ) REFERENCES fenjiu_contract.source_refs (
        tenant_id, project_id, business_line_id, id, is_synthetic
    ),
    CONSTRAINT entity_metadata_version_scope_fk FOREIGN KEY (
        tenant_id, project_id, business_line_id, source_ref_id,
        data_version_id, is_synthetic
    ) REFERENCES fenjiu_contract.data_versions (
        tenant_id, project_id, business_line_id, source_ref_id,
        id, is_synthetic
    )
);

INSERT INTO fenjiu_contract.schema_migrations (version, description)
VALUES ('0001', 'scope contracts and mandatory metadata constraints')
ON CONFLICT (version) DO NOTHING;

COMMIT;
