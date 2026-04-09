.DEFAULT_GOAL := help

ENV ?= development

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD  := \033[1m
CYAN  := \033[0;36m
GREEN := \033[0;32m
NC    := \033[0m

.PHONY: help
help:
	@echo ""
	@echo "$(BOLD)$(CYAN)Hermes — available targets$(NC)"
	@echo ""
	@echo "$(BOLD)Dev$(NC)"
	@echo "  up              Start all services (development)"
	@echo "  down            Stop all services"
	@echo "  restart         Down + up"
	@echo "  logs            Follow logs for all services"
	@echo "  logs-backend    Follow backend logs only"
	@echo "  ps              Show running containers"
	@echo "  shell           Open a shell in the backend container"
	@echo ""
	@echo "$(BOLD)Build$(NC)"
	@echo "  build           Build all images (no cache)"
	@echo "  build-backend   Build backend image only"
	@echo "  build-frontend  Build frontend image only"
	@echo "  build-admin     Build frontend-admin image only"
	@echo ""
	@echo "$(BOLD)Database$(NC)"
	@echo "  migrate         Run alembic upgrade head"
	@echo "  migrate-down    Downgrade one revision"
	@echo "  migrate-history Show migration history"
	@echo "  seed            Copy + run seed_jobs.py inside backend container"
	@echo "  seed-creds      Copy + run seed_creds.py inside backend container"
	@echo "  backup          Dump the database to backups/"
	@echo "  restore         Restore latest dump (LATEST=path/to/file.dump)"
	@echo ""
	@echo "$(BOLD)Tests$(NC)"
	@echo "  test            Run backend unit + integration tests"
	@echo "  test-frontend   Run user frontend tests"
	@echo "  test-admin      Run admin frontend tests"
	@echo "  test-e2e        Run E2E tests (starts full test stack)"
	@echo "  test-all        Run test + test-frontend + test-admin sequentially"
	@echo ""
	@echo "$(BOLD)Config$(NC)"
	@echo "  check-config    Validate all env files (ENV=development|staging|production|all)"
	@echo ""
	@echo "$(BOLD)Cleanup$(NC)"
	@echo "  clean           Down + remove volumes"
	@echo "  clean-test      Tear down test stack + remove volumes"
	@echo "  prune           Remove dangling Docker images"
	@echo ""

# ── Dev ───────────────────────────────────────────────────────────────────────

.PHONY: up
up:
	docker compose up -d --build

.PHONY: down
down:
	docker compose down

.PHONY: restart
restart: down up

.PHONY: logs
logs:
	docker compose logs -f

.PHONY: logs-backend
logs-backend:
	docker compose logs -f backend

.PHONY: ps
ps:
	docker compose ps

.PHONY: shell
shell:
	docker exec -it hermes_backend bash

# ── Build ─────────────────────────────────────────────────────────────────────

.PHONY: build
build:
	docker compose build --no-cache

.PHONY: build-backend
build-backend:
	docker compose build --no-cache backend

.PHONY: build-frontend
build-frontend:
	docker compose build --no-cache frontend

.PHONY: build-admin
build-admin:
	docker compose build --no-cache frontend-admin

# ── Database ──────────────────────────────────────────────────────────────────

.PHONY: migrate
migrate:
	docker exec hermes_backend alembic -c /app/alembic.ini upgrade head

.PHONY: migrate-down
migrate-down:
	docker exec hermes_backend alembic -c /app/alembic.ini downgrade -1

.PHONY: migrate-history
migrate-history:
	docker exec hermes_backend alembic -c /app/alembic.ini history --verbose

.PHONY: seed
seed:
	docker cp scripts/seed_jobs.py hermes_backend:/app/seed_jobs.py
	docker exec hermes_backend python seed_jobs.py

.PHONY: seed-creds
seed-creds:
	docker cp scripts/seed_creds.py hermes_backend:/app/seed_creds.py
	docker exec hermes_backend python seed_creds.py

# ── Tests ─────────────────────────────────────────────────────────────────────

.PHONY: test
test:
	docker compose -f docker-compose.test.yml up -d --build --wait postgresql redis pgbouncer backend
	docker exec test_backend alembic -c /app/alembic.ini upgrade head
	docker exec test_backend python -m pytest tests/unit/ tests/integration/ \
		--cov=app \
		--cov-report=xml:/app/coverage.xml \
		--cov-report=term-missing \
		-q
	docker cp test_backend:/app/coverage.xml coverage.xml
	$(MAKE) clean-test

.PHONY: test-frontend
test-frontend:
	docker build -t hermes_frontend_ci src/frontend
	mkdir -p src/frontend/coverage
	chmod 777 src/frontend/coverage
	docker run --rm \
		--env-file config/test/.env.frontend \
		-v $(PWD)/src/frontend/coverage:/app/coverage \
		hermes_frontend_ci \
		python -m pytest tests/ \
			--cov=app \
			--cov-report=xml:/app/coverage/coverage.xml \
			--cov-report=term-missing \
			-q

.PHONY: test-admin
test-admin:
	docker build -t hermes_frontend_admin_ci src/frontend-admin
	mkdir -p src/frontend-admin/coverage
	chmod 777 src/frontend-admin/coverage
	docker run --rm \
		--env-file config/test/.env.frontend-admin \
		-v $(PWD)/src/frontend-admin/coverage:/app/coverage \
		hermes_frontend_admin_ci \
		python -m pytest tests/ \
			--cov=app \
			--cov-report=xml:/app/coverage/coverage.xml \
			--cov-report=term-missing \
			-q

.PHONY: test-e2e
test-e2e:
	docker compose -f docker-compose.test.yml up -d --build --wait
	docker exec test_backend alembic -c /app/alembic.ini upgrade head
	pip install -q -r tests/e2e/requirements.txt
	FRONTEND_URL=http://localhost:8080 \
	ADMIN_URL=http://localhost:8081 \
	BACKEND_URL=http://localhost:8000 \
		pytest tests/e2e/ --tb=short -q
	$(MAKE) clean-test

.PHONY: test-all
test-all: test test-frontend test-admin

# ── Cleanup ───────────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	docker compose down -v

.PHONY: clean-test
clean-test:
	docker compose -f docker-compose.test.yml down -v

.PHONY: prune
prune:
	docker image prune -f
