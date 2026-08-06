SHELL := /bin/sh
COMPOSE ?= docker compose
PYTHON ?= python3
COMPOSE_FILE ?= docker-compose.yml

.PHONY: help bootstrap compose-config dev-up health migrate load-fixtures dev-down regression

help:
	@printf '%s\n' 'Fenjiu local-only runtime targets:'
	@printf '%s\n' '  make bootstrap      Compile stdlib-only skeleton; does not install packages or copy .env.'
	@printf '%s\n' '  make compose-config Render docker compose config; no pull/up.'
	@printf '%s\n' '  make dev-up         Start local-only containers; no host ports, ingest, send, crawl, model call, quote, payment, order, refund, or publish.'
	@printf '%s\n' '  make health         Run container-local health probes through compose exec.'
	@printf '%s\n' '  make migrate        Safe no-op migration probe; writes no data.'
	@printf '%s\n' '  make load-fixtures  Safe no-op fixture probe; loads no real or synthetic rows.'
	@printf '%s\n' '  make dev-down       Stop local containers and remove named local runtime containers.'
	@printf '%s\n' '  make regression     Run compileall, architecture tests, regression tests, and local runtime tests.'

bootstrap:
	$(PYTHON) -m compileall -q apps core modules adapters workflows tests

compose-config:
	$(COMPOSE) -f $(COMPOSE_FILE) config --quiet

dev-up:
	$(COMPOSE) -f $(COMPOSE_FILE) up -d --wait

health:
	$(COMPOSE) -f $(COMPOSE_FILE) exec -T api python -m apps.api.local_runtime --healthcheck --url http://127.0.0.1:8000/health
	$(COMPOSE) -f $(COMPOSE_FILE) exec -T worker python -m apps.worker.local_runtime --healthcheck
	$(COMPOSE) -f $(COMPOSE_FILE) exec -T admin python -m apps.admin.local_runtime --healthcheck --url http://127.0.0.1:8001/health

migrate:
	$(COMPOSE) -f $(COMPOSE_FILE) exec -T worker python -m apps.worker.local_runtime --migrate-noop

load-fixtures:
	$(COMPOSE) -f $(COMPOSE_FILE) exec -T worker python -m apps.worker.local_runtime --load-fixtures-noop

dev-down:
	$(COMPOSE) -f $(COMPOSE_FILE) down

regression:
	$(PYTHON) -m compileall -q apps core modules adapters workflows tests
	$(PYTHON) -m unittest discover -s tests/architecture
	$(PYTHON) -m unittest discover -s tests/regression
	$(PYTHON) -m unittest discover -s tests/local_runtime
