# ingestion

P03-01 owns stdlib/local-only contracts for synthetic source registration,
hash/idempotency, quarantine, field locators, failure retention, and staging
candidates. Input bytes are ephemeral and only their SHA-256 is retained.

The module does not parse real XLSX/CSV/DOCX/PDF/images, read folders, call OCR,
write approved truth, authenticate actors, connect to production, or enable any
external action. Fake extraction ports live behind the module-owned port
contract and consume only value-free synthetic descriptors.
