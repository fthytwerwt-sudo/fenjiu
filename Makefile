SHELL := /bin/sh
COMPOSE ?= docker compose
PYTHON ?= python3
COMPOSE_FILE ?= docker-compose.yml
WORKTREE_PATH := $(shell pwd -P)
COMPOSE_PROJECT_SUFFIX := $(shell printf '%s\n' "$(WORKTREE_PATH)" | cksum | awk '{print $$1}')
COMPOSE_PROJECT_NAME ?= fenjiu-local-runtime-$(COMPOSE_PROJECT_SUFFIX)
COMPOSE_CMD = COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) $(COMPOSE) -f $(COMPOSE_FILE)
MIGRATION_FILES := $(sort $(wildcard migrations/[0-9][0-9][0-9][0-9]_*.sql))

.PHONY: help bootstrap compose-config dev-up health migrate migration-test load-fixtures dev-down regression

help:
	@printf '%s\n' 'Fenjiu local-only runtime targets:'
	@printf '%s\n' '  make bootstrap      Compile stdlib-only skeleton and control plane; does not install packages or copy .env.'
	@printf '%s\n' '  make compose-config Render docker compose config with a worktree-derived project name; no pull/up.'
	@printf '%s\n' '  make dev-up         Start isolated local-only containers; no host ports, ingest, send, crawl, model call, quote, payment, order, refund, or publish.'
	@printf '%s\n' '  make health         Run container-local health probes through compose exec.'
	@printf '%s\n' '  make migrate        Apply allowlisted pure SQL migrations to the isolated local PostgreSQL container.'
	@printf '%s\n' '  make migration-test Require Docker/Compose, then replay migrations and negative constraints in an isolated disposable database.'
	@printf '%s\n' '  make load-fixtures  Safe no-op fixture probe; loads no real or synthetic rows.'
	@printf '%s\n' '  make dev-down       Stop local containers and remove named local runtime containers.'
	@printf '%s\n' '  make regression     Require Docker/Compose; run migration replay/negative constraints and all local test suites.'

bootstrap:
	$(PYTHON) -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests

compose-config:
	$(COMPOSE_CMD) config --quiet

dev-up:
	$(COMPOSE_CMD) up -d --wait

health:
	$(COMPOSE_CMD) exec -T api python -m apps.api.local_runtime --healthcheck
	$(COMPOSE_CMD) exec -T worker python -m apps.worker.local_runtime --healthcheck
	$(COMPOSE_CMD) exec -T admin python -m apps.admin.local_runtime --healthcheck

migrate:
	@test -n "$(MIGRATION_FILES)" || { printf '%s\n' 'No numbered SQL migrations found.' >&2; exit 1; }
	@set -eu; for migration in $(MIGRATION_FILES); do \
		printf 'applying %s\n' "$$migration"; \
		$(COMPOSE_CMD) exec -T postgres \
			psql -X -v ON_ERROR_STOP=1 -h 127.0.0.1 \
			-U fenjiu_local -d fenjiu_local_only \
			< "$$migration"; \
	done

migration-test:
	sh tests/migrations/run_scope_migration_regression.sh

load-fixtures:
	$(COMPOSE_CMD) exec -T worker python -m apps.worker.local_runtime --load-fixtures-noop

dev-down:
	$(COMPOSE_CMD) down

regression:
	$(MAKE) compose-config
	$(MAKE) migration-test
	$(PYTHON) -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests
	$(PYTHON) -m unittest discover -s tests/architecture
	$(PYTHON) -m unittest discover -s tests/regression
	$(PYTHON) -m unittest discover -s tests/local_runtime
	$(PYTHON) -m unittest discover -s tests/control_plane
	$(PYTHON) -m unittest discover -s tests/contracts
