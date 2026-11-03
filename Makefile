.PHONY: install dev test test-compile lint fmt typegen e2e

install:
	cd backend && uv sync
	cd compiler && uv sync
	cd frontend && npm ci

dev:
	docker compose up

test:
	cd backend && uv run pytest -m "not compile and not live"
	cd compiler && uv run pytest -m "not compile"
	cd frontend && npm test

# pytest exits 5 when nothing is collected, which is expected until the compile tests land (step 8)
test-compile:
	cd backend && uv run pytest -m compile; code=$$?; [ $$code -eq 5 ] || exit $$code
	cd compiler && uv run pytest -m compile; code=$$?; [ $$code -eq 5 ] || exit $$code

lint:
	cd backend && uv run ruff check && uv run ruff format --check && uv run mypy
	cd compiler && uv run ruff check && uv run ruff format --check && uv run mypy
	cd frontend && npm run lint && npm run typecheck && npm run format:check

fmt:
	cd backend && uv run ruff check --fix && uv run ruff format
	cd compiler && uv run ruff check --fix && uv run ruff format
	cd frontend && npm run format

typegen:
	@echo "typegen needs the FastAPI app (step 2) and openapi-typescript (step 11)" >&2; exit 1

e2e:
	@echo "e2e needs docker-compose (step 14) and Playwright (Phase 2)" >&2; exit 1
