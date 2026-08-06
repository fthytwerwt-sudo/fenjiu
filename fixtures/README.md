# fixtures

Synthetic-only metadata for tests.

Fixtures in this repository must never copy real source files, private people
data, secret values, media, business-gate values, or provider responses.
P01-01 allows only this README and `synthetic_metadata.json`; later explicit
contracts additionally allowlist `ingestion/synthetic_source_profiles.json`
and `ingestion/synthetic_mapping_profiles.json`. All other fixture formats
stay ignored.
