# customer_service

Owns future conversation, draft, risk, and handoff contracts.

P06-01 adds local-only synthetic contracts for inbound conversation records,
message replay idempotency, intent classification references, draft-only reply
references, privacy minimization, scoped human handoff cases, and separate
unknown-scope quarantine records.

It still does not integrate WhatsApp, TikTok, Meta, email, webhooks, channel
adapters, production storage, or outbound delivery. Records keep hashes and
opaque references instead of raw chat bodies or attachments.
