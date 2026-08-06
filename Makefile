SHELL := /bin/sh
COMPOSE ?= docker compose
PYTHON ?= python3
COMPOSE_FILE ?= docker-compose.yml
WORKTREE_PATH := $(shell pwd -P)
COMPOSE_PROJECT_SUFFIX := $(shell printf '%s\n' "$(WORKTREE_PATH)" | cksum | awk '{print $$1}')
COMPOSE_PROJECT_NAME ?= fenjiu-local-runtime-$(COMPOSE_PROJECT_SUFFIX)
COMPOSE_CMD = COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) $(COMPOSE) -f $(COMPOSE_FILE)

.PHONY: help bootstrap compose-config dev-up health migrate load-fixtures dev-down regression

help:
	@printf '%s\n' 'Fenjiu local-only runtime targets:'
	@printf '%s\n' '  make bootstrap      Compile stdlib-only skeleton; does not install packages or copy .env.'
	@printf '%s\n' '  make compose-config Render docker compose config with a worktree-derived project name; no pull/up.'
	@printf '%s\n' '  make dev-up         Start isolated local-only containers; no host ports, ingest, send, crawl, model call, quote, payment, order, refund, or publish.'
	@printf '%s\n' '  make health         Run container-local health probes through compose exec.'
	@printf '%s\n' '  make migrate        Safe no-op migration probe; writes no data.'
	@printf '%s\n' '  make load-fixtures  Safe no-op fixture probe; loads no real or synthetic rows.'
	@printf '%s\n' '  make dev-down       Stop local containers and remove named local runtime containers.'
	@printf '%s\n' '  make regression     Render compose config, then run compileall, architecture tests, regression tests, and local runtime tests.'

bootstrap:
	$(PYTHON) -m compileall -q apps core modules adapters workflows tests

compose-config:
	$(COMPOSE_CMD) config --quiet

dev-up:
	$(COMPOSE_CMD) up -d --wait

health:
	$(COMPOSE_CMD) exec -T api python -m apps.api.local_runtime --healthcheck
	$(COMPOSE_CMD) exec -T worker python -m apps.worker.local_runtime --healthcheck
	$(COMPOSE_CMD) exec -T admin python -m apps.admin.local_runtime --healthcheck

migrate:
	$(COMPOSE_CMD) exec -T worker python -m apps.worker.local_runtime --migrate-noop

load-fixtures:
	$(COMPOSE_CMD) exec -T worker python -m apps.worker.local_runtime --load-fixtures-noop

dev-down:
	$(COMPOSE_CMD) down

regression:
	$(MAKE) compose-config
	$(PYTHON) -m compileall -q apps core modules adapters workflows tests
	$(PYTHON) -m unittest discover -s tests/architecture
	$(PYTHON) -m unittest discover -s tests/regression
	$(PYTHON) -m unittest discover -s tests/local_runtime
