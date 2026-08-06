# migrations

P02-01 provides replay-safe pure SQL schema migrations for the isolated local
PostgreSQL service. Migrations contain schema metadata and constraints only:
no tenant rows, SKU, price, inventory, credentials, or real data.

`make migrate` streams numbered SQL files to `psql` inside the pinned local
PostgreSQL container. It does not read `.env`, accept a database URL, or expose
a production/external connection surface. RLS, encryption, retention policy,
and real business scopes remain deferred.
