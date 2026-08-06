# apps

Delivery entrypoints for the modular monolith.

Phase 1 keeps these packages importable only. They may depend on
`core.application` and `core.contracts`, but they must not call provider SDKs or
perform external actions.
