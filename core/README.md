# core

Inner application, domain, contract, and security packages.

`core.domain` and `modules` are the protected inner layers. They may import
stable contracts, but they must not import `apps`, `adapters`, `workflows`, SDKs,
network clients, database clients, or environment-variable readers.
