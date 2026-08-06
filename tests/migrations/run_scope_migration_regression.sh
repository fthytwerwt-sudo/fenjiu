#!/bin/sh
set -eu

cd "$(dirname "$0")/../.."

WORKTREE_PATH=$(pwd -P)
COMPOSE_PROJECT_SUFFIX=$(printf '%s\n' "$WORKTREE_PATH" | cksum | awk '{print $1}')
COMPOSE_PROJECT_NAME="fenjiu-local-runtime-$COMPOSE_PROJECT_SUFFIX"

fail() {
    printf 'migration regression failed: %s\n' "$1" >&2
    exit 1
}

compose() {
    COMPOSE_PROJECT_NAME="$COMPOSE_PROJECT_NAME" docker compose -f docker-compose.yml "$@"
}

cleanup() {
    compose down -v --remove-orphans >/dev/null 2>&1 || true
}

command -v docker >/dev/null 2>&1 || fail "docker command unavailable"
docker compose version >/dev/null 2>&1 || fail "docker compose unavailable"
docker info >/dev/null 2>&1 || fail "docker daemon unavailable"

trap cleanup EXIT HUP INT TERM
cleanup
compose up -d --wait postgres
sh tests/migrations/test_scope_migrations.sh
cleanup
trap - EXIT HUP INT TERM

printf 'P02-01 isolated migration regression passed and cleaned up.\n'
