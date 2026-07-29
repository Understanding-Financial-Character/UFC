SHELL := /bin/bash

COMPOSE := docker compose -f compose.yaml -f compose.dev.yaml
COMPOSE_AI := docker compose -f compose.yaml -f compose.dev.yaml --profile ai
BACKEND_HEALTH := http://localhost:$${BACKEND_PORT:-8000}/health
BACKEND_READY := http://localhost:$${BACKEND_PORT:-8000}/ready
FRONTEND_URL := http://localhost:$${FRONTEND_PORT:-5173}

.PHONY: help init dev up down restart build ps logs logs-backend logs-frontend migrate migration-check test lint verify reset clean doctor ai-up ai-pull ai-health wait-db wait-backend wait-frontend

help:
	@printf "UFC development commands\n\n"
	@printf "  make init             Create .env if missing and generate local secrets\n"
	@printf "  make dev              Initialize, build, start, migrate, and health-check local services\n"
	@printf "  make up               Start db/backend/frontend\n"
	@printf "  make down             Stop local services\n"
	@printf "  make restart          Restart local services\n"
	@printf "  make build            Build local service images\n"
	@printf "  make ps               Show service status\n"
	@printf "  make logs             Follow all service logs\n"
	@printf "  make logs-backend     Follow backend logs\n"
	@printf "  make logs-frontend    Follow frontend logs\n"
	@printf "  make migrate          Run Alembic upgrade head\n"
	@printf "  make migration-check  Show Alembic current revision\n"
	@printf "  make test             Run backend pytest\n"
	@printf "  make lint             Run backend ruff and frontend lint\n"
	@printf "  make verify           Run config, migrations, tests, lint, frontend build, and diff checks\n"
	@printf "  make reset CONFIRM=1  Drop local DB volume, restart, and migrate\n"
	@printf "  make clean            Remove project-local build/cache artifacts only\n"
	@printf "  make doctor           Check local tool availability\n"
	@printf "  make ai-up            Start optional Ollama profile\n"
	@printf "  make ai-pull          Pull qwen3:4b into optional Ollama service\n"
	@printf "  make ai-health        Check optional Ollama service\n"

init:
	@python3 scripts/bootstrap_env.py

doctor:
	@command -v docker >/dev/null || { echo "docker not found"; exit 1; }
	@docker info >/dev/null || { echo "docker is not running or is not accessible"; exit 1; }
	@command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }
	@echo "doctor ok"

dev: init
	@echo "checking compose config"
	@$(COMPOSE) config >/dev/null
	@echo "building services"
	@$(COMPOSE) build db backend frontend
	@echo "starting services"
	@$(COMPOSE) up -d db backend frontend
	@$(MAKE) wait-db
	@$(MAKE) migrate
	@$(MAKE) wait-backend
	@$(MAKE) wait-frontend
	@$(MAKE) ps

up:
	@$(COMPOSE) up -d db backend frontend

down:
	@$(COMPOSE) down

restart: down up

build:
	@$(COMPOSE) build db backend frontend

ps:
	@$(COMPOSE) ps

logs:
	@$(COMPOSE) logs -f

logs-backend:
	@$(COMPOSE) logs -f backend

logs-frontend:
	@$(COMPOSE) logs -f frontend

migrate:
	@$(COMPOSE) exec -T backend alembic upgrade head

migration-check:
	@$(COMPOSE) exec -T backend alembic current

test:
	@$(COMPOSE) run --rm backend pytest

lint:
	@$(COMPOSE) run --rm backend ruff check app tests
	@$(COMPOSE) run --rm frontend npm run lint

verify: init
	@$(COMPOSE) config >/dev/null
	@$(COMPOSE) up -d db backend frontend
	@$(MAKE) wait-db
	@$(MAKE) migrate
	@$(MAKE) test
	@$(MAKE) lint
	@$(COMPOSE) run --rm frontend npm run build
	@git diff --check

reset:
	@if [ "$(CONFIRM)" != "1" ]; then \
		echo "This will stop containers and delete the local PostgreSQL volume."; \
		echo "Run make reset CONFIRM=1 to continue."; \
		exit 1; \
	fi
	@$(COMPOSE) down -v
	@$(COMPOSE) up -d db backend frontend
	@$(MAKE) wait-db
	@$(MAKE) migrate

clean:
	@$(COMPOSE) rm -f
	@find backend frontend -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name dist \) -prune -exec rm -rf {} +
	@rm -f frontend/tsconfig.tsbuildinfo
	@echo "clean ok"

ai-up:
	@$(COMPOSE_AI) up -d ollama

ai-pull:
	@$(COMPOSE_AI) exec -T ollama ollama pull qwen3:4b

ai-health:
	@$(COMPOSE_AI) exec -T ollama ollama list

wait-db:
	@echo "waiting for PostgreSQL"
	@for attempt in {1..30}; do \
		if $(COMPOSE) exec -T db pg_isready -U $${POSTGRES_USER:-ufc} -d $${POSTGRES_DB:-ufc} >/dev/null 2>&1; then \
			echo "PostgreSQL ready"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "PostgreSQL did not become ready"; \
	exit 1

wait-backend:
	@echo "waiting for backend"
	@for attempt in {1..30}; do \
		if curl -fsS "$(BACKEND_HEALTH)" >/dev/null && curl -fsS "$(BACKEND_READY)" >/dev/null; then \
			echo "backend ready"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "backend did not become ready"; \
	exit 1

wait-frontend:
	@echo "waiting for frontend"
	@for attempt in {1..30}; do \
		if curl -fsS "$(FRONTEND_URL)" >/dev/null; then \
			echo "frontend ready"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "frontend did not become ready"; \
	exit 1
